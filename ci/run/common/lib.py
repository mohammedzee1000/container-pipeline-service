import os
import select
import subprocess
import sys
import jinja2
import json
from ci.run.common.constants.nodes import NODE_ADDRESS, NODE_KEY, NODE_NAME, \
    NODE_USER, JENKINS_MASTER_NODE, JENKINS_SLAVE_NODE, SCANNER_NODE, \
    OPENSHIFT_NODE, CONTROLLER_NODE, HOSTS_ENV


class Node(object):

    def __init__(self, name=None, address=None, user='root', ssh_key=None):
        self.name = name
        self.address = address
        self.user = user
        self.ssh_key = ssh_key

    def marshall(self):
        return {
            NODE_NAME: str(self.name),
            NODE_ADDRESS: str(self.address),
            NODE_USER: str(self.user),
            NODE_KEY: str(self.ssh_key)
        }

    def unmarshall(self, data):
        self.name = data.get(NODE_NAME)
        self.address = data.get(NODE_ADDRESS)
        self.user = data.get(NODE_USER),
        self.ssh_key = data.get(NODE_KEY)
        return self


def _print(msg):
    """
    Custom print function for printing instantly and not waiting on buffer

    Args:
        msg (str): Message to print message on stdout.
    """
    print(msg)
    sys.stdout.flush()


def run_cmd(cmd, node, stream=False):
    """"
    Run the shell command

    Args:
        node (ci.run.common.lib.Node):
            The node on which, the command needs to run.
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
    if node.address:
        private_key_args = ''
        if node.ssh_key:
            private_key_args = '-i {path}'.format(
                path=os.path.expanduser(node.ssh_key))
        _cmd = (
            "ssh -t -o UserKnownHostsFile=/dev/null -o "
            "StrictHostKeyChecking=no {private_key_args} {user}@{host} '"
            "{cmd}"
            "'"
        ).format(user=node.user, cmd=cmd, host=node.address,
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


def get_node_info():

    cccp_ci_hosts = json.loads(
        os.environ.get('CCCP_CI_HOSTS')
    )

    nodes = None

    if cccp_ci_hosts:
        os_node = Node().unmarshall(
            cccp_ci_hosts.get(OPENSHIFT_NODE)
        )
        jenkins_master_node = Node().unmarshall(
            cccp_ci_hosts.get(JENKINS_MASTER_NODE)
        )
        jenkins_slave_node = Node().unmarshall(
            cccp_ci_hosts.get(JENKINS_SLAVE_NODE)
        )
        scanner_node = Node().unmarshall(
            cccp_ci_hosts.get(SCANNER_NODE)
        )
        controller_node = Node().unmarshall(
            cccp_ci_hosts.get(CONTROLLER_NODE)
        )
        nodes = {
            OPENSHIFT_NODE: os_node,
            JENKINS_MASTER_NODE: jenkins_master_node,
            JENKINS_SLAVE_NODE: jenkins_slave_node,
            SCANNER_NODE: scanner_node,
            CONTROLLER_NODE: controller_node
        }
    return nodes


def set_node_info(nodes):
    if nodes:
        os.environ[HOSTS_ENV] = json.dumps(nodes)
