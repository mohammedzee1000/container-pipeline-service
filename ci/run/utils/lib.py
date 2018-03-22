import json
import os
import select
import subprocess
import sys

from time import sleep


def _print(msg):
    """
    Custom print function for printing instantly and not waiting on buffer

    Args:
        msg (str): Message to print message on stdout.
    """
    print(msg)
    sys.stdout.flush()

def sync_controller(controller, stream=False):
    """
    Syncs the controller host pipeline service code

    Args:
        controller (str): Hostname of controller node
        strem (bool): Whether to stream output of syncing
    """
    run_cmd(
        "rsync -auvr --delete "
        "-e 'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' "
        "%s/ root@%s:%s" % (
            PROJECT_DIR, controller, CONTROLLER_WORK_DIR), stream=stream)
