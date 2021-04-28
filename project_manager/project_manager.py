import json
import os
import subprocess
import sys
from pathlib import Path
import platform
from typing import List, Dict, Union

try:
    import stringcase
    import gy
    import toml
except Exception as e:
    print("Manually install optional packages")
    print(e)


class ProjectManager:

    @staticmethod
    def create_proj_name(name: str) -> str:
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
        poetry_proj_conda_env_name = PoetryProjectManager.get_poetry_proj_env_name_from_poetry_toml_for_py_file(
            file_importing_from)  # gets env from poetry.toml
        rc = PoetryProjectManager.add_dependency_to_pyproject_toml(dir_containing_pyproject_toml,
                                                                   poetry_proj_conda_env_name, dependency)
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
    def search_for_toml_files(filepath: str, toml_pattern: str):
        dir_containing_toml = Path(filepath)
        if dir_containing_toml.is_file():
            dir_containing_toml = dir_containing_toml.parent
        toml_paths = list(dir_containing_toml.glob(toml_pattern))
        return dir_containing_toml, toml_paths

    @staticmethod
    def get_poetry_project_dir(filepath_importing_from: str, toml_pattern="*pyproject.toml"):
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
    def get_poetry_toml(path: str):
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
    def get_pyproject_toml(path: str):
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
    def get_import_error_dependencies_from_imported_py_poetry_proj_file(e):
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
    def add_poetry_package_from_requirements_txt(dir_containing_pyproject_toml: str, poetry_proj_conda_env_name: str,
                                                 path_to_requirements_txt: str, try_pinned_versions: bool = False):
        # TODO: Refactor
        reqs = CommonPSCommands.parse_requirements_txt(path_to_requirements_txt)
        for cur_dependency in reqs:
            dependency = cur_dependency['name']
            if cur_dependency['is_pinned']:
                dependency_pinned = cur_dependency['line_in_reqs_txt']
            else:
                dependency_pinned = cur_dependency['name']
            poetry_cmd = f"poetry add {dependency}"
            poetry_cmd_pinned = f"poetry add {dependency_pinned}"
            try_again = False
            if try_pinned_versions and (dependency_pinned != dependency):
                print("Will attempt to add {}")
                try:
                    rc = PoetryProjectManager.execute_poetry_cmd(poetry_cmd_pinned, dir_containing_pyproject_toml,
                                                                 poetry_proj_conda_env_name)
                    assert rc == 0
                except Exception as e:
                    try_again = True
                    print(e)
                    print("Unable to add poetry dependency with pinned version\nAttempting to add without pinning")
            if (not try_pinned_versions) or (dependency_pinned == dependency) or try_again:
                try:
                    rc = PoetryProjectManager.execute_poetry_cmd(poetry_cmd, dir_containing_pyproject_toml,
                                                                 poetry_proj_conda_env_name)
                    assert rc == 0
                except Exception as e:
                    print(e)
                    print("Unable to add poetry dependency with pinned version")

    @staticmethod
    def add_dependency_to_pyproject_toml(dir_containing_pyproject_toml: str, poetry_proj_conda_env_name: str,
                                         dependency: str):
        poetry_cmd = f"poetry add {dependency}"
        rc = PoetryProjectManager.execute_poetry_cmd(poetry_cmd, dir_containing_pyproject_toml,
                                                     poetry_proj_conda_env_name)
        return rc

    @staticmethod
    def clear_poetry_cache(poetry_proj_conda_env_name: str):
        poetry_cmd = "poetry cache clear --all pypi"
        dir_containing_pyproject_toml = Path(".").resolve().as_posix()
        rc = PoetryProjectManager.execute_poetry_cmd(poetry_cmd, dir_containing_pyproject_toml,
                                                     poetry_proj_conda_env_name)
        assert rc == 0
        return rc

    @staticmethod
    def execute_poetry_cmd(poetry_cmd: str, poetry_proj_dir, env_name, **kwargs):
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
    def link_poetry_proj_with_conda_env(clean_env_name, **kwargs):
        poetry_cmd = PoetryProjectManager.get_poetry_config_virtualenv_path_cmd_for_conda_env(clean_env_name)
        rc = PoetryProjectManager.execute_poetry_cmd(poetry_cmd, poetry_proj_dir=os.getcwd(), env_name=clean_env_name,
                                                     **kwargs)

        poetry_cmd = "poetry config virtualenvs.create 0 --local"
        rc = PoetryProjectManager.execute_poetry_cmd(poetry_cmd, poetry_proj_dir=os.getcwd(), env_name=clean_env_name,
                                                     **kwargs)

        poetry_cmd = "poetry config virtualenvs.in-project 0 --local"
        rc = PoetryProjectManager.execute_poetry_cmd(poetry_cmd, poetry_proj_dir=os.getcwd(), env_name=clean_env_name,
                                                     **kwargs)

        assert rc == 0
        print(f"Successfully linked {clean_env_name} to its conda env!")
        return rc

    @staticmethod
    def create_poetry_project(conda_env_name, proj_name=None, proj_dir=".", **kwargs):
        old_path = os.getcwd()
        proj_path = Path(proj_dir).expanduser().resolve()
        path_to_proj = PoetryProjectManager.check_if_poetry_proj_path_is_available(conda_env_name, proj_path, proj_name)

        rc = PoetryProjectManager.create_poetry_project_cmd(conda_env_name, proj_name, **kwargs)
        assert rc == 0
        rc = PoetryProjectManager.link_poetry_proj_with_conda_env(conda_env_name)
        assert rc == 0
        os.chdir(old_path)
        return rc, path_to_proj

    @staticmethod
    def check_if_poetry_proj_path_is_available(conda_env_name, proj_path, proj_name):
        try:
            assert proj_path.exists()
            assert proj_path.is_dir()
            os.chdir(proj_path.as_posix())
        except Exception as e:
            print("Unable to cd into folder since it doesn't exist! Will create proj in current directory")
        try:
            if proj_name:
                path_to_proj = (proj_path / proj_name)
            else:
                path_to_proj = (proj_path / conda_env_name)
            assert not path_to_proj.exists()
        except Exception as e:
            print("Unable to create poetry project since directory or environment already exists!")
            raise e
        return path_to_proj

    @staticmethod
    def create_poetry_project_cmd(conda_env_name, proj_name, **kwargs):
        if proj_name:
            poetry_cmd = f"poetry new {proj_name}"
        else:
            poetry_cmd = f"poetry new {conda_env_name}"
        rc = PoetryProjectManager.execute_poetry_cmd(poetry_cmd, poetry_proj_dir=os.getcwd(), env_name=conda_env_name,
                                                     **kwargs)
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
            rc, path_to_proj = PoetryProjectManager.create_poetry_project(clean_env_name, proj_name=proj_name,
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
    def find_poetry_toml_and_get_virtual_env_path(path: str):
        cur_poetry_file = PoetryProjectManager.get_poetry_toml(path)
        path_to_env = PoetryProjectManager.get_virtualenv_path_from_poetry_toml(cur_poetry_file)
        return path_to_env

    @staticmethod
    def get_virtualenv_path_from_poetry_toml(cur_poetry_file: str) -> Path:
        """
        This reads a poetry.toml file and gets the virtualenv path found in the poetry.toml file

        :param cur_poetry_file:
        :return:
        """
        virtualenvs_path = CommonPSCommands.read_toml(cur_poetry_file, 'virtualenv')
        path_to_env = Path(virtualenvs_path['path'])
        return path_to_env

    @staticmethod
    def get_poetry_proj_env_name_from_poetry_toml_for_py_file(poetry_proj_py_filepath: str):
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
            deps = PoetryProjectManager.get_import_error_dependencies_from_imported_py_poetry_proj_file(
                caught_exception)
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
                    collect_stripped_text=False, verbose=True, **kwargs):
        if isinstance(cmd_args, str):
            if ("&&" in cmd_args) and (platform.system() == "Windows"):
                # If && is split on MacOS everything is executed seperately,
                cmd_args = cmd_args.split()
            else:
                cmd_args = [cmd_args]
        if collect_stripped_text:
            return_process = False
        p = subprocess.Popen(cmd_args, *args, stdin=stdin, stdout=stdout, text=text, **kwargs)
        if return_process:
            return p
        text_collected = []  # TODO: Find out built-ins on polling and collecting this output
        while True:
            cur_status = p.poll()
            if cur_status:  # 0s won't be printed
                print(cur_status)
            output = p.stdout.readline()
            if (output == '') and p.poll() is not None:  # might be redundant
                break
            if output:
                cur_text = output.strip()
                if collect_stripped_text:
                    text_collected.append(cur_text)
                if verbose:
                    print(cur_text)
            if cur_status == 0:
                print(f"Success!\nFinished running {cmd_args}")
                break
        rc = p.poll()
        if collect_stripped_text:
            return rc, text_collected
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
                    key, values = cur_line.split("=")  # assuming we have simple dependencies with 1 = sign
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
        use_shell = False
        if platform.system() == "Windows":
            use_shell = True
        p1 = subprocess.Popen(["echo", y_cmd], stdout=subprocess.PIPE, text=True, shell=use_shell)
        return p1

    @staticmethod
    def parse_requirements_txt(reqs_path: str) -> List[Dict[str, Union[str, bool]]]:
        all_dependencies = []
        with open(reqs_path, 'r') as f:
            lines = list(filter(None, f.read().splitlines()))
            lines = list(map(lambda x: x.split("#")[0] if "#" in x else x, lines))  # remove comments
            lines = list(filter(None, lines))
            for dep in lines:
                cur_dep = {}
                cur_dep['line_in_reqs_txt'] = dep
                cur_dep['name'] = ""
                cur_dep['is_git_dependency'] = False
                cur_dep['is_pinned'] = False
                if dep.startswith("git"):
                    try:
                        cur_dep['name'] = dep.split("/")[-1]
                    except Exception as e:
                        cur_dep['name'] = dep
                        print(e)
                    cur_dep['is_git_dependency'] = True
                elif "==" in dep:
                    cur_dep['name'] = dep.split("==")[0]
                    cur_dep['is_pinned'] = True
                else:
                    cur_dep['name'] = dep
                all_dependencies.append(cur_dep)
        return all_dependencies


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
    def lookup_kernel(env_name: str):
        rel_path_to_kernel = f"Jupyter/kernels/{env_name}/kernel.json"
        if platform.system() == "Windows":
            # TODO: Test on PC
            path_to_kernel = Path(os.getenv("APPDATA")).resolve().joinpath(rel_path_to_kernel)
        else:
            path_to_kernel = Path(f"~/Library").expanduser().joinpath(rel_path_to_kernel)
        try:
            assert path_to_kernel.exists()
        except Exception as e:
            print(e)
            raise e
        return path_to_kernel

    @staticmethod
    def verify_kernel_pairing(env_name):
        kernel_config_path = CondaEnvManager.lookup_kernel(env_name)
        kernel_config = CondaEnvManager.load_kernel_config(kernel_config_path)
        kernel_paired_to_env = CondaEnvManager.verify_if_kernel_config_contains_env_path(env_name, kernel_config)
        return kernel_paired_to_env

    @staticmethod
    def load_kernel_config(kernel_config_path):
        with open(kernel_config_path, 'r') as f:
            kernel_config = json.load(f)
        return kernel_config

    @staticmethod
    def verify_if_kernel_config_contains_env_path(env_name, kernel_config):
        argv = kernel_config.get('argv', [])
        if argv:
            path_to_py = Path(argv[0])
            try:
                assert env_name in path_to_py.parts
                return True
            except Exception as e:
                print(e)
                print("The Kernel is improperly matched to its conda name!")
                return False
        else:
            print("Kernel config doesn't exist")
            return False

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
        # TODO: Make this work on all platforms
        echo_cmds = ['conda', 'info', '--base']
        if platform.system() == "Windows":
            # TODO: This always prints out for windows commands
            rc, text = CommonPSCommands.run_command(echo_cmds, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                                                    verbose=False, collect_stripped_text=True)
            output = text[0].strip()  # TODO: last elem is a new line str for some reason
        else:
            p = CommonPSCommands.run_command(echo_cmds, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                                             return_process=True, shell=False)
            output, errors = p.communicate()
        return output.strip()

    @staticmethod
    def get_conda_sh():
        try:
            conda_base = CondaEnvManager.get_conda_base()
            conda_sh = (Path(conda_base.strip()) / "etc/profile.d/conda.sh").resolve()
            assert conda_sh.parent.exists()
        except Exception as e:
            print(e)
            print("trying to get base from dot_conda environments txt file!")
            conda_base = CondaEnvManager.get_conda_base_from_dot_conda_envs_txt()
            conda_sh = (Path(conda_base.strip()) / "etc/profile.d/conda.sh").resolve()

        assert conda_sh.parent.exists()
        return conda_sh.as_posix()

    @staticmethod
    def get_conda_base_from_dot_conda_envs_txt():
        path_to_dot_conda_envs = Path("~/.conda/environments.txt").expanduser()
        assert path_to_dot_conda_envs.exists()
        with open(path_to_dot_conda_envs, 'r') as f:
            all_lines = f.readlines()
            all_lines = [l.strip() for l in all_lines]
        try:
            assert len(all_lines) == 1
        except Exception as e:
            print(e)
            print(f"Multiple base conda environments exist!\n inspect\n{path_to_dot_conda_envs}")
            print("Returning first line")
        return all_lines[0]

    @staticmethod
    def activate_conda_env(env_name, return_cmd=False):
        #     echo_cmd = ["python", "--version"]
        #     echo_cmd_str = " ".join(echo_cmd)
        conda_sh = CondaEnvManager.get_conda_sh()

        source_conda = ['source', conda_sh]
        source_conda_str = " ".join(source_conda)

        conda_act = ['conda', 'activate', env_name]
        conda_act_str = " ".join(conda_act)

        conda_act_test = source_conda + ["&&"] + conda_act
        conda_act_test_str = " ".join(conda_act_test)
        if return_cmd:
            if platform.system() == "Windows":
                # shell scripts aren't runnable on windows, so just return the activate str
                return conda_act_str
            else:
                return conda_act_test_str
        else:
            if platform.system() == "Windows":
                conda_act_test_str = conda_act_str
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
        if dir_path is None:
            dir_path = Path(".").resolve().as_posix()
        else:
            dir_path = Path(dir_path)
            if dir_path.is_file():
                dir_path = dir_path.parent
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


