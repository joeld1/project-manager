import json
import os
import platform
import re
import subprocess
import sys
from collections import defaultdict, deque
from functools import reduce
from os import PathLike
from pathlib import Path, PosixPath
from subprocess import Popen
from typing import Any, Dict, List, Union


def import_optional_dependency(object_name: str):
    """
    This method imports optional dependencies, an exception is raised if the module doesn't exist
    :param object_name:
    :return:
    """
    # TODO: Implement importlib
    mod_to_return = None
    if object_name == "gy":
        import gy
        mod_to_return = gy
    elif object_name == "parse_single_constraint":
        from poetry.core.semver import parse_single_constraint
        mod_to_return = parse_single_constraint
    return mod_to_return


def convert_camel_to_snakecase(camel_input):
    """


    :param camel_input:

    """
    words = re.findall(r"[A-Z]?[a-z]+|[A-Z]{2,}(?=[A-Z][a-z]|\d|\W|$)|\d+", camel_input)
    return "_".join(map(str.lower, words))


class ProjectManager:
    """ """

    @staticmethod
    def create_proj_name(name: str) -> str:
        """
        This reformats names such that they are in snake case

        :param name:
        :type name: str
        :rtype: str

        """
        clean_proj_name = convert_camel_to_snakecase(name)
        return clean_proj_name

    @staticmethod
    def find_env_and_add_dependency(file_importing_from: str, dependency: str):
        """


        :param file_importing_from:
        :type file_importing_from: str
        :param dependency:
        :type dependency: str

        """
        dir_containing_pyproject_toml = PoetryProjectManager.get_poetry_project_dir(
            file_importing_from
        )
        poetry_proj_conda_env_name = (
            PoetryProjectManager.get_poetry_proj_env_name_from_poetry_toml_for_py_file(
                file_importing_from
            )
        )  # gets env from poetry.toml
        rc = PoetryProjectManager.add_dependency_to_pyproject_toml(
            dir_containing_pyproject_toml, poetry_proj_conda_env_name, dependency
        )
        return rc

    @staticmethod
    def get_gitignore_contents():
        """ """
        git_ignores_to_add = [
            "dropbox",
            "jetbrains",
            "jupyternotebooks",
            "macos",
            "microsoftoffice",
            "python",
            "sublimetext",
            "virtualenv",
            "visualstudio",
            "visualstudiocode",
        ]
        gy_cmd = ["gy", "generate"] + git_ignores_to_add
        p_gy = subprocess.Popen(gy_cmd, stdout=subprocess.PIPE, text=True)
        output = p_gy.communicate()[0]
        return output

    @staticmethod
    def create_gitignores_in_repos(all_python_dirs):
        """


        :param all_python_dirs:

        """
        gitignore_text = ProjectManager.get_gitignore_contents()
        for p in all_python_dirs:
            GitProjectManager.write_gitignore_contents(p, gitignore_text)

    @staticmethod
    def add_git_ignore_to_project(path_to_proj):
        """


        :param path_to_proj:

        """
        gitignore_text = ProjectManager.get_gitignore_contents()
        GitProjectManager.write_gitignore_contents(
            Path(path_to_proj), gitignore_text=gitignore_text
        )


