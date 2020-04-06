#!/usr/bin/env bash

################################################################################
# Script to start a screen session shareable with an approver in the read-only #
# mode.                                                                        #
#                                                                              #
# Usage:                                                                       #
#                                                                              #
#     start_shared_screen <approver_username> [screen_name]                    #
#                                                                              #
################################################################################


APPROVER_USERNAME="${1}"
SCREEN_NAME="${2:-$(whoami)-${APPROVER_USERNAME}-$(date +%s)}"


function usage() {
    echo "Usage:"
    echo -e "\t$0 <approver_username> [screen_name]"
    echo
    echo "approver_username: The username of the approver user. Required."
    echo "screen_name:       The name of the screen to be created. Optional."
}

function check_args() {
    if [ -z "${APPROVER_USERNAME}" ]; then
        echo "Invalid usage. Need at least one argument."
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
    screen -S "${SCREEN_NAME}" -X bindkey -k k1 detach
}

function display_screen_name() {
    screen -S "${SCREEN_NAME}" -X hardstatus on
    screen -S "${SCREEN_NAME}" -X hardstatus alwayslastline
    screen -S "${SCREEN_NAME}" -X hardstatus string "$(whoami)/${SCREEN_NAME}    F1-detach    F12-kill"
}

function attach_to_screen() {
    screen -x "${SCREEN_NAME}"
}


check_args
start_screen
enable_multiuser
add_approver_user
limit_shared_screen_permissions
add_keybindings
display_screen_name
attach_to_screen
