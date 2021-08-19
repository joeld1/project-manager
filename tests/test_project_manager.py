import os
import types
from collections import defaultdict
from contextlib import nullcontext as does_not_raise
from pathlib import Path

import pytest

from project_manager import (
    CommonPSCommands,
    CondaEnvManager,
    GitProjectManager,
    LocalProjectManager,
    PoetryProjectManager,
    ProjectManager,
    SublimeBuildConfigGenerator,
)
from project_manager.project_manager import (
    convert_camel_to_snakecase,
    import_optional_dependency,
)

PATH_TO_REQUIREMENTS_TXT: str = Path(__file__).parent.joinpath("requirements.txt").as_posix()
PATH_TO_PYPROJECT_TOML_FILE: str = Path(__file__).parent.parent.resolve().joinpath("patches/sandboxenv/verifypm/pyproject.toml")
PATH_TO_POETRY_TOML_FILE: str = Path(__file__).parent.parent.resolve().joinpath("poetry.toml")


@pytest.fixture
def conda_env_manager():
    return CondaEnvManager()


@pytest.fixture
def project_manager():
    return ProjectManager()


@pytest.fixture
def poetry_project_manager():
    return PoetryProjectManager()


@pytest.fixture
def common_ps_commands():
    return CommonPSCommands()


@pytest.fixture
def git_project_manager():
    return GitProjectManager()


@pytest.fixture
def local_project_manager():
    return LocalProjectManager()


@pytest.fixture
def sublime_build_config_generator():
    return SublimeBuildConfigGenerator()


@pytest.fixture
def parse_requirements_txt():
    reqs = CommonPSCommands.parse_requirements_txt(PATH_TO_REQUIREMENTS_TXT)
    return reqs


class TestProjectManager:
    def test_create_proj_name(self):
        assert False

    def test_find_env_and_add_dependency(self):
        assert False

    def test_get_gitignore_contents(self):
        assert False

    def test_create_gitignores_in_repos(self):
        assert False

    def test_add_git_ignore_to_project(self):
        assert False


class TestPoetryProjectManager:

    def test_search_for_toml_files(self):
        assert False

    def test_get_poetry_project_dir(self):
        assert False

    def test_get_poetry_toml(self):
        assert False

    def test_get_pyproject_toml(self):
        assert False

    def test_get_poetry_module_dependencies(self):
        assert False

    def test_get_import_error_dependencies_from_imported_py_poetry_proj_file(self):
        assert False

    def test_add_poetry_package_from_exception(self):
        assert False

    def test_add_poetry_package(self):
        assert False

    def test_format_deps_from_reqs_txt(self, parse_requirements_txt):
        cur_dependencies = PoetryProjectManager.format_deps_from_reqs_txt(parse_requirements_txt)
        assert isinstance(cur_dependencies, dict)

    def test_add_poetry_package_from_requirements_txt(self, dir_containing_pyproject_toml: str = Path(
        PATH_TO_PYPROJECT_TOML_FILE).parent.as_posix(),
                                                      poetry_proj_conda_env_name: str = "verifypm",
                                                      path_to_requirements_txt: str = Path(
                                                          PATH_TO_REQUIREMENTS_TXT).as_posix(),
                                                      warn_before_add=True,
                                                      ):
        reqs = CommonPSCommands.parse_requirements_txt(path_to_requirements_txt)
        cur_dependencies = PoetryProjectManager.format_deps_from_reqs_txt(reqs)

        rc = LocalProjectManager.iterate_and_add_dependencies(toml_file_dependencies_section_dict=cur_dependencies,
                                                              dest_pyproject_toml_dir=dir_containing_pyproject_toml,
                                                              poetry_proj_conda_env_name=poetry_proj_conda_env_name,
                                                              toml_section_type="",
                                                              warn_before_add=warn_before_add)
        assert rc == 0

    def test_attempt_adding_dependency(self):
        assert False

    def test_prompt_before_adding_dependency(self):
        assert False

    def test_get_poetry_add_cmds_for_dependency(self):
        assert False

    def test_try_adding_dependency(self):
        assert False

    def test_add_pinned_dependency(self):
        assert False

    def test_add_dependency_to_pyproject_toml(self):
        assert False

    def test_clear_poetry_cache(self):
        assert False

    def test_execute_poetry_cmd(self):
        assert False

    def test_execute_poetry_init(self):
        assert False

    def test_get_poetry_config_virtualenv_path_cmd_for_conda_env(self):
        assert False

    def test_link_poetry_proj_with_conda_env(self):
        assert False

    def test_create_poetry_project(self):
        assert False

    def test_check_if_poetry_proj_path_is_available(self):
        assert False

    def test_create_poetry_project_cmd(self):
        assert False

    def test_get_conda_activate_str(self):
        assert False

    def test_init_poetry_project(self):
        assert False

    def test_find_poetry_toml_and_get_virtual_env_path(self):
        assert False

    def test_get_virtualenv_path_from_poetry_toml(self, path_to_poetry_toml_file=PATH_TO_POETRY_TOML_FILE):
        path_to_venv = PoetryProjectManager.get_virtualenv_path_from_poetry_toml(
            cur_poetry_file=PATH_TO_POETRY_TOML_FILE)
        assert isinstance(path_to_venv, Path)

    def test_get_virtual_env_name_from_poetry_toml(self):
        path_to_venv = PoetryProjectManager.get_virtualenv_path_from_poetry_toml(PATH_TO_POETRY_TOML_FILE)
        return path_to_venv.name

    def test_get_virtual_env_name_from_pyproject_toml(self, pyproject_toml_path=PATH_TO_PYPROJECT_TOML_FILE):
        env_name = PoetryProjectManager.get_virtual_env_name_from_pyproject_toml(
            pyproject_toml_path=pyproject_toml_path)
        assert isinstance(env_name, str)

    def test_get_poetry_proj_env_name_from_poetry_toml_for_py_file(self):
        assert False

    def test_get_missing_poetry_dependency(self):
        assert False

    def test_add_notebook_ipykernel_dependencies_to_pypoetry(self):
        assert False


