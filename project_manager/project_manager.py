import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

try:
    import stringcase
    import gy
    import toml
except Exception as e:
    print("Manually install optional packages")
    print(e)


class ProjectManager:

    @staticmethod
    def create_proj_name(name:str)->str:
        """

        This reformats names such that they are in snake case

        :param str: name:
        :return:
        """
        clean_proj_name = stringcase.snakecase(name)
        return clean_proj_name

    @staticmethod
    def find_env_and_add_dependency(file_importing_from: str, dependency: str):
        dir_containing_pyproject_toml = PoetryProjectManager.get_poetry_project_dir(file_importing_from)
        poetry_proj_conda_env_name = PoetryProjectManager.get_poetry_proj_env_name_from_poetry_toml_for_py_file(file_importing_from)  # gets env from poetry.toml
        rc = PoetryProjectManager.add_dependency_to_pyproject_toml(dir_containing_pyproject_toml, poetry_proj_conda_env_name, dependency)
        return rc

    @staticmethod
    def get_gitignore_contents():
        git_ignores_to_add = ['dropbox', 'jetbrains', 'jupyternotebooks', 'macos', 'microsoftoffice', 'python',
                              'sublimetext', 'virtualenv', 'visualstudio', 'visualstudiocode']
        gy_cmd = ["gy", "generate"] + git_ignores_to_add
        p_gy = subprocess.Popen(gy_cmd, stdout=subprocess.PIPE, text=True)
        output = p_gy.communicate()[0]
        return output

    @staticmethod
    def create_gitignores_in_repos(all_python_dirs):
        gitignore_text = ProjectManager.get_gitignore_contents()
        for p in all_python_dirs:
            GitProjectManager.write_gitignore_contents(p, gitignore_text)

    @staticmethod
    def add_git_ignore_to_project(path_to_proj):
        gitignore_text = ProjectManager.get_gitignore_contents()
        GitProjectManager.write_gitignore_contents(Path(path_to_proj), gitignore_text=gitignore_text)


