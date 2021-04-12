import os
from pathlib import Path

from project_manager.common_ps_commands import chain_and_execute_commands, read_toml, get_traceback_file_origin
from project_manager.conda_env_manager import activate_conda_env, get_path_to_conda_env, \
    conda_and_kernel_name_available, create_conda_env, init_prev_made_conda_env
from project_manager.git_project_manager import init_dir


def get_poetry_project_dir(filepath_importing_from, toml_pattern="*pyproject.toml"):
    path = Path(filepath_importing_from)
    if path.is_file():
        path = path.parent
    pyproject_toml_path = list(path.glob(toml_pattern))
    if not pyproject_toml_path:
        return get_poetry_project_dir(path.parent.as_posix())
    else:
        return path.as_posix()


def get_poetry_toml(path):
    toml_pattern = "*poetry.toml"
    poetry_proj_dir = get_poetry_project_dir(path, toml_pattern=toml_pattern)
    cur_poetry_file = Path(poetry_proj_dir) / toml_pattern.replace("*", "")
    return cur_poetry_file


def get_pyproject_toml(path):
    toml_pattern = "pypoetry.toml"
    dir_containing_pyproject_toml = get_poetry_project_dir(path, toml_pattern=toml_pattern)
    path_to_toml = Path(dir_containing_pyproject_toml) / toml_pattern
    return path_to_toml


def get_poetry_module_dependencies(path: str):
    path_to_toml = get_pyproject_toml(path)
    dependencies = read_toml(path_to_toml, 'tool.poetry.dependencies')
    return dependencies


def get_import_error_dependencies(e):
    path_to_loaded_module = get_traceback_file_origin(e)
    deps = get_poetry_module_dependencies(path_to_loaded_module)
    return deps


def add_poetry_package_from_exception(file_importing_from: str, except_obj: ModuleNotFoundError, ignore_verion=True):
    assert isinstance(except_obj, ModuleNotFoundError)
    dependency = get_missing_poetry_dependency(except_obj, ignore_verion=ignore_verion)
    break_stmnt = input(f"poetry add {dependency}? [q to break]")
    if break_stmnt.lower() == "q":
        return
    old_path = os.getcwd()
    poetry_proj_dir = get_poetry_project_dir(file_importing_from)
    env_name = get_poetry_project_env_name(file_importing_from)
    os.chdir(poetry_proj_dir)
    act_env_str = activate_conda_env(env_name, return_cmd=True)
    poetry_cmd = f"poetry add {dependency}"
    rc = chain_and_execute_commands([act_env_str, poetry_cmd], text=True, shell=True, cwd=poetry_proj_dir)
    os.chdir(old_path)
    return rc


def add_poetry_package(file_importing_from: str, env_name: str, dependency: str):
    old_path = os.getcwd()
    poetry_proj_dir = get_poetry_project_dir(file_importing_from)
    os.chdir(poetry_proj_dir)

    act_env_str = activate_conda_env(env_name, return_cmd=True)
    poetry_cmd = f"poetry add {dependency}"
    rc = chain_and_execute_commands([act_env_str, poetry_cmd], text=True, shell=True, cwd=poetry_proj_dir)
    os.chdir(old_path)
    return rc


def link_poetry_proj_with_conda_env(clean_env_name, *args, **kwargs):
    conda_env_path = get_path_to_conda_env(clean_env_name)
    act_env_str = activate_conda_env(clean_env_name, return_cmd=True)
    poetry_cmd = f"poetry config virtualenvs.path {conda_env_path} --local"
    rc = chain_and_execute_commands([act_env_str, poetry_cmd], *args, text=True, shell=True, cwd=os.getcwd(), **kwargs)

    poetry_cmd = "poetry config virtualenvs.create 0 --local"
    rc = chain_and_execute_commands([act_env_str, poetry_cmd], *args, text=True, shell=True, cwd=os.getcwd(), **kwargs)

    poetry_cmd = "poetry config virtualenvs.in-project 0 --local"
    rc = chain_and_execute_commands([act_env_str, poetry_cmd], *args, text=True, shell=True, cwd=os.getcwd(), **kwargs)

    assert rc == 0
    print(f"Successfully linked {clean_env_name} to its conda env!")
    return rc


def create_poetry_proj(clean_env_name, *args, proj_name=None, proj_dir=".", **kwargs):
    old_path = os.getcwd()
    proj_path = Path(proj_dir).expanduser().resolve()
    try:
        assert proj_path.exists()
        os.chdir(proj_path.as_posix())
    except Exception as e:
        print("Unable to cd into folder since it doesn't exist! Will create proj in current directory")
        os.chdir(old_path)
    try:
        conda_envs_and_kernels_made = not conda_and_kernel_name_available(clean_env_name, both=True)

        if proj_name:
            path_to_proj = (proj_path / proj_name)
            assert not path_to_proj.exists()
        else:
            path_to_proj = (proj_path / clean_env_name)
    except Exception as e:
        print("Unable to create poetry project since directory or environment already exists!")
        return -1, Path("..")
    try:
        assert conda_envs_and_kernels_made
        act_env_str = activate_conda_env(clean_env_name, return_cmd=True)
    except Exception as e:
        print(e)
        print("Create the conda environment and register the jupyter kernel before retrying this method!")
        return -1, Path("..")

    if proj_name:
        cmd = f"poetry new {proj_name}"
    else:
        cmd = f"poetry new {clean_env_name}"
    rc = chain_and_execute_commands([act_env_str, cmd], *args, text=True, shell=True, cwd=os.getcwd(), **kwargs)
    assert rc == 0
    rc = link_poetry_proj_with_conda_env(clean_env_name)
    assert rc == 0
    os.chdir(old_path)
    return rc, path_to_proj


def init_poetry_project(clean_env_name, proj_name=None, proj_dir=".", python_version="3.9"):
    cur_dir = os.getcwd()
    proj_dir_path = Path(proj_dir).expanduser().resolve().as_posix()

    if proj_name is None:
        proj_name = clean_env_name
    proj_available = conda_and_kernel_name_available(clean_env_name, both=True)
    if proj_available:
        print("it's available! Now making conda env!")
        rc = create_conda_env(clean_env_name, python_version)
        assert rc == 0
        rc = init_prev_made_conda_env(clean_env_name)
        assert rc == 0
        # make conda env before this step
        rc, path_to_proj = create_poetry_proj(clean_env_name, proj_name=proj_name, proj_dir=proj_dir_path)
        os.chdir(path_to_proj)
        assert rc == 0
        rc = init_dir(path_to_proj)
        assert rc == 0
        os.chdir(cur_dir)
        return rc
    else:
        print("Project is not available!")


def get_poetry_virtual_env_path(path):
    cur_poetry_file = get_poetry_toml(path)
    virtualenvs_path = read_toml(cur_poetry_file, 'virtualenv')
    path_to_env = Path(virtualenvs_path['path'])
    return path_to_env


def get_poetry_project_env_name(file_importing_from):
    path_to_env = get_poetry_virtual_env_path(file_importing_from)
    env_name = path_to_env.name
    return env_name


def get_missing_poetry_dependency(caught_exception, ignore_verion=True):
    dep_name = caught_exception.name
    if not ignore_verion:
        deps = get_import_error_dependencies(caught_exception)
    else:
        deps = {dep_name: dep_name}
    if not ignore_verion:
        dep_version = deps.get(dep_name)
        dependency = f'{dep_name}=="{dep_version}"'
    else:
        dependency = dep_name
    return dependency
