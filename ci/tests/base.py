import copy
import json
import os
import time
import unittest
from xml.dom.minidom import parseString
from ci.run.common.lib import Node, run_cmd, _print, get_node_info

from container_pipeline.lib import settings


class BaseTestCase(unittest.TestCase):
    """Base test case to extend test cases from"""

    def setUp(self):
        self.hosts = get_node_info()

    def run_cmd(self, cmd, node=None, stream=False):
        """
        Run command on local or remote machine (over SSH).

        Args:
            cmd (str): Command to execute
            node (ci.run.common.lib.Node)
            stream (bool): Whether to stream output or not

        Returns:
            Output string

        Raises:
            Exception if command execution fails
        """
        host_info = self.hosts.get(self.node)
        return run_cmd(cmd, node=node or host_info,
                       stream=stream)

    def cleanup_openshift(self):
        try:
            print self.run_cmd(
                'oc --config /var/lib/origin/openshift.local.config/master/'
                'admin.kubeconfig delete project '
                '53b1a8ddd3df5d4fd94756e8c20ae160e565a4b339bfb47165285955',
                node=self.hosts['openshift'])
        except:
            pass
        time.sleep(10)

    def cleanup_beanstalkd(self):
        print self.run_cmd('sudo systemctl stop cccp_imagescanner',
                           node=self.hosts['jenkins_master'])
        print self.run_cmd('sudo systemctl stop cccp-dockerfile-lint-worker',
                           node=self.hosts['jenkins_slave'])
        print self.run_cmd('sudo systemctl stop cccp-scan-worker',
                           node=self.hosts['scanner'])
        print self.run_cmd('sudo docker stop build-worker; '
                           'sudo docker stop delivery-worker; '
                           'sudo docker stop dispatcher-worker',
                           node=self.hosts['jenkins_slave'])

        print self.run_cmd('sudo systemctl restart beanstalkd',
                           node=self.hosts['openshift'])
        time.sleep(5)

        print self.run_cmd('sudo docker start build-worker; '
                           'sudo docker start delivery-worker; '
                           'sudo docker start dispatcher-worker',
                           node=self.hosts['jenkins_slave'])
        print self.run_cmd('sudo systemctl start cccp-dockerfile-lint-worker',
                           node=self.hosts['jenkins_slave'])
        print self.run_cmd('sudo systemctl start cccp-scan-worker',
                           node=self.hosts['scanner'])
        print self.run_cmd('sudo systemctl start cccp_imagescanner',
                           node=self.hosts['jenkins_master'])

    def get_jenkins_builds_for_job(self, job):
        """Get builds for a Jenkins job"""
        s = self.run_cmd('curl -g "http://localhost:8080/job/%s/api/xml?'
                         'tree=allBuilds[result,number]&"' % job,
                         node=self.hosts['jenkins_master']).strip()
        dom = parseString(s)
        builds = [child.getElementsByTagName('number')[0].childNodes[0].data
                  for child in dom.childNodes[0].childNodes]
        return builds
