"""MCP server providing a keyword search tool.

Run this module with Python to expose the Model Context Protocol (MCP)
server over stdio. The server offers a single tool, `search_keyword`,
that scans a UTF-8 text file for occurrences of a keyword and returns
annotated matches.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import anyio
from anyio import to_thread
from mcp.server import FastMCP
from mcp.types import TextContent

# Default to the current working directory when no root is provided.
DEFAULT_ROOT = Path(os.environ.get("RESSL_WORKSPACE_ROOT", Path.cwd())).resolve()


def _ensure_within_root(candidate: Path, root: Path) -> Path:
    """Resolve *candidate* against *root* and guard against traversal."""
    resolved = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"{resolved} is outside the allowed workspace root {root}") from exc
    return resolved


@dataclass(frozen=True)
class Match:
    """Represents a single keyword match in a text file."""

    line_number: int
    line: str

    def format(self, keyword: str, case_sensitive: bool) -> str:
        """Render the match with the keyword highlighted in brackets."""
        highlight = keyword if case_sensitive else keyword.lower()
        search_line = self.line if case_sensitive else self.line.lower()
        start_index = search_line.find(highlight)
        if start_index == -1:
            return f"{self.line_number}: {self.line.strip()}"
        end_index = start_index + len(highlight)
        return (
            f"{self.line_number}: {self.line[:start_index]}["
            f"{self.line[start_index:end_index]}"
            f"]{self.line[end_index:]}".rstrip("\n")
        )


def _collect_matches(
    file_contents: Sequence[str],
    keyword: str,
    *,
    case_sensitive: bool,
    max_matches: int,
) -> list[Match]:
    """Identify up to *max_matches* keyword occurrences in *file_contents*."""
    needle = keyword if case_sensitive else keyword.lower()
    matches: list[Match] = []
    for index, original_line in enumerate(file_contents, start=1):
        haystack = original_line if case_sensitive else original_line.lower()
        if needle in haystack:
            matches.append(Match(index, original_line.rstrip("\n")))
            if len(matches) >= max_matches:
                break
    return matches


def build_server(workspace_root: Path = DEFAULT_ROOT) -> FastMCP:
    """Create and configure the MCP server instance."""

    server = FastMCP(
        name="keyword-search-server",
        instructions=(
            "Expose the `search_keyword` tool to look for keyword occurrences "
            "inside files that live within the configured workspace root."
        ),
        website_url="https://github.com/An-Ano-nymus/RESSL-TASK",
    )

    normalized_root = workspace_root.resolve()

    @server.tool(
        name="search_keyword",
        description=(
            "Search for occurrences of a keyword in a UTF-8 text file. "
            "Accepts relative paths and limits results to the configured workspace."
        ),
    )
    async def search_keyword(
        file_path: str,
        keyword: str,
        *,
        case_sensitive: bool = False,
        max_matches: int = 20,
    ) -> list[TextContent]:
        """Return a formatted list of keyword matches within *file_path*."""

        if not keyword:
            raise ValueError("'keyword' must not be empty.")

        if max_matches < 1:
            raise ValueError("'max_matches' must be at least 1.")

        resolved_path = _ensure_within_root(Path(file_path), normalized_root)

        if not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {resolved_path}")

        if not resolved_path.is_file():
            raise ValueError(f"Expected a file path but received: {resolved_path}")

        try:
            raw_contents = await to_thread.run_sync(run_read_text, resolved_path)
        except UnicodeDecodeError as exc:
            raise ValueError(
                f"Could not decode {resolved_path} using UTF-8. Provide a UTF-8 encoded text file."
            ) from exc

        lines = raw_contents.splitlines()
        matches = _collect_matches(lines, keyword, case_sensitive=case_sensitive, max_matches=max_matches)

        if not matches:
            message = (
                f"No matches for '{keyword}' in {resolved_path.relative_to(normalized_root)} "
                f"(case {'sensitive' if case_sensitive else 'insensitive'} search)."
            )
            return [TextContent(type="text", text=message)]

        rendered_matches = "\n".join(match.format(keyword, case_sensitive) for match in matches)
        summary = (
            f"Found {len(matches)} match(es) for '{keyword}' in "
            f"{resolved_path.relative_to(normalized_root)}."
        )

        return [
            TextContent(type="text", text=summary),
            TextContent(type="text", text=rendered_matches),
        ]

    return server


def run_read_text(path: Path) -> str:
    """Helper to allow ``Path.read_text`` inside ``anyio.to_thread``."""
    return path.read_text(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for manually launching the server."""

    parser = argparse.ArgumentParser(description="Run the keyword search MCP server over stdio.")
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=DEFAULT_ROOT,
        help=(
            "Root directory for resolving relative file paths. Defaults to the "
            "current working directory or RESSL_WORKSPACE_ROOT when set."
        ),
    )
    return parser.parse_args()


def main() -> None:
    """Entrypoint when executed as a script."""

    args = parse_args()
    workspace_root = args.workspace_root.resolve()
    server = build_server(workspace_root)
    anyio.run(server.run_stdio_async)


if __name__ == "__main__":
    main()
