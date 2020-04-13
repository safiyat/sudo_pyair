#!/usr/bin/env bash

################################################################################
# Script to start a screen session shareable with an approver in the read-only #
# mode.                                                                        #
#                                                                              #
# Usage:                                                                       #
#                                                                              #
#     start_shared_screen <approver_username>                                  #
#                                                                              #
################################################################################


APPROVER_USERNAME="${1}"
SCREEN_NAME="$(whoami)-${APPROVER_USERNAME}-$(date +%s)"

function get_valid_approvers() {
    # approver_user=$(grep -o -e 'approver_user=\S*' /etc/pam.d/sudo | cut -d= -f2)
    approver_group=$(grep -o -e 'approver_group=\S*' /etc/pam.d/sudo | cut -d= -f2)

    all_users=$(getent passwd | cut -d: -f1 | grep -v -e root -e $(whoami))
    for user in ${all_users}; do
        user_in_groups=$(groups ${user} 2> /dev/null | cut -d: -f2 | xargs | tr ' ' '|')
        if [[ ${approver_group} =~ ^(${user_in_groups})$ ]]; then
            users_in_approver_group="${users_in_approver_group} ${user}"
        fi
    done

    valid_approvers=$(echo "${approver_user} ${users_in_approver_group}" | tr ' ' '\n' | sort -u)
    echo ${valid_approvers}
}


function usage() {
    echo "Usage:"
    echo -e "\t$0 <approver_username>"
    echo
    echo "approver_username: The username of the approver user. Required."
    echo
    echo "HINT: Valid approvers are one of these: $(get_valid_approvers)"
}

function check_args() {
    valid_approvers=$(get_valid_approvers)
    names=$(echo ${valid_approvers} | tr ' ' '|')

    if ! [[ ${APPROVER_USERNAME} =~ ^(${names})$ ]]; then
        echo "${APPROVER_USERNAME} is not a valid approver."
        echo
        usage
        exit 1
    fi
}

function start_screen() {
    screen -d -m -S "${SCREEN_NAME}"
}

function enable_multiuser() {
    screen -S "${SCREEN_NAME}" -X multiuser on
}

function add_approver_user() {
    screen -S "${SCREEN_NAME}" -X acladd "${APPROVER_USERNAME}"
}

function limit_shared_screen_permissions() {
    screen -S "${SCREEN_NAME}" -X aclchg "${APPROVER_USERNAME}" -w "#"
}

function add_keybindings() {
    screen -S "${SCREEN_NAME}" -X bindkey -k F2 kill
    screen -S "${SCREEN_NAME}" -X autodetach off
    screen -S "${SCREEN_NAME}" -X bind d
    # screen -S "${SCREEN_NAME}" -X bindkey -k k1 detach
}

function display_screen_name() {
    screen -S "${SCREEN_NAME}" -X hardstatus on
    screen -S "${SCREEN_NAME}" -X hardstatus alwayslastline
    screen -S "${SCREEN_NAME}" -X hardstatus string "$(whoami)/${SCREEN_NAME}            F12-kill"
}

function attach_to_screen() {
    screen -S "${SCREEN_NAME}" -X stuff ^L  # CTRL-L
    screen -S "${SCREEN_NAME}" -X clear
    screen -x "${SCREEN_NAME}"
}

if [ $# -ne 1 ]; then
    usage
    exit 1
fi

check_args
start_screen
enable_multiuser
add_approver_user
limit_shared_screen_permissions
add_keybindings
display_screen_name
attach_to_screen