class PoetryProjectManager:
    """ """

    @staticmethod
    def search_for_toml_files(filepath: str, toml_pattern: str) -> Path:
        """


        :param filepath:
        :type filepath: str
        :param toml_pattern:
        :type toml_pattern: str
        :rtype: Path

        """
        cur_path = Path(filepath)
        if cur_path.is_file():
            if Path(filepath).name == toml_pattern:
                return Path(filepath).parent
            else:
                return PoetryProjectManager.search_for_toml_files(
                    cur_path.parent.as_posix(), toml_pattern
                )
        if cur_path.is_dir():
            if toml_pattern in os.listdir(filepath):
                return cur_path
            else:
                return PoetryProjectManager.search_for_toml_files(
                    cur_path.parent.as_posix(), toml_pattern
                )

    @staticmethod
    def get_poetry_project_dir(
            filepath_importing_from: str, toml_pattern: str = "pyproject.toml"
    ) -> PosixPath:
        """
        This recursively finds a pyproject.toml from a given filepath.

        If the filepath is a file it'll look at sibling files for a toml file, if it's a directory it'll look within
        its contents for a pyproject.toml file. If nothing is found, it'll go up 1 folder and restart the search and
        repeat the process until a toml pattern is found

        :param filepath_importing_from:
        :type filepath_importing_from: str
        :param toml_pattern: (Default value = "pyproject.toml")
        :rtype: PosixPath
        :type toml_pattern: str
        :rtype: PosixPath

        """
        # TODO: Find out how to determine if is poetry proj, or regular python proj (i.e. requirements.txt)
        toml_path = PoetryProjectManager.search_for_toml_files(
            filepath_importing_from, toml_pattern
        )
        return Path(toml_path)

    @staticmethod
    def get_poetry_toml(path: str):
        """
        This searches for a poetry.toml file that is a sibling of the given path. It recursively searches parent
        paths for a parent that contains a poetry.toml file.

        :param path:
        :type path: str

        """
        toml_pattern = "poetry.toml"
        dir_containing_toml = PoetryProjectManager.get_poetry_project_dir(
            path, toml_pattern=toml_pattern
        )
        cur_poetry_file = Path(dir_containing_toml).joinpath(toml_pattern)
        return cur_poetry_file

    @staticmethod
    def get_pyproject_toml(path: str) -> PosixPath:
        """
        This searches for a pyproject.toml file that is a sibling of the given path. It recursively searches parent
        paths for a parent that contains a poetry.toml file, and returns the final parent that contains a .toml file.

        :param path:
        :type path: str
        :rtype: PosixPath

        """
        toml_pattern = "pyproject.toml"
        dir_containing_pyproject_toml = PoetryProjectManager.get_poetry_project_dir(
            path, toml_pattern=toml_pattern
        )
        path_to_toml = Path(dir_containing_pyproject_toml).joinpath(toml_pattern)
        return path_to_toml

    @staticmethod
    def get_poetry_module_dependencies(poetry_proj_py_filepath: str):
        """
        Finds gets the poetry.dependencies (in pyproject.toml) that a py file in a poetry project is associated with

        :param poetry_proj_py_filepath:
        :type poetry_proj_py_filepath: str

        """
        path_to_toml = PoetryProjectManager.get_pyproject_toml(poetry_proj_py_filepath)
        dependencies = CommonPSCommands.read_toml(
            path_to_toml, "tool.poetry.dependencies"
        )
        return dependencies

    @staticmethod
    def get_import_error_dependencies_from_imported_py_poetry_proj_file(e):
        """


        :param e:

        """
        path_to_loaded_module = CommonPSCommands.get_traceback_file_origin(e)
        deps = PoetryProjectManager.get_poetry_module_dependencies(
            path_to_loaded_module
        )
        return deps

    @staticmethod
    def add_poetry_package_from_exception(
            file_importing_from: str, except_obj: ModuleNotFoundError, ignore_verion=True
    ):
        """


        :param file_importing_from:
        :type file_importing_from: str
        :param except_obj:
        :type except_obj: ModuleNotFoundError
        :param ignore_verion:  (Default value = True)

        """
        assert isinstance(except_obj, ModuleNotFoundError)
        dependency = PoetryProjectManager.get_missing_poetry_dependency(
            except_obj, ignore_verion=ignore_verion
        )
        break_stmnt = input(f"poetry add {dependency}? [q to break]")
        if break_stmnt.lower() == "q":
            return
        env_name = (
            PoetryProjectManager.get_poetry_proj_env_name_from_poetry_toml_for_py_file(
                file_importing_from
            )
        )
        rc = PoetryProjectManager.add_poetry_package(
            file_importing_from, env_name, dependency
        )
        return rc

    @staticmethod
    def add_poetry_package(file_importing_from: str, env_name: str, dependency: str):
        """


        :param file_importing_from:
        :type file_importing_from: str
        :param env_name:
        :type env_name: str
        :param dependency:
        :type dependency: str

        """
        poetry_proj_dir = PoetryProjectManager.get_poetry_project_dir(
            file_importing_from
        )
        rc = PoetryProjectManager.add_dependency_to_pyproject_toml(
            poetry_proj_dir, env_name, dependency
        )
        return rc

    @staticmethod
    def format_deps_from_reqs_txt(reqs: List[Dict[str, str]]):
        cur_dependencies = {}
        for r in reqs:
            cur_name = r['name']
            cur_line = r['line_in_reqs_txt']
            is_pinned = r['is_pinned']
            is_git_dependency = r['is_git_dependency']
            if is_pinned or is_git_dependency:
                if "==" in cur_line:
                    l, *r = cur_line.split("==")
                    dependency_pinned = "==" + "==".join(r)
                else:
                    dependency_pinned = cur_line
                cur_dependencies[cur_name] = dependency_pinned
            else:
                cur_dependencies[cur_name] = ""
        return cur_dependencies

    @staticmethod
    def add_poetry_package_from_requirements_txt(
            dir_containing_pyproject_toml: str,
            poetry_proj_conda_env_name: str,
            path_to_requirements_txt: str,
            warn_before_add=True,
    ):
        """


        :param dir_containing_pyproject_toml:
        :type dir_containing_pyproject_toml: str
        :param poetry_proj_conda_env_name:
        :type poetry_proj_conda_env_name: str
        :param path_to_requirements_txt:
        :type path_to_requirements_txt: str
        :param try_pinned_versions:  (Default value = False)
        :type try_pinned_versions: bool
        :param warn_before_add:  (Default value = True)

        """
        reqs = CommonPSCommands.parse_requirements_txt(path_to_requirements_txt)
        cur_dependencies = PoetryProjectManager.format_deps_from_reqs_txt(reqs)
        rc = LocalProjectManager.iterate_and_add_dependencies(toml_file_dependencies_section_dict=cur_dependencies,
                                                              dest_pyproject_toml_dir=dir_containing_pyproject_toml,
                                                              poetry_proj_conda_env_name=poetry_proj_conda_env_name,
                                                              toml_section_type="",
                                                              warn_before_add=warn_before_add)
        return rc

    @staticmethod
    def attempt_adding_dependency(
            poetry_proj_conda_env_name,
            dir_containing_pyproject_toml,
            dependency,
            try_pinned_versions,
            warn_before_add,
    ):
        """


        :param poetry_proj_conda_env_name:
        :param dir_containing_pyproject_toml:
        :param dependency:
        :param try_pinned_versions:
        :param warn_before_add:

        """
        required_keys = {"line_in_reqs_txt", "name", "is_git_dependency", "is_pinned"}
        keys_found = required_keys.issubset(set(dependency.keys()))
        assert keys_found  # want to fit this structure

        poetry_cmds = PoetryProjectManager.get_poetry_add_cmds_for_dependency(dependency=dependency)
        dependency_is_pinned = poetry_cmds["dependency_is_pinned"]
        try_add_pinned_dependency = try_pinned_versions and (dependency_is_pinned)
        cont_reply = PoetryProjectManager.prompt_before_adding_dependency(
            poetry_cmds=poetry_cmds,
            try_add_pinned_dependency=try_add_pinned_dependency,
            warn_before_add=warn_before_add,
        )
        break_out = cont_reply.lower() == "q"
        skip_add = cont_reply.lower() == "s"
        continue_w_adding = (not skip_add) and (not break_out)
        try_add_wo_pinned_version = (not try_pinned_versions) or (
            not dependency_is_pinned
        )
        if continue_w_adding:
            PoetryProjectManager.try_adding_dependency(
                poetry_proj_conda_env_name=poetry_proj_conda_env_name,
                dir_containing_pyproject_toml=dir_containing_pyproject_toml,
                poetry_cmds=poetry_cmds,
                try_add_wo_pinned_version=try_add_wo_pinned_version,
                try_add_pinned_dependency=try_add_pinned_dependency,
            )
        elif break_out:
            print("Now raising exception in order to break out of script")
            raise Exception

    @staticmethod
    def prompt_before_adding_dependency(
            poetry_cmds, try_add_pinned_dependency, warn_before_add
    ):
        """


        :param poetry_cmds:
        :param try_add_pinned_dependency:
        :param warn_before_add:

        """
        cont_reply = ""
        if warn_before_add:
            if try_add_pinned_dependency:
                cur_dep = poetry_cmds["dep_w_version_pinned"]
            else:
                cur_dep = poetry_cmds["dep_wo_version_pinned"]
            cont_reply = input(
                f"Will attempt to add {cur_dep}\nEnter [s] to skip, [q] to break, enter to continue"
            )
        return cont_reply

    @staticmethod
    def get_poetry_add_cmds_for_dependency(dependency: Dict[str, str]):
        """


        :param dependency:
        :type dependency: Dict[str, str]

        """
        # TODO: Refactor
        poetry_cmds = {}
        dependency_name = dependency["name"]
        if dependency["is_pinned"]:
            dependency_pinned = dependency["line_in_reqs_txt"]
        else:
            dependency_pinned = dependency["name"]
        poetry_cmd = f"poetry add {dependency_name}"
        poetry_cmd_pinned = f"poetry add {dependency_pinned}"
        poetry_cmds["dep_wo_version_pinned"] = dependency_name
        poetry_cmds["dep_w_version_pinned"] = dependency_pinned

        poetry_cmds["cmd_wo_version_pinned"] = poetry_cmd
        poetry_cmds["cmd_w_version_pinned"] = poetry_cmd_pinned

        poetry_cmds["dependency_is_pinned"] = dependency_pinned != dependency_name
        return poetry_cmds

    @staticmethod
    def try_adding_dependency(
            poetry_proj_conda_env_name,
            dir_containing_pyproject_toml,
            poetry_cmds,
            try_add_wo_pinned_version,
            try_add_pinned_dependency,
    ):
        """


        :param poetry_proj_conda_env_name:
        :param dir_containing_pyproject_toml:
        :param poetry_cmds:
        :param try_add_wo_pinned_version:
        :param try_add_pinned_dependency:

        """
        cur_dep = poetry_cmds["dep_w_version_pinned"]
        try_again = PoetryProjectManager.add_pinned_dependency(
            poetry_proj_conda_env_name=poetry_proj_conda_env_name,
            dir_containing_pyproject_toml=dir_containing_pyproject_toml,
            dependency=cur_dep,
            try_add_pinned_dependency=try_add_pinned_dependency,
        )
        if try_add_wo_pinned_version or try_again:
            try:
                cur_dep = poetry_cmds["dep_wo_version_pinned"]
                rc = PoetryProjectManager.add_dependency_to_pyproject_toml(
                    dir_containing_pyproject_toml=dir_containing_pyproject_toml,
                    poetry_proj_conda_env_name=poetry_proj_conda_env_name,
                    dependency=cur_dep,
                )
                assert rc == 0
            except Exception as e:
                print(e)
                print("Unable to add poetry dependency without pinned version")

    @staticmethod
    def add_pinned_dependency(
            poetry_proj_conda_env_name,
            dir_containing_pyproject_toml,
            dependency,
            try_add_pinned_dependency,
    ):
        """


        :param poetry_proj_conda_env_name:
        :param dir_containing_pyproject_toml:
        :param dependency:
        :param try_add_pinned_dependency:

        """
        try_again = False
        if try_add_pinned_dependency:
            try:
                rc = PoetryProjectManager.add_dependency_to_pyproject_toml(
                    dir_containing_pyproject_toml=dir_containing_pyproject_toml,
                    poetry_proj_conda_env_name=poetry_proj_conda_env_name,
                    dependency=dependency,
                )
                assert rc == 0
            except Exception as e:
                try_again = True
                print(e)
                print(
                    "Unable to add poetry dependency with pinned version\nAttempting to add without pinning"
                )
        return try_again

    @staticmethod
    def add_dependency_to_pyproject_toml(
            dir_containing_pyproject_toml: str,
            poetry_proj_conda_env_name: str,
            dependency: str,
            wrap_in_quotes: bool = False,
            options: str = "",
    ):
        """


        :param dir_containing_pyproject_toml:
        :type dir_containing_pyproject_toml: str
        :param poetry_proj_conda_env_name:
        :type poetry_proj_conda_env_name: str
        :param dependency:
        :type dependency: str
        :param wrap_in_quotes:  (Default value = False)
        :type wrap_in_quotes: bool
        :param options:  (Default value = "")
        :type options: str

        """
        # TODO: Remove redundant add methods
        dependency = PoetryProjectManager.wrap_dep_in_quotes(dependency, wrap_in_quotes=wrap_in_quotes)
        poetry_cmd = PoetryProjectManager.create_poetry_cmd_for_dep(dependency, options=options, method="add")
        rc = PoetryProjectManager.execute_poetry_cmd(
            poetry_cmd, dir_containing_pyproject_toml, poetry_proj_conda_env_name
        )
        return rc

    @staticmethod
    def create_poetry_cmd_for_dep(dependency: str, options=None, method: str = "add"):
        if options:
            poetry_cmd = f"poetry {method} {options} {dependency}"
        else:
            poetry_cmd = f"poetry {method} {dependency}"
        return poetry_cmd

    @staticmethod
    def wrap_dep_in_quotes(dependency: str, wrap_in_quotes: bool = False):
        has_quote = '"' in dependency
        has_dash = "-" in dependency
        must_wrap = (not has_quote) and has_dash
        if wrap_in_quotes or must_wrap:
            dependency = f'"{dependency}"'  # wrap in quotes
        return dependency

    @staticmethod
    def remove_dependency_from_pyproject_toml(
            dir_containing_pyproject_toml: str,
            poetry_proj_conda_env_name: str,
            dependency: str,
            wrap_in_quotes: bool = False,
            options: str = "",
    ):
        """


        :param dir_containing_pyproject_toml:
        :type dir_containing_pyproject_toml: str
        :param poetry_proj_conda_env_name:
        :type poetry_proj_conda_env_name: str
        :param dependency:
        :type dependency: str
        :param wrap_in_quotes:  (Default value = False)
        :type wrap_in_quotes: bool
        :param options:  (Default value = "")
        :type options: str

        """
        # TODO: Remove redundant add methods
        dependency = PoetryProjectManager.wrap_dep_in_quotes(dependency, wrap_in_quotes=wrap_in_quotes)
        poetry_cmd = PoetryProjectManager.create_poetry_cmd_for_dep(dependency, options=options, method="remove")
        rc = PoetryProjectManager.execute_poetry_cmd(
            poetry_cmd, dir_containing_pyproject_toml, poetry_proj_conda_env_name
        )
        return rc

    @staticmethod
    def poetry_remove(options_and_packages_str: str, dir_containing_pyproject_toml: str,
                      poetry_proj_conda_env_name: str):
        """

        Equivalent to poetry remove {...} where everything found within the brackets is what you want to remove (options_and_packages_str)

        :param dir_containing_pyproject_toml: command to execute with poetry remove
        :type dir_containing_pyproject_toml: str
        :param poetry_proj_conda_env_name:
        :type poetry_proj_conda_env_name: str
        :param options_and_packages_str:
        :type options_and_packages_str: str
        """
        poetry_cmd = PoetryProjectManager.create_poetry_cmd_for_dep(options_and_packages_str, method="remove")
        rc = PoetryProjectManager.execute_poetry_cmd(poetry_cmd, dir_containing_pyproject_toml, poetry_proj_conda_env_name)
        return rc

    @staticmethod
    def poetry_add(options_and_packages_str: str, dir_containing_pyproject_toml: str,
                      poetry_proj_conda_env_name: str):
        """

        Equivalent to poetry add {...} where everything found within the brackets is what you want to add (options_and_packages_str)

        :param dir_containing_pyproject_toml: command to execute with poetry add
        :type dir_containing_pyproject_toml: str
        :param poetry_proj_conda_env_name:
        :type poetry_proj_conda_env_name: str
        :param options_and_packages_str:
        :type options_and_packages_str: str
        """
        poetry_cmd = PoetryProjectManager.create_poetry_cmd_for_dep(options_and_packages_str, method="add")
        rc = PoetryProjectManager.execute_poetry_cmd(poetry_cmd, dir_containing_pyproject_toml, poetry_proj_conda_env_name)
        return rc



    @staticmethod
    def clear_poetry_cache(poetry_proj_conda_env_name: str):
        """


        :param poetry_proj_conda_env_name:
        :type poetry_proj_conda_env_name: str

        """
        yes = CommonPSCommands.echo_yes(return_cmd=True)
        # TODO: Echo update this
        poetry_cmd = "poetry cache clear --all pypi"
        dir_containing_pyproject_toml = Path(".").resolve().as_posix()
        rc = PoetryProjectManager.execute_poetry_cmd(
            poetry_cmd, dir_containing_pyproject_toml, poetry_proj_conda_env_name
        )
        assert rc == 0
        return rc

    @staticmethod
    def execute_poetry_cmd(
            poetry_cmd: str, poetry_proj_dir: str, env_name: str, **kwargs) -> int:
        """


        :param poetry_cmd:
        :type poetry_cmd: str
        :param poetry_proj_dir:
        :type poetry_proj_dir: str
        :param env_name:
        :type env_name: str
        :param **kwargs:
        :rtype: int

        """
        old_path = os.getcwd()
        os.chdir(poetry_proj_dir)
        act_env_str = CondaEnvManager.activate_conda_env(env_name, return_cmd=True)
        kwargs["text"] = True
        kwargs["shell"] = True
        kwargs["cwd"] = poetry_proj_dir
        rc = CommonPSCommands.chain_and_execute_commands(
            [act_env_str, poetry_cmd], **kwargs
        )
        os.chdir(old_path)
        return rc

    @staticmethod
    def execute_poetry_init(env_name: str, poetry_proj_dir: None = None) -> int:
        """


        :param env_name:
        :type env_name: str
        :param poetry_proj_dir:  (Default value = None)
        :type poetry_proj_dir: None
        :rtype: int

        """
        if poetry_proj_dir is None:
            poetry_proj_dir = Path(".").resolve().as_posix()
        poetry_cmd = "poetry init --no-interaction"
        rc = PoetryProjectManager.execute_poetry_cmd(
            poetry_cmd, poetry_proj_dir, env_name
        )
        return rc

    @staticmethod
    def get_poetry_config_virtualenv_path_cmd_for_conda_env(clean_env_name: str) -> str:
        """


        :param clean_env_name:
        :type clean_env_name: str
        :rtype: str

        """
        conda_env_path = CondaEnvManager.get_path_to_conda_env(clean_env_name)
        if platform.system() == "Windows":
            conda_env_path = Path(conda_env_path).joinpath("python.exe").as_posix()
        poetry_cmd = f"poetry config virtualenvs.path {conda_env_path} --local"
        return poetry_cmd

    @staticmethod
    def link_poetry_proj_with_conda_env(clean_env_name: str, **kwargs) -> int:
        """


        :param clean_env_name:
        :type clean_env_name: str
        :param **kwargs:
        :rtype: int

        """
        poetry_cmd = (
            PoetryProjectManager.get_poetry_config_virtualenv_path_cmd_for_conda_env(
                clean_env_name
            )
        )
        rc = PoetryProjectManager.execute_poetry_cmd(
            poetry_cmd, poetry_proj_dir=os.getcwd(), env_name=clean_env_name, **kwargs
        )

        poetry_cmd = "poetry config virtualenvs.create 0 --local"
        rc = PoetryProjectManager.execute_poetry_cmd(
            poetry_cmd, poetry_proj_dir=os.getcwd(), env_name=clean_env_name, **kwargs
        )

        poetry_cmd = "poetry config virtualenvs.in-project 0 --local"
        rc = PoetryProjectManager.execute_poetry_cmd(
            poetry_cmd, poetry_proj_dir=os.getcwd(), env_name=clean_env_name, **kwargs
        )

        assert rc == 0
        print(f"Successfully linked {clean_env_name} to its conda env!")
        return rc

    @staticmethod
    def create_poetry_project(conda_env_name, proj_name=None, proj_dir=".", **kwargs):
        """


        :param conda_env_name:
        :param proj_name:  (Default value = None)
        :param proj_dir:  (Default value = ".")
        :param **kwargs:

        """
        old_path = os.getcwd()
        proj_path = Path(proj_dir).expanduser().resolve()
        path_to_proj = PoetryProjectManager.check_if_poetry_proj_path_is_available(
            conda_env_name, proj_path, proj_name
        )

        rc = PoetryProjectManager.create_poetry_project_cmd(
            conda_env_name, proj_name, **kwargs
        )
        assert rc == 0
        os.chdir(path_to_proj)
        rc = PoetryProjectManager.link_poetry_proj_with_conda_env(conda_env_name)
        assert rc == 0
        os.chdir(old_path)
        return rc, path_to_proj

    @staticmethod
    def check_if_poetry_proj_path_is_available(conda_env_name, proj_path, proj_name):
        """


        :param conda_env_name:
        :param proj_path:
        :param proj_name:

        """
        try:
            assert proj_path.exists()
            assert proj_path.is_dir()
            os.chdir(proj_path.as_posix())
        except Exception:
            print(
                "Unable to cd into folder since it doesn't exist! Will create proj in current directory"
            )
        try:
            if proj_name:
                path_to_proj = proj_path / proj_name
            else:
                path_to_proj = proj_path / conda_env_name
            assert not path_to_proj.exists()
        except Exception as e:
            print(
                "Unable to create poetry project since directory or environment already exists!"
            )
            raise e
        return path_to_proj

    @staticmethod
    def create_poetry_project_cmd(conda_env_name, proj_name, **kwargs):
        """


        :param conda_env_name:
        :param proj_name:
        :param **kwargs:

        """
        if proj_name:
            poetry_cmd = f"poetry new {proj_name}"
        else:
            poetry_cmd = f"poetry new {conda_env_name}"
        rc = PoetryProjectManager.execute_poetry_cmd(
            poetry_cmd, poetry_proj_dir=os.getcwd(), env_name=conda_env_name, **kwargs
        )
        return rc

    @staticmethod
    def get_conda_activate_str(clean_env_name):
        """


        :param clean_env_name:

        """
        try:
            conda_envs_and_kernels_made = (
                not CondaEnvManager.conda_and_kernel_name_available(
                    clean_env_name, both=True
                )
            )
            assert conda_envs_and_kernels_made
            act_env_str = CondaEnvManager.activate_conda_env(
                clean_env_name, return_cmd=True
            )
        except Exception as e:
            print(e)
            print(
                "Create the conda environment and register the jupyter kernel before retrying this method!"
            )
            raise e
        return act_env_str

    @staticmethod
    def init_poetry_project(
            clean_env_name, proj_name=None, proj_dir=".", python_version="3.9"
    ):
        """


        :param clean_env_name:
        :param proj_name:  (Default value = None)
        :param proj_dir:  (Default value = ".")
        :param python_version:  (Default value = "3.9")

        """
        cur_dir = os.getcwd()
        proj_dir_path = Path(proj_dir).expanduser().resolve().as_posix()

        if proj_name is None:
            proj_name = clean_env_name
        proj_available = CondaEnvManager.conda_and_kernel_name_available(
            clean_env_name, both=True
        )
        if proj_available:
            print("it's available! Now making conda env!")
            CondaEnvManager.create_and_init_conda_env(clean_env_name, python_version)
            # make conda env before this step
            rc, path_to_proj = PoetryProjectManager.create_poetry_project(
                clean_env_name, proj_name=proj_name, proj_dir=proj_dir_path
            )
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
        """


        :param path:
        :type path: str

        """
        cur_poetry_file = PoetryProjectManager.get_poetry_toml(path)
        path_to_env = PoetryProjectManager.get_virtualenv_path_from_poetry_toml(
            cur_poetry_file
        )
        return path_to_env

    @staticmethod
    def get_virtualenv_path_from_poetry_toml(cur_poetry_file: str) -> Path:
        """
        This reads a poetry.toml file and gets the virtualenv path found in the poetry.toml file

        :param cur_poetry_file:
        :type cur_poetry_file: str
        :rtype: Path

        """
        virtualenvs_path = CommonPSCommands.read_toml(path_to_toml=cur_poetry_file, start_line="virtualenvs")
        path_to_env = Path(virtualenvs_path["path"])
        return path_to_env

    @staticmethod
    def get_virtual_env_name_from_poetry_toml(poetry_toml_path: str) -> str:
        """

        This gets the virtual env name by reading getting the name of the virtual env found in the poetry.toml file.

        :param str poetry_toml_path:
        :return:
        """
        path_to_venv = PoetryProjectManager.get_virtualenv_path_from_poetry_toml(poetry_toml_path)
        return path_to_venv.name

    @staticmethod
    def get_virtual_env_name_from_pyproject_toml(pyproject_toml_path: str) -> str:
        """

        This opens up the neighboring poetry.toml file and identifies the virtual env name associated with the poetry project.

        :param pyproject_toml_path:
        :return:
        """
        dir_containing_pyproject_toml = Path(pyproject_toml_path).parent
        try:
            poetry_toml_path = dir_containing_pyproject_toml.joinpath("poetry.toml")
            env_name = PoetryProjectManager.get_virtual_env_name_from_poetry_toml(poetry_toml_path)
            return env_name
        except Exception as e:
            raise e

    @staticmethod
    def get_poetry_proj_env_name_from_poetry_toml_for_py_file(
            poetry_proj_py_filepath: str,
    ):
        """
        This searches for the poetry.toml file a .py file (in a poetry proj) is associated with.

        :param poetry_proj_py_filepath:
        :type poetry_proj_py_filepath: str

        """
        path_to_env = PoetryProjectManager.find_poetry_toml_and_get_virtual_env_path(
            poetry_proj_py_filepath
        )
        env_name = path_to_env.name
        return env_name

    @staticmethod
    def get_missing_poetry_dependency(caught_exception, ignore_verion=True):
        """


        :param caught_exception:
        :param ignore_verion:  (Default value = True)

        """
        dep_name = caught_exception.name
        if not ignore_verion:
            deps = PoetryProjectManager.get_import_error_dependencies_from_imported_py_poetry_proj_file(
                caught_exception
            )
        else:
            deps = {dep_name: dep_name}
        if not ignore_verion:
            dep_version = deps.get(dep_name)
            dependency = f'{dep_name}=="{dep_version}"'
        else:
            dependency = dep_name
        return dependency

    @staticmethod
    def add_notebook_ipykernel_dependencies_to_pypoetry(
            clean_env_name: str, dir_containing_pypoetry_file: str
    ) -> int:
        """


        :param clean_env_name:
        :type clean_env_name: str
        :param dir_containing_pypoetry_file:
        :type dir_containing_pypoetry_file: str
        :rtype: int

        """
        try:
            rc = PoetryProjectManager.add_dependency_to_pyproject_toml(
                dir_containing_pypoetry_file,
                poetry_proj_conda_env_name=clean_env_name,
                dependency="notebook",
                options="-D",
            )
            assert rc == 0
            rc = PoetryProjectManager.add_dependency_to_pyproject_toml(
                dir_containing_pypoetry_file,
                poetry_proj_conda_env_name=clean_env_name,
                dependency="ipykernel",
                options="-D",
            )
            assert rc == 0
        except Exception as e:
            print(e)
            print("Unable to add notebook or ipykernel")
            rc = 1

        return rc