class TestCommonPSCommands:
    def test_run_command(self):
        cmd = 'source /opt/homebrew/anaconda3/etc/profile.d/conda.sh && conda activate allrepos && poetry remove -D "notebook" -D "ipykernel" -D "pre-commit" -D "pytest"'
        kwargs = {'text': True,
                  'shell': True,
                  'cwd': '/Users/jd/Dropbox/Python Scripts/test-dir'}
        rc = CommonPSCommands.run_command(cmd, **kwargs)


    def test_chain_and_execute_commands(self):
        assert False

    def test_get_python_dirs(self):
        assert False

    def test_get_traceback_file_origin(self):
        assert False

    def test_read_toml(self, common_ps_commands):
        pyproject_toml_path = PATH_TO_PYPROJECT_TOML_FILE
        toml_dict = common_ps_commands.read_toml(pyproject_toml_path, start_line="")
        assert toml_dict

    def test_echo_yes(self):
        assert False

    def test_parse_requirements_txt(self):
        reqs = CommonPSCommands.parse_requirements_txt(PATH_TO_REQUIREMENTS_TXT)
        assert reqs[0]['name'] == 'fastapi'

    def test_relate_paths_using_dot_notation(self):
        assert False


class TestCondaEnvManager:

    @pytest.mark.parametrize(['all_lines', 'expected'],
                             [pytest.param(['base                     /opt/homebrew/anaconda3'],
                                           (['base'], ['/opt/homebrew/anaconda3']))])
    def test_get_env_info_from_lines(self, conda_env_manager, all_lines, expected):
        output = conda_env_manager.get_env_info_from_lines(all_lines)
        assert len(output) == 2
        all_env_names, all_env_paths = output
        assert all([isinstance(x, list) for x in output])
        base_env_name_expected = expected[0][0]
        base_env_name_output = all_env_names[0]
        assert base_env_name_output == base_env_name_expected
        assert 'conda' in all_env_paths[0]

    @pytest.mark.parametrize('expected', [pytest.param((['base'], ['/opt/homebrew/anaconda3']))])
    def test_get_conda_envs(self, conda_env_manager, expected):
        output = conda_env_manager.get_conda_envs()
        assert len(output) == 2
        all_env_names, all_env_paths = output
        assert all([isinstance(x, list) for x in output])
        base_env_name_expected = expected[0][0]
        base_env_name_output = all_env_names[0]
        assert base_env_name_output == base_env_name_expected
        assert 'conda' in all_env_paths[0]

    def test_get_kernel_specs(self, conda_env_manager):
        output = conda_env_manager.get_kernel_specs()
        kernel_names, kernel_paths = output
        assert len(kernel_names) == len(kernel_paths)
        assert isinstance(kernel_names, list) and isinstance(kernel_paths, list)
        assert all([(k in kernel_paths[i]) and ('jupyter' in kernel_paths[i].lower()) and
                    ('kernels' in kernel_paths[i].lower()) for i, k in enumerate(kernel_names)])

    @pytest.mark.parametrize(['env_name', 'expected_raise', 'expected_output'],
                             [pytest.param('base', pytest.raises(AssertionError), None),
                              pytest.param('py38', does_not_raise(), Path)])
    def test_lookup_kernel(self, conda_env_manager, env_name, expected_raise, expected_output):
        with expected_raise:
            path_to_kernel = conda_env_manager.lookup_kernel(env_name)
        if expected_output is not None:
            assert isinstance(path_to_kernel, Path)
            assert path_to_kernel.exists()

    @pytest.mark.parametrize(['env_name', 'expected_raise', 'expected_output'],
                             [pytest.param('base', pytest.raises(AssertionError), None),
                              pytest.param('py38', does_not_raise(),
                                           "/Users/jd/Library/Jupyter/kernels/py38/kernel.json")])
    def test_load_kernel_config(self, conda_env_manager, env_name, expected_raise, expected_output):
        with expected_raise:
            kernel_config_path = CondaEnvManager.lookup_kernel(env_name)
        if expected_output is not None:
            assert Path(expected_output) == kernel_config_path
            kernel_config = CondaEnvManager.load_kernel_config(kernel_config_path)
            assert isinstance(kernel_config, dict)
            assert kernel_config['display_name'] == env_name

    @pytest.mark.parametrize(['env_name', 'expected_raise', 'expected_output'],
                             [pytest.param('base', pytest.raises(AssertionError), None),
                              pytest.param('py38', does_not_raise(), True)])
    def test_verify_kernel_pairing(self, env_name, expected_raise, expected_output):
        with expected_raise:
            is_paired = CondaEnvManager.verify_kernel_pairing(env_name)
        if expected_output is not None:
            assert expected_output == is_paired
            assert isinstance(is_paired, bool)

    def test_verify_if_kernel_config_contains_env_path(self):
        assert False

    @pytest.mark.parametrize(['clean_proj_name', 'both', 'expected'],
                             [pytest.param('base', True, False), pytest.param('base', False, False)])
    def test_conda_and_kernel_name_available(self, conda_env_manager, clean_proj_name, both, expected):
        output = conda_env_manager.conda_and_kernel_name_available(clean_proj_name=clean_proj_name, both=both)
        if not both:
            output = conda_env_manager.conda_and_kernel_name_available(clean_proj_name=clean_proj_name, both=both)
            assert len(output) == 2
            assert output[0] == expected
        else:
            assert output == expected

    def test_get_path_to_conda_env(self):
        assert False

    def test_reset_conda_channel_priority(self):
        assert False

    def test_upgrade_pip(self):
        assert False

    def test_install_ipykernel(self):
        assert False

    def test_add_conda_forge_priority(self):
        assert False

    def test_register_kernel(self):
        assert False

    def test_create_conda_env(self):
        assert False

    def test_init_prev_made_conda_env(self):
        assert False

    def test_uninstall_kernel(self):
        assert False

    def test_uninstall_conda_env(self):
        assert False

    def test_uninstall_conda_and_kernel(self):
        assert False

    def test_uninstall_conda_envs_and_kernels(self):
        assert False

    def test_get_conda_base(self):
        assert False

    def test_get_conda_sh(self):
        assert False

    def test_get_conda_base_from_dot_conda_envs_txt(self):
        assert False

    def test_activate_conda_env(self):
        assert False

    def test_create_and_init_conda_env(self):
        assert False

    def test_get_available_conda_versions(self, conda_env_manager):
        versions_available = conda_env_manager.get_available_conda_versions()
        assert isinstance(versions_available, defaultdict)

    def test_get_suitable_python_versions_for_conda(self, conda_env_manager):
        python_version = '^3.9'
        filtered_versions = CondaEnvManager.get_suitable_python_versions_for_conda(python_version)
        assert isinstance(filtered_versions, dict)

    def test_get_python_version_for_conda(self, conda_env_manager):
        python_version = '^3.9'
        python_version_str = CondaEnvManager.get_python_version_for_conda(python_version)
        assert python_version_str.startswith("python=")


