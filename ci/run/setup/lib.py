from ci.run.common.lib import run_cmd, render_j2_template
from ci.run.common.constants.constants import PROJECT_DIR, CONTROLLER_WORK_DIR
from ci.run.common.constants.provision import CI_PROVISION_INVENTORY, \
    CI_PROVISION_INVENTORY_TEMPL


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


def sync_controller(controller, stream=False):
    """
    Syncs the controller host pipeline service code

    Args:
        controller (str): Hostname of controller node
        stream (bool): Whether to stream output of syncing
    """
    run_cmd(
        "rsync -auvr --delete "
        "-e 'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' "
        "%s/ root@%s:%s" % (
            PROJECT_DIR, controller, CONTROLLER_WORK_DIR), stream=stream)


def setup_controller(controller):
    """
    Install needed packages and utilities on controller node

    Args:
        controller (str): Hostname of controller node
    """
    # provision controller node, install required packages
    run_cmd(
        "yum install -y git && "
        "yum install -y rsync && "
        "yum install -y gcc libffi-devel python-devel openssl-devel && "
        "yum install -y epel-release && "
        "yum install -y PyYAML python-networkx python-nose python-pep8 && "
        "yum install -y "
        "http://cbs.centos.org/kojifiles/packages/ansible/2.2.1.0/"
        "2.el7/noarch/ansible-2.2.1.0-2.el7.noarch.rpm",
        host=controller)


def generate_ansible_inventory(jenkins_master_host, jenkins_slave_host,
                               openshift_host, scanner_host, nfs_share):
    """Generates ansible inventory text for provisioning nodes.

    Args:
        jenkins_master_host (str): Hostanme of Jenkins master
        jenkins_slave_host (str): Hostname of Jenkins slave
        openshift_host (str): Hostname of OpenShift node
        scanner_host (str): Hostname of scanner node
        nfs_share (str): NFS mount path to be configured on all nodes

    Note:
        This function writes ansible inventory file to "hosts" file
        inside project directory. This inventory is then used for
        provisioning.
    """

    test_nfs_share = scanner_host + ":" + nfs_share

    context = {
        "jenkins_master_host": jenkins_master_host,
        "jenkins_slave_host": jenkins_slave_host,
        "openshift_host": openshift_host,
        "scanner_host": scanner_host,
        "test_nfs_share": test_nfs_share
    }
    
    render_j2_template(
        CI_PROVISION_INVENTORY_TEMPL,
        context,
        CI_PROVISION_INVENTORY
    )
