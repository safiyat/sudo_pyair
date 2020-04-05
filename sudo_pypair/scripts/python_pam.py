# -*- coding: utf-8 -*-

import grp
import os
import sys
import json
import pwd
import random
import requests
import SocketServer
import stat
import syslog
import passlib.hash
import tempfile
import time
import traceback


approval_data = None


def mera_log(string, mode="a"):

    # If you want /var/log/auth.log
    # syslog.syslog(syslog.LOG_INFO, string)

    import datetime
    with open("/tmp/tmp", mode) as fp:
        fp.write("%s: %s\n\n" % (str(datetime.datetime.now()), string))


mera_log("It's time.", mode="w")


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
    def printc(string, colors):
        print(''.join(colors))
        print(string),
        print(Color.CEND)


def _get_config(argv):
    """
    Read the parameters from the arguments. If the argument can be split with a
    "=", the parameter will get the given value.

    :param argv:
    :return: dictionary with the parameters
    """
    mera_log("_get_config()")
    config = {}
    for arg in argv:
        # argument = arg.split("=")
        sep = arg.find("=")
        if sep == -1:  # No key-value pair
            config[arg] = True
        else:
            config[arg[:sep]] = arg[sep+1:]
    mera_log("config:\n%s" % json.dumps(config, indent=2))
    return config


def inspect_object(object_to_inspect):
        mera_log('*' * 80)
        mera_log('*' * 80)
        mera_log('type: %s' % str(type(object_to_inspect)))
        mera_log('str: %s' % str(object_to_inspect))
        for obj in dir(object_to_inspect):
            try:
                mera_log('object_to_inspect.%s: %s (%s)' % (str(obj), str(getattr(object_to_inspect, obj)), type(getattr(object_to_inspect, obj))))
            except Exception as e:
                import traceback
                mera_log(traceback.format_exc())
                mera_log('object_to_inspect.%s' % str(obj))
        mera_log('*' * 80)
        mera_log('*' * 80)


def gen_id(seed):
    random.seed(a=seed)
    # Generate an ID 12345-65536
    id = int(random.random() * seed + 12345) % 65536
    return id


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
            inspect_object(data.decode())
            mera_log(data.decode())
            json_data = json.loads(data.decode())
        except Exception as e:
            mera_log(str(e))

        mera_log(json_data)
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
    mera_log("Setting uid: %d and gid: %d" % (uid, gid))
    os.chown(socket_file, uid, gid)
    os.chmod(socket_file, stat.S_IWUSR | stat.S_IWGRP)
    return server

def setup_approve(pamh, flags, config):
    id = gen_id(pamh.pamh)
    # inspect_object(pamh)
    pid = os.getpid()
    mera_log("Generated ID-pid: %s-%s" % (str(id), str(pid)))

    approver_user = config.get('approver_user', 'root')
    approver_group = config.get('approver_group', 'root')
    uid = pwd.getpwnam(approver_user).pw_uid
    gid = grp.getgrnam(approver_group).gr_gid
    server = setup_approval_server(id, pid, uid=uid, gid=gid)

    return server, {'id': id, 'pid': pid, 'user': pamh.get_user(), 'randnum': gen_id(pamh.pamh)}


def wait_for_approve(pamh, server, randnum):
    """
    Handle one request. Return.

    Required data format:
        {"id": approval_request_id, "pid": pid, "randnum": randnum}
    """
    server.handle_request()
    inspect_object(server)
    print("Result: %s" % (str(approval_data)))
    server.server_close()
    os.unlink(server.server_address)

    if approval_data["randnum"] == randnum:
        print(os.path.realpath('/dev/stdout'))
        return pamh.PAM_SUCCESS
    else:
        return pamh.PAM_AUTH_ERR


# class Authenticator(object):

