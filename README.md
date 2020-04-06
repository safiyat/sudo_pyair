# sudo_pyair

A distant cousin of [sudo_pair](https://github.com/square/sudo_pair/).

### Flow

1. The user `alex` starts a screen session.
2. The user `alex` shares the session with the approver user `bridget`.
3. The user `alex` runs the command requiring elevated privileges: `sudo systemctl restart ssh.service`.

The `sudo` PAM module passes control to the python script for auth.

The python script prompts for dual password on the screen. First password followed by the second password, separated by a space.
(But space is also a valid character in the password. So, maybe accept the passwords separately?)
