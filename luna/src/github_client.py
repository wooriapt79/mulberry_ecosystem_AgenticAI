"""
Luna GitHub Client
GitHub API wrapper for Luna's autonomous workbench operations.

Usage:
    client = GitHubClient()
    client.create_issue("wooriapt79/mulberry-research-lab", "title", "body")
    client.upload_file("wooriapt79/mulberry_ecosystem_AgenticAI", "luna/src/foo.py", code, "feat: add foo")
"""

import base64
import logging
import os
from typing import Optional

import requests

logger = logging.getLogger("luna.github_client")


class GitHubError(Exception):
    """Raised when GitHub API returns a non-2xx response."""
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"GitHub API {status}: {message}")


class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise RuntimeError("GITHUB_TOKEN not set — add to Railway env vars")
        self._headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }

    # ──────────────────────────────────────────────
    # Issues
    # ──────────────────────────────────────────────

    def create_issue(self, repo: str, title: str, body: str,
                     labels: Optional[list] = None) -> dict:
        """Create an issue. repo = 'owner/repo'"""
        resp = requests.post(
            f"{self.BASE}/repos/{repo}/issues",
            headers=self._headers,
            json={"title": title, "body": body, "labels": labels or []},
        )
        self._raise_for_status(resp)
        data = resp.json()
        logger.info(f"[GITHUB] Issue #{data['number']} created: {data['html_url']}")
        return data

    def add_comment(self, repo: str, issue_number: int, body: str) -> dict:
        """Add a comment to an issue."""
        resp = requests.post(
            f"{self.BASE}/repos/{repo}/issues/{issue_number}/comments",
            headers=self._headers,
            json={"body": body},
        )
        self._raise_for_status(resp)
        return resp.json()

    def close_issue(self, repo: str, issue_number: int, comment: Optional[str] = None) -> dict:
        """Close an issue, optionally leaving a comment first."""
        if comment:
            self.add_comment(repo, issue_number, comment)
        resp = requests.patch(
            f"{self.BASE}/repos/{repo}/issues/{issue_number}",
            headers=self._headers,
            json={"state": "closed"},
        )
        self._raise_for_status(resp)
        return resp.json()

    # ──────────────────────────────────────────────
    # Files
    # ──────────────────────────────────────────────

    def upload_file(self, repo: str, path: str, content: str,
                    message: str, branch: str = "main") -> dict:
        """
        Create or update a file in the repo.
        Automatically fetches SHA if file already exists (upsert).
        """
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")

        # Check if file exists → get SHA for update
        sha = self._get_file_sha(repo, path, branch)

        body = {"message": message, "content": encoded, "branch": branch}
        if sha:
            body["sha"] = sha

        resp = requests.put(
            f"{self.BASE}/repos/{repo}/contents/{path}",
            headers=self._headers,
            json=body,
        )
        self._raise_for_status(resp)
        data = resp.json()
        action = "updated" if sha else "created"
        logger.info(f"[GITHUB] File {action}: {path} @ {branch}")
        return data

    def read_file(self, repo: str, path: str, branch: str = "main") -> str:
        """Read a file's decoded text content."""
        resp = requests.get(
            f"{self.BASE}/repos/{repo}/contents/{path}",
            headers=self._headers,
            params={"ref": branch},
        )
        self._raise_for_status(resp)
        return base64.b64decode(resp.json()["content"].replace("\n", "")).decode("utf-8")

    def list_directory(self, repo: str, path: str = "", branch: str = "main") -> list:
        """List files/dirs in a path."""
        resp = requests.get(
            f"{self.BASE}/repos/{repo}/contents/{path}",
            headers=self._headers,
            params={"ref": branch},
        )
        self._raise_for_status(resp)
        return [{"name": f["name"], "type": f["type"], "path": f["path"]}
                for f in resp.json()]

    # ──────────────────────────────────────────────
    # Pull Requests
    # ──────────────────────────────────────────────

    def create_pr(self, repo: str, title: str, body: str,
                  head: str, base: str = "main") -> dict:
        """Create a pull request. head = branch name."""
        resp = requests.post(
            f"{self.BASE}/repos/{repo}/pulls",
            headers=self._headers,
            json={"title": title, "body": body, "head": head, "base": base},
        )
        self._raise_for_status(resp)
        data = resp.json()
        logger.info(f"[GITHUB] PR #{data['number']} created: {data['html_url']}")
        return data

    def list_open_prs(self, repo: str) -> list:
        """List open PRs."""
        resp = requests.get(
            f"{self.BASE}/repos/{repo}/pulls",
            headers=self._headers,
            params={"state": "open"},
        )
        self._raise_for_status(resp)
        return [{"number": p["number"], "title": p["title"], "head": p["head"]["ref"]}
                for p in resp.json()]

    # ──────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────

    def _get_file_sha(self, repo: str, path: str, branch: str) -> Optional[str]:
        resp = requests.get(
            f"{self.BASE}/repos/{repo}/contents/{path}",
            headers=self._headers,
            params={"ref": branch},
        )
        if resp.status_code == 200:
            return resp.json().get("sha")
        return None

    def _raise_for_status(self, resp: requests.Response):
        if not resp.ok:
            try:
                msg = resp.json().get("message", resp.text)
            except Exception:
                msg = resp.text
            raise GitHubError(resp.status_code, msg)
