"""GitHub Discussions publisher for Weekly Platform Intelligence."""

from __future__ import annotations

import os
import json
import httpx
from datetime import date


def get_issue_number(token: str, repo: str = "brianpelow/weekly-platform-intelligence") -> int:
    """Get the next issue number by counting existing discussions."""
    try:
        query = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            discussions(first: 100, categorySlug: "announcements") {
              totalCount
            }
          }
        }
        """
        owner, name = repo.split("/")
        with httpx.Client(timeout=15) as client:
            r = client.post(
                "https://api.github.com/graphql",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": query, "variables": {"owner": owner, "repo": name}},
            )
            if r.status_code == 200:
                count = r.json()["data"]["repository"]["discussions"]["totalCount"]
                return count + 1
    except Exception:
        pass
    return 1


def get_discussion_category_id(token: str, repo: str = "brianpelow/weekly-platform-intelligence") -> str | None:
    """Get the Announcements discussion category ID."""
    try:
        query = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            discussionCategories(first: 10) {
              nodes { id name slug }
            }
          }
        }
        """
        owner, name = repo.split("/")
        with httpx.Client(timeout=15) as client:
            r = client.post(
                "https://api.github.com/graphql",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": query, "variables": {"owner": owner, "repo": name}},
            )
            if r.status_code == 200:
                categories = r.json()["data"]["repository"]["discussionCategories"]["nodes"]
                for cat in categories:
                    if cat["slug"] in ("announcements", "general"):
                        return cat["id"]
    except Exception:
        pass
    return None


def get_repo_id(token: str, repo: str = "brianpelow/weekly-platform-intelligence") -> str | None:
    """Get the repository node ID."""
    try:
        query = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) { id }
        }
        """
        owner, name = repo.split("/")
        with httpx.Client(timeout=15) as client:
            r = client.post(
                "https://api.github.com/graphql",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": query, "variables": {"owner": owner, "repo": name}},
            )
            if r.status_code == 200:
                return r.json()["data"]["repository"]["id"]
    except Exception:
        pass
    return None


def publish_discussion(brief: str, issue_number: int, token: str, repo: str = "brianpelow/weekly-platform-intelligence") -> bool:
    """Publish the brief as a GitHub Discussion."""
    today = date.today()
    week_num = today.isocalendar()[1]
    title = f"Week {week_num} {today.year} - Issue #{issue_number}: Weekly Platform Intelligence"

    repo_id = get_repo_id(token, repo)
    category_id = get_discussion_category_id(token, repo)

    if not repo_id or not category_id:
        print(f"[publisher] Could not get repo or category ID - saving locally only")
        return False

    try:
        mutation = """
        mutation($repoId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
          createDiscussion(input: {
            repositoryId: $repoId
            categoryId: $categoryId
            title: $title
            body: $body
          }) {
            discussion { url }
          }
        }
        """
        with httpx.Client(timeout=15) as client:
            r = client.post(
                "https://api.github.com/graphql",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "query": mutation,
                    "variables": {
                        "repoId": repo_id,
                        "categoryId": category_id,
                        "title": title,
                        "body": brief,
                    }
                },
            )
            if r.status_code == 200:
                data = r.json()
                if "errors" not in data:
                    url = data["data"]["createDiscussion"]["discussion"]["url"]
                    print(f"[publisher] Published: {url}")
                    return True
                else:
                    print(f"[publisher] GraphQL errors: {data['errors']}")
    except Exception as e:
        print(f"[publisher] Error: {e}")
    return False