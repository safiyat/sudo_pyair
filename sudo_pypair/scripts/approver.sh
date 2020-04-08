#!/usr/bin/env bash

approval_codes="$@"

function run_approver_py() {
    PYTHONPATH=/opt/ python3 -B -m approver ${approval_codes}
}

function get_screen_name() {
    PYTHONPATH=/opt/ python3 -B -m approver -c "${approval_codes}"
}

function attach_after_approval() {
    screen -x $1
}

function kill_screen_Session() {
    # Doesn't work.
    screen -S $1 -X kill
}

screen_name=$(get_screen_name 2> /dev/null)
run_approver_py

case "$?" in
    "11")
        # Approved boy
        attach_after_approval ${screen_name}
        # When detached
        # set -x
        # kill_screen_Session ${screen_name}
        ;;
    "22")
        # Declined
        ;;
    "33")
        # On hold
        ;;
esac
