#!/usr/bin/env python3

"""Update the profile README with Flutter organization pull requests."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


GITHUB_API = "https://api.github.com/search/issues"
GITHUB_USER = "faheemabbas766"
README_PATH = Path(__file__).resolve().parents[1] / "README.md"
START_MARKER = "<!-- FLUTTER_PRS:START -->"
END_MARKER = "<!-- FLUTTER_PRS:END -->"


def search_pull_requests(state: str) -> list[dict[str, Any]]:
    qualifiers = f"type:pr author:{GITHUB_USER} org:flutter is:{state}"
    query = urlencode(
        {
            "q": qualifiers,
            "sort": "updated",
            "order": "desc",
            "per_page": 100,
        }
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{GITHUB_USER}-profile-readme",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(f"{GITHUB_API}?{query}", headers=headers)
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)

    return payload["items"]


def repository_name(item: dict[str, Any]) -> str:
    return "/".join(item["repository_url"].split("/")[-2:])


def markdown_title(title: str) -> str:
    return title.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]").replace("|", "\\|")


def pull_request_line(item: dict[str, Any], *, show_state: bool) -> str:
    repository = repository_name(item)
    label = f"{repository}#{item['number']}"
    state = ""
    if show_state:
        state = " - **Draft**" if item.get("draft") else " - **Ready for review**"
    return f"- [`{label}`]({item['html_url']}) - {markdown_title(item['title'])}{state}"


def badge(label: str, count: int, color: str, label_color: str) -> str:
    encoded_label = label.replace("-", "--").replace("_", "__").replace(" ", "%20")
    return (
        f"![{label}](https://img.shields.io/badge/{encoded_label}-{count}-{color}"
        f"?style=flat-square&labelColor={label_color})"
    )


def render_section(merged: list[dict[str, Any]], open_prs: list[dict[str, Any]]) -> str:
    merged_lines = "\n".join(pull_request_line(item, show_state=False) for item in merged)
    active_lines = "\n".join(pull_request_line(item, show_state=True) for item in open_prs)
    if not merged_lines:
        merged_lines = "_No merged Flutter organization pull requests found._"
    if not active_lines:
        active_lines = "_No active Flutter organization pull requests._"

    return "\n".join(
        [
            START_MARKER,
            "<!-- This section is maintained by scripts/update_flutter_prs.py. -->",
            "",
            badge("Flutter Merged", len(merged), "0f172a", "0ea5e9"),
            badge("Flutter Active", len(open_prs), "0f172a", "f59e0b"),
            "",
            "### Merged Contributions",
            "",
            merged_lines,
            "",
            "### Active Contributions",
            "",
            active_lines,
            END_MARKER,
        ]
    )


def update_readme(section: str) -> bool:
    readme = README_PATH.read_text(encoding="utf-8")
    if readme.count(START_MARKER) != 1 or readme.count(END_MARKER) != 1:
        raise RuntimeError("README must contain exactly one Flutter PR marker pair")

    before, remainder = readme.split(START_MARKER, maxsplit=1)
    _, after = remainder.split(END_MARKER, maxsplit=1)
    updated = f"{before}{section}{after}"
    if updated == readme:
        return False

    README_PATH.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    try:
        merged = search_pull_requests("merged")
        open_prs = search_pull_requests("open")
        changed = update_readme(render_section(merged, open_prs))
    except (OSError, RuntimeError, KeyError, json.JSONDecodeError) as error:
        print(f"Unable to update Flutter pull requests: {error}", file=sys.stderr)
        return 1

    status = "updated" if changed else "already current"
    print(f"README {status}: {len(merged)} merged, {len(open_prs)} active Flutter PRs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
