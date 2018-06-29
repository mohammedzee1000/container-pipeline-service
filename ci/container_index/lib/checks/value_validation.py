"""
This file contains validators that check for validity of values provided in the
index
"""
from os import path

from ci.container_index.lib.checks.basevalidation import \
    OptionalClonedValidator
from  ci.container_index.lib.constants import *


class GitCloneValidator(OptionalClonedValidator):
    """
    Validates if git repo is clonable and requisite branch can be checked out.
    """
    def __init__(self, validation_data, file_name):
        super(GitCloneValidator, self).__init__(validation_data, file_name)

    def _validate_after(self):
        self.message.title = "Git Clone Validator"
        if not self.clone_location:
            self._invalidate("Failed to clone git repo or checkout git branch")
            return


class CccpYamlExistsValidator(OptionalClonedValidator):
    """
    Acts as base class for for all CCCP Yaml Validators
    """
    def __init__(self, validation_data, file_name):
        super(CccpYamlExistsValidator, self).__init__(
            validation_data, file_name
        )

    def _validate_after(self):
        self.message.title = "CCCP YAML Validator"
        if all(False in s for s in [
            path.exists(path.join(self.clone_location, "cccp.yml")),
            path.exists(path.join(self.clone_location, ".cccp.yml")),
            path.exists(path.join(self.clone_location, "cccp.yaml")),
            path.exists(path.join(self.clone_location, ".cccp.yaml"))
        ]):
            self._invalidate("CCCP yaml file does not exist in repository.")
            return


class TargetFileExistsValidator(OptionalClonedValidator):
    def __init__(self, validation_data, file_name):
        super(TargetFileExistsValidator, self).__init__(
            validation_data, file_name
        )

    def _validate_after(self):
        self.message.title = "Target File Exists Validator"
        if (not path.exists(
            path.join(
                self.clone_location,
                self.validation_data.get(FieldKeys.GIT_PATH),
                self.validation_data.get(FieldKeys.TARGET_FILE)
            )
        )):
            self._invalidate(
                str.format(
                    "Target File {} does not exist, at the path {}",
                    self.validation_data.get(FieldKeys.TARGET_FILE),
                    self.validation_data.get(FieldKeys.GIT_PATH)
                )
            )
            return