#     def __init__(self, pamh, config):
#         mera_log("__init__()")
#         self.pamh = pamh
#         self.user = pamh.get_user(None)
#         self.URL = config.get("url", "https://localhost")
#         self.sslverify = not config.get("nosslverify", False)
#         cacerts = config.get("cacerts")
#         # If we do verify SSL certificates and if a CA Cert Bundle file is
#         # provided, we set this.
#         if self.sslverify and cacerts:
#             self.sslverify = cacerts
#         self.realm = config.get("realm")
#         self.debug = config.get("debug")

#         syslog.syslog(syslog.LOG_INFO, "".join(traceback.format_stack()))
#         mera_log("".join(traceback.format_stack()))
#         # self.sqlfile = config.get("sqlfile", "/etc/privacyidea/pam.sqlite")


def authenticate(pamh, flags, argv):
    rval = pamh.PAM_AUTH_ERR
    try:
        mera_log("authenticate()")
        config = _get_config(argv)
        debug = config.get("debug")

        syslog.openlog(facility=syslog.LOG_AUTH)

        print("This is a test message.")

        Color.printc("Is this message coloured?", colors=[Color.CRED, Color.CBLUEBG])

        try:
            # inspect_object(pamh)

            # mera_log("env: %s" % str(pamh.env.keys()))

            # pam_message = pamh.Message(pamh.PAM_PROMPT_ECHO_ON, "Press some keys and enter.")
            # response = pamh.conversation(pam_message)
            # inspect_object(response)
            # print(response.resp)
            # print(response.resp_retcode)

            server, message = setup_approve(pamh, flags, config)

            print("%s %s %s" % (message["id"], message["pid"], message["randnum"]))

            rval = wait_for_approve(pamh, server, randnum=message["randnum"])

            # rval = pamh.PAM_SUCCESS

        except Exception as exx:
            import traceback
            syslog.syslog(syslog.LOG_ERR, traceback.format_exc())
            syslog.syslog(syslog.LOG_ERR, "%s: %s" % (__name__, exx))
            rval = pamh.PAM_AUTH_ERR
        except requests.exceptions.SSLError:
            syslog.syslog(syslog.LOG_CRIT, "%s: SSL Validation error. Get a valid "
                                        "SSL certificate for your privacyIDEA "
                                        "system. For testing you can use the "
                                        "options 'nosslverify'." % __name__)
        finally:
            syslog.closelog()

        mera_log("End of pam_sm_authenticate()")
    except Exception as e:
        import traceback
        mera_log("Error in authenticate:")
        mera_log(traceback.format_exc())
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
    mera_log("pam_sm_authenticate()")
    return authenticate(pamh, flags, argv)


def pam_sm_setcred(pamh, flags, argv):
    mera_log("pam_sm_setcred()")
    # return authenticate(pamh, flags, argv)
    return pamh.PAM_SUCCESS


def pam_sm_acct_mgmt(pamh, flags, argv):
    mera_log("pam_sm_acct_mgmt()")
    return pamh.PAM_SUCCESS


def pam_sm_open_session(pamh, flags, argv):
    """
    The pam_sm_open_session function is the service module's implementation of
    the pam_open_session(3) interface.
    This function is called to commence a session.
    https://linux.die.net/man/3/pam_sm_open_session
    """
    mera_log("pam_sm_open_session()")
    mera_log("".join(traceback.format_stack()))
    mera_log("pamh: type=%s" % str(type(pamh)))
    # import inspect
    # mera_log("inspect: %s" % str(inspect.getsource(PamHandle_type)))

    # The session was successfully started.
    return pamh.PAM_SUCCESS


def pam_sm_close_session(pamh, flags, argv):
    """
    The pam_sm_close_session function is the service module's implementation of
    the pam_close_session(3) interface.
    This function is called to terminate a session.
    https://linux.die.net/man/3/pam_sm_close_session
    """
    mera_log("pam_sm_close_session()")
    # The session was successfully terminated.
    return pamh.PAM_SUCCESS


def pam_sm_chauthtok(pamh, flags, argv):
    mera_log("pam_sm_chauthtok()")
    return pamh.PAM_SUCCESS