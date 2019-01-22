# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from ccp.apis.v1.ccp_server.models.base_model_ import Model
from ccp.apis.v1.ccp_server.models.meta import Meta  # noqa: F401,E501
from ccp.apis.v1.ccp_server.models.project_builds import \
    ProjectBuilds  # noqa: F401,E501
from ccp.apis.v1.ccp_server import util


class ProjectBuildsInfo(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, builds: List[ProjectBuilds], meta: Meta = None):  # noqa: E501
        """ProjectBuildsInfo - a model defined in Swagger

        :param meta: The meta of this ProjectBuildsInfo.  # noqa: E501
        :type meta: Meta
        :param builds: The builds of this ProjectBuildsInfo.  # noqa: E501
        :type builds: ProjectBuilds
        """
        self.swagger_types = {
            'meta': Meta,
            'builds': List[ProjectBuilds]
        }

        self.attribute_map = {
            'meta': 'meta',
            'builds': 'builds'
        }

        self._meta = meta
        self._builds = builds

    @classmethod
    def from_dict(cls, dikt) -> 'ProjectBuildsInfo':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ProjectBuildsInfo of this ProjectBuildsInfo.  # noqa: E501
        :rtype: ProjectBuildsInfo
        """
        return util.deserialize_model(dikt, cls)

    @property
    def meta(self) -> Meta:
        """Gets the meta of this ProjectBuildsInfo.


        :return: The meta of this ProjectBuildsInfo.
        :rtype: Meta
        """
        return self._meta

    @meta.setter
    def meta(self, meta: Meta):
        """Sets the meta of this ProjectBuildsInfo.


        :param meta: The meta of this ProjectBuildsInfo.
        :type meta: Meta
        """

        self._meta = meta

    @property
    def builds(self) -> List[ProjectBuilds]:
        """Gets the builds of this ProjectBuildsInfo.


        :return: The builds of this ProjectBuildsInfo.
        :rtype: ProjectBuilds
        """
        return self._builds if self._builds else []

    @builds.setter
    def builds(self, builds: List[ProjectBuilds]):
        """Sets the builds of this ProjectBuildsInfo.


        :param builds: The builds of this ProjectBuildsInfo.
        :type builds: ProjectBuilds
        """

        self._builds = builds