class PoetryProjectManager:

    @staticmethod
    def search_for_toml_files(filepath:str, toml_pattern:str):
        dir_containing_toml = Path(filepath)
        if dir_containing_toml.is_file():
            dir_containing_toml = dir_containing_toml.parent
        toml_paths = list(dir_containing_toml.glob(toml_pattern))
        return dir_containing_toml, toml_paths

    @staticmethod
    def get_poetry_project_dir(filepath_importing_from:str, toml_pattern="*pyproject.toml"):
        """
        This recursively finds a pyproject.toml from a given filepath.

        If the filepath is a file it'll look at sibling files for a toml file, if it's a director it'll look within
        its contents for a pyproject.toml file. If nothing is found, it'll go up 1 folder and restart the search and
        repeat the process until a toml pattern is found

        :param filepath_importing_from:
        :param toml_pattern:
        :return:
        """
        # TODO: Find out how to determine if is poetry proj, or regular python proj (i.e. requirements.txt)
        path, toml_paths = PoetryProjectManager.search_for_toml_files(filepath_importing_from, toml_pattern)
        if not toml_paths:
            return PoetryProjectManager.get_poetry_project_dir(path.parent.as_posix())
        else:
            return path.as_posix()


    @staticmethod
    def get_poetry_toml(path:str):
        """
        This searches for a poetry.toml file that is a sibling of the given path. It recursively searches parent
        paths for a parent that contains a poetry.toml file.
        :param path:
        :return:
        """
        toml_pattern = "*poetry.toml"
        poetry_proj_dir = PoetryProjectManager.get_poetry_project_dir(path, toml_pattern=toml_pattern)
        cur_poetry_file = Path(poetry_proj_dir) / toml_pattern.replace("*", "")
        return cur_poetry_file

    @staticmethod
    def get_pyproject_toml(path:str):
        """
        This searches for a pypoetry.toml file that is a sibling of the given path. It recursively searches parent
        paths for a parent that contains a poetry.toml file.
        :param path:
        :return:
        """
        toml_pattern = "pypoetry.toml"
        dir_containing_pyproject_toml = PoetryProjectManager.get_poetry_project_dir(path, toml_pattern=toml_pattern)
        path_to_toml = Path(dir_containing_pyproject_toml) / toml_pattern
        return path_to_toml

    @staticmethod
    def get_poetry_module_dependencies(poetry_proj_py_filepath: str):
        """
        Finds gets the poetry.dependencies (in pyproject.toml) that a py file in a poetry project is associated with
        :param poetry_proj_py_filepath:
        :return:
        """
        path_to_toml = PoetryProjectManager.get_pyproject_toml(poetry_proj_py_filepath)
        dependencies = CommonPSCommands.read_toml(path_to_toml, 'tool.poetry.dependencies')
        return dependencies

    @staticmethod
    def get_import_error_dependencies(e):
        path_to_loaded_module = CommonPSCommands.get_traceback_file_origin(e)
        deps = PoetryProjectManager.get_poetry_module_dependencies(path_to_loaded_module)
        return deps

    @staticmethod
    def add_poetry_package_from_exception(file_importing_from: str, except_obj: ModuleNotFoundError,
                                          ignore_verion=True):
        assert isinstance(except_obj, ModuleNotFoundError)
        dependency = PoetryProjectManager.get_missing_poetry_dependency(except_obj, ignore_verion=ignore_verion)
        break_stmnt = input(f"poetry add {dependency}? [q to break]")
        if break_stmnt.lower() == "q":
            return
        env_name = PoetryProjectManager.get_poetry_proj_env_name_from_poetry_toml_for_py_file(file_importing_from)
        rc = PoetryProjectManager.add_poetry_package(file_importing_from, env_name, dependency)
        return rc

    @staticmethod
    def add_poetry_package(file_importing_from: str, env_name: str, dependency: str):
        poetry_proj_dir = PoetryProjectManager.get_poetry_project_dir(file_importing_from)
        rc = PoetryProjectManager.add_dependency_to_pyproject_toml(poetry_proj_dir, env_name, dependency)
        return rc

    @staticmethod
    def add_dependency_to_pyproject_toml(dir_containing_pyproject_toml:str, poetry_proj_conda_env_name:str, dependency:str):
        poetry_cmd = f"poetry add {dependency}"
        rc = PoetryProjectManager.execute_poetry_cmd(poetry_cmd, dir_containing_pyproject_toml, poetry_proj_conda_env_name)
        return rc

    @staticmethod
    def execute_poetry_cmd(poetry_cmd:str, poetry_proj_dir, env_name,**kwargs):
        old_path = os.getcwd()
        os.chdir(poetry_proj_dir)
        act_env_str = CondaEnvManager.activate_conda_env(env_name, return_cmd=True)
        kwargs['text'] = True
        kwargs['shell'] = True
        kwargs['cwd'] = poetry_proj_dir
        rc = CommonPSCommands.chain_and_execute_commands([act_env_str, poetry_cmd], **kwargs)
        os.chdir(old_path)
        return rc

    @staticmethod
    def execute_poetry_init(env_name: str, poetry_proj_dir: str = None):
        if poetry_proj_dir is None:
            poetry_proj_dir = Path(".").resolve().as_posix()
        poetry_cmd = "poetry init --no-interaction"
        rc = PoetryProjectManager.execute_poetry_cmd(poetry_cmd, poetry_proj_dir, env_name)
        return rc

    @staticmethod
    def get_poetry_config_virtualenv_path_cmd_for_conda_env(clean_env_name):
        conda_env_path = CondaEnvManager.get_path_to_conda_env(clean_env_name)
        poetry_cmd = f"poetry config virtualenvs.path {conda_env_path} --local"
        return poetry_cmd

    @staticmethod
    def link_poetry_proj_with_conda_env(clean_env_name,**kwargs):
        poetry_cmd = PoetryProjectManager.get_poetry_config_virtualenv_path_cmd_for_conda_env(clean_env_name)
        rc = PoetryProjectManager.execute_poetry_cmd(poetry_cmd,poetry_proj_dir=os.getcwd(),env_name=clean_env_name, **kwargs)

        poetry_cmd = "poetry config virtualenvs.create 0 --local"
        rc = PoetryProjectManager.execute_poetry_cmd(poetry_cmd,poetry_proj_dir=os.getcwd(),env_name=clean_env_name, **kwargs)

        poetry_cmd = "poetry config virtualenvs.in-project 0 --local"
        rc = PoetryProjectManager.execute_poetry_cmd(poetry_cmd,poetry_proj_dir=os.getcwd(),env_name=clean_env_name, **kwargs)

        assert rc == 0
        print(f"Successfully linked {clean_env_name} to its conda env!")
        return rc


    @staticmethod
    def create_poetry_proj(clean_env_name, proj_name=None, proj_dir=".", **kwargs):
        old_path = os.getcwd()
        proj_path = Path(proj_dir).expanduser().resolve()
        try:
            assert proj_path.exists()
            os.chdir(proj_path.as_posix())
        except Exception as e:
            print("Unable to cd into folder since it doesn't exist! Will create proj in current directory")
            os.chdir(old_path)
        try:
            if proj_name:
                path_to_proj = (proj_path / proj_name)
                assert not path_to_proj.exists()
            else:
                path_to_proj = (proj_path / clean_env_name)
        except Exception as e:
            print("Unable to create poetry project since directory or environment already exists!")
            return -1, Path("..")

        rc = PoetryProjectManager.create_poetry_project(clean_env_name, proj_name, **kwargs)
        assert rc == 0
        rc = PoetryProjectManager.link_poetry_proj_with_conda_env(clean_env_name)
        assert rc == 0
        os.chdir(old_path)
        return rc, path_to_proj

    @staticmethod
    def create_poetry_project(clean_env_name, proj_name,**kwargs):
        if proj_name:
            poetry_cmd = f"poetry new {proj_name}"
        else:
            poetry_cmd = f"poetry new {clean_env_name}"
        rc = PoetryProjectManager.execute_poetry_cmd(poetry_cmd, poetry_proj_dir=os.getcwd(), env_name=clean_env_name, **kwargs)
        return rc

    @staticmethod
    def get_conda_activate_str(clean_env_name):
        try:
            conda_envs_and_kernels_made = not CondaEnvManager.conda_and_kernel_name_available(clean_env_name, both=True)
            assert conda_envs_and_kernels_made
            act_env_str = CondaEnvManager.activate_conda_env(clean_env_name, return_cmd=True)
        except Exception as e:
            print(e)
            print("Create the conda environment and register the jupyter kernel before retrying this method!")
            raise e
        return act_env_str

    @staticmethod
    def init_poetry_project(clean_env_name, proj_name=None, proj_dir=".", python_version="3.9"):
        cur_dir = os.getcwd()
        proj_dir_path = Path(proj_dir).expanduser().resolve().as_posix()

        if proj_name is None:
            proj_name = clean_env_name
        proj_available = CondaEnvManager.conda_and_kernel_name_available(clean_env_name, both=True)
        if proj_available:
            print("it's available! Now making conda env!")
            CondaEnvManager.create_and_init_conda_env(clean_env_name, python_version)
            # make conda env before this step
            rc, path_to_proj = PoetryProjectManager.create_poetry_proj(clean_env_name, proj_name=proj_name,
                                                                       proj_dir=proj_dir_path)
            os.chdir(path_to_proj)
            assert rc == 0
            rc = GitProjectManager.init_dir(path_to_proj)
            assert rc == 0
            os.chdir(cur_dir)
            return rc
        else:
            print("Project is not available!")

    @staticmethod
    def find_poetry_toml_and_get_virtual_env_path(path:str):
        cur_poetry_file = PoetryProjectManager.get_poetry_toml(path)
        path_to_env = PoetryProjectManager.get_virtualenv_path_from_poetry_toml(cur_poetry_file)
        return path_to_env

    @staticmethod
    def get_virtualenv_path_from_poetry_toml(cur_poetry_file:str)->Path:
        """
        This reads a poetry.toml file and gets the virtualenv path found in the poetry.toml file

        :param cur_poetry_file:
        :return:
        """
        virtualenvs_path = CommonPSCommands.read_toml(cur_poetry_file, 'virtualenv')
        path_to_env = Path(virtualenvs_path['path'])
        return path_to_env

    @staticmethod
    def get_poetry_proj_env_name_from_poetry_toml_for_py_file(poetry_proj_py_filepath:str):
        """
        This searches for the poetry.toml file a .py file (in a poetry proj) is associated with.

        :param poetry_proj_py_filepath:
        :return:
        """
        path_to_env = PoetryProjectManager.find_poetry_toml_and_get_virtual_env_path(poetry_proj_py_filepath)
        env_name = path_to_env.name
        return env_name

    @staticmethod
    def get_missing_poetry_dependency(caught_exception, ignore_verion=True):
        dep_name = caught_exception.name
        if not ignore_verion:
            deps = PoetryProjectManager.get_import_error_dependencies(caught_exception)
        else:
            deps = {dep_name: dep_name}
        if not ignore_verion:
            dep_version = deps.get(dep_name)
            dependency = f'{dep_name}=="{dep_version}"'
        else:
            dependency = dep_name
        return dependency


