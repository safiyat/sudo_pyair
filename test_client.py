import json
import os
import sys
import socket
import tempfile


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

argv = sys.argv

socket_file = get_socketfile_path(argv[1], argv[2])

with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
    sock.connect(socket_file)
    # sock.sendall(bytes(json.dumps({"test": "Okay"}), "utf-8"))
    sock.sendall(bytes(json.dumps({"randnum": int(argv[3])}), "utf-8"))
