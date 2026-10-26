# Copyright (c) 2026 Jack Plowman

# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "loguru==0.7.3",
#     "pygithub==2.10.0",
#     "requests==2.34.2",
# ]
# ///

from enum import Enum
from pathlib import Path
from re import sub

from github import Github
from loguru import logger
from requests import get

STATUSES_FILE = (
    "https://raw.githubusercontent.com/JackPlowman/projects/refs/heads/main/STATUSES.md"
)


class Badge(Enum):
    """Enumeration for repository status badges."""

    Development = "![Development](https://img.shields.io/badge/Development-8A2BE2?style=for-the-badge&color=ff9500&label=Status)"
    Maintenance = "![Maintenance](https://img.shields.io/badge/Maintenance-8A2BE2?style=for-the-badge&color=19e650&label=Status)"
    Deprecated = "![Deprecated](https://img.shields.io/badge/Deprecated-8A2BE2?style=for-the-badge&color=ff0000&label=Status)"
    Terminated = "![Terminated](https://img.shields.io/badge/Terminated-8A2BE2?style=for-the-badge&color=ff0000&label=Status)"


def run() -> None:
    """Check that all repositories are mentioned in the README.md file."""
    readme_contents = Path(__file__).with_name("README.md").read_text(encoding="utf-8")
    logger.info("Read README.md contents from the current checkout.")

    github = Github()
    repositories = github.search_repositories(
        query="user:JackPlowman archived:false is:public fork:false",
    )
    logger.info(
        f"Found {repositories.totalCount} public repositories for user JackPlowman.",
    )

    not_found = []
    active_repositories = set()

    for repo in repositories:
        active_repositories.add(repo.name)
        not_found = check_repository_in_readme(
            repo.name,
            readme_contents,
            not_found,
        )

    if not_found:
        logger.error("The following repositories were not found in README.md:")
        for repo_name in not_found:
            logger.error(f"- {repo_name}")
        msg = "Some repositories are missing from README.md."
        raise ValueError(msg)

    project_statuses = convert_markdown_table_to_dict(readme_contents)
    incorrect_statuses = []

    for repo_name, status in project_statuses.items():
        if repo_name in active_repositories and status:
            incorrect_statuses = check_status_matches(
                incorrect_statuses, repo_name, status
            )

    if incorrect_statuses:
        logger.error("The following repositories have incorrect status badges:")
        for repo_name in incorrect_statuses:
            logger.error(f"- {repo_name}")
        msg = "Some repositories have incorrect status badges."
        raise ValueError(msg)


def convert_markdown_table_to_dict(readme_contents: str) -> dict:
    """Convert a markdown table to a dictionary."""
    readme_lines = readme_contents.split("\n")

    current_projects_start = readme_lines.index("## Current Projects")
    current_projects_end = readme_lines.index("## Contributing") - 1
    data = {}

    for line in readme_lines[current_projects_start + 1 : current_projects_end]:
        if not line.startswith("| ["):
            continue
        # Remove link and instead use project name
        parts = [
            sub(r"!?\[([^\]]+)\]\([^)]+\)", r"\1", part).strip()
            for part in line.split("|")
        ]
        if len(parts) >= 4:  # noqa: PLR2004
            data[parts[1]] = parts[2]

    return data


def check_repository_in_readme(
    repo_name: str,
    readme_contents: str,
    not_found: list,
) -> list:
    """Check if a repository is mentioned in the README.md file."""
    if repo_name in readme_contents:
        logger.info(f"Found repository {repo_name} in README.md.")
    else:
        logger.warning(f"Repository {repo_name} not found in README.md.")
        not_found.append(repo_name)
    return not_found


def check_status_matches(incorrect_statuses: list, repo_name: str, status: str) -> list:
    """Check if the status of a repository matches the expected status in the markdown table."""  # noqa: E501
    badge = Badge[status]
    repo_readme = get(
        f"https://raw.githubusercontent.com/JackPlowman/{repo_name}/refs/heads/main/README.md",
        timeout=10,
    )
    repo_readme.raise_for_status()

    if badge.value.removesuffix("&label=Status)") in repo_readme.text:
        logger.info(f"Repository {repo_name} has the correct status badge.")
    else:
        logger.warning(
            f"Repository {repo_name} does not have the correct status badge: {badge.value}",  # noqa: E501
        )
        incorrect_statuses.append(repo_name)

    return incorrect_statuses


if __name__ == "__main__":
    run()
