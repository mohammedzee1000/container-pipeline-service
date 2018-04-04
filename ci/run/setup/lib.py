from ci.run.common.lib import run_cmd, render_j2_template
from ci.run.common.constants.constants import PROJECT_DIR, CONTROLLER_WORK_DIR
from ci.run.common.constants.provision import CI_PROVISION_INVENTORY, \
    CI_PROVISION_INVENTORY_TEMPL


def sync_controller(controller, stream=False):
    """
    Syncs the controller host pipeline service code

    Args:
        controller (ci.run.common.lib.Node): Controller node
        stream (bool): Whether to stream output of syncing
    """
    run_cmd(
        "rsync -auvr --delete "
        "-e 'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no' "
        "%s/ root@%s:%s" % (
            PROJECT_DIR, controller.address, CONTROLLER_WORK_DIR),
        stream=stream)


def setup_controller(controller):
    """
    Install needed packages and utilities on controller node

    Args:
        controller (ci.run.common.lib.Node): Node object of controller node
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
        host=controller.address)


def generate_ansible_inventory(jenkins_master, jenkins_slave,
                               openshift, scanner, nfs_share):
    """Generates ansible inventory text for provisioning nodes.

    Args:
        jenkins_master (ci.run.common.lib.Node): Jenkins master node
        jenkins_slave (ci.run.common.lib.Node): Jenkins slave node
        openshift (ci.run.common.lib.Node): OpenShift node
        scanner (ci.run.common.lib.Node): Scanner node
        nfs_share (str): NFS mount path to be configured on all nodes

    Note:
        This function writes ansible inventory file to "hosts" file
        inside project directory. This inventory is then used for
        provisioning.
    """

    test_nfs_share = scanner + ":" + nfs_share

    context = {
        "jenkins_master_host": jenkins_master.address,
        "jenkins_slave_host": jenkins_slave.address,
        "openshift_host": openshift.address,
        "scanner_host": scanner.address,
        "test_nfs_share": test_nfs_share
    }
    
    render_j2_template(
        CI_PROVISION_INVENTORY_TEMPL,
        context,
        CI_PROVISION_INVENTORY
    )