class CommonPSCommands:

    @staticmethod
    def run_command(cmd_args, *args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=None, return_process=False,
                    **kwargs):
        if isinstance(cmd_args, str):
            cmd_args = [cmd_args]
        p = subprocess.Popen(cmd_args, *args, stdin=stdin, stdout=stdout, text=text, **kwargs)
        if return_process:
            return p
        while True:
            cur_status = p.poll()
            if cur_status:  # 0s won't be printed
                print(cur_status)
            output = p.stdout.readline()
            if (output == '') and p.poll() is not None:  # might be redundant
                break
            if output:
                print(output.strip())
            if cur_status == 0:
                print(f"Success!\nFinished running {cmd_args}")
                break
        rc = p.poll()
        return rc

    @staticmethod
    def chain_and_execute_commands(cmds, *args, **kwargs):
        cmd = " && ".join(cmds)
        kwargs['shell'] = True
        kwargs['text'] = True
        rc = CommonPSCommands.run_command(cmd, *args, **kwargs)
        return rc

    @staticmethod
    def get_python_dirs():
        p = Path(".")
        current_files = list(p.iterdir())
        all_python_dirs = list(
            filter(lambda x: x.is_dir() and ("." not in str(x)) and (not str(x).startswith("__")), current_files))
        return all_python_dirs

    @staticmethod
    def get_traceback_file_origin(e):
        path_to_loaded_module = e.__traceback__.tb_next.tb_frame.f_locals['__file__']
        return path_to_loaded_module

    @staticmethod
    def read_toml(path_to_toml, start_line="tool.poetry.dependencies"):
        """
        Reads for toml file using open context manager in order to reduce 3rd party toml parser deps

        :param path_to_toml:
        :param start_line:
        :return:
        """
        # TODO: This might not work if a dependency spans multiple lines
        toml_dict = {}
        save_lines = False
        with open(path_to_toml, "r") as f:
            all_lines = f.readlines()
            for i, l in enumerate(all_lines):
                cur_line = l.strip()
                start_line_found = start_line in cur_line
                if start_line_found:
                    save_lines = True
                if (not cur_line) and save_lines:
                    save_lines = False
                if (cur_line and save_lines) and (not start_line_found):
                    print(cur_line)
                    key, value = cur_line.split("=")
                    key = key.strip()
                    value = value.replace('"', "").strip()
                    toml_dict[key] = value
        return toml_dict

    @staticmethod
    def echo_yes(return_cmd=False):
        # TODO: Refactor for different platforms
        #     cur_os = platform.system()
        #     if cur_os == "Darwin":

        y_cmd = "yes"
        if return_cmd:
            return f"echo {y_cmd} | "
        p1 = subprocess.Popen(["echo", y_cmd], stdout=subprocess.PIPE, text=True)
        return p1


