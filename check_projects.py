# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "loguru==0.7.3",
#     "pygithub==2.6.1",
#     "requests==2.32.4",
# ]
# ///

from requests import get
from github import Github
from loguru import logger



def run() -> None:
    """Check that all repositories are mentioned in the README.md file."""

    readme_contents = get("https://raw.githubusercontent.com/JackPlowman/projects/refs/heads/main/README.md")
    logger.info("Retrieved README.md contents from GitHub.")

    github = Github()
    repositories = github.search_repositories(
        query="user:JackPlowman archived:false is:public"
    )
    logger.info(f"Found {repositories.totalCount} public repositories for user JackPlowman.")

    not_found = []

    for repo in repositories:
        if repo.name in readme_contents.text:
            logger.info(f"Found repository {repo.name} in README.md.")
        else:
            logger.warning(f"Repository {repo.name} not found in README.md.")
            not_found.append(repo.name)

    if not_found:
        logger.error("The following repositories were not found in README.md:")
        for repo_name in not_found:
            logger.error(f"- {repo_name}")
        raise ValueError("Some repositories are missing from README.md.")

if __name__ == "__main__":
    run()