class LocalProjectManager:

    @staticmethod
    def init_current_dir_as_a_poetry_conda_project(clean_env_name: str = "hello_world", python_version: str = "3.9",
                                                   add_git=False):
        """

        :param str clean_env_name: A name for your conda env without illegal characterss
        :param str python_version: The python version of conda you're interested in
        :param bool add_git: Initialize the current directory with `git init`
        :return: 0
        """
        CondaEnvManager.create_and_init_conda_env(clean_env_name, python_version)
        PoetryProjectManager.execute_poetry_init(clean_env_name)
        PoetryProjectManager.link_poetry_proj_with_conda_env(clean_env_name)
        if add_git:
            GitProjectManager.init_dir()
            try:
                ProjectManager.add_git_ignore_to_project(".")
            except Exception as e:
                print(e)
                print("Make sure that you install gy if you want to add .gitignore files")
        return 0

    @staticmethod
    def create_init_link_conda_env_to_existing_poetry_project(clean_env_name: str = "hello_world", python_version: str = "3.9"):
        CondaEnvManager.create_and_init_conda_env(clean_env_name, python_version)
        PoetryProjectManager.link_poetry_proj_with_conda_env(clean_env_name)
        return 0

    @staticmethod
    def migrate_requirements_to_poetry_toml(poetry_proj_conda_env_name: str = "hello_world", requirements_txt_name:str=None,try_pinned_versions: bool = False):
        cur_dir = Path(".").resolve()
        cur_dir_str = cur_dir.as_posix()

        dir_containing_pyproject_toml = cur_dir_str
        if requirements_txt_name is None:
            path_to_requirements_txt = cur_dir.joinpath("requirements.txt")
        else:
            path_to_requirements_txt = cur_dir.joinpath(requirements_txt_name)

        try:
            assert path_to_requirements_txt.exists()
            path_to_requirements_txt = path_to_requirements_txt.as_posix()
        except Exception as e:
            print(e)
            print("There's no requirements file to add! Returning")
            return



        add_poetry_package_from_requirements_txt(dir_containing_pyproject_toml, poetry_proj_conda_env_name,path_to_requirements_txt,
            try_pinned_versions=try_pinned_versions)
        CondaEnvManager.create_and_init_conda_env(clean_env_name, python_version)
        PoetryProjectManager.link_poetry_proj_with_conda_env(clean_env_name)
        return 0