class CondaEnvManager:

    @staticmethod
    def get_env_info_from_lines(all_lines):
        all_env_names = []
        all_env_paths = []
        for l in all_lines:
            env_name, *env_path = l.split()
            all_env_names.append(env_name)
            all_env_paths.append(env_path)
        return all_env_names, all_env_paths

    @staticmethod
    def get_conda_envs():
        conda_cmd = ["conda", "info", "--envs"]
        with subprocess.Popen(conda_cmd, stdout=subprocess.PIPE, text=True) as p:
            output, errors = p.communicate()

        all_lines = output.replace(r"*", " ").split("\n")
        all_lines = list(filter(None, all_lines))  # remove empty strs
        all_lines = list(filter(lambda x: "#" not in x, all_lines))  # remove comments
        env_names, env_paths = CondaEnvManager.get_env_info_from_lines(all_lines)
        return env_names, env_paths

    @staticmethod
    def get_kernel_specs():
        kernel_cmd = ["jupyter", "kernelspec", "list"]
        with subprocess.Popen(kernel_cmd, stdout=subprocess.PIPE, text=True) as p:
            output, errors = p.communicate()

        all_lines = output.strip().replace(r"*", " ").split("\n")
        all_lines = [l.strip() for l in all_lines if ("Available kernels" not in l)]
        kernel_names, kernel_paths = CondaEnvManager.get_env_info_from_lines(all_lines)
        return kernel_names, kernel_paths

    @staticmethod
    def conda_and_kernel_name_available(clean_proj_name, both=False):
        kernel_names, _ = CondaEnvManager.get_kernel_specs()
        conda_names, _ = CondaEnvManager.get_conda_envs()

        kernel_exists = (clean_proj_name in kernel_names)
        conda_env_exists = (clean_proj_name in conda_names)
        if both:
            return (not conda_env_exists) and (not kernel_exists)
        else:
            return (not conda_env_exists), (not kernel_exists)

    @staticmethod
    def get_path_to_conda_env(env_name):
        conda_base = CondaEnvManager.get_conda_base()
        path_to_env = (Path(conda_base) / f"envs/{env_name}").resolve().as_posix()
        return path_to_env

    @staticmethod
    def reset_conda_channel_priority(act_env_str, *args, **kwargs):
        cmd = "conda config --set channel_priority false"
        rc = CommonPSCommands.chain_and_execute_commands([act_env_str, cmd], *args, **kwargs)
        return rc

    @staticmethod
    def upgrade_pip(act_env_str, *args, **kwargs):
        yes = CommonPSCommands.echo_yes(True)
        cmd = yes + "python -m pip install --upgrade pip setuptools wheel"
        rc = CommonPSCommands.chain_and_execute_commands([act_env_str, cmd], *args, **kwargs)
        return rc

    @staticmethod
    def install_ipykernel(act_env_str, *args, **kwargs):
        yes = CommonPSCommands.echo_yes(True)
        cmd = yes + "conda install notebook ipykernel"
        rc = CommonPSCommands.chain_and_execute_commands([act_env_str, cmd], *args, **kwargs)
        return rc

    @staticmethod
    def add_conda_forge_priority(act_env_str, *args, **kwargs):
        cmd = "conda config --add channels conda-forge"
        rc = CommonPSCommands.chain_and_execute_commands([act_env_str, cmd], *args, **kwargs)
        if rc == 0:
            cmd = "conda config --set channel_priority strict"
            rc = CommonPSCommands.chain_and_execute_commands([act_env_str, cmd], *args, **kwargs)
            return rc
        else:
            return rc

    @staticmethod
    def register_kernel(env_name, *args, **kwargs):
        act_env_str = CondaEnvManager.activate_conda_env(env_name, return_cmd=True)
        cmd = f"ipython kernel install --user --name {env_name} --display-name {env_name}"
        rc = CommonPSCommands.chain_and_execute_commands([act_env_str, cmd], *args, **kwargs)
        return rc

    @staticmethod
    def create_conda_env(env_name, python_version):
        p0 = CommonPSCommands.echo_yes(return_cmd=False)
        python_version_str = f"python={python_version}"
        args = ["conda", "create", "-n", env_name, python_version_str]
        rc = CommonPSCommands.run_command(args, stdin=p0.stdout, text=True)
        return rc

    @staticmethod
    def init_prev_made_conda_env(env_name):
        act_env = CondaEnvManager.activate_conda_env(env_name, return_cmd=True)
        rc = CondaEnvManager.reset_conda_channel_priority(act_env)
        assert rc == 0
        rc = CondaEnvManager.upgrade_pip(act_env)
        assert rc == 0
        rc = CondaEnvManager.install_ipykernel(act_env)
        assert rc == 0
        rc = CondaEnvManager.add_conda_forge_priority(act_env)
        assert rc == 0
        rc = CondaEnvManager.register_kernel(env_name)
        assert rc == 0
        return rc

    @staticmethod
    def uninstall_kernel(kernel_name: str = ""):
        try:
            kernel_names, _ = CondaEnvManager.get_kernel_specs()
            assert kernel_name in kernel_names
        except Exception as e:
            print(f"Kernel {kernel_name!r} does not exist!")
        kernel_cmd = ["jupyter", "kernelspec", "uninstall", kernel_name, '-y']
        y = CommonPSCommands.echo_yes(return_cmd=True)
        kernel_cmd_str = " ".join(kernel_cmd)
        cmd = y + kernel_cmd_str
        rc = CommonPSCommands.run_command([cmd], text=True, shell=True)
        return rc

    @staticmethod
    def uninstall_conda_env(conda_env_name: str = ""):
        try:
            kernel_names, _ = CondaEnvManager.get_conda_envs()
            assert conda_env_name in kernel_names
        except Exception as e:
            print(f"Conda {conda_env_name!r} does not exist!")
        conda_cmd = ["conda", "env", "remove", '-n', conda_env_name]
        rc = CommonPSCommands.run_command(conda_cmd, text=True)
        return rc

    @staticmethod
    def uninstall_conda_and_kernel(conda_env_name: str = "", kernel_name: str = ""):
        if (not conda_env_name) and (not kernel_name):
            print("Please specify the env name and kernel name!")
            return -1
        if conda_env_name and (not kernel_name):
            kernel_name = conda_env_name
        if kernel_name and (not conda_env_name):
            conda_env_name = kernel_name

        rc1 = CondaEnvManager.uninstall_kernel(kernel_name)
        rc2 = CondaEnvManager.uninstall_conda_env(conda_env_name)
        if rc1 == rc2:
            return rc1
        else:
            return rc1, rc2

    @staticmethod
    def uninstall_conda_envs_and_kernels(conda_env_names):
        for env in conda_env_names:
            print(env)
            CondaEnvManager.uninstall_conda_and_kernel(env, env)
            print()

    @staticmethod
    def get_conda_base():
        echo_cmds = ['conda', 'info', '--base']
        p = CommonPSCommands.run_command(echo_cmds, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                                         return_process=True)
        output, errors = p.communicate()
        return output.strip()

    @staticmethod
    def get_conda_sh():
        # TODO: Make this work on all platforms
        conda_base = CondaEnvManager.get_conda_base()
        conda_sh = (Path(conda_base.strip()) / "etc/profile.d/conda.sh").resolve().as_posix()
        return conda_sh

    @staticmethod
    def activate_conda_env(env_name, return_cmd=False):
        #     echo_cmd = ["python", "--version"]
        #     echo_cmd_str = " ".join(echo_cmd)
        conda_sh = CondaEnvManager.get_conda_sh()

        source_conda = ['source', conda_sh]
        source_conda_str = " ".join(source_conda)

        conda_act = ['conda', 'activate', env_name]
        conda_act_str = " ".join(conda_act)

        conda_act_test = [source_conda_str, conda_act_str]
        conda_act_test = source_conda + ["&&"] + conda_act
        conda_act_test_str = " ".join(conda_act_test)
        if return_cmd:
            return conda_act_test_str
        p = subprocess.Popen(conda_act_test_str, stdout=subprocess.PIPE, stdin=subprocess.PIPE, text=True,
                             cwd=Path(conda_sh).parent, shell=True)
        return p

    @staticmethod
    def create_and_init_conda_env(clean_env_name, python_version):
        rc = CondaEnvManager.create_conda_env(clean_env_name, python_version)
        assert rc == 0
        rc = CondaEnvManager.init_prev_made_conda_env(clean_env_name)
        assert rc == 0


