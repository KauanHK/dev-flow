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
