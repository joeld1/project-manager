import os
import subprocess
import sys
from pathlib import Path

try:
    import stringcase
    import gy
    import toml
except Exception as e:
    print(e)

from project_manager.common_ps_commands import chain_and_execute_commands
from project_manager.conda_env_manager import activate_conda_env
from project_manager.git_project_manager import write_gitignore_contents
from project_manager.poetry_project_manager import get_poetry_project_dir, init_poetry_project, \
    get_poetry_project_env_name


def create_proj_name(name):
    clean_proj_name = stringcase.snakecase(name)
    return clean_proj_name


def find_env_and_add_dependency(file_importing_from: str, dependency: str):
    old_path = os.getcwd()
    poetry_proj_dir = get_poetry_project_dir(file_importing_from)
    env_name = get_poetry_project_env_name(file_importing_from)
    os.chdir(poetry_proj_dir)
    act_env_str = activate_conda_env(env_name, return_cmd=True)
    poetry_cmd = f"poetry add {dependency}"
    rc = chain_and_execute_commands([act_env_str, poetry_cmd], text=True, shell=True, cwd=poetry_proj_dir)
    os.chdir(old_path)
    return rc


def get_gitignore_contents():
    git_ignores_to_add = ['dropbox', 'jetbrains', 'jupyternotebooks', 'macos', 'microsoftoffice', 'python',
                          'sublimetext', 'virtualenv', 'visualstudio', 'visualstudiocode']
    gy_cmd = ["gy", "generate"] + git_ignores_to_add
    p_gy = subprocess.Popen(gy_cmd, stdout=subprocess.PIPE, text=True)
    output = p_gy.communicate()[0]
    return output


def create_gitignores_in_repos(all_python_dirs):
    gitignore_text = get_gitignore_contents()
    for p in all_python_dirs:
        write_gitignore_contents(p, gitignore_text)


def add_git_ignore_to_project(path_to_proj):
    gitignore_text = get_gitignore_contents()
    write_gitignore_contents(Path(path_to_proj), gitignore_text=gitignore_text)


if __name__ == "__main__":
    env_name = "docker_sandbox"
    clean_env_name = create_proj_name(env_name)
    rc = init_poetry_project(clean_env_name, proj_dir="..", python_version="3.9")
    assert rc == 0
    print(rc)
    sys.exit()