class CommonPSCommands:
    """ """

    @staticmethod
    def run_command(
            cmd_args: Union[List[str], str],
            *args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=None,
            return_process=False,
            collect_stripped_text=False,
            verbose=True,
            **kwargs
    ) -> Union[int, Popen]:
        """


        :param cmd_args:
        :type cmd_args: Union[str, List[str]]
        :param *args:
        :param stdin:  (Default value = subprocess.PIPE)
        :param stdout:  (Default value = subprocess.PIPE)
        :param text:  (Default value = None)
        :param return_process:  (Default value = False)
        :param collect_stripped_text:  (Default value = False)
        :param verbose:  (Default value = True)
        :param **kwargs:
        :rtype: Union[Popen,int]

        """
        if isinstance(cmd_args, str):
            if ("&&" in cmd_args) and (platform.system() == "Windows"):
                # If && is split on MacOS everything is executed seperately,
                cmd_args = cmd_args.split()
            else:
                if not isinstance(cmd_args, list):
                    cmd_args = [cmd_args]
        if collect_stripped_text:
            return_process = False
        p = subprocess.Popen(
            cmd_args, *args, stdin=stdin, stdout=stdout, text=text, **kwargs
        )
        if return_process:
            return p
        text_collected = (
            []
        )  # TODO: Find out built-ins on polling and collecting this output
        while True:
            cur_status = p.poll()
            if cur_status:  # 0s won't be printed
                print(cur_status)
            output = p.stdout.readline()
            if (output == "") and p.poll() is not None:  # might be redundant
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
    def chain_and_execute_commands(cmds: List[str], *args, **kwargs) -> int:
        """


        :param cmds:
        :type cmds: List[str]
        :param *args:
        :param **kwargs:
        :rtype: int

        """
        cmd = " && ".join(cmds)
        kwargs["shell"] = True
        kwargs["text"] = True
        rc = CommonPSCommands.run_command(cmd, *args, **kwargs)
        return rc

    @staticmethod
    def get_python_dirs():
        """ """
        p = Path(".")
        current_files = list(p.iterdir())
        all_python_dirs = list(
            filter(
                lambda x: x.is_dir()
                          and ("." not in str(x))
                          and (not str(x).startswith("__")),
                current_files,
            )
        )
        return all_python_dirs

    @staticmethod
    def get_traceback_file_origin(e):
        """


        :param e:

        """
        path_to_loaded_module = e.__traceback__.tb_next.tb_frame.f_locals["__file__"]
        return path_to_loaded_module

    @staticmethod
    def read_toml(path_to_toml, start_line="tool.poetry.dependencies", verbose: bool = False) -> Dict[str, str]:
        """
        Reads for toml file using open context manager in order to reduce 3rd party toml parser deps

        :param path_to_toml:
        :param start_line: (Default value = "tool.poetry.dependencies")

        """
        # TODO: This might not work if a dependency spans multiple lines
        toml_dict = defaultdict(lambda: {})
        all_dicts = deque()
        with open(path_to_toml, "r") as f:
            all_lines = f.readlines()
            for i, l in enumerate(all_lines):
                is_section = ('[' in l) and (']' in l) and ('=' not in l)
                if is_section:
                    cur_section_name = l.replace('[', '').replace(']', '').strip()
                    cur_dict = toml_dict[cur_section_name]
                else:
                    cur_dict = all_dicts.pop()
                cur_line = l.strip()
                if is_section:
                    all_dicts.append(cur_dict)
                elif not is_section:
                    if verbose:
                        print(cur_line)
                    if cur_line:
                        key, *value = cur_line.split(
                            "="
                        )  # assuming we have simple dependencies with 1 = sign
                        key = key.strip()
                        value = "=".join(value)
                        if len(value) == 2:
                            pass
                        else:
                            value = value.replace('"', "").strip()

                        cur_dict[key] = value
                    all_dicts.append(cur_dict)
        if start_line:
            dict_to_return = toml_dict[start_line].copy()
            return dict_to_return
        return toml_dict

    @staticmethod
    def echo_yes(return_cmd: bool = False) -> Union[str, Popen]:
        """


        :param return_cmd:  (Default value = False)
        :type return_cmd: bool
        :rtype: Union[str,Popen]

        """
        # TODO: Refactor for different platforms
        #     cur_os = platform.system()
        #     if cur_os == "Darwin":

        y_cmd = "yes"
        if return_cmd:
            return f"echo {y_cmd} | "
        use_shell = False
        if platform.system() == "Windows":
            use_shell = True
        p1 = subprocess.Popen(
            ["echo", y_cmd], stdout=subprocess.PIPE, text=True, shell=use_shell
        )
        return p1

    @staticmethod
    def parse_requirements_txt(reqs_path: str) -> List[Dict[str, Union[str, bool]]]:
        """


        :param reqs_path:
        :type reqs_path: str
        :rtype: List[Dict[str,Union[str,bool]]]

        """
        all_dependencies = []
        with open(reqs_path, "r") as f:
            lines = list(filter(None, f.read().splitlines()))
            lines = list(
                map(lambda x: x.split("#")[0] if "#" in x else x, lines)
            )  # remove comments
            lines = list(filter(None, lines))
            for dep in lines:
                cur_dep = {}
                cur_dep["line_in_reqs_txt"] = dep
                cur_dep["name"] = ""
                cur_dep["is_git_dependency"] = False
                cur_dep["is_pinned"] = False
                if dep.startswith("git"):
                    try:
                        cur_dep["name"] = dep.split("/")[-1]
                    except Exception as e:
                        cur_dep["name"] = dep
                        print(e)
                    cur_dep["is_git_dependency"] = True
                elif "==" in dep:
                    cur_dep["name"] = dep.split("==")[0]
                    cur_dep["is_pinned"] = True
                else:
                    cur_dep["name"] = dep
                all_dependencies.append(cur_dep)
        return all_dependencies

    @staticmethod
    def relate_paths_using_dot_notation(
            first_path: PathLike, second_path: PathLike
    ) -> str:
        """
        Get the first path relative to second path using dot notation

        :param first_path:
        :type first_path: PathLike
        :param second_path:
        :type second_path: PathLike
        :rtype: str

        """
        abs_path_1 = Path(first_path).resolve()
        if abs_path_1.is_file() and (
                abs_path_1.name == "__init__.py"
        ):  # have to point to dir containing file if this is True
            abs_path_1 = abs_path_1.parent
        abs_path_2 = Path(second_path).resolve()
        if abs_path_2.name == "__init__.py":
            abs_path_2 = (
                abs_path_2.parent
            )  # Don't care if its a file or dir, unless __init__.py
        try:
            relative_path = abs_path_1.relative_to(abs_path_2)
            return relative_path.as_posix()
        except ValueError:
            print(
                "Relating directories using dot notation from first_path -> second_path"
            )
            common_path = Path(os.path.commonpath([abs_path_1, abs_path_2]))
            path_to_abs_path_1_from_common = abs_path_1.relative_to(common_path)
            path_to_abs_path_2_from_common = abs_path_2.relative_to(common_path)
            relative_dots = [
                Path(os.pardir) for _ in path_to_abs_path_1_from_common.parts
            ]
            if relative_dots:
                dots_to_common_path_from_path_1 = reduce(
                    lambda x, y: x.joinpath(y), relative_dots
                )
                dots_from_path_1_to_path_2 = dots_to_common_path_from_path_1.joinpath(
                    path_to_abs_path_2_from_common
                ).as_posix()
            else:
                dots_from_path_1_to_path_2 = path_to_abs_path_2_from_common.as_posix()
            return dots_from_path_1_to_path_2


