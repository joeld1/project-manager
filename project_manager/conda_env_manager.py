import subprocess
from pathlib import Path

from project_manager.common_ps_commands import run_command, chain_and_execute_commands


def get_env_info_from_lines(all_lines):
    all_env_names = []
    all_env_paths = []
    for l in all_lines:
        env_name, *env_path = l.split()
        all_env_names.append(env_name)
        all_env_paths.append(env_path)
    return all_env_names, all_env_paths


def get_conda_envs():
    conda_cmd = ["conda", "info", "--envs"]
    with subprocess.Popen(conda_cmd, stdout=subprocess.PIPE, text=True) as p:
        output, errors = p.communicate()

    all_lines = output.replace(r"*", " ").split("\n")
    all_lines = list(filter(None, all_lines))  # remove empty strs
    all_lines = list(filter(lambda x: "#" not in x, all_lines))  # remove comments
    env_names, env_paths = get_env_info_from_lines(all_lines)
    return env_names, env_paths


def get_kernel_specs():
    kernel_cmd = ["jupyter", "kernelspec", "list"]
    with subprocess.Popen(kernel_cmd, stdout=subprocess.PIPE, text=True) as p:
        output, errors = p.communicate()

    all_lines = output.strip().replace(r"*", " ").split("\n")
    all_lines = [l.strip() for l in all_lines if ("Available kernels" not in l)]
    kernel_names, kernel_paths = get_env_info_from_lines(all_lines)
    return kernel_names, kernel_paths


def conda_and_kernel_name_available(clean_proj_name, both=False):
    kernel_names, _ = get_kernel_specs()
    conda_names, _ = get_conda_envs()

    kernel_exists = (clean_proj_name in kernel_names)
    conda_env_exists = (clean_proj_name in conda_names)
    if both:
        return (not conda_env_exists) and (not kernel_exists)
    else:
        return (not conda_env_exists), (not kernel_exists)


def echo_yes(return_cmd=False):
    #     cur_os = platform.system()
    #     if cur_os == "Darwin":

    y_cmd = "yes"
    if return_cmd:
        return f"echo {y_cmd} | "
    p1 = subprocess.Popen(["echo", y_cmd], stdout=subprocess.PIPE, text=True)
    return p1


def get_path_to_conda_env(env_name):
    conda_base = get_conda_base()
    path_to_env = (Path(conda_base) / f"envs/{env_name}").resolve().as_posix()
    return path_to_env


def reset_conda_channel_priority(act_env_str, *args, **kwargs):
    cmd = "conda config --set channel_priority false"
    rc = chain_and_execute_commands([act_env_str, cmd], *args, **kwargs)
    return rc


def upgrade_pip(act_env_str, *args, **kwargs):
    yes = echo_yes(True)
    cmd = yes + "python -m pip install --upgrade pip setuptools wheel"
    rc = chain_and_execute_commands([act_env_str, cmd], *args, **kwargs)
    return rc


def install_ipykernel(act_env_str, *args, **kwargs):
    yes = echo_yes(True)
    cmd = yes + "conda install notebook ipykernel"
    rc = chain_and_execute_commands([act_env_str, cmd], *args, **kwargs)
    return rc


def add_conda_forge_priority(act_env_str, *args, **kwargs):
    cmd = "conda config --add channels conda-forge"
    rc = chain_and_execute_commands([act_env_str, cmd], *args, **kwargs)
    if rc == 0:
        cmd = "conda config --set channel_priority strict"
        rc = chain_and_execute_commands([act_env_str, cmd], *args, **kwargs)
        return rc
    else:
        return rc


def register_kernel(env_name, *args, **kwargs):
    act_env_str = activate_conda_env(env_name, return_cmd=True)
    cmd = f"ipython kernel install --user --name {env_name} --display-name {env_name}"
    rc = chain_and_execute_commands([act_env_str, cmd], *args, **kwargs)
    return rc


def create_conda_env(env_name, python_version):
    python_version_str = f"python={python_version}"
    p0 = echo_yes(return_cmd=False)

    args = ["conda", "create", "-n", env_name, f"python={python_version}"]
    rc = run_command(args, stdin=p0.stdout, text=True)
    return rc


def init_prev_made_conda_env(env_name):
    act_env = activate_conda_env(env_name, return_cmd=True)
    rc = reset_conda_channel_priority(act_env)
    assert rc == 0
    rc = upgrade_pip(act_env)
    assert rc == 0
    rc = install_ipykernel(act_env)
    assert rc == 0
    rc = add_conda_forge_priority(act_env)
    assert rc == 0
    rc = register_kernel(env_name)
    assert rc == 0
    return rc


def uninstall_kernel(kernel_name: str = ""):
    try:
        kernel_names, _ = get_kernel_specs()
        assert kernel_name in kernel_names
    except Exception as e:
        print(f"Kernel {kernel_name!r} does not exist!")
    kernel_cmd = ["jupyter", "kernelspec", "uninstall", kernel_name, '-y']
    y = echo_yes(return_cmd=True)
    kernel_cmd_str = " ".join(kernel_cmd)
    cmd = y + kernel_cmd_str
    rc = run_command([cmd], text=True, shell=True)
    return rc


def uninstall_conda_env(conda_env_name: str = ""):
    try:
        kernel_names, _ = get_conda_envs()
        assert conda_env_name in kernel_names
    except Exception as e:
        print(f"Conda {conda_env_name!r} does not exist!")
    conda_cmd = ["conda", "env", "remove", '-n', conda_env_name]
    rc = run_command(conda_cmd, text=True)
    return rc


def uninstall_conda_and_kernel(conda_env_name: str = "", kernel_name: str = ""):
    if (not conda_env_name) and (not kernel_name):
        print("Please specify the env name and kernel name!")
        return -1
    if conda_env_name and (not kernel_name):
        kernel_name = conda_env_name
    if kernel_name and (not conda_env_name):
        conda_env_name = kernel_name

    rc1 = uninstall_kernel(kernel_name)
    rc2 = uninstall_conda_env(conda_env_name)
    if rc1 == rc2:
        return rc1
    else:
        return rc1, rc2


def uninstall_conda_envs_and_kernels(conda_env_names):
    for env in conda_env_names:
        print(env)
        uninstall_conda_and_kernel(env, env)
        print()


def get_conda_base():
    echo_cmds = ['conda', 'info', '--base']
    p = run_command(echo_cmds, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, return_process=True)
    output, errors = p.communicate()
    return output.strip()


def get_conda_sh():
    conda_base = get_conda_base()
    conda_sh = (Path(conda_base.strip()) / "etc/profile.d/conda.sh").resolve().as_posix()
    return conda_sh


def activate_conda_env(env_name, return_cmd=False):
    #     echo_cmd = ["python", "--version"]
    #     echo_cmd_str = " ".join(echo_cmd)
    conda_sh = get_conda_sh()

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


if __name__ == "__main__":
    uninstall_conda_envs_and_kernels(['test_env'])
