__version__ = '0.1.0'

from project_manager.project_manager import ProjectManager, PoetryProjectManager, CommonPSCommands, CondaEnvManager, \
    GitProjectManager, LocalProjectManager

# Include these here to lazily access static methods
create_and_init_conda_env = CondaEnvManager.create_and_init_conda_env
execute_poetry_init = PoetryProjectManager.execute_poetry_init
link_poetry_proj_with_conda_env = PoetryProjectManager.link_poetry_proj_with_conda_env
init_curent_dir_as_a_poetry_conda_project = LocalProjectManager.init_curent_dir_as_a_poetry_conda_project