class CondaEnvManager:
    """ """

    @staticmethod
    def get_env_info_from_lines(all_lines):
        """


        :param all_lines:

        """
        all_env_names = []
        all_env_paths = []
        for l in all_lines:
            env_name, *env_path = l.split()
            all_env_names.append(env_name)
            all_env_paths.append("".join(env_path).strip())
        return all_env_names, all_env_paths

    @staticmethod
    def get_conda_envs():
        """ """
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
        """ """
        kernel_cmd = ["jupyter", "kernelspec", "list"]
        with subprocess.Popen(kernel_cmd, stdout=subprocess.PIPE, text=True) as p:
            output, errors = p.communicate()

        all_lines = output.strip().replace(r"*", " ").split("\n")
        all_lines = [l.strip() for l in all_lines if ("Available kernels" not in l)]
        kernel_names, kernel_paths = CondaEnvManager.get_env_info_from_lines(all_lines)
        return kernel_names, kernel_paths

    @staticmethod
    def lookup_kernel(env_name: str):
        """


        :param env_name:
        :type env_name: str

        """
        rel_path_to_kernel = f"Jupyter/kernels/{env_name}/kernel.json"
        if platform.system() == "Windows":
            # TODO: Test on PC
            path_to_kernel = (
                Path(os.getenv("APPDATA")).resolve().joinpath(rel_path_to_kernel)
            )
        else:
            path_to_kernel = (
                Path(f"~/Library").expanduser().joinpath(rel_path_to_kernel)
            )
        try:
            assert path_to_kernel.exists()
        except Exception as e:
            print(e)
            raise e
        return path_to_kernel

    @staticmethod
    def load_kernel_config(kernel_config_path):
        """


        :param kernel_config_path:

        """
        with open(kernel_config_path, "r") as f:
            kernel_config = json.load(f)
        return kernel_config

    @staticmethod
    def verify_if_kernel_config_contains_env_path(env_name: str, kernel_config: Dict[str, Any]) -> bool:
        """

        This method determines if the conda_env_name == ipykernel name and returns True or False


        :param str env_name:
        :param kernel_config:

        """
        argv = kernel_config.get("argv", [])
        if argv:
            path_to_py = Path(argv[0])
            try:
                assert (env_name in path_to_py.parts) and (kernel_config.get('display_name', '') == env_name)
                return True
            except Exception as e:
                print(e)
                print("The Kernel is improperly matched to its conda name!")
                return False
        else:
            print("Kernel config doesn't exist")
            return False

    @staticmethod
    def verify_kernel_pairing(env_name: str):
        """

        This determines if the ipykernel name matches the conda env name.

        :param str env_name:

        """
        kernel_config_path = CondaEnvManager.lookup_kernel(env_name)
        kernel_config = CondaEnvManager.load_kernel_config(kernel_config_path)
        kernel_paired_to_env = (
            CondaEnvManager.verify_if_kernel_config_contains_env_path(
                env_name, kernel_config
            )
        )
        return kernel_paired_to_env

    @staticmethod
    def conda_and_kernel_name_available(clean_proj_name, both=False):
        """


        :param clean_proj_name:
        :param both:  (Default value = False)

        """
        kernel_names, _ = CondaEnvManager.get_kernel_specs()
        conda_names, _ = CondaEnvManager.get_conda_envs()

        kernel_name_taken = clean_proj_name in kernel_names
        conda_name_taken = clean_proj_name in conda_names
        if both:
            return (not conda_name_taken) and (not kernel_name_taken)
        else:
            return (not conda_name_taken), (not kernel_name_taken)

    @staticmethod
    def get_path_to_conda_env(env_name: str) -> str:
        """


        :param env_name:
        :type env_name: str
        :rtype: str

        """
        conda_base = CondaEnvManager.get_conda_base()
        path_to_env = (Path(conda_base) / f"envs/{env_name}").resolve().as_posix()
        return path_to_env

    @staticmethod
    def reset_conda_channel_priority(act_env_str: str, *args, **kwargs) -> int:
        """


        :param act_env_str:
        :type act_env_str: str
        :param *args:
        :param **kwargs:
        :rtype: int

        """
        cmd = "conda config --set channel_priority false"
        rc = CommonPSCommands.chain_and_execute_commands(
            [act_env_str, cmd], *args, **kwargs
        )
        return rc

    @staticmethod
    def upgrade_pip(act_env_str: str, *args, **kwargs) -> int:
        """


        :param act_env_str:
        :type act_env_str: str
        :param *args:
        :param **kwargs:
        :rtype: int

        """
        yes = CommonPSCommands.echo_yes(True)
        cmd = yes + "python -m pip install --upgrade pip setuptools wheel"
        rc = CommonPSCommands.chain_and_execute_commands(
            [act_env_str, cmd], *args, **kwargs
        )
        return rc

    @staticmethod
    def install_ipykernel(act_env_str: str, *args, **kwargs) -> int:
        """


        :param act_env_str:
        :type act_env_str: str
        :param *args:
        :param **kwargs:
        :rtype: int

        """
        yes = CommonPSCommands.echo_yes(True)
        cmd = yes + "conda install notebook ipykernel"  # TODO: Don't install, use poetry add
        rc = CommonPSCommands.chain_and_execute_commands(
            [act_env_str, cmd], *args, **kwargs
        )
        return rc

    @staticmethod
    def add_conda_forge_priority(act_env_str: str, *args, **kwargs) -> int:
        """


        :param act_env_str:
        :type act_env_str: str
        :param *args:
        :param **kwargs:
        :rtype: int

        """
        cmd = "conda config --add channels conda-forge"
        rc = CommonPSCommands.chain_and_execute_commands(
            [act_env_str, cmd], *args, **kwargs
        )
        if rc == 0:
            cmd = "conda config --set channel_priority strict"
            rc = CommonPSCommands.chain_and_execute_commands(
                [act_env_str, cmd], *args, **kwargs
            )
            return rc
        else:
            return rc

    @staticmethod
    def register_kernel(env_name: str, *args, **kwargs) -> int:
        """


        :param env_name:
        :type env_name: str
        :param *args:
        :param **kwargs:
        :rtype: int

        """
        act_env_str = CondaEnvManager.activate_conda_env(env_name, return_cmd=True)
        cmd = (
            f"ipython kernel install --user --name {env_name} --display-name {env_name}"
        )
        rc = CommonPSCommands.chain_and_execute_commands(
            [act_env_str, cmd], *args, **kwargs
        )
        return rc

    @staticmethod
    def get_available_conda_versions():
        """

        Returns a dict of python versions that are available for Conda:
        the keys are the python versions
        the values are tuples corresponding to the Name, Version, Build, and Channel
        :return:
        """
        args = ["conda", "search", "python"]
        p = CommonPSCommands.run_command(args, text=True, return_process=True)
        output, errors = p.communicate()
        versions_available_ls = list(map(lambda x: x.strip().split(), output.splitlines()[2::]))
        versions_available = defaultdict(list)
        for v in versions_available_ls:
            cur_version = v[1]
            versions_available[cur_version].append(tuple(v))
        return versions_available

    @staticmethod
    def get_suitable_python_versions_for_conda(python_version: str):
        """
        Returns a dict of available conda python interpreter versions that meet the python_version contraint passed in

        :param python_version:
        :return:
        """
        parse_single_constraint = import_optional_dependency('parse_single_constraint')
        parsed_pyproject_toml_python_version = parse_single_constraint(python_version)
        available_versions = CondaEnvManager.get_available_conda_versions()
        parsed_versions = {pv: parse_single_constraint(pv) for pv in available_versions.keys()}
        filtered_versions = {}
        for conda_version, parsed_conda_version in parsed_versions.items():
            if parsed_pyproject_toml_python_version.allows(parsed_conda_version):
                filtered_versions[conda_version] = parsed_conda_version
        return filtered_versions

    @staticmethod
    def get_python_version_for_conda(python_version: str):
        """
        This returns a str that specifies the python version to use for a new conda python environment
        The return str must start with 'python='

        :param python_version:
        :return:
        """
        if ("^" in python_version) or ("~" in python_version) or ("*" in python_version):
            filtered_versions = CondaEnvManager.get_suitable_python_versions_for_conda(python_version)
            python_version_new = ""
            if ("^" in python_version):
                python_version_new = list(filtered_versions.keys())[-1]
            elif ("~" in python_version):
                python_version_new = list(filtered_versions.keys())[0]
            elif ("*" in python_version):
                python_version_new = list(filtered_versions.keys())[-1]
            python_version_str = f"python={python_version_new}"
        else:
            python_version_str = f"python={python_version}"
        return python_version_str

    @staticmethod
    def create_conda_env(env_name: str, python_version: str) -> int:
        """


        :param env_name:
        :type env_name: str
        :param python_version:
        :type python_version: str
        :rtype: int

        """
        p0 = CommonPSCommands.echo_yes(return_cmd=False)
        python_version_str = CondaEnvManager.get_python_version_for_conda(python_version)
        args = ["conda", "create", "-n", env_name, python_version_str]
        rc = CommonPSCommands.run_command(args, stdin=p0.stdout, text=True)
        return rc

    @staticmethod
    def init_prev_made_conda_env(env_name: str) -> int:
        """


        :param env_name:
        :type env_name: str
        :rtype: int

        """
        act_env = CondaEnvManager.activate_conda_env(env_name, return_cmd=True)
        rc = CondaEnvManager.reset_conda_channel_priority(act_env)
        assert rc == 0
        rc = CondaEnvManager.upgrade_pip(act_env)
        assert rc == 0
        rc = CondaEnvManager.install_ipykernel(act_env)  # TODO: Don't install, use poetry add
        assert rc == 0
        rc = CondaEnvManager.add_conda_forge_priority(act_env)
        assert rc == 0
        rc = CondaEnvManager.register_kernel(env_name)
        assert rc == 0
        return rc

    # @staticmethod
    # def uninstall_kernel(kernel_name: str = ""):
    #     """
    #
    #
    #     :param kernel_name:  (Default value = "")
    #     :type kernel_name: str
    #
    #     """
    #     try:
    #         kernel_names, _ = CondaEnvManager.get_kernel_specs()
    #         assert kernel_name in kernel_names
    #     except Exception as e:
    #         print(f"Kernel {kernel_name!r} does not exist!")
    #     kernel_cmd = ["jupyter", "kernelspec", "uninstall", kernel_name, "-y"]
    #     y = CommonPSCommands.echo_yes(return_cmd=True)
    #     kernel_cmd_str = " ".join(kernel_cmd)
    #     cmd = y + kernel_cmd_str

    @staticmethod
    def uninstall_kernel(kernel_name: str = ""):
        """


        :param kernel_name:  (Default value = "")
        :type kernel_name: str

        """
        try:
            kernel_names, _ = CondaEnvManager.get_kernel_specs()
            assert kernel_name in kernel_names
        except Exception:
            print(f"Kernel {kernel_name!r} does not exist!")
        kernel_cmd = ["jupyter", "kernelspec", "uninstall", kernel_name, "-y"]
        y = CommonPSCommands.echo_yes(return_cmd=True)
        kernel_cmd_str = " ".join(kernel_cmd)
        cmd = y + kernel_cmd_str
        if platform.system() == "Windows":
            rc = CommonPSCommands.run_command(kernel_cmd, text=True, shell=False)
        else:
            # TODO: Debug this for mac
            rc = CommonPSCommands.run_command([cmd], text=True, shell=True)
        return rc

    @staticmethod
    def uninstall_conda_env(conda_env_name: str = ""):
        """


        :param conda_env_name:  (Default value = "")
        :type conda_env_name: str

        """
        try:
            kernel_names, _ = CondaEnvManager.get_conda_envs()
            assert conda_env_name in kernel_names
        except Exception:
            print(f"Conda {conda_env_name!r} does not exist!")
        conda_cmd = ["conda", "env", "remove", "-n", conda_env_name]
        rc = CommonPSCommands.run_command(conda_cmd, text=True)
        return rc

    @staticmethod
    def uninstall_conda_and_kernel(conda_env_name: str = "", kernel_name: str = ""):
        """


        :param conda_env_name:  (Default value = "")
        :type conda_env_name: str
        :param kernel_name:  (Default value = "")
        :type kernel_name: str

        """
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
        """


        :param conda_env_names:

        """
        for env in conda_env_names:
            print(env)
            CondaEnvManager.uninstall_conda_and_kernel(env, env)
            print()

    @staticmethod
    def get_conda_base() -> str:
        """



        :rtype: str

        """
        # TODO: Make this work on all platforms
        echo_cmds = ["conda", "info", "--base"]
        if platform.system() == "Windows":
            # TODO: This always prints out for windows commands
            rc, text = CommonPSCommands.run_command(
                echo_cmds,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                verbose=False,
                collect_stripped_text=True,
            )
            output = text[
                0
            ].strip()  # TODO: last elem is a new line str for some reason
        else:
            p = CommonPSCommands.run_command(
                echo_cmds,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                return_process=True,
                shell=False,
            )
            output, errors = p.communicate()
        return output.strip()

    @staticmethod
    def get_conda_sh() -> str:
        """



        :rtype: str

        """
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
        """ """
        path_to_dot_conda_envs = Path("~/.conda/environments.txt").expanduser()
        assert path_to_dot_conda_envs.exists()
        with open(path_to_dot_conda_envs, "r") as f:
            all_lines = f.readlines()
            all_lines = [l.strip() for l in all_lines]
        try:
            assert len(all_lines) == 1
        except Exception as e:
            print(e)
            print(
                f"Multiple base conda environments exist!\n inspect\n{path_to_dot_conda_envs}"
            )
            print("Returning first line")
        return all_lines[0]

    @staticmethod
    def activate_conda_env(env_name: str, return_cmd: bool = False) -> str:
        """


        :param env_name:
        :type env_name: str
        :param return_cmd:  (Default value = False)
        :type return_cmd: bool
        :rtype: str

        """
        #     echo_cmd = ["python", "--version"]
        #     echo_cmd_str = " ".join(echo_cmd)
        conda_sh = CondaEnvManager.get_conda_sh()

        source_conda = ["source", conda_sh]
        " ".join(source_conda)

        conda_act = ["conda", "activate", env_name]
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
            p = subprocess.Popen(
                conda_act_test_str,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                cwd=Path(conda_sh).parent,
                shell=True,
            )
            return p

    @staticmethod
    def create_and_init_conda_env(clean_env_name: str, python_version: str) -> None:
        """


        :param clean_env_name:
        :type clean_env_name: str
        :param python_version:
        :type python_version: str
        :rtype: None

        """
        rc = CondaEnvManager.create_conda_env(clean_env_name, python_version)
        assert rc == 0
        rc = CondaEnvManager.init_prev_made_conda_env(clean_env_name)
        assert rc == 0


