import base64
import json
import re
from urllib.parse import urlparse

from django.conf import settings

from apps.extraction.exceptions import EmptyDocumentError, InvalidSourceURLError, RemoteFetchError
from apps.extraction.http import fetch_url
from apps.extraction.text_utils import normalize_text

from .base import ProcessingResult, SubmissionProcessor

_GITHUB_HOSTS = {"github.com", "www.github.com"}
# GitHub usernames/repo names: alphanumeric and hyphens/underscores/dots,
# no leading/trailing separator. Validated before being interpolated into
# an api.github.com request URL — defense-in-depth against path/URL
# injection via a crafted source_url, on top of the host check above and
# the same check already enforced at the serializer layer.
_VALID_SEGMENT = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9])?$")
_USER_AGENT = "RoastAnythingBot/1.0"


class GitHubProcessor(SubmissionProcessor):
    """
    Retrieves public repository or user-profile metadata (plus, for a
    repository, its README — the only extra file ever fetched; never a
    tree/tarball/per-file walk) from the GitHub REST API and summarizes
    it as normalized text + structured metadata.

    Anonymous by default (access_token=None), subject to GitHub's
    unauthenticated rate limit (~60 requests/hour/IP). A future per-user
    OAuth flow would look up that user's stored GitHub token and pass it
    here via apps.extraction.processors.registry.get_processor — this
    constructor parameter is the entire extension point; no other change
    would be needed. No OAuth flow is implemented in this phase.

    Requests always target settings.EXTRACTION_GITHUB_API_BASE_URL, a
    fixed host built from a Python literal — never derived from
    submission.source_url — so unlike WebsiteProcessor, these calls are
    not routed through apps.extraction.http.is_safe_public_url()'s
    SSRF guard: there is no way for user input to redirect them
    elsewhere. submission.source_url is still validated (host + path
    shape) below, but only to identify an owner/repo, never to build the
    request target itself.
    """

    processor_name = "github"

    def __init__(self, *, access_token: str | None = None):
        self._access_token = access_token

    def process(self, submission) -> ProcessingResult:
        owner, repo = self._parse_owner_repo(submission.source_url)
        headers = self._headers()

        if repo:
            text, metadata = self._process_repo(owner, repo, headers)
        else:
            text, metadata = self._process_user(owner, headers)

        text = normalize_text(text, max_chars=settings.EXTRACTION_MAX_TEXT_CHARS)
        if not text:
            raise EmptyDocumentError("No usable GitHub profile/repository information found.")
        return ProcessingResult(text=text, metadata=metadata)

    def _parse_owner_repo(self, url: str | None) -> tuple[str, str | None]:
        parsed = urlparse(url or "")
        if parsed.hostname not in _GITHUB_HOSTS:
            raise InvalidSourceURLError("Not a github.com URL.")

        segments = [s for s in parsed.path.split("/") if s]
        if not segments:
            raise InvalidSourceURLError(
                "Could not identify a GitHub user or repository in this URL."
            )

        owner, repo = segments[0], (segments[1] if len(segments) > 1 else None)
        for segment in (owner, repo):
            if segment and not _VALID_SEGMENT.match(segment):
                raise InvalidSourceURLError("GitHub URL contains an invalid owner/repository name.")
        return owner, repo

    def _headers(self) -> dict:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": _USER_AGENT}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    def _get_json(self, path: str, headers: dict) -> dict:
        response = fetch_url(
            f"{settings.EXTRACTION_GITHUB_API_BASE_URL}{path}",
            timeout=settings.EXTRACTION_HTTP_TIMEOUT_SECONDS,
            max_bytes=settings.EXTRACTION_HTTP_MAX_RESPONSE_BYTES,
            headers=headers,
        )
        try:
            return json.loads(response.body.decode("utf-8", errors="replace"))
        except ValueError as exc:
            raise RemoteFetchError("GitHub API returned an unparseable response.") from exc

    def _process_repo(self, owner: str, repo: str, headers: dict) -> tuple[str, dict]:
        try:
            data = self._get_json(f"/repos/{owner}/{repo}", headers)
        except RemoteFetchError as exc:
            raise RemoteFetchError(
                f"Could not fetch GitHub repository {owner}/{repo}: {exc}"
            ) from exc

        description = data.get("description") or ""
        language = data.get("language") or ""
        stars = data.get("stargazers_count", 0)
        forks = data.get("forks_count", 0)
        topics = data.get("topics") or []
        readme = self._fetch_readme(owner, repo, headers)

        lines = [f"GitHub repository: {data.get('full_name', f'{owner}/{repo}')}"]
        if description:
            lines.append(f"Description: {description}")
        if language:
            lines.append(f"Primary language: {language}")
        lines.append(f"Stars: {stars} | Forks: {forks}")
        if topics:
            lines.append(f"Topics: {', '.join(topics)}")
        if readme:
            lines.append("\nREADME excerpt:\n" + readme)

        metadata = {
            "source_url": f"https://github.com/{owner}/{repo}",
            "owner": owner,
            "repo": repo,
            "description": description,
            "language": language,
            "stars": stars,
            "forks": forks,
            "topics": topics,
        }
        return "\n".join(lines), metadata

    def _fetch_readme(self, owner: str, repo: str, headers: dict) -> str:
        # README-only, by design — repository content beyond this is
        # never fetched ("avoid downloading unnecessary files"). Failure
        # here is non-fatal: repo metadata alone is still useful.
        try:
            data = self._get_json(f"/repos/{owner}/{repo}/readme", headers)
        except RemoteFetchError:
            return ""
        content = data.get("content", "")
        if data.get("encoding") == "base64" and content:
            try:
                return base64.b64decode(content).decode("utf-8", errors="replace")
            except (ValueError, UnicodeDecodeError):
                return ""
        return ""

    def _process_user(self, owner: str, headers: dict) -> tuple[str, dict]:
        try:
            data = self._get_json(f"/users/{owner}", headers)
        except RemoteFetchError as exc:
            raise RemoteFetchError(f"Could not fetch GitHub user {owner}: {exc}") from exc

        name = data.get("name") or owner
        bio = data.get("bio") or ""
        company = data.get("company") or ""
        location = data.get("location") or ""
        public_repos = data.get("public_repos", 0)
        followers = data.get("followers", 0)

        lines = [f"GitHub profile: {name} (@{owner})"]
        if bio:
            lines.append(f"Bio: {bio}")
        if company:
            lines.append(f"Company: {company}")
        if location:
            lines.append(f"Location: {location}")
        lines.append(f"Public repositories: {public_repos} | Followers: {followers}")

        metadata = {
            "source_url": f"https://github.com/{owner}",
            "owner": owner,
            "name": name,
            "bio": bio,
            "public_repos": public_repos,
            "followers": followers,
        }
        return "\n".join(lines), metadata
