__version__ = '0.1.0'

from project_manager.project_manager import ProjectManager, PoetryProjectManager, CommonPSCommands, CondaEnvManager, \
    GitProjectManager, LocalProjectManager, SublimeBuildConfigGenerator

# Include these here to lazily access static methods



# Sets up Ipykernel and registers conda kernel name for a previously made conda env
init_prev_made_conda_env = CondaEnvManager.init_prev_made_conda_env

# creates, inits, and registers a conda env and kernel
create_and_init_conda_env = CondaEnvManager.create_and_init_conda_env

# same as poetry init
execute_poetry_init = PoetryProjectManager.execute_poetry_init

# creates a poetry.toml and pyproject.toml in same directory
link_poetry_proj_with_conda_env = PoetryProjectManager.link_poetry_proj_with_conda_env

init_curent_dir_as_a_poetry_conda_project = LocalProjectManager.init_curent_dir_as_a_poetry_conda_project