# import subprocess
# from django.db import models
# from django.conf import settings
import json
import os

DATA_FILE_DIR_DEFAULT="/srv/pipeline-logs"

# TODO : Change implementation into proper model and move this class into model package.


class ContainerLinksModel(object):
    """Represents information about the container, stored in the model."""

    def __init__(self, data_dir=DATA_FILE_DIR_DEFAULT):
        """
        Intialize the Model
        :param data_dir: The directory to which we need to dump the data file to.
        """
        self._data_dir = data_dir
        self.data_file = data_dir + "/container_info.json"
        self.data = dict()
        if os.path.exists(self.data_file):
            self.unmarshall()
        else:
            self.marshall()

    def unmarshall(self):
        """Loads the model information into the object."""

        with open(self.data_file) as f:
            self.data = json.load(f)

    def marshall(self):
        """Saves the model information"""

        with open(self.data_file, "w") as f:
            json.dump(self.data, f)

    def append_info(self, container_name, dockerfile_link):
        """
        Appends the container information to the model
        :param container_name: The name of the container
        :param dockerfile_link: The link to the dockerfile.
        """
        self.data[container_name] = {
            "dockerfile_link": dockerfile_link
        }

    def delete_info(self, container_name):
        """
        Given a container name, deletes information about it, if it exists.
        :param container_name: The name of the container.
        """
        if container_name in self.data:
            self.data.pop(container_name, None)
