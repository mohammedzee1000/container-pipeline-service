#!/usr/bin/env python
import os
import subprocess
import sys
import tempfile
from glob import glob

import yaml

jjb_defaults_file = 'project-defaults.yml'

required_attrs = ['image_name', 'image_version']
optional_attrs = ['rundotshargs']
overwritten_attrs = ['jobid', 'git_url', 'appid', 'jobs']


def projectify(
        new_project, app_id, job_id, git_url, git_path, git_branch, target_file,
        depends_on, notify_email, desired_tag):
    """
    Populates the new_project object with rest of the information in a properly formatted manner
    and returns the same.
    Keyword arguments:
        new_project -- The new_project object to populate with formatted information
        app_id -- The app_id of the container.
        job_id -- The job id of the container.
        git_url -- The git url of the repository from which to the container source can be got.
        git_path -- The path relative to the git repository root where target_file can be found.
        git_branch -- The git branch from which the container needs to be built.
        target_file -- The file containing the source of the container to be built.
        depends_on -- The comma seperated list of containers on which the current container relies on
        notify_email -- The email id to which all email communication from the pipeline will happen.
        desired_tag -- The tag of the container.
    """
    new_project[0]['project']['app_id'] = app_id
    new_project[0]['project']['job_id'] = job_id
    new_project[0]['project']['name'] = app_id
    new_project[0]['project']['git_url'] = git_url
    new_project[0]['project']['git_branch'] = git_branch
    new_project[0]['project']['rel_path'] = ('/' + git_path) \
        if (git_path and not git_path.startswith('/')) else '/'
    new_project[0]['project']['jobs'] = ['cccp-rundotsh-job']

    if 'rundotshargs' not in new_project[0]:
        new_project[0]['project']['rundotshargs'] = ''
    elif new_project[0]['project']['rundotshargs'] is None:
        new_project[0]['project']['rundotshargs'] = ''

    new_project[0]['project']['target_file'] = target_file
    new_project[0]['project']['depends_on'] = depends_on
    new_project[0]['project']['notify_email'] = notify_email
    new_project[0]['project']['desired_tag'] = desired_tag
    return new_project


def main(index_location):

    # Get all the yml format index files inside the index directory.
    for yaml_file in glob(index_location + "/*.yml"):
        # If the file name is not index_template.yml which is a template file, process it further.
        if "index_template" not in yaml_file:
            # Load the index information to memory
            stream = open(yaml_file, 'r')
            index_yaml = yaml.load(stream)
            stream.close()
            # print index_yaml['Projects']

            # Go through all project entries one by one.
            for project in index_yaml['Projects']:
                # If we have a missing or invalid git url then skip that entry
                if not project['git-url']:
                    continue
                else:
                    try:
                        # Create a temp directory where the project data will be saved before applying to project
                        t = tempfile.mkdtemp()
                        print("creating: {}".format(t))
                        # Read the project details, assuming sensible defaults as needed.
                        app_id = project['app-id']
                        job_id = project['job-id']
                        git_url = project['git-url']
                        git_path = project['git-path'] \
                            if (project['git-path'] is not None) else ''
                        git_branch = project['git-branch']
                        target_file = project['target-file']
                        depends_on = project['depends-on']
                        notify_email = project['notify-email']

                        try:
                            desired_tag = project['desired-tag'] \
                                if (project['desired-tag'] is not None) \
                                else 'latest'
                        except Exception as e:
                            desired_tag = 'latest'

                        # workdir = os.path.join(t, git_path)
                        # Generate a file name to be save project data in format acceptable to jjb.
                        # The path is "tempdir/cccp_GENERATED.yaml"
                        generated_filename = os.path.join(
                            t,
                            'cccp_GENERATED.yaml'
                        )
                        # Initialize new_project object to save jjb yaml for project
                        new_project = [{'project': {}}]

                        # Openshift does not accept certain characters. While this is tested in ci, its
                        # still better to have fail safe for corner cases
                        app_id = app_id.replace(
                            '_', '-').replace('/', '-').replace('.', '-')
                        job_id = job_id.replace(
                            '_', '-').replace('/', '-').replace('.', '-')
                        if depends_on is not None:
                            if isinstance(depends_on, list):
                                depends_on = ','.join(depends_on)
                            else:
                                depends_on = str(depends_on)
                            depends_on = depends_on.replace(
                                ':', '-').replace('/', '-')

                        # overwrite any attributes we care about see:
                        # Populate the new_project jjb information and dump it into the temp file
                        # projectify
                        with open(generated_filename, 'w') as outfile:
                            yaml.dump(projectify(
                                new_project, app_id, job_id, git_url, git_path,
                                git_branch, target_file, depends_on, notify_email,
                                desired_tag),
                                outfile)

                        # run jenkins job builder, with generated jjb file to update the job
                        myargs = ['jenkins-jobs',
                                  '--ignore-cache',
                                  'update',
                                  ':'.join(
                                      [jjb_defaults_file, generated_filename])
                                  ]
                        print(myargs)
                        proc = subprocess.Popen(myargs,
                                                stdout=subprocess.PIPE)
                        proc.communicate()

                    finally:
                        print("Removing {}".format(t))
                        # shutil.rmtree(t)


if __name__ == '__main__':
    main(sys.argv[1])