class GitProjectManager:
    @staticmethod
    def write_gitignore_contents(proj_dir: Path, gitignore_text: str):
        output_file = (proj_dir / ".gitignore").as_posix()
        with open(output_file, "w") as f:
            f.write(gitignore_text)
        assert Path(output_file).exists()

    @staticmethod
    def init_dir(dir_path):
        git_cmds = ['git', 'init']
        rc = CommonPSCommands.run_command(git_cmds, cwd=dir_path, text=True)
        return rc

    @staticmethod
    def add_repo(dir_path, repo_name, uname=""):
        assert uname
        repo_to_add = f"git@github.com:{uname}/{repo_name}.git"
        git_cmds = ['git', 'remote', 'add', 'origin', repo_to_add]
        with subprocess.Popen(git_cmds, stdout=subprocess.PIPE, text=True, cwd=dir_path) as p:
            output, errors = p.communicate()
        print(output)
        print(errors)


if __name__ == "__main__":
    env_name = "docker_sandbox"
    python_version = "3.9"
    clean_env_name = ProjectManager.create_proj_name(env_name)
    CondaEnvManager.create_and_init_conda_env(clean_env_name, python_version)
    rc, path_to_proj = PoetryProjectManager.create_poetry_proj(clean_env_name, proj_name=env_name,proj_dir=os.getcwd())
    assert rc == 0
    rc = PoetryProjectManager.init_poetry_project(clean_env_name, proj_dir=".", python_version="3.9")
    assert rc == 0
    print(rc)
    sys.exit()
