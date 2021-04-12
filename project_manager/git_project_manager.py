import subprocess
from pathlib import Path

from project_manager.common_ps_commands import run_command


def write_gitignore_contents(proj_dir: Path, gitignore_text: str):
    output_file = (proj_dir / ".gitignore").as_posix()
    with open(output_file, "w") as f:
        f.write(gitignore_text)
    assert Path(output_file).exists()


def init_dir(dir_path):
    git_cmds = ['git', 'init']
    rc = run_command(git_cmds, cwd=dir_path, text=True)
    return rc


def add_repo(dir_path, repo_name, uname=""):
    assert uname
    repo_to_add = f"git@github.com:{uname}/{repo_name}.git"
    git_cmds = ['git', 'remote', 'add', 'origin', repo_to_add]
    with subprocess.Popen(git_cmds, stdout=subprocess.PIPE, text=True, cwd=dir_path) as p:
        output, errors = p.communicate()
    print(output)
    print(errors)