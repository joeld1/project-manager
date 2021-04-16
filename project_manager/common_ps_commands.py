import subprocess
from pathlib import Path


def run_command(cmd_args, *args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=None, return_process=False,
                **kwargs):
    if isinstance(cmd_args,str):
        cmd_args = [cmd_args]
    p = subprocess.Popen(cmd_args, *args, stdin=stdin, stdout=stdout, text=text, **kwargs)
    if return_process:
        return p
    while True:
        cur_status = p.poll()
        if cur_status:  # 0s won't be printed
            print(cur_status)
        output = p.stdout.readline()
        if (output == '') and p.poll() is not None:  # might be redundant
            break
        if output:
            print(output.strip())
        if cur_status == 0:
            print(f"Success!\nFinished running {cmd_args}")
            break
    rc = p.poll()
    return rc


def chain_and_execute_commands(cmds, *args, **kwargs):
    cmd = " && ".join(cmds)
    kwargs['shell'] = True
    kwargs['text'] = True
    rc = run_command(cmd, *args, **kwargs)
    return rc


def get_python_dirs():
    p = Path("..")
    current_files = list(p.iterdir())
    all_python_dirs = list(
        filter(lambda x: x.is_dir() and ("." not in str(x)) and (not str(x).startswith("__")), current_files))
    return all_python_dirs


def get_traceback_file_origin(e):
    path_to_loaded_module = e.__traceback__.tb_next.tb_frame.f_locals['__file__']
    return path_to_loaded_module


def read_toml(path_to_toml, start_line="tool.poetry.dependencies"):
    toml_dict = {}
    save_lines = False
    with open(path_to_toml, "r") as f:
        all_lines = f.readlines()
        for i,l in enumerate(all_lines):
            cur_line = l.strip()
            start_line_found = start_line in cur_line
            if start_line_found:
                save_lines = True
            if (not cur_line) and save_lines:
                save_lines = False
            if (cur_line and save_lines) and (not start_line_found):
                print(cur_line)
                key, value = cur_line.split("=")
                key = key.strip()
                value = value.replace('"',"").strip()
                toml_dict[key] = value
    return toml_dict