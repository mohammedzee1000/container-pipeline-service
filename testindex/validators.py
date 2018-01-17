from constants import index_keys, cccp_yml_keys
from nuts_and_bolts import execute_command
from os import path, getcwd, chdir, system
import re
from summary import SummaryCollector
from yaml import load


class Validator(object):
    """Base class for all validators"""

    def __init__(self, context):
        """
        Initialize a validator
        Keyword arguments:
            context -- nuts_and_bolts.Context object that holds the global information
            such as environment, summary and Dependency Validator
        """
        self._success = True
        self._summary_collector = None
        self._context = context
        pass

    @staticmethod
    def _load_yml(file_name):
        """
        Loads yml data into a yaml.load object and returns it.
        None and exception object is returned if load failed.
        Keyword arguments:
            file_name -- The path of the yml file to load
        """

        try:
            with open(file_name, "r") as yml_file:
                return load(yml_file), None
        except Exception as e:
            return None, e

    def run(self):
        """"Runs the validator. returning True or False based on success or failure"""
        raise NotImplementedError("Implement this method")


class IndexValidator(Validator):
    """Top level class for index validators"""

    def __init__(self, context, index_file):
        """
        Initialize the IndexValidator object
        Keyword arguments:
            context -- nuts_and_bolts.Context object that holds the global information
            such as environment, summary and Dependency Validator.
            index_file -- The path of the index.d file that is to be validated
        """
        Validator.__init__(self, context=context)
        self._file_name = path.basename(index_file)
        self._index_file = index_file
        temp_index_data, ex = self._load_yml(self._index_file)

        if temp_index_data:
            if index_keys.PROJECTS in temp_index_data:
                self._index_data = temp_index_data[index_keys.PROJECTS]
            else:
                self._success = False
                self._context.summary.global_errors.append("Projects absent in " + self._index_file)
        else:
            self._success = False
            self._context.summary.global_errors.append("Malformed " + path.basename(self._index_file) + " : " + str(ex))
        self._status_list = {
            "fail": [],
            "success": []
        }

    def _mark_entry_invalid(self, entry):
        self._success = False
        if entry in self._status_list["success"]:
            self._status_list["success"].remove(entry)
        if entry not in self._status_list["fail"]:
            self._status_list["fail"].append(entry)

    def _mark_entry_valid(self, entry):
        if entry not in self._status_list["success"]:
            self._status_list["success"].append(entry)

    def run(self):
        """Runs the IndexValidator, returning True or False based on success or failure"""
        raise NotImplementedError("Implement this method.")


class IndexFormatValidator(IndexValidator):
    """Checks the format of index files"""

    def __init__(self, context, index_file):

        IndexValidator.__init__(self, context, index_file)

    def run(self):

        if not self._success:
            return False, self._status_list

        id_list = []

        for entry in self._index_data:

            self._summary_collector = SummaryCollector(self._context, self._file_name, entry)
            self._mark_entry_valid(entry)

            # Check if id field exists
            if index_keys.ID not in entry or (index_keys.ID in entry and entry[index_keys.ID] is None):
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("Missing id")

            else:
                # Check if id has not already been passed
                if entry[index_keys.ID] in id_list:
                    self._mark_entry_invalid(entry)
                    self._summary_collector.add_error("id field must be unique in the file")

                else:
                    id_list.append(entry["id"])

            # Check for pre-build script and pre-build context
            if index_keys.PREBUILD_SCRIPT in entry and entry[index_keys.PREBUILD_SCRIPT] is not None:
                prebuild_path = entry.get(index_keys.PREBUILD_CONTEXT)
                if not prebuild_path:
                    self._mark_entry_invalid(entry)
                    self._summary_collector.add_error("If pre-build script is specified,"
                                                      " then prebuild-context should also "
                                                      "be specified")

            # Checking app-id field
            if index_keys.APP_ID not in entry or (index_keys.APP_ID in entry and entry[index_keys.APP_ID] is None):
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("Missing app-id")

            else:
                if entry[index_keys.APP_ID] != self._file_name.split(".")[0]:
                    self._mark_entry_invalid(entry)
                    self._summary_collector.add_error("app-id should be same as first part of the file name")

                if "_" in entry[index_keys.APP_ID] or "/" in entry[index_keys.APP_ID] or "." in entry[index_keys.APP_ID]:
                    self._mark_entry_invalid(entry)
                    self._summary_collector.add_error("app-id cannot contain _, / or . character.")

            # Checking job-id field
            if index_keys.JOB_ID not in entry or (index_keys.JOB_ID in entry and entry[index_keys.JOB_ID] is None):
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("Missing job-id field")

            else:
                try:
                    int(entry[index_keys.JOB_ID])
                    self._mark_entry_invalid(entry)
                    self._summary_collector.add_error("Job id must be a string")
                except ValueError:
                    pass
                if "_" in entry[index_keys.JOB_ID] or "/" in entry[index_keys.JOB_ID] or "." in entry[index_keys.JOB_ID]:
                    self._mark_entry_invalid(entry)
                    self._summary_collector.add_error("job-id cannot contain _, / or . character.")

            # Check for git-url
            if index_keys.GIT_URL not in entry or (index_keys.GIT_URL in entry and entry[index_keys.GIT_URL] is None):
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("Missing git-url")
            else:
                if "gitlab." in entry[index_keys.GIT_URL] and not entry[index_keys.GIT_URL].endswith(".git"):
                    self._mark_entry_invalid(entry)
                    self._summary_collector.add_error("Git urls from gitlab must end with .git, try {0}.git".format(entry["git-url"]))

            # Checking git-path
            if index_keys.GIT_PATH not in entry or (index_keys.GIT_PATH in entry and entry[index_keys.GIT_PATH] is None):
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("Missing git-path")

            # Check git-branch
            if index_keys.GIT_BRANCH not in entry or (index_keys.GIT_BRANCH in entry and entry[index_keys.GIT_BRANCH] is None):
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("Missing git-branch")

            # Check target-file
            if index_keys.TARGET_FILE not in entry or (index_keys.TARGET_FILE in entry and entry[index_keys.TARGET_FILE] is None):
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("Missing target-file")

            # Check desired-tag
            if index_keys.DESIRED_TAG not in entry or (index_keys.DESIRED_TAG in entry and entry[index_keys.DESIRED_TAG] is None):
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("Missing desired-tag")

            # Check for build-context
            # Ideally, build-context will be a compulsory field but for now im just checking its None
            # TODO : Need to update this to make it compulsory
            if index_keys.BUILD_CONTEXT not in entry and not (index_keys.BUILD_CONTEXT in entry and
                                                             entry[index_keys.BUILD_CONTEXT] is None):
                pass

            # Check notify-email
            if index_keys.NOTIFY_EMAIL not in entry or (index_keys.NOTIFY_EMAIL in entry and entry[index_keys.NOTIFY_EMAIL] is None):
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("Missing notify-email")

            # Check depends-on
            if index_keys.DEPENDS_ON not in entry:
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("Missing depends-on")
            elif entry[index_keys.DEPENDS_ON]:
                depends_on = entry[index_keys.DEPENDS_ON]
                if not isinstance(depends_on, list):
                    depends_on = [depends_on]
                matcher = re.compile("^(([0-9a-zA-Z_-]+[.]{1})*([0-9a-zA-Z_-]+){1}[/]{1})?[0-9a-zA-Z_-]+[/]{1}"
                                     "[0-9a-zA-Z_-]+[:]{1}([0-9a-zA-Z_-]+\.?)+$")
                for item in depends_on:
                    if not matcher.search(str(item)):
                        self._mark_entry_invalid(entry)
                        self._summary_collector.add_error("Depends on entry pattern mismatch found {0} must be"
                                                          " <string>/<string>:<string>, ".format(str(item)))

        return self._success, self._status_list


class IndexProjectsValidator(IndexValidator):
    """Does deeper analysis of index, checking for correctness of provided values."""

    def __init__(self, context, index_file):

        IndexValidator.__init__(self, context, index_file)

    @staticmethod
    def update_git_url(repo_dump, git_url, git_branch):

        clone_path = None

        # Work out the path to clone repo to
        clone_to = git_url

        if ":" in clone_to:
            clone_to = clone_to.split(":")[1]

        clone_to = repo_dump + "/" + clone_to

        # If the path doesnt already exist, attempt to clone repo
        if not path.exists(clone_to):
            cmd = ["git", "clone", git_url, clone_to]
            if not execute_command(cmd):
                return None

        # Update repo
        get_back = getcwd()
        chdir(clone_to)

        cmd = "git branch -r | grep -v '\->' | while read remote; do git branch --track \"${remote#origin/}\"" \
              " \"$remote\" &> /dev/null; done"

        # Get all the branches
        system(cmd)

        # fetch the branches
        cmd = ["git", "fetch", "--all"]
        execute_command(cmd)

        # Pull for update
        cmd = ["git", "pull", "--all"]
        execute_command(cmd)

        # Checkout required branch
        cmd = ["git", "checkout", "origin/" + git_branch]

        if execute_command(cmd):
            clone_path = clone_to

        chdir(get_back)

        return clone_path

    def run(self):

        if not self._success:
            return False, self._status_list

        container_names = {}

        for entry in self._index_data:
            self._mark_entry_valid(entry)
            self._summary_collector = SummaryCollector(self._context, self._file_name, entry)

            clone_path = self.update_git_url(self._context.environment.repo_dump, entry["git-url"], entry["git-branch"])

            if clone_path is None:
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error(
                    "Could not clone specified git-url or could not find specified branch")
                continue

            # Else clone was success, check the git path
            git_path = clone_path + "/" + str(entry["git-path"])

            # Check if specified path exists
            if not path.exists(git_path):
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("The specified git-path does not exist in git repo.")
                continue

            # Else, continue with remaining checks
            cccp_yml_path = None

            # * Check if cccp.yml file exists

            for item in ["cccp.yml", ".cccp.yml", "cccp.yaml", ".cccp.yaml"]:
                check_path = git_path + "/" + item
                if path.exists(check_path):
                    cccp_yml_path = check_path
                    break

            if cccp_yml_path is None:
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("Missing cccp yml file, please check your git-path")
                continue

            # * Check for duplicate entry for same container name
            container_name = entry[index_keys.APP_ID] + "/" + entry[index_keys.JOB_ID] + ":" + str(entry[index_keys.DESIRED_TAG])
            if container_name in container_names:
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error(
                    "Duplicate entry exists at ids : " + str(container_names[container_name]))

            else:
                container_names[container_name] = []

            container_names[container_name].append(entry["id"])

            # * Check for build-context
            if index_keys.BUILD_CONTEXT in entry:
                build_context = entry.get(index_keys.BUILD_CONTEXT)
                if build_context and not path.exists(path.join(clone_path, git_path, build_context)):
                    self._mark_entry_invalid(entry)
                    self._summary_collector.add_error("Specified build context does not exist.")

            # * Check for pre-build script
            # TODO : Make a better implementation of pre-build script checking
            # TODO : Ideally, if prebuild is not in entry, it wont reach here and this should happen if it is not None
            prebuild_exists = False
            if index_keys.PREBUILD_SCRIPT in entry and index_keys.PREBUILD_CONTEXT in entry:
                prebuild_exists = True
                prebuild_script = entry.get(index_keys.PREBUILD_SCRIPT)
                prebuild_context = entry.get(index_keys.PREBUILD_CONTEXT)
                if (prebuild_script and not path.exists(path.join(git_path, prebuild_script))
                    and prebuild_context and not path.exists(path.join(git_path, prebuild_context))):
                    self._mark_entry_invalid(entry)
                    self._summary_collector.add_error("Invalid pre-build script or path specified")

            # * Check for existence of target-file
            if not prebuild_exists and not path.exists(git_path + "/" + entry["target-file"]):
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("The specified target-file does not exist at the git-path")

            # * Validate the cccp yml file
            self._cccp_yml_check(git_path, cccp_yml_path, entry)

        return self._success, self._status_list

    def _cccp_yml_check(self, git_path, cccp_yaml_path, entry):
        """Validates the cccp yaml file"""

        temp_cccp, ex = self._load_yml(cccp_yaml_path)
        if not temp_cccp:
            self._mark_entry_invalid(entry)
            self._summary_collector.add_error("Malformed cccp yml : " + str(ex))
        cccp_yaml = temp_cccp
        self._entry_valid = True

        get_back = getcwd()
        chdir(git_path)
        # * Check for job-entry_id
        if index_keys.JOB_ID not in cccp_yaml:
            self._mark_entry_invalid(entry)
            self._summary_collector.add_error("Missing job-id field in cccp yaml")

        # * Check for test-skip
        if cccp_yml_keys.TEST_SKIP in cccp_yaml:
            value = cccp_yaml[cccp_yml_keys.TEST_SKIP]

            try:
                if value and (value is True or value is False):
                    pass
                if value is None:
                    self._summary_collector.add_warning("Optional test-skip is set None, which means its value will be"
                                                        " ignored")
            except Exception as ex:
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("test-skip should either be True or False as it is a flag")

        # * Check test-script
        if cccp_yml_keys.TEST_SCRIPT in cccp_yaml:
            self._summary_collector.add_warning("Custom test-script has been specified")
            value = cccp_yaml[cccp_yml_keys.TEST_SCRIPT]
            if value and not path.exists(str(value)):
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("The specified test-script does not exist")
            if value is None:
                self._summary_collector.add_warning("Optional test-script has a value of None, which means it will be"
                                                    " ignored")

        # * Check build-script
        if cccp_yml_keys.BUILD_SCRIPT in cccp_yaml:
            self._summary_collector.add_warning("Custom build-script has been specified")
            value = cccp_yaml[cccp_yml_keys.BUILD_SCRIPT]
            if value and not path.exists(str(value)):
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("The specified build-script does not exist")
            if value is None:
                self._summary_collector.add_warning("Optional build-script has has a value None, which means it will be"
                                                    " ignored")

        # * Check delivery-script
        if cccp_yml_keys.DELIVERY_SCRIPT in cccp_yaml:
            self._summary_collector.add_warning("Custom delivery-script has been specified.")
            value = cccp_yaml[cccp_yml_keys.DELIVERY_SCRIPT]
            if value and not path.exists(str(value)):
                self._mark_entry_invalid(entry)
                self._summary_collector.add_error("The specified delivery-script does not exist")
            if value is None:
                self._summary_collector.add_warning("Optional delivery script has value None, which means it will be"
                                                    " ignored")

        chdir(get_back)


class DependencyValidationUpdater(IndexValidator):
    """This script reads the index file and updates the dependency graph, created nodes and edges, for containers and
    dependencies respectively."""

    def __init__(self, context, index_file):
        """Initialize the validator"""

        IndexValidator.__init__(self, context, index_file)

    def run(self):
        """Run the validator the read the index and update the dependency graph"""

        if not self._success:
            return False

        for entry in self._index_data:
            # Form the container name from index yaml
            primary_container_name = str(entry[index_keys.APP_ID]) + "/" + str(entry[index_keys.JOB_ID]) + ":" + str(entry[index_keys.DESIRED_TAG])
            # Add the container to dependency graph (if it does not already exist)
            self._context.dependency_validator.dependency_graph.add_container(primary_container_name, from_index=True)
            # Check if entry has any dependencies to account for
            if entry[index_keys.DEPENDS_ON]:
                if not isinstance(entry[index_keys.DEPENDS_ON], list):
                    value = [entry[index_keys.DEPENDS_ON]]
                else:
                    value = entry[index_keys.DEPENDS_ON]
                for item in value:
                    if ":" not in item:
                        item += ":latest"
                    # Add the dependent container to dependency graph, if it does not already exist
                    self._context.dependency_validator.dependency_graph.add_container(str(item), from_index=True)
                    # Ensure that the dependency from current depends-on container and the current container is
                    #  established
                    self._context.dependency_validator.dependency_graph.add_dependency(str(item),
                                                                                       primary_container_name)
            # Work out the path to targetfile
            git_branch = entry[index_keys.GIT_BRANCH]
            target_file_dir = entry[index_keys.GIT_URL]
            git_path = str(entry[index_keys.GIT_PATH])
            if ":" in target_file_dir:
                # If the git-url containers :, then we dont need the protocol part, so just get the uri
                target_file_dir = target_file_dir.split(":")[1]
            # The final git-path would be path where all repos are dumped + the git-url part + git-path
            # Example : repo_dump = /mydir, git-url = https://github.com/user/repo, git-path= /mydir
            # then final path = /mydir/github.com/user/repo/mydir
            target_file_dir = self._context.environment.repo_dump + "/" + target_file_dir
            target_file = target_file_dir + "/" + git_path + "/" + entry[index_keys.TARGET_FILE]
            get_back = getcwd()
            chdir(target_file_dir)
            # Checkout required branch
            cmd = ["git", "checkout", "origin/" + git_branch]
            execute_command(cmd)
            chdir(get_back)
            base_image = None
            try:
                with open(target_file, "r") as f:
                    for line in f:
                        l = line.strip()
                        if l.startswith("FROM"):
                            base_image = l.split()[1]
                            break
            except Exception as e:
                print e
            if base_image:
                self._context.dependency_validator.dependency_graph.add_container(container_name=base_image,
                                                                                  from_target_file=True)
                self._context.dependency_validator.dependency_graph.add_dependency(base_image, primary_container_name)
        return True


class LightWeightValidator(IndexValidator):
    """Light weight validator does minimum validation, and focuses mostly on building dependency graph"""

    def __init__(self, context, index_file):
        IndexValidator.__init__(self, context, index_file)

    def run(self):
        for entry in self._index_data:
            self._summary_collector = SummaryCollector(self._context, self._file_name, entry)
            if index_keys.GIT_URL not in entry or index_keys.GIT_BRANCH not in entry or index_keys.GIT_PATH not in entry or index_keys.TARGET_FILE not in \
                    entry:
                self._summary_collector.add_error("Missing git-url, git-path, git-branch or target-file")
                self._success = False
                continue
            clone_location = IndexProjectsValidator.update_git_url(self._context.environment.repo_dump,
                                                                   entry[index_keys.GIT_URL], entry[index_keys.GIT_BRANCH])
            if not clone_location:
                self._summary_collector.add_error("Unable to clone specified git-url or find specified git-branch")
                self._success = False
                continue
            validation_path = clone_location + "/" + str(entry[index_keys.GIT_PATH]) + "/" + entry[index_keys.TARGET_FILE]
            if not path.exists(validation_path):
                self._summary_collector.add_error("Invalid git-path or target-file specified")
                self._success = False

        if self._success:
            DependencyValidationUpdater(context=self._context, index_file=self._index_file).run()
        return self._success
