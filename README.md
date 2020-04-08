# sudo_pyair

A python-based cousin of [sudo_pair](https://github.com/square/sudo_pair/).

### Usage

After setup, the flow is as follows.

The user `alex` wishes to run a command with elevated privileges using `sudo`.
The user runs the command, for example: `sudo systemctl restart ssh.service`
The user is provided with a tuple of three numbers: `1234 5678 9012`

The user `alex` communicates this tuple to the approver `bridget`.

The approver `bridget` then runs the command `approve_sudo` followed by the tuple of numbers.
`bridget` runs this command to approve: `approve_sudo 1234 5678 9012`.

### Setup

Install these scripts in the following locations:

```
+-------------------------------------------------+--------------------------------------+
| sudo_pypair/scripts/python_pam.py               | /opt/python_pam_server.py            |
| sudo_pypair/scripts/approver.py                 | /opt/approver.py                     |
| sudo_pypair/scripts/approver.sh                 | /usr/local/bin/approve               |
| sudo_pypair/scripts/start_shared_screen.sh      | /usr/local/bin/start_shared_screen   |
+-------------------------------------------------+--------------------------------------+
```


Modify the file at `/etc/pam.d/sudo`.

In the `auth` section of the file, add the following line above all other auth lines:
    `auth       sufficient pam_python.so /opt/python_pam.py config_key1=config_value1 config_key2=config_value2 config_key3=config_value3 ...`

Also, remove or comment the line `@include common-auth`.

Configuration is described in the section below.


#### Configuration

The configuration options are described as follows:

- **debug** - A flag to enable debug logging. Valid values: True, False. Default: False.
- **approver_user** - Name of the user(s) who can approve the requests for elevated privileges. Accepts comma-separated values.
- **approver_group** - Name of the group(s), users of whose can approve the requests for elevated privileges. Accepts comma-separated values.