class TestGitProjectManager:
    def test_write_gitignore_contents(self):
        assert False

    def test_init_dir(self):
        assert False

    def test_add_repo(self):
        assert False

    def test_replace_global_git_username(self):
        assert False

    def test_replace_global_git_email(self):
        assert False

    def test_verify_github_ssh(self):
        assert False

    def test_create_ssh_key(self):
        assert False


class TestLocalProjectManager:
    def test_init_current_dir_as_a_poetry_conda_project(self):
        assert False

    def test_create_init_link_conda_env_to_existing_poetry_project(self):
        assert False

    def test_migrate_requirements_to_pypoetry_toml(self, poetry_proj_conda_env_name: str = 'verifypm',
                                                   src_path_to_reqs: str = PATH_TO_REQUIREMENTS_TXT,
                                                   dest_path_to_pyproject_toml: str = PATH_TO_PYPROJECT_TOML_FILE,
                                                   warn_before_add=True):
        rc = LocalProjectManager.migrate_requirements_to_pypoetry_toml(
            poetry_proj_conda_env_name=poetry_proj_conda_env_name,
            src_path_to_reqs=src_path_to_reqs,
            dest_path_to_pyproject_toml=dest_path_to_pyproject_toml,
            warn_before_add=warn_before_add)
        assert rc == 0

    # def test_migrate_pyproject_toml_to_pyproject_toml(self,local_project_manager,
    #                                                   poetry_proj_conda_env_name,
    #                                                   src_pyproject_toml,
    #                                                   dest_pyproject_toml,
    #                                                   warn_before_add,
    #                                                   dependency_section_name):
    def test_migrate_pyproject_toml_to_pyproject_toml(self):
        poetry_proj_conda_env_name = "project_manager"
        src_pyproject_toml = PATH_TO_PYPROJECT_TOML_FILE
        dest_pyproject_toml = r"pyproject.toml"
        warn_before_add = True
        dependency_section_name = "tool.poetry.dev-dependencies"
        rc = LocalProjectManager.migrate_pyproject_toml_to_pyproject_toml(poetry_proj_conda_env_name,
                                                                          src_pyproject_toml,
                                                                          dest_pyproject_toml,
                                                                          warn_before_add,
                                                                          dependency_section_name)
        assert rc == 0

    def test_get_requirements_txt_path(self):
        assert False

    def test_create_conda_env_for_existing_pyproject_toml(self, common_ps_commands, conda_env_manager,
                                                          local_project_manager):
        rc = local_project_manager.create_conda_env_for_existing_pyproject_toml(PATH_TO_PYPROJECT_TOML_FILE)
        assert rc == 0


class TestSublimeConfigGenerator:
    def test_get_filepath_to_sublime_text_build_config(self):
        assert False

    def test_generate_sublime_text_3_build_config_from_conda_env(self):
        assert False

    def test_export_sublime_text_build_config(self):
        assert False

    def test_get_sublime_text_build_config_contents(self):
        assert False


@pytest.mark.parametrize(['camel_input', 'expected'],
                         [pytest.param('name with spaces', 'name_with_spaces')])
def test_convert_camel_to_snakecase(camel_input, expected):
    output = convert_camel_to_snakecase(camel_input=camel_input)
    assert output == expected


def test_import_optional_dependency():
    # TODO: test exceptions
    import_to_return = import_optional_dependency('parse_single_constraint')
    assert import_to_return.__name__ == "parse_single_constraint"
    is_function_type = isinstance(import_to_return, types.FunctionType)
    is_module_type = isinstance(import_to_return, types.ModuleType)
    is_method_type = isinstance(import_to_return, types.MethodType)
    assert is_function_type or is_module_type or is_method_type