class GitProjectManager:
    """ """

    @staticmethod
    def write_gitignore_contents(proj_dir: Path, gitignore_text: str):
        """


        :param proj_dir:
        :type proj_dir: Path
        :param gitignore_text:
        :type gitignore_text: str

        """
        output_file = (proj_dir / ".gitignore").as_posix()
        with open(output_file, "w") as f:
            f.write(gitignore_text)
        assert Path(output_file).exists()

    @staticmethod
    def init_dir(dir_path):
        """


        :param dir_path:

        """
        if dir_path is None:
            dir_path = Path(".").resolve().as_posix()
        else:
            dir_path = Path(dir_path)
            if dir_path.is_file():
                dir_path = dir_path.parent
        git_cmds = ["git", "init"]
        rc = CommonPSCommands.run_command(git_cmds, cwd=dir_path, text=True)
        return rc

    @staticmethod
    def add_repo(dir_path, repo_name, uname=""):
        """


        :param dir_path:
        :param repo_name:
        :param uname:  (Default value = "")

        """
        # TODO: Rename to add remote repo origin
        assert uname
        repo_to_add = f"git@github.com:{uname}/{repo_name}.git"
        git_cmds = ["git", "remote", "add", "origin", repo_to_add]
        with subprocess.Popen(
                git_cmds, stdout=subprocess.PIPE, text=True, cwd=dir_path
        ) as p:
            output, errors = p.communicate()
        print(output)
        print(errors)

    @staticmethod
    def replace_global_git_username(new_username):
        """


        :param new_username:

        """
        # TODO: Rename to add remote repo origin
        assert new_username
        dir_path = os.getcwd()
        git_cmds = [
            "git",
            "config",
            "--global",
            "--replace-all",
            "user.name",
            f'"{new_username}"',
        ]
        with subprocess.Popen(
                git_cmds, stdout=subprocess.PIPE, text=True, cwd=dir_path
        ) as p:
            output, errors = p.communicate()
        print(output)
        print(errors)

    @staticmethod
    def replace_global_git_email(new_email):
        """


        :param new_email:

        """
        assert new_email
        dir_path = os.getcwd()
        git_cmds = [
            "git",
            "config",
            "--global",
            "--replace-all",
            "user.email",
            f'"{new_email}"',
        ]
        with subprocess.Popen(
                git_cmds, stdout=subprocess.PIPE, text=True, cwd=dir_path
        ) as p:
            output, errors = p.communicate()
        print(output)
        print(errors)

    @staticmethod
    def verify_github_ssh():
        """ """
        # https://docs.github.com/en/github-ae@latest/github/authenticating-to-github/checking-for-existing-ssh-keys
        dir_path = os.getcwd()
        git_cmds = ["ssh", "-T", "git@github.com"]
        with subprocess.Popen(
                git_cmds, stdout=subprocess.PIPE, text=True, cwd=dir_path
        ) as p:
            output, errors = p.communicate()
        print(output)
        print(errors)

    @staticmethod
    def create_ssh_key():
        """ """
        # https://docs.github.com/en/github-ae@latest/github/authenticating-to-github/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent
        dir_path = os.getcwd()
        git_cmds = ["ssh", "-T", "git@github.com"]
        with subprocess.Popen(
                git_cmds, stdout=subprocess.PIPE, text=True, cwd=dir_path
        ) as p:
            output, errors = p.communicate()
        print(output)
        print(errors)


