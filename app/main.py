import shlex
import sys
import os
import subprocess
from pathlib import Path

# TODO:


### shell builtins
def cmdExit(cmd):
    global std_err
    cmd_lst = shlex.split(cmd)

    if len(cmd_lst) == 2:
        code = int(cmd_lst[1])
        match code:
            case 0:
                sys.exit(code)
            case _:
                std_err = "ERROR: Must supply a valid exit status code"
    else:
        std_err = "ERROR: Must supply a valid exit status code"


def cmdEcho(cmd):
    global std_out
    # if cmd.startswith("'") and cmd.endswith("'"):
    #     out_str = cmd[6:-1]
    # else:
    #     split_str = shlex.split(cmd[5:])
    #     out_str = " ".join(split_str)
    split_str = shlex.split(cmd[5:])
    std_out = " ".join(split_str)


def cmdType(cmd, valid_list):
    global std_out, std_err
    cmd_lst = shlex.split(cmd)

    if len(cmd_lst) == 2:
        if cmd_lst[1] in valid_list:
            cmd_type = "builtin"
        else:
            cmd_type = findInPATH(cmd_lst[1])

        match cmd_type:
            case "builtin":
                std_out = cmd_lst[1] + " is a shell builtin"
            case None:
                std_err = cmd_lst[1] + ": not found"
            case _:
                std_out = cmd_lst[1] + " is " + cmd_type
    else:
        std_err = "ERROR: Must supply criteria for command"


def cmdPwd():
    global std_out
    std_out = os.getcwd()


def cmdCd(cmd, previous_dir):
    global std_err
    cmd_lst = shlex.split(cmd)

    if ("~" in cmd_lst) or (len(cmd_lst) == 1):
        previous_dir = os.getcwd()
        os.chdir(os.getenv("HOME"))
    elif "-" in cmd_lst:
        os.chdir(previous_dir)
    else:
        if Path(cmd_lst[1]).exists():
            pd_tmp = previous_dir
            try:
                previous_dir = os.getcwd()
                os.chdir(cmd_lst[1])
            except NotADirectoryError:
                previous_dir = pd_tmp
                std_err = "cd: " + cmd_lst[1] + ": Not a directory"
        else:
            std_err = "cd: " + cmd_lst[1] + ": No such file or directory"


### helper functions
def notFound(cmd):
    global std_err
    std_err = cmd + ": command not found"


def findInPATH(target_name):
    result = None

    if "PATH" in os.environ:
        path = os.environ.get("PATH").split(":")
        for each in path:
            # only search if no command has yet been found
            if result is None:
                for dirpath, dirs, files in os.walk(each):
                    if target_name in files:
                        result = os.path.join(dirpath, target_name)
                    else:
                        result = None

    return result


def runCommand(cmd):
    global std_out, std_err
    split_cmd = shlex.split(cmd)
    lookup_res = findInPATH(split_cmd[0])

    if lookup_res:
        cmd_out = subprocess.run(split_cmd, capture_output=True, text=True)
        std_out = cmd_out.stdout
        std_err = cmd_out.stderr

        # remove trailing newline
        if std_out:
            if (std_out[-1] == "\n"):
                std_out = std_out[:-1]

        if std_err:
            if (std_err[-1] == "\n"):
                std_err = std_err[:-1]
    else:
        notFound(split_cmd[0])


def redirect_check(cmd, red_sym):
    global redirect
    split_cmd = shlex.split(cmd)
    # find intersections of input and redirects using list comprehension
    red_found = "".join([val for val in red_sym if val in split_cmd])

    if red_found:
        redirect = []
        redirect.append(red_found)
        # get the index of the redirect target
        rf_target_idx = split_cmd.index(red_found) + 1
        redirect.append(split_cmd.pop(rf_target_idx))
        split_cmd.pop(split_cmd.index(red_found))
        cmd = " ".join(split_cmd)

    return cmd


### main()
def main():
    global std_out, redirect, std_err
    prev_dir = os.getcwd()
    builtin_commands = ["exit", "echo", "type", "pwd", "cd"]
    redirection_sym = [">", "1>", "2>", ">>", "1>>", "2>>"]

    while True:
        # write prompt and flush buffer
        sys.stdout.write("$ ")
        sys.stdout.flush()

        input_str = input()
        input_str = redirect_check(input_str, redirection_sym)
        command = shlex.split(input_str)[0]

        match command:
            case "exit":
                cmdExit(input_str)
            case "echo":
                cmdEcho(input_str)
            case "type":
                cmdType(input_str, builtin_commands)
            case "pwd":
                cmdPwd()
            case "cd":
                cmdCd(input_str, prev_dir)
            case _:
                runCommand(input_str)

        if redirect:
            # determine file open mode
            if redirect[0].count(">") == 1:
                fd_mode = 'w'
            elif redirect[0].count(">") == 2:
                fd_mode = 'a'
            else:
                fd_mode = 'r'

            f = open(redirect[1], fd_mode, encoding="utf-8")

            # write std_out or std_err to file
            match redirect[0]:
                case ">" | ">>" | "1>" | "1>>":
                    if std_out:
                        f.writelines(std_out + '\n')

                    std_out = None
                case "2>" | "2>>":
                    if std_err:
                        f.writelines(std_err + '\n')

                    std_err = None
                case _:
                    std_out = None
                    std_err = None

            f.close()

        # print std_out and std_error if no redirects
        # and contain data
        if std_out:
            print(std_out)

        if std_err:
            print(std_err)

        # Clear outputs
        std_out = None
        std_err = None
        redirect = None


if __name__ == "__main__":
    std_out = None
    std_err = None
    redirect = None
    main()
