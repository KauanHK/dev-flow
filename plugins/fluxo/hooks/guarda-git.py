"""Hook PreToolUse do fluxo: pede confirmação antes de push e merge arriscados.

Vale só em repositórios com `.claude/fluxo.yml`. Pede confirmação da pessoa
(`permissionDecision: ask`) quando um comando Bash:

- faz `gh pr merge`: o merge é de quem revisa;
- faz `git push` para `git.base` ou `git.producao`, inclusive apagando a branch;
- faz force push (`-f`, `--force*`, `+refspec`) ou `--all`, `--mirror`, `--prune`.

O resto passa sem saída, e a permissão segue o fluxo normal do Claude Code. É uma
grade de proteção, não uma barreira de segurança: a análise do comando é de
melhor esforço e erra para o lado de perguntar.
"""

import json
import os
import re
import shlex
import subprocess
import sys

PONTUACAO = ";&|()"
REDIRECAO = re.compile(r"^\d*(&>|>>?|<<?<?)")
SO_OPERADOR = re.compile(r"^\d*(&>|>>?|<<?<?)$")
PREFIXOS = {"rtk", "proxy", "command", "env", "sudo", "time", "nohup", "exec"}
OPCOES_GIT_COM_VALOR = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
OPCOES_PUSH_COM_VALOR = {"--repo", "-o", "--push-option", "--receive-pack", "--exec"}
PADRAO_PROTEGIDAS = {"main", "master"}


def git(diretorio, *args):
    resultado = subprocess.run(
        ["git", "-C", diretorio, *args],
        capture_output=True,
        text=True,
        timeout=5,
    )
    return resultado.stdout.strip() if resultado.returncode == 0 else ""


