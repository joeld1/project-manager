__version__ = "0.0.1.dev47+c2864e4"

from project_manager.project_manager import CommonPSCommands
from project_manager.project_manager import CommonPSCommands as CPSC
from project_manager.project_manager import CondaEnvManager
from project_manager.project_manager import CondaEnvManager as CEM
from project_manager.project_manager import GitProjectManager
from project_manager.project_manager import GitProjectManager as GPM
from project_manager.project_manager import LocalProjectManager
from project_manager.project_manager import LocalProjectManager as LPM
from project_manager.project_manager import PoetryProjectManager
from project_manager.project_manager import PoetryProjectManager as PPM
from project_manager.project_manager import ProjectManager
from project_manager.project_manager import ProjectManager as PM
from project_manager.project_manager import SublimeBuildConfigGenerator
from project_manager.project_manager import SublimeBuildConfigGenerator as SBCG

# Include these here to lazily access static methods


# Sets up Ipykernel and registers conda kernel name for a previously made conda env
init_prev_made_conda_env = CEM.init_prev_made_conda_env

# creates, inits, and registers a conda env and kernel
create_and_init_conda_env = CEM.create_and_init_conda_env

# same as poetry init
execute_poetry_init = PPM.execute_poetry_init

# creates a poetry.toml and pyproject.toml in same directory
link_poetry_proj_with_conda_env = PPM.link_poetry_proj_with_conda_env

init_current_dir_as_a_poetry_conda_project = LPM.init_current_dir_as_a_poetry_conda_project

generate_sublime_text_3_build_config_from_conda_env = SBCG.generate_sublime_text_3_build_config_from_conda_env
