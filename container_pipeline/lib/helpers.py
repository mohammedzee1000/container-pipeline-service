

def form_Dockerfile_link(git_URL, git_path, git_branch, target_file):
    """
    Helper function to generate Dockerfile link.
    :param git_URL: The url of the git repository.
    :param git_path: The path, relative to the git repository root, where the file resides.
    :param git_branch: The repository branch where the file resides.
    :param target_file: The name of the target file.
    :return: The reachable link to the dockerfile.
    """

    link_url = None
    if "github" in git_URL or "gitlab" in git_URL:
        link_url = str.format(
            "{git_url}/blob/{git_branch}/{git_path}/{target_file}",
            git_url=git_URL,
            git_branch=git_branch,
            git_path=git_path,
            target_file=target_file
        )
    return link_url