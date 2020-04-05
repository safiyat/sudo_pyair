import json
import os
import stat
import sys
import SocketServer
import tempfile


gresult = None


def inspect_object(object_to_inspect):
    print('*' * 80)
    print('*' * 80)
    print(str(object_to_inspect))
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


class SudoApprovalSeekServer(SocketServer.UnixStreamServer):
    def _handle_request_noblock(self):
        global gresult
        result = None
        try:
            request, client_address = self.get_request()
        except OSError:
            return result

        result = self.interpret_request(request, client_address)

        self.shutdown_request(request)
        gresult = result
        return gresult

    def interpret_request(self, request, client_address):
        # inspect_object(request)
        # inspect_object(client_address)
        j = None
        data = request.recv(2 ** 16)
        try:
            # inspect_object(data.decode())
            print(data.decode())
            j = json.loads(data.decode())
        except Exception as e:
            print(str(e))

        print(j)
        return j




def get_socketfile_path(id, pid):
    return os.path.join(tempfile.gettempdir(), '%d-%d.sock' % (id, pid))


socket_file = get_socketfile_path(1234, 56789)
max_tries = 3

print(socket_file)


server = SudoApprovalSeekServer(socket_file, None)

os.chown(socket_file, -1, -1)
os.chmod(socket_file, stat.S_IWUSR | stat.S_IWGRP)

counter = 0
while True:
    counter += 1
    result = server.handle_request()

    print("GResult(%d): %s" % (counter, str(gresult)))
    print("Result(%d): %s" % (counter, str(result)))

    if counter == max_tries:
        server.server_close()
        break

os.unlink(socket_file)