import os
import select
import subprocess
import sys
import jinja2


def _print(msg):
    """
    Custom print function for printing instantly and not waiting on buffer

    Args:
        msg (str): Message to print message on stdout.
    """
    print(msg)
    sys.stdout.flush()


def run_cmd(cmd, user='root', host=None, private_key='', stream=False):
    """"
    Run the shell command

    Args:
        cmd (str): Shell command to run on the given node.
        user (str): User with which to run command. Defaults to root.
        host (str):
            Host to run command upon, this could be hostname or IP address.
            Defaults to None, which means run command on local host.
        private_key (str):
            private key for the authentication purpose. Defaults to ''.
        stream (bool):
            Whether stream output of command back. Defaults to False.

    Returns:
        str: The output of command.

    Note:
        If stream=True, the function writes to stdout.
    """

    """ # NOTE: Stop printing run command on CI console, uncomment if needed
    _print('=' * 30 + 'RUN COMMAND' + "=" * 30)
    _print({
        'cmd': cmd,
        'user': user,
        'host': host,
        'private_key': private_key,
        'stream': stream
    })
    """
    if host:
        private_key_args = ''
        if private_key:
            private_key_args = '-i {path}'.format(
                path=os.path.expanduser(private_key))
        _cmd = (
            "ssh -t -o UserKnownHostsFile=/dev/null -o "
            "StrictHostKeyChecking=no {private_key_args} {user}@{host} '"
            "{cmd}"
            "'"
        ).format(user=user, cmd=cmd, host=host,
                 private_key_args=private_key_args)
    else:
        _cmd = cmd

    p = subprocess.Popen(_cmd, shell=True,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = "", ""
    if stream:
        def read(out, err):
            reads = [p.stdout.fileno(), p.stderr.fileno()]
            ret = select.select(reads, [], [], 0.0)

            for fd in ret[0]:
                if fd == p.stdout.fileno():
                    c = p.stdout.read(1)
                    sys.stdout.write(c)
                    out += c
                if fd == p.stderr.fileno():
                    c = p.stderr.read(1)
                    sys.stderr.write(c)
                    err += c
            return out, err

        while p.poll() is None:
            out, err = read(out, err)

        # Retrieve remaining data from stdout, stderr
        for fd in select.select([p.stdout.fileno(), p.stderr.fileno()],
                                [], [], 0.0)[0]:
            if fd == p.stdout.fileno():
                for c in iter(lambda: p.stdout.read(1), ''):
                    sys.stdout.write(c)
                    out += c
            if fd == p.stderr.fileno():
                for c in iter(lambda: p.stderr.read(1), ''):
                    sys.stderr.write(c)
                    err += c
        sys.stdout.flush()
        sys.stderr.flush()
    else:
        out, err = p.communicate()
    if p.returncode is not None and p.returncode != 0:
        if not stream:
            _print("=" * 30 + "ERROR" + "=" * 30)
            _print('ERROR: %s\nOUT: %s' % (err, out))
        raise Exception('Run Command Error for: %s\n%s' % (_cmd, err))
    return out


def setup_ssh_access(from_node, to_nodes):
    """
    Configures password less ssh access

    Args:
        from_node (str): The source node to have ssh access from
        to_nodes (list):
            List of target nodes to configure ssh access from from_node.
    """
    # generate a new key for from_node
    run_cmd('rm -f ~/.ssh/id_rsa* && '
            'ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa',
            host=from_node)

    # get the public key for from_node
    pub_key = run_cmd('cat ~/.ssh/id_rsa.pub', host=from_node).strip()

    # copy the public key of from_node to to_node(s) authorized_keys file
    for node in to_nodes:
        run_cmd(
            'echo "%s" >> ~/.ssh/authorized_keys' % pub_key,
            host=node)


def render_j2_template(template_path, context, destination_path=None):
    """
    Renders a jinja 2 template
    :param template_path: The path to the template to render.
    :param context: Values to render in the template as a dict of key to value
    :param destination_path: The destination file to where we want to render.
    :return: None, if destination_path is given, else the rendered content
    """
    path, filename = os.path.split(template_path)
    data = jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)
    if destination_path:
        with open(destination_path, "w") as f:
            f.write(data)
        return None
    return data

