"""Testes do hook guarda-git do plugin fluxo.

Rode da raiz do repositório: `python3 -m unittest discover testes`.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HOOK = os.path.join(
    os.path.dirname(__file__), "..", "plugins", "fluxo", "hooks", "guarda-git.py"
)

FLUXO_YML = """\
jira:
  projeto: DES                 # comentário
git:
  base: dev                    # de onde nasce a branch
  producao: main
specs:
  dir: docs
"""


def sh(cwd, *args):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


def rodar_hook(comando, cwd):
    entrada = {"cwd": cwd, "tool_name": "Bash", "tool_input": {"command": comando}}
    saida = subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(entrada),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    if not saida.strip():
        return None
    return json.loads(saida)["hookSpecificOutput"]


class GuardaGit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        raiz = cls.tmp.name
        cls.remoto = os.path.join(raiz, "remoto.git")
        cls.repo = os.path.join(raiz, "repo")
        cls.fora = os.path.join(raiz, "fora")
        sh(raiz, "git", "init", "-q", "--bare", cls.remoto)
        for caminho in (cls.repo, cls.fora):
            sh(raiz, "git", "init", "-q", "-b", "main", caminho)
            sh(caminho, "git", "config", "user.email", "t@t")
            sh(caminho, "git", "config", "user.name", "t")
            sh(caminho, "git", "commit", "-q", "--allow-empty", "-m", "inicio")
        os.makedirs(os.path.join(cls.repo, ".claude"))
        with open(os.path.join(cls.repo, ".claude", "fluxo.yml"), "w") as arquivo:
            arquivo.write(FLUXO_YML)
        sh(cls.repo, "git", "remote", "add", "origin", cls.remoto)
        sh(cls.repo, "git", "push", "-q", "-u", "origin", "main")
        sh(cls.repo, "git", "switch", "-q", "-c", "dev")
        sh(cls.repo, "git", "push", "-q", "-u", "origin", "dev")
        sh(cls.repo, "git", "switch", "-q", "-c", "feat/conta-01-x")
        sh(cls.repo, "git", "push", "-q", "-u", "origin", "feat/conta-01-x")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def no_branch(self, branch):
        sh(self.repo, "git", "switch", "-q", branch)
        self.addCleanup(sh, self.repo, "git", "switch", "-q", "feat/conta-01-x")

    def assertPergunta(self, comando, trecho="", cwd=None):
        decisao = rodar_hook(comando, cwd or self.repo)
        self.assertIsNotNone(decisao, f"devia perguntar: {comando}")
        self.assertEqual(decisao["permissionDecision"], "ask")
        self.assertIn(trecho, decisao["permissionDecisionReason"])

    def assertPassa(self, comando, cwd=None):
        self.assertIsNone(rodar_hook(comando, cwd or self.repo), f"devia passar: {comando}")

    def escrever_config(self, texto):
        with open(os.path.join(self.repo, ".claude", "fluxo.yml"), "w") as arquivo:
            arquivo.write(texto)

    def usar_config(self, texto):
        """Troca o fluxo.yml do repositório até o fim do teste."""
        self.escrever_config(texto)
        self.addCleanup(self.escrever_config, FLUXO_YML)

    def test_push_da_branch_da_spec_passa(self):
        self.assertPassa("git push -u origin feat/conta-01-x")
        self.assertPassa("git push")
        self.assertPassa("git push origin HEAD")
        self.assertPassa("rtk git push origin feat/conta-01-x 2>&1 | tail -3")

    def test_push_para_base_ou_producao_pergunta(self):
        self.assertPergunta("git push origin dev", "`dev`")
        self.assertPergunta("git push origin main", "`main`")
        self.assertPergunta("git push origin HEAD:dev", "`dev`")
        self.assertPergunta("git push origin feat/conta-01-x:refs/heads/main", "`main`")
        self.assertPergunta("git add . && git commit -m 'x' && git push origin dev")

    def test_push_sem_refspec_na_base_pergunta(self):
        self.no_branch("dev")
        self.assertPergunta("git push", "`dev`")
        self.assertPergunta("git push origin 2>&1", "`dev`")
        self.assertPergunta("git push origin HEAD", "`dev`")

    def test_apagar_branch_protegida_pergunta(self):
        self.assertPergunta("git push origin :dev", "apaga")
        self.assertPergunta("git push origin --delete main", "apaga")
        self.assertPassa("git push origin --delete feat/conta-01-x")

    def test_worktree_do_lote_usa_a_config_do_checkout_principal(self):
        # O /fluxo:lote cria as worktrees em .claude/worktrees/<id>; o fluxo.yml
        # deste repositório não é versionado, então só existe no checkout principal.
        worktree = os.path.join(self.repo, ".claude", "worktrees", "conta-02")
        sh(self.repo, "git", "worktree", "add", "-q", "-b", "feat/conta-02-y", worktree, "dev")
        self.addCleanup(sh, self.repo, "git", "branch", "-q", "-D", "feat/conta-02-y")
        self.addCleanup(sh, self.repo, "git", "worktree", "remove", "--force", worktree)
        self.assertFalse(os.path.exists(os.path.join(worktree, ".claude", "fluxo.yml")))
        self.assertPassa("git push -u origin feat/conta-02-y", cwd=worktree)
        self.assertPergunta("git push origin dev", "`dev`", cwd=worktree)
        self.assertPergunta("cd .claude/worktrees/conta-02 && git push origin HEAD:main", "`main`")
        self.assertPergunta("git -C .claude/worktrees/conta-02 push origin dev", "`dev`")
        self.assertPassa("cd .claude/worktrees/conta-02 && git push")

    def test_push_para_protegida_em_lista_inline_pergunta(self):
        self.usar_config(
            "git:\n"
            "  base: dev\n"
            "  producao: main\n"
            "  protegidas: ['staging', \"hml\"]   # entre a dev e a main\n"
        )
        self.assertPergunta(
            "git push origin staging", "envia direto para a branch protegida `staging`"
        )
        self.assertPergunta("git push origin HEAD:hml", "`hml`")
        self.assertPergunta("git push origin dev", "`dev`")
        self.assertPergunta("git push origin main", "`main`")
        self.assertPassa("git push origin feat/conta-01-x")
        self.assertPassa("git push origin staging-velha")

    def test_push_para_protegida_em_lista_de_bloco_pergunta(self):
        self.usar_config(
            "git:\n"
            "  base: dev\n"
            "  protegidas:            # além da base e da produção\n"
            "    - staging\n"
            "\n"
            "    - 'release/*'        # uma por versão\n"
            "  producao: main\n"
            "specs:\n"
            "  - fora\n"
        )
        self.assertPergunta("git push origin staging", "`staging`")
        self.assertPergunta("git push origin feat/conta-01-x:release/1.2", "`release/1.2`")
        self.assertPergunta("git push origin main", "`main`")
        self.assertPassa("git push origin fora")
        self.assertPassa("git push origin feat/conta-01-x")

    def test_lista_de_bloco_no_mesmo_recuo_da_chave(self):
        self.usar_config("git:\n  base: dev\n  protegidas:\n  - staging\n  producao: main\n")
        self.assertPergunta("git push origin staging", "`staging`")
        self.assertPergunta("git push origin main", "`main`")

    def test_padrao_glob_casa_so_o_que_deve(self):
        self.usar_config("git:\n  base: dev\n  producao: main\n  protegidas: [release/*, hml?]")
        self.assertPergunta("git push origin release/1.2", "`release/1.2`")
        self.assertPergunta("git push origin HEAD:refs/heads/release/2.0", "`release/2.0`")
        self.assertPergunta("git push origin hml2", "`hml2`")
        self.assertPassa("git push origin releases")
        self.assertPassa("git push origin release")
        self.assertPassa("git push origin feat/release/1.2")
        self.assertPassa("git push origin hml")

    def test_apagar_protegida_pergunta(self):
        self.usar_config("git:\n  base: dev\n  producao: main\n  protegidas: [staging, release/*]")
        self.assertPergunta("git push origin :staging", "apaga a branch protegida `staging`")
        self.assertPergunta("git push origin --delete staging", "apaga")
        self.assertPergunta(
            "git push -d origin release/1.2", "apaga a branch protegida `release/1.2`"
        )
        self.assertPassa("git push origin --delete feat/conta-01-x")

    def test_protegidas_vazia_nao_muda_nada(self):
        for vazia in ("  protegidas: []\n", "  protegidas:\n", "  protegidas:   # nenhuma\n"):
            with self.subTest(vazia=vazia):
                self.usar_config(
                    "git:\n  base: dev\n  producao: main\n" + vazia + "specs:\n  dir: docs\n"
                )
                self.assertPergunta("git push origin dev", "`dev`")
                self.assertPergunta("git push origin main", "`main`")
                self.assertPassa("git push origin master")
                self.assertPassa("git push origin staging")
                self.assertPassa("git push origin feat/conta-01-x")

    def test_protegida_com_valor_unico(self):
        self.usar_config("git:\n  protegidas: 'staging'   # só uma\n")
        self.assertPergunta("git push origin staging", "`staging`")
        # sem base nem produção, `main` e `master` continuam protegidas
        self.assertPergunta("git push origin main", "`main`")
        self.assertPergunta("git push origin master", "`master`")
        self.assertPassa("git push origin feat/conta-01-x")

    def test_force_push_pergunta(self):
        self.assertPergunta("git push --force-with-lease", "force push")
        self.assertPergunta("git push -f origin feat/conta-01-x", "force push")
        self.assertPergunta("git push origin +feat/conta-01-x", "force push")
        self.assertPergunta("git push --mirror", "--mirror")

    def test_dry_run_passa(self):
        self.assertPassa("git push -n origin dev")

    def test_merge_de_pr_pergunta(self):
        self.assertPergunta("gh pr merge 12 --squash", "merge")
        self.assertPergunta("rtk gh pr merge 12", "merge")
        self.assertPergunta("gh api -X PUT repos/o/r/pulls/12/merge", "merge")
        self.assertPassa("gh pr view 12")

    def test_git_C_e_cd_mudam_o_repositorio(self):
        self.assertPergunta(f"git -C {self.repo} push origin dev", cwd=self.fora)
        self.assertPergunta(f"cd {self.repo} && git push origin main", cwd=self.fora)
        self.assertPassa(f"cd {self.fora} && git push origin main")

    def test_subshell_e_bash_c(self):
        self.assertPergunta("echo $(git push origin dev)")
        self.assertPergunta("bash -c 'git push origin dev'")

    def test_texto_de_heredoc_nao_conta(self):
        comando = (
            "git commit -q -m \"$(cat <<'EOF'\n"
            "docs: explica que git push origin main não pode\n"
            "EOF\n"
            ")\" && git push"
        )
        self.assertPassa(comando)

    def test_fora_do_fluxo_nada_muda(self):
        self.assertPassa("git push origin main", cwd=self.fora)
        self.assertPassa("gh pr merge 3", cwd=self.fora)

    def test_comando_sem_push_nem_merge_passa(self):
        self.assertPassa("git status && git log -3")


if __name__ == "__main__":
    unittest.main()
