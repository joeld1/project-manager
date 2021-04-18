project_manager
==
A conda poetry project manager
--
A collection of actions that allow you to use subprocess to create/manage conda envs, poetry projects, register ipykernels, and export Sublime Text 3 Python Build configuration settings.

Things are actively being refactored and haven't been documented and annotated. As such, method names are long and verbose for the meantime.

This package was created in order to practice replacing shell/.bat scripts with Python, and to allow me to use conda to install packages (via poetry) not available for computers with a Mac M1 chip. The Sublime Text 3 build config generator was created in order to be able to execute Python code with little performance issues I've been experiencing with my IDE. 

For some methods found in this module to work you need to have the following:

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
    

Aside from that, running the following command:

    
    import sys

    from project_manager import LocalProjectManager as LPM
    
    env_name = "hello_world"
    python_version = "3.9"
    
    LPM.init_curent_dir_as_a_poetry_conda_project(env_name, python_version)
    sys.exit()

should allow you to create a 3.9 python environment and initialize your current directory as a poetry project with your newly created conda environment as a virtualenv.

If you're interested in registering any Python interpreter with Sublime Text 3, running the following block should help you do that.

    import sys

    from project_manager import SublimeBuildConfigGenerator as SBCG
    
    path_to_python_bin = "/opt/homebrew/anaconda3/envs/hello_world/bin"
    build_config_name = "hello_world" 

    SBCG.export_sublime_text_build_config(path_to_python_bin, build_config_name)
    sys.exit()

If you want to register a Conda env with Sublime Text 3 without looking up the path to it, then the following block should suffice.

    import sys
    
    from project_manager import SublimeBuildConfigGenerator as SBCG

    conda_env_name = "hello_world"
    SBCG.generate_sublime_text_3_build_config_from_conda_env(conda_env_name)
    sys.exit()

You should now be able to see a .sublime-build config in your application data folder
for Mac users, it'll be:


    Users/{YOUR_USERNAME}/Library/Application Support/Sublime Text 3/Packages/User/{build_config_name}

For PC users, it'll be:

    C:\Users\{YOUR_USERNAME}\AppData\Roaming\Sublime Text 3\Packages\User\{build_config_name}

