#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone
import getpass
import json
import os
import pwd
import re
import socket
import stat
from subprocess import getoutput
import sys
import tempfile


CEND   = '\33[0m'
CRED   = '\33[31m'
CGREEN = '\33[32m'
CBLUE  = '\33[34m'

PROMPT = """
################################################################################
#                                                                              #
#                       %seSIM Manager screen session tool%s                       #
#                                                                              #
# !!! Restricted use !!!                                                       #
#                                                                              #
# Use this tool only for actions that require:                                 #
#                                                                              #
#    - %sDual access%s                                                             #
#    - %s4-eyes principle%s                                                        #
#                                                                              #
# Note: This user has a screen session with the following details:             #
# %s{}%s #
# %s{}%s #
# %s{}%s #
# To join the session, run:                                                    #
# %s{}%s #
################################################################################
""" % (CRED, CEND, CGREEN, CEND, CGREEN, CEND, CBLUE, CEND, CBLUE, CEND, CBLUE,
       CEND, CGREEN, CEND)


NO_OF_ARGS = 3

def inspect_object(object_to_inspect):
    print('*' * 80)
    print('*' * 80)
    print('type: %s' % str(type(object_to_inspect)))
    print('str: %s' % str(object_to_inspect))
    for obj in dir(object_to_inspect):
        try:
            print('object_to_inspect.%s: %s (%s)' % (str(obj), str(getattr(object_to_inspect, obj)), type(getattr(object_to_inspect, obj))))
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            print('object_to_inspect.%s' % str(obj))
    print('*' * 80)
    print('*' * 80)


def get_socketfile_path(id, pid):
    return os.path.join(tempfile.gettempdir(), '%s-%s.sock' % (str(id), str(pid)))


def socket_file_exists(socket_file):
    if not os.path.exists(socket_file):
        return False
    st_mode = os.stat(socket_file).st_mode
    return stat.S_ISSOCK(st_mode)


def get_pid_from_socket_file(socket_file):
    numeric_matches = re.findall('\d+', os.path.basename(socket_file))
    if len(numeric_matches) != 2:
        return False
    request_pid = numeric_matches[1]
    return request_pid

def get_command_from_pid(pid):
    command = getoutput('ps -o args= %s' % pid).strip()
    return command


def get_command_from_socket_file(socket_file):
    request_pid = get_pid_from_socket_file(socket_file)
    shell_pid = getoutput('ps -o ppid= %s' % request_pid).strip()
    if shell_pid == '1':
        return None
    screen_pid = getoutput('ps -o ppid= %s' % shell_pid).strip()
    if screen_pid == '1':
        return None
    command = get_command_from_pid(screen_pid)
    return command


def get_screen_name_from_requesting_uid(requesting_uid):
    requesting_user = pwd.getpwuid(requesting_uid).pw_name
    self_username = getpass.getuser()
    screen_list = getoutput('screen -list %s/' % requesting_user)
    screens = [x for x in screen_list.split() if '%s-%s-' % (requesting_user, self_username) in x]
    if screens:
        return screens[-1]
    return None


def socket_file_is_valid(socket_file, requesting_uid):
    socket_stat = os.stat(socket_file)
    # Check if permissions are sane
    if socket_stat.st_uid != os.geteuid() and socket_stat.st_gid != os.getegid():
        print('You are not the designated approver for this request.', file=sys.stderr)
        return False
    # Check if originated in a shared screen session
    # command = get_command_from_socket_file(socket_file)

    if not get_screen_name_from_requesting_uid(requesting_uid):
        print('This request was not invoked in a shared screen session.', file=sys.stderr)
        return False
    return True


def get_approval(socket_file, requesting_uid):
    screen_name = get_screen_name_from_requesting_uid(requesting_uid)
    pid_requester_user, _, screen_unixtime = screen_name.split('-')
    timestamp = datetime.fromtimestamp(
        int(screen_unixtime),
        tz=timezone(timedelta(0))).strftime('%c %Z')
    pid, requester_user = pid_requester_user.split('.')
    command_invoked = get_command_from_pid(get_pid_from_socket_file(socket_file))
    command_invoked = command_invoked[:37] + '...' if len(command_invoked) > 40 else command_invoked
    full_screen_name = '%s/%s' % (requester_user, screen_name)
    user_info = 'user:'.rjust(17).ljust(36) + requester_user.ljust(40)
    time_info = 'screen invocation time:'.rjust(35).ljust(36) + timestamp.ljust(40)
    command_info = 'command invoked:'.rjust(28).ljust(36) + command_invoked.ljust(40)
    screen_join_cmd = ('screen -x %s' % full_screen_name).center(76)
    prompt = PROMPT.format(user_info, time_info, command_info, screen_join_cmd)
    print(prompt.strip())
    question = 'Approve user\'s session? (yes/no/hold): '
    answer = ''
    while answer not in ['yes', 'no', 'hold']:
        answer = input(question)
    translation_table = {'yes': True, 'no': False, 'hold': None}
    return translation_table[answer]


def write_to_socket(socket_file, randnum):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        # print("Connecting to %s" % socket_file)
        sock.connect(socket_file)
        # sock.sendall(bytes(json.dumps({"test": "Okay"}), "utf-8"))
        sock.sendall(bytes(json.dumps({'randnum': int(randnum)}), 'utf-8'))

def get_screen_name(approval_code):
    """
    This method is here only for usage from the shell.

    :param approval_code: A string of three space separated numbers.
    """
    argv = approval_code.split()
    if len(argv) != NO_OF_ARGS:
        print('Invalid usage. Three arguments required.', file=sys.stderr)
        sys.exit(1)
    session_id = argv[0]
    pid = argv[1]
    randnum = argv[2]
    requesting_uid = int(randnum) - int(pid) - int(session_id)
    socket_file = get_socketfile_path(session_id, pid)
    if not socket_file_exists(socket_file):
        print('Incorrect arguments. '
              'No session using this approval code exists.', file=sys.stderr)
        sys.exit(1)
    if not socket_file_is_valid(socket_file, requesting_uid):
        sys.exit(1)
    screen_name = get_screen_name_from_requesting_uid(requesting_uid)
    if screen_name is None:
        print('No screen session with this approval code exists.', file=sys.stderr)
        exit(1)
    requester_user = pwd.getpwuid(requesting_uid).pw_name
    print('%s/%s' % (requester_user, screen_name))


def main():
    argv = sys.argv

    if len(argv) == NO_OF_ARGS:
        get_screen_name(argv[-1])
        return

    if len(argv) != NO_OF_ARGS + 1:
        print('Invalid usage.', file=sys.stderr)
        sys.exit(1)

    session_id = argv[1]
    pid = argv[2]
    randnum = argv[3]
    requesting_uid = int(randnum) - int(pid) - int(session_id)

    socket_file = get_socketfile_path(session_id, pid)

    if not socket_file_exists(socket_file):
        print('Invalid arguments. '
              'No session using this approval code exists.', file=sys.stderr)
        sys.exit(1)

    if not socket_file_is_valid(socket_file, requesting_uid):
        sys.exit(1)

    approval = get_approval(socket_file, requesting_uid)

    if approval:
        write_to_socket(socket_file, randnum)
        # print('Approved.')
        return 11
    elif approval is False:
        write_to_socket(socket_file, '0')
        # print('Declined.')
        return 22
    else:
        print('Request on hold.')
        return 33


if __name__ == '__main__':
    sys.exit(main())