class SublimeBuildConfigGenerator:

    @staticmethod
    def get_filepath_to_sublime_text_build_config(env_name):
        file_name = f"{env_name}.sublime-build"
        if platform.system() == "Windows":
            app_data = Path(os.getenv("APPDATA"))
        else:
            app_data = Path("~").expanduser() / f"Library/Application Support"
        sublime_build_path = f"Sublime Text 3/Packages/User/{file_name}"
        path_to_build_config_settings = app_data.joinpath(sublime_build_path)
        assert path_to_build_config_settings.parent.exists()
        return path_to_build_config_settings.as_posix()

    @staticmethod
    def generate_sublime_text_3_build_config_from_conda_env(env_name):
        path_to_env = CondaEnvManager.get_path_to_conda_env(env_name)
        path_to_python_bin = Path(path_to_env).joinpath("bin").as_posix()
        SublimeBuildConfigGenerator.export_sublime_text_build_config(path_to_python_bin, env_name)

    @staticmethod
    def export_sublime_text_build_config(path_to_python_bin, build_config_name):
        sublime_build_config_file_contents = SublimeBuildConfigGenerator.get_sublime_text_build_config_contents(
            path_to_python_bin)
        sublime_config_filepath = SublimeBuildConfigGenerator.get_filepath_to_sublime_text_build_config(
            build_config_name)
        with open(sublime_config_filepath, 'w') as f:
            f.write(json.dumps(sublime_build_config_file_contents, indent=4))

    @staticmethod
    def get_sublime_text_build_config_contents(path_to_python_bin: str):
        sublime_build_config_file_contents = {
            "path": path_to_python_bin,
            "cmd": ["python", "-u", "$file"],
            "file_regex": "^[ ]*File \"(...*?)\", line ([0-9]*)",
            "selector": "source.python"
        }
        return sublime_build_config_file_contents


if __name__ == "__main__":
    env_name = "hello_world"
    python_version = "3.9"
    rc = LocalProjectManager.init_current_dir_as_a_poetry_conda_project(env_name, python_version)
    sys.exit()