def achar_config(diretorio):
    """Caminho do `.claude/fluxo.yml` do repositório, ou None fora do fluxo.

    Numa worktree o arquivo pode não estar versionado; nesse caso vale o da
    worktree principal.
    """
    raizes = [git(diretorio, "rev-parse", "--show-toplevel")]
    comum = git(diretorio, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if comum.endswith("/.git"):
        raizes.append(os.path.dirname(comum))
    for raiz in raizes:
        caminho = os.path.join(raiz, ".claude", "fluxo.yml") if raiz else ""
        if caminho and os.path.isfile(caminho):
            return caminho
    return None


def ler_protegidas(caminho):
    """`git.base` e `git.producao` do fluxo.yml, sem depender de PyYAML."""
    secao = None
    valores = {}
    with open(caminho, encoding="utf-8") as arquivo:
        for linha in arquivo:
            linha = re.sub(r"(^|\s)#.*$", "", linha.rstrip("\n"))
            if not linha.strip():
                continue
            if not linha[0].isspace():
                secao = linha.split(":", 1)[0].strip()
                continue
            achado = re.match(r"\s+(base|producao):\s*(.*)$", linha)
            if secao == "git" and achado:
                valor = achado.group(2).strip().strip("'\"")
                if valor:
                    valores[achado.group(1)] = valor
    return set(valores.values()) or set(PADRAO_PROTEGIDAS)


def tirar_heredocs(comando):
    """Remove o corpo dos heredocs, que é texto (mensagem de commit, por exemplo)."""
    linhas = comando.split("\n")
    saida = []
    fim = None
    for linha in linhas:
        if fim is not None:
            if linha.strip() == fim:
                fim = None
            continue
        saida.append(linha)
        achado = re.search(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1", linha)
        if achado:
            fim = achado.group(2)
    return "\n".join(saida)


def segmentos(comando):
    """Quebra o comando em comandos simples, cada um como lista de palavras.

    Separadores (`;`, `&&`, `|`, subshell) fecham um comando. Redirecionamentos
    saem da lista, para `2>&1` não virar refspec de um push.
    """
    lexer = shlex.shlex(
        tirar_heredocs(comando).replace("\n", " ; "),
        posix=True,
        punctuation_chars=PONTUACAO,
    )
    lexer.whitespace_split = True
    atual = []
    pular_alvo = False
    for palavra in lexer:
        if set(palavra) <= set(PONTUACAO):
            if atual:
                yield atual
            atual = []
            pular_alvo = False
        elif pular_alvo:
            pular_alvo = False
        elif REDIRECAO.match(palavra):
            pular_alvo = bool(SO_OPERADOR.match(palavra))
        else:
            atual.append(palavra)
    if atual:
        yield atual


def sem_prefixos(palavras):
    i = 0
    while i < len(palavras):
        palavra = palavras[i]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", palavra) or palavra in PREFIXOS:
            i += 1
        elif palavra.startswith("-") and i > 0 and palavras[i - 1] in PREFIXOS:
            i += 1
        else:
            break
    return palavras[i:]


def branch_atual(diretorio):
    return git(diretorio, "symbolic-ref", "--quiet", "--short", "HEAD")


def destino_upstream(diretorio):
    upstream = git(diretorio, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    return upstream.split("/", 1)[1] if "/" in upstream else ""


def analisar_push(args, diretorio, protegidas):
    """Motivos para pedir confirmação de um `git push`, ou lista vazia."""
    motivos = []
    posicionais = []
    apagar = False
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in OPCOES_PUSH_COM_VALOR:
            i += 2
            continue
        if arg in ("-n", "--dry-run"):
            return []
        if arg.startswith("--"):
            nome = arg.split("=", 1)[0]
            if nome.startswith("--force"):
                motivos.append("force push")
            elif nome in ("--all", "--branches", "--mirror", "--prune"):
                motivos.append(f"`{nome}` mexe em todas as branches, inclusive as protegidas")
            elif nome == "--delete":
                apagar = True
        elif arg.startswith("-") and len(arg) > 1:
            if "f" in arg[1:]:
                motivos.append("force push")
            if "d" in arg[1:]:
                apagar = True
        else:
            posicionais.append(arg)
        i += 1

    refspecs = posicionais[1:]
    destinos = {}  # branch de destino -> se o push apaga a branch
    if not refspecs:
        for destino in (branch_atual(diretorio), destino_upstream(diretorio)):
            if destino:
                destinos[destino] = False
    for refspec in refspecs:
        if refspec.startswith("+"):
            motivos.append(f"force push (`{refspec}`)")
            refspec = refspec[1:]
        origem, dois_pontos, destino = refspec.partition(":")
        if not dois_pontos:
            destino = origem
        if destino in ("HEAD", "@"):
            destino = branch_atual(diretorio)
        destinos[destino.removeprefix("refs/heads/")] = apagar or (dois_pontos and not origem)

    for destino in sorted(destinos.keys() & protegidas):
        acao = "apaga" if destinos[destino] else "envia direto para"
        motivos.append(f"{acao} a branch protegida `{destino}`, que só recebe PR revisado")
    return motivos


def analisar(comando, cwd):
    motivos = []
    diretorio = cwd
    for palavras in segmentos(comando):
        palavras = sem_prefixos(palavras)
        if not palavras:
            continue
        programa = os.path.basename(palavras[0])

        if programa in ("cd", "pushd") and len(palavras) > 1:
            diretorio = os.path.normpath(os.path.join(diretorio, os.path.expanduser(palavras[1])))
        elif programa in ("bash", "sh", "zsh") and "-c" in palavras:
            interno = palavras[palavras.index("-c") + 1 :]
            if interno:
                motivos += analisar(interno[0], diretorio)
        elif programa == "gh" and (
            palavras[1:3] == ["pr", "merge"]
            or palavras[1:2] == ["api"] and any(p.endswith("/merge") for p in palavras)
        ):
            if achar_config(diretorio):
                motivos.append("merge de PR, que é decisão de quem revisa")
        elif programa == "git":
            alvo = diretorio
            i = 1
            while i < len(palavras) and palavras[i].startswith("-"):
                if palavras[i] == "-C" and i + 1 < len(palavras):
                    alvo = os.path.normpath(os.path.join(alvo, os.path.expanduser(palavras[i + 1])))
                i += 2 if palavras[i] in OPCOES_GIT_COM_VALOR else 1
            if i < len(palavras) and palavras[i] == "push":
                config = achar_config(alvo)
                if config:
                    motivos += analisar_push(palavras[i + 1 :], alvo, ler_protegidas(config))
    return motivos


def main():
    entrada = json.load(sys.stdin)
    comando = (entrada.get("tool_input") or {}).get("command") or ""
    if not re.search(r"\b(push|merge)\b", comando):
        return
    cwd = entrada.get("cwd") or os.getcwd()
    try:
        motivos = analisar(comando, cwd)
    except Exception as erro:  # comando que não deu para analisar: pergunte
        motivos = [f"não consegui analisar o comando ({erro})"]
    if not motivos:
        return
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": "fluxo: " + "; ".join(dict.fromkeys(motivos)) + ".",
                }
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