class LocalProjectManager:
    """ """

    @staticmethod
    def init_current_dir_as_a_poetry_conda_project(
            clean_env_name: str = "hello_world",
            python_version: str = "3.9",
            add_git: bool = False,
    ) -> int:
        """


        :param clean_env_name: A name for your conda env without illegal characterss (Default value = "hello_world")
        :type clean_env_name: str
        :param python_version: The python version of conda you're interested in (Default value = "3.9")
        :type python_version: str
        :param add_git: Initialize the current directory with `git init` (Default value = False)
        :type add_git: bool
        :returns: 0
        :rtype: int

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
                print(
                    "Make sure that you install gy if you want to add .gitignore files"
                )
        pyproject_toml_dir = PoetryProjectManager.get_pyproject_toml(os.getcwd()).parent.as_posix()
        print("Now running add_notebook_ipykernel_dependencies_to_pypoetry")
        rc = PoetryProjectManager.add_notebook_ipykernel_dependencies_to_pypoetry(
            clean_env_name, Path(pyproject_toml_dir).as_posix()
        )
        return rc

    @staticmethod
    def create_init_link_conda_env_to_existing_poetry_project(
            clean_env_name: str = "hello_world", python_version: str = "3.9"
    ):
        """

        This assumes that the current directory is the root folder of the poetry project

        :param clean_env_name:  (Default value = "hello_world")
        :type clean_env_name: str
        :param python_version:  (Default value = "3.9")
        :type python_version: str

        """
        CondaEnvManager.create_and_init_conda_env(clean_env_name, python_version)
        PoetryProjectManager.link_poetry_proj_with_conda_env(clean_env_name)
        cur_dir = os.getcwd()
        rc = PoetryProjectManager.add_notebook_ipykernel_dependencies_to_pypoetry(clean_env_name, cur_dir)
        return rc

    @staticmethod
    def migrate_requirements_to_pypoetry_toml(
            poetry_proj_conda_env_name: str,
            src_path_to_reqs: str = None,
            dest_path_to_pyproject_toml: str = None,
            warn_before_add=True,
    ):
        """


        :param poetry_proj_conda_env_name:
        :type poetry_proj_conda_env_name: str
        :param src_path_to_reqs:  (Default value = None)
        :type src_path_to_reqs: str
        :param dest_path_to_pyproject_toml:  (Default value = None)
        :type dest_path_to_pyproject_toml: str
        :param try_pinned_versions:  (Default value = False)
        :type try_pinned_versions: bool
        :param warn_before_add:  (Default value = True)

        """
        cur_dir = Path(".").resolve()
        if src_path_to_reqs is None:
            requirements_txt_name = "requirements.txt"
            path_to_reqs = cur_dir.joinpath(requirements_txt_name)
        else:
            path_to_reqs = Path(src_path_to_reqs)
        assert path_to_reqs.exists()
        path_to_reqs = path_to_reqs.resolve()

        if dest_path_to_pyproject_toml is None:
            dir_containing_pyproject_toml = cur_dir.as_posix()
        else:
            dir_containing_pyproject_toml = Path(dest_path_to_pyproject_toml).parent.as_posix()

        rc = PoetryProjectManager.add_poetry_package_from_requirements_txt(
            dir_containing_pyproject_toml=dir_containing_pyproject_toml,
            poetry_proj_conda_env_name=poetry_proj_conda_env_name,
            path_to_requirements_txt=path_to_reqs.as_posix(),
            warn_before_add=warn_before_add,
        )
        return rc

    @staticmethod
    def iterate_and_add_dependencies(toml_file_dependencies_section_dict, dest_pyproject_toml_dir: str,
                                     poetry_proj_conda_env_name: str, toml_section_type: str = "",
                                     warn_before_add: bool = True):
        if toml_section_type == "dev":
            toml_section_type = "development"
            options = "-D"
        else:
            toml_section_type = "required"
            options = ""
        for dependency_name, dependency_val in toml_file_dependencies_section_dict.items():
            dep_str = f"{dependency_name}"
            if dep_str.lower() != "python":
                if warn_before_add:
                    q0 = "(i.e. 'poetry add {...}')"
                    q1 = f"Enter [q] to break, [c] to add unpinned {toml_section_type} dependency, [a] to input your own or manually enter the pinned dependency {q0}, [p] to pass"
                    resp = input(
                        f"Would you like to add the following unpinned {toml_section_type} dependency ({dep_str!r}) (it's pinned version is {dependency_val!r}) to {poetry_proj_conda_env_name!r}?\n{q1}"
                    )
                else:
                    resp = "c"
                if resp.lower() == "q":
                    print("Now raising Exception to exit")
                    raise Exception
                elif resp.lower() in ["c", "a"]:
                    if resp.lower() == "a":
                        dep_str = input(
                            "Input your own dependency to fill in 'poetry add {...}' and quotes as needed"
                        )
                        options = ""
                    try:
                        PoetryProjectManager.add_dependency_to_pyproject_toml(
                            dir_containing_pyproject_toml=dest_pyproject_toml_dir,
                            poetry_proj_conda_env_name=poetry_proj_conda_env_name,
                            dependency=dep_str,
                            wrap_in_quotes=False,
                            options=options,
                        )
                    except Exception as e:
                        print("See output to identify un-addable dependency")
                        print(e)
                else:
                    continue
        else:
            return 0

    @staticmethod
    def migrate_pyproject_toml_to_pyproject_toml(
            poetry_proj_conda_env_name: str,
            src_pyproject_toml: str = None,
            dest_pyproject_toml: str = None,
            warn_before_add: bool = True,
            dependency_section_name: str = ""):
        """

        if dependency_section_name is empty, read both required and dev dependencies from .toml file

        :param poetry_proj_conda_env_name:
        :type poetry_proj_conda_env_name: str
        :param src_pyproject_toml:  (Default value = None)
        :type src_pyproject_toml: str
        :param dest_pyproject_toml:  (Default value = None)
        :type dest_pyproject_toml: str
        :param warn_before_add:  (Default value = True)
        :type warn_before_add: bool

        """

        assert Path(src_pyproject_toml).resolve().exists() and Path(dest_pyproject_toml).resolve().exists()

        dependencies = CommonPSCommands.read_toml(src_pyproject_toml, dependency_section_name)
        if dependency_section_name:
            dep_dict = {}
            dep_dict[dependency_section_name] = dependencies.copy()
            dependencies = dep_dict.copy()
        dest_pyproject_toml_dir = Path(dest_pyproject_toml).parent.as_posix()
        dev_dependency_section_specified = ("dev-dependencies" in dependency_section_name)

        if dev_dependency_section_specified:
            dependency_type = "dev"
        elif (not dev_dependency_section_specified) and (dependency_section_name != ""):
            dependency_type = ""
        else:
            dependency_type = "all"

        if (dependency_type == "all") or dev_dependency_section_specified:
            toml_section_type = "dev"
            dev_dependencies = dependencies.get('tool.poetry.dev-dependencies')
            LocalProjectManager.iterate_and_add_dependencies(toml_file_dependencies_section_dict=dev_dependencies,
                                                             toml_section_type=toml_section_type,
                                                             dest_pyproject_toml_dir=dest_pyproject_toml_dir,
                                                             poetry_proj_conda_env_name=poetry_proj_conda_env_name,
                                                             warn_before_add=warn_before_add)
        if (dependency_type == "all") or (not dev_dependency_section_specified):
            toml_section_type = ""
            if dependency_section_name:
                dependencies_req = dependencies.get(dependency_section_name)
            else:
                dependencies_req = dependencies.get("tool.poetry.dependencies")
            LocalProjectManager.iterate_and_add_dependencies(toml_file_dependencies_section_dict=dependencies_req,
                                                             toml_section_type=toml_section_type,
                                                             dest_pyproject_toml_dir=dest_pyproject_toml_dir,
                                                             poetry_proj_conda_env_name=poetry_proj_conda_env_name,
                                                             warn_before_add=warn_before_add)
        return 0

    @staticmethod
    def get_requirements_txt_path(
            requirements_directory: Path = None, requirements_txt_name: str = None
    ):
        """


        :param requirements_directory:  (Default value = None)
        :type requirements_directory: Path
        :param requirements_txt_name:  (Default value = None)
        :type requirements_txt_name: str

        """
        if requirements_directory is None:
            requirements_directory = Path(".").resolve()
        rc = 0
        if requirements_txt_name is None:
            path_to_requirements_txt = requirements_directory.joinpath(
                "requirements.txt"
            )
        else:
            path_to_requirements_txt = requirements_directory.joinpath(
                requirements_txt_name
            )
        try:
            assert path_to_requirements_txt.exists()
            path_to_requirements_txt = path_to_requirements_txt.as_posix()
        except Exception as e:
            print(e)
            print("There's no requirements file to add! Returning")
            rc = 1
        return rc, path_to_requirements_txt

    @staticmethod
    def create_conda_env_for_existing_pyproject_toml(pyproject_toml_path: str):
        """
        This creates a conda env for a pre-existing pyproject.toml file. This function should be used if one is interested
        in using conda instead of .venv for a virtual environment.

        :param str pyproject_toml_path:
        :return:
        """
        old_path = os.getcwd()
        pyproject_toml_path = Path(pyproject_toml_path).resolve()
        assert pyproject_toml_path.exists()
        os.chdir(pyproject_toml_path.parent)  # change dir to root folder; assume poetry.toml, poetry.lock are adjacent
        toml_dict = CommonPSCommands.read_toml(pyproject_toml_path, start_line="")
        project_name = toml_dict.get('tool.poetry', {}).get('name', {})

        # Assume we want to register kernel
        conda_env_name_available = CondaEnvManager.conda_and_kernel_name_available(clean_proj_name=project_name,
                                                                                   both=True)
        python_version = toml_dict.get('tool.poetry.dependencies', {}).get('python', {})
        assert conda_env_name_available and python_version
        rc = LocalProjectManager.create_init_link_conda_env_to_existing_poetry_project(clean_env_name=project_name,
                                                                                       python_version=python_version)
        os.chdir(old_path)  # Go back to old dir
        return rc


class SublimeBuildConfigGenerator:
    """ """

    @staticmethod
    def get_filepath_to_sublime_text_build_config(env_name):
        """


        :param env_name:

        """
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
        """


        :param env_name:

        """
        path_to_env = CondaEnvManager.get_path_to_conda_env(env_name)
        path_to_python_bin = Path(path_to_env).joinpath("bin").as_posix()
        SublimeBuildConfigGenerator.export_sublime_text_build_config(
            path_to_python_bin, env_name
        )

    @staticmethod
    def export_sublime_text_build_config(path_to_python_bin, build_config_name):
        """


        :param path_to_python_bin:
        :param build_config_name:

        """
        sublime_build_config_file_contents = (
            SublimeBuildConfigGenerator.get_sublime_text_build_config_contents(
                path_to_python_bin
            )
        )
        sublime_config_filepath = (
            SublimeBuildConfigGenerator.get_filepath_to_sublime_text_build_config(
                build_config_name
            )
        )
        print(sublime_config_filepath)
        with open(sublime_config_filepath, "w") as f:
            f.write(json.dumps(sublime_build_config_file_contents, indent=4))

    @staticmethod
    def get_sublime_text_build_config_contents(path_to_python_bin: str):
        """


        :param path_to_python_bin:
        :type path_to_python_bin: str

        """
        sublime_build_config_file_contents = {
            "path": path_to_python_bin,
            "cmd": ["python", "-u", "$file"],
            "file_regex": '^[ ]*File "(...*?)", line ([0-9]*)',
            "selector": "source.python",
        }
        return sublime_build_config_file_contents


if __name__ == "__main__":
    # env_name = "hello_world"
    # python_version = "3.9"
    # rc = LocalProjectManager.init_current_dir_as_a_poetry_conda_project(env_name, python_version)
    clean_env_name = "py39"
    rc = CondaEnvManager.init_prev_made_conda_env(clean_env_name)
    sys.exit()
