project_manager
==
A conda poetry project manager
--
A collection of actions that allow you to use subprocess to create/manage conda envs, poetry projects, and register ipykernels

Things are actively being refactored and haven't been documented and annotated. As such, method names are long and verbose for the meantime 

This package was created in order to practice replacing shell/.bat scripts with Python, and to allow me to use conda to install packages (via poetry) not available for computers with a Mac M1 chip. 

For the methods found in this module to work you need to have the following:

- Required
    - Conda
    - Poetry

- Optional
    - gy
        - Used for creating `.gitignore` files
    - stringcase
        - used to convert text to snake_case
    - toml
        - as a backup for parsing `.toml` files
    

Aside from that, running the following command

    
    import sys

    from project_manager import LocalProjectManager
    
    env_name = "hello_world"
    python_version = "3.9"
    LocalProjectManager.init_curent_dir_as_a_poetry_conda_project(env_name, python_version)
    sys.exit()

Should allow you to create a 3.9 python environment and initialize your current directory as a poetry project with your newly created conda environment as a virtualenv.

