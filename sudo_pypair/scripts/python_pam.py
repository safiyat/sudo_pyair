# -*- coding: utf-8 -*-

from __future__ import print_function
import getpass
import grp
import json
import os
import passlib.hash
import pty
import pwd
import random
import requests
import shlex
import SocketServer
import stat

import sys
import syslog
import subprocess
import tempfile
import time
import traceback


approval_data = None

debug = False

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
# The usage of the tool should be in coordination with a designated approver.  #
#                                                                              #
# Please provide the following code to the approver:                           #
#                                                                              #
# {} #
################################################################################
""" % (CRED, CEND, CGREEN, CEND, CGREEN, CEND)

def log(string, mode="a"):

    updated_string = "(user: %s) " % pwd.getpwuid(os.getuid()).pw_name + string

    # If you want /var/log/auth.log
    syslog.syslog(syslog.LOG_INFO, updated_string)

    # import datetime
    # with open("/tmp/tmp", mode) as fp:
    #     fp.write("%s: %s\n\n" % (str(datetime.datetime.now()), string))


class Color(object):
    CEND      = '\33[0m'
    CBOLD     = '\33[1m'
    CITALIC   = '\33[3m'
    CURL      = '\33[4m'
    CBLINK    = '\33[5m'
    CBLINK2   = '\33[6m'
    CSELECTED = '\33[7m'

    CBLACK  = '\33[30m'
    CRED    = '\33[31m'
    CGREEN  = '\33[32m'
    CYELLOW = '\33[33m'
    CBLUE   = '\33[34m'
    CVIOLET = '\33[35m'
    CBEIGE  = '\33[36m'
    CWHITE  = '\33[37m'

    CBLACKBG  = '\33[40m'
    CREDBG    = '\33[41m'
    CGREENBG  = '\33[42m'
    CYELLOWBG = '\33[43m'
    CBLUEBG   = '\33[44m'
    CVIOLETBG = '\33[45m'
    CBEIGEBG  = '\33[46m'
    CWHITEBG  = '\33[47m'

    CGREY    = '\33[90m'
    CRED2    = '\33[91m'
    CGREEN2  = '\33[92m'
    CYELLOW2 = '\33[93m'
    CBLUE2   = '\33[94m'
    CVIOLET2 = '\33[95m'
    CBEIGE2  = '\33[96m'
    CWHITE2  = '\33[97m'

    @staticmethod
    def printc(string, colors, do_not_print=False):
        output = ''.join(colors)
        output += str(string)
        output += Color.CEND
        if do_not_print:
            return output.strip()
        print(output)


def _get_config(argv):
    """
    Read the parameters from the arguments. If the argument can be split with a
    "=", the parameter will get the given value.

    :param argv:
    :return: dictionary with the parameters
    """
    # log("_get_config()")
    config = {}
    for arg in argv:
        # argument = arg.split("=")
        sep = arg.find("=")
        if sep == -1:  # No key-value pair
            config[arg] = True
        else:
            config[arg[:sep]] = arg[sep+1:]
    # log("config:\n%s" % json.dumps(config, indent=2))
    return config


def parse_csv(csv_string):
    return csv_string.split(',') if csv_string else None


def inspect_object(object_to_inspect):
        log('*' * 80)
        log('*' * 80)
        log('type: %s' % str(type(object_to_inspect)))
        log('str: %s' % str(object_to_inspect))
        for obj in dir(object_to_inspect):
            try:
                log('object_to_inspect.%s: %s (%s)' % (str(obj), str(getattr(object_to_inspect, obj)), type(getattr(object_to_inspect, obj))))
            except Exception as e:
                import traceback
                log(traceback.format_exc())
                log('object_to_inspect.%s' % str(obj))
        log('*' * 80)
        log('*' * 80)


def gen_id(seed):
    random.seed(a=seed)
    # Generate an ID 12345-65536
    id = int(random.random() * seed + 12345) % 65536
    return id


def run_command(cmd, env=None, stdin=None, current_working_directory=None):
    stdout_fd, stdout_fn = tempfile.mkstemp()
    stderr_fd, stderr_fn = tempfile.mkstemp()

    master, slave = pty.openpty()
    popen = subprocess.Popen(
        shlex.split(cmd), preexec_fn=os.setsid, shell=False,
        stdin=slave, stdout=stdout_fd, stderr=stderr_fd,
        cwd=current_working_directory, env=env)
    if stdin is not None:
        popen.stdin.write(stdin)
    rc = popen.wait()

    with open(stdout_fn, 'r') as fp:
        stdout = fp.read()

    with open(stderr_fn, 'r') as fp:
        stderr = fp.read()

    return rc, stdout, stderr


def get_command_from_pid(pid):
    command = run_command('ps -o args= %s' % pid)[1].strip()
    return command


def get_screen_command():
    shell_pid = run_command('ps -o ppid= %s' % os.getpid())[1].strip()
    screen_pid = run_command('ps -o ppid= %s' % shell_pid)[1].strip()

    command = get_command_from_pid(screen_pid)
    return command


def check_if_invoked_from_screen():
    command = get_screen_command()
    if command.split()[0] != 'SCREEN':
        return False
    return True


class SudoApprovalSeekServer(SocketServer.UnixStreamServer):
    def _handle_request_noblock(self):
        result = None
        try:
            request, client_address = self.get_request()
        except OSError:
            return result

        result = self.interpret_request(request, client_address)

        self.shutdown_request(request)
        global approval_data
        approval_data = result.copy() if result else None
        return result

    def interpret_request(self, request, client_address):
        # inspect_object(request)
        # inspect_object(client_address)
        json_data = None
        data = request.recv(2 ** 16)
        try:
            # inspect_object(data.decode())
            # log(data.decode())
            json_data = json.loads(data.decode())
        except Exception as e:
            log(str(e))
            log(traceback.format_exc())

        # log(json_data)
        return json_data


def get_socketfile_path(id, pid):
    return os.path.join(tempfile.gettempdir(), '%d-%d.sock' % (id, pid))


def setup_approval_server(id, pid, uid=-1, gid=-1):
    """
    Method to setup an approval server for the given id and pid with ownership
    set to the given uid and gid. -1 value implies no change.
    """
    socket_file = get_socketfile_path(id, pid)
    server = SudoApprovalSeekServer(socket_file, None)
    log("Setting uid: %d and gid: %d for socket file %s." % (uid, gid, socket_file))
    os.chown(socket_file, uid, gid)
    os.chmod(socket_file, stat.S_IWUSR | stat.S_IWGRP)
    return server

def setup_approve(pamh, flags, config):
    session_id = gen_id(pamh.pamh)
    # inspect_object(pamh)
    pid = os.getpid()
    log("Generated ID-pid: %s-%s" % (str(session_id), str(pid)))

    command = get_screen_command()
    # approver_user = config.get('approver_user', 'root')
    approver_group = config.get('approver_group', 'root')
    # uid = pwd.getpwnam(approver_user).pw_uid
    uid = ''
    gid = grp.getgrnam(approver_group).gr_gid
    server = setup_approval_server(session_id, pid, uid=uid, gid=gid)

    return server, {'id': session_id, 'pid': pid, 'user': pamh.get_user(), 'randnum': session_id + pid + os.getuid()}


def wait_for_approve(pamh, server, randnum):
    """
    Handle one request. Return.

    Required received data format:
        {"id": approval_request_id, "pid": pid, "randnum": randnum}
    """
    server.handle_request()
    # inspect_object(server)
    # print("Result: %s" % (str(approval_data)))
    server.server_close()
    os.unlink(server.server_address)

    if approval_data["randnum"] == randnum:
        # print(os.path.realpath('/dev/stdout'))
        return pamh.PAM_SUCCESS
    else:
        if debug:
            log("Approval code mismatch.")
            log("Expected: %s" % (randnum))
            log("Actual:   %s" % (approval_data["randnum"]))
        return pamh.PAM_AUTH_ERR


def authenticate(pamh, flags, argv):
    global debug
    rval = pamh.PAM_AUTH_ERR
    try:
        # log("authenticate()")
        syslog.openlog(facility=syslog.LOG_AUTH)
        config = _get_config(argv)
        debug = config.get("debug").lower() in "true"

        if debug:
            log("Config: %s" % json.dumps(config))

        # print("This is a test message.")

        # Color.printc("Is this message coloured?", colors=[Color.CRED, Color.CBLUEBG])

        exempted_users = config.get("exempted_users")
        if exempted_users:
            current_user = getpass.getuser()
            if current_user in exempted_users:
                return pamh.PAM_SUCCESS

        exempted_groups = config.get("exempted_groups")
        if exempted_groups:
            current_user = grp.getgrgid(os.getgid()).gr_name
            if current_user in exempted_groups:
                return pamh.PAM_SUCCESS

        try:
            # inspect_object(pamh)

            # log("env: %s" % str(pamh.env.keys()))
            if not check_if_invoked_from_screen():
                print("Request for sudo not raised from a screen session!", file=sys.stderr)
                return pamh.PAM_AUTH_ERR

            server, message = setup_approve(pamh, flags, config)

            approval_code = "%s %s %s" % (message["id"], message["pid"], message["randnum"])

            # colorized_approval_code = " ".join([Color.printc(message["id"], colors=[Color.CRED], do_not_print=True),
            #                                     Color.printc(message["pid"], colors=[Color.CGREEN], do_not_print=True),
            #                                     Color.printc(message["randnum"], colors=[Color.CBLUE], do_not_print=True)])

            if debug:
                log("Approval code for user %s: %s" % (pamh.user, approval_code))

            print(PROMPT.format(approval_code.center(76)).strip())

            rval = wait_for_approve(pamh, server, randnum=message["randnum"])

            # rval = pamh.PAM_SUCCESS

        except Exception as ex:
            import traceback
            log(traceback.format_exc())
            log(ex)
            rval = pamh.PAM_AUTH_ERR
        finally:
            syslog.closelog()

        if debug:
            log("End of pam_sm_authenticate()")
    except Exception as e:
        import traceback
        log("Error in authenticate:")
        log(traceback.format_exc())
        rval = pamh.PAM_SUCCESS
    # rval = pamh.PAM_SUCCESS
    return rval


def pam_sm_authenticate(pamh, flags, argv):
    """
    The pam_sm_authenticate function is the service module's implementation of
    the pam_authenticate(3) interface.

    This function performs the task of authenticating the user.

    pamh: PamHandle_type
    flags: Integer
    argv:  A list of args to pam_python.so in pam file.
    """
    # log("pam_sm_authenticate()")
    return authenticate(pamh, flags, argv)


def pam_sm_setcred(pamh, flags, argv):
    # log("pam_sm_setcred()")
    # return authenticate(pamh, flags, argv)
    return pamh.PAM_SUCCESS


def pam_sm_acct_mgmt(pamh, flags, argv):
    # log("pam_sm_acct_mgmt()")
    return pamh.PAM_SUCCESS


def pam_sm_open_session(pamh, flags, argv):
    """
    The pam_sm_open_session function is the service module's implementation of
    the pam_open_session(3) interface.
    This function is called to commence a session.
    https://linux.die.net/man/3/pam_sm_open_session
    """
    # log("pam_sm_open_session()")
    # log("".join(traceback.format_stack()))
    # log("pamh: type=%s" % str(type(pamh)))
    # import inspect
    # log("inspect: %s" % str(inspect.getsource(PamHandle_type)))

    # The session was successfully started.
    return pamh.PAM_SUCCESS


def pam_sm_close_session(pamh, flags, argv):
    """
    The pam_sm_close_session function is the service module's implementation of
    the pam_close_session(3) interface.
    This function is called to terminate a session.
    https://linux.die.net/man/3/pam_sm_close_session
    """
    # log("pam_sm_close_session()")
    # The session was successfully terminated.
    return pamh.PAM_SUCCESS


def pam_sm_chauthtok(pamh, flags, argv):
    # log("pam_sm_chauthtok()")
    return pamh.PAM_SUCCESS
