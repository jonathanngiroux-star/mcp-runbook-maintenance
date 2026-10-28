#!/usr/bin/env python3
"""Tool definitions for mcp-runbook-maintenance."""

from mcp.types import Tool

TOOLS = [
    Tool(
        name="create_changelog_entry",
        description=(
            "Create and PERSIST a real changelog entry: id, timestamp, semantic version, "
            "category, summary, body, author, plus computed metadata (breaking-change flag, "
            "affected components, link to matching runbook). Validates semver format and "
            "category enum."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "version": {
                    "type": "string",
                    "description": "Semantic version (e.g. v2.1.0).",
                },
                "category": {
                    "type": "string",
                    "enum": ["added", "changed", "deprecated", "removed", "fixed", "security"],
                    "description": "Changelog category.",
                },
                "summary": {
                    "type": "string",
                    "description": "One-line summary.",
                },
                "body": {
                    "type": "string",
                    "description": "Full changelog body text.",
                },
                "author": {
                    "type": "string",
                    "description": "Author of the entry.",
                },
                "affected_components": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Components affected by this change.",
                },
                "persist": {"type": "boolean", "default": True},
            },
            "required": ["version", "category", "summary", "body", "author"],
        },
    ),
    Tool(
        name="get_runbook_status",
        description=(
            "Return REAL staleness/rot metrics for a runbook: last-modified date, days since "
            "last review against cadence target, cadence compliance, per-section coverage, "
            "missing sections vs a required-section template, staleness score (0-100), and a "
            "rot_risk verdict."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "runbook_id": {
                    "type": "string",
                    "description": "Runbook identifier.",
                },
            },
            "required": ["runbook_id"],
        },
    ),
    Tool(
        name="update_runbook",
        description=(
            "Apply and PERSIST a real section update: bumps the runbook revision, records a "
            "versioned history entry (who, when, what changed, previous content hash), updates "
            "staleness, and returns a diff summary (added/removed line counts, revision number)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "runbook_id": {
                    "type": "string",
                    "description": "Runbook identifier.",
                },
                "section": {
                    "type": "string",
                    "description": "Section to update.",
                },
                "content": {
                    "type": "string",
                    "description": "New section content.",
                },
                "author": {
                    "type": "string",
                    "default": "system",
                    "description": "Author of the update.",
                },
                "persist": {"type": "boolean", "default": True},
            },
            "required": ["runbook_id", "section", "content"],
        },
    ),
    Tool(
        name="get_changelog_history",
        description=(
            "Return persisted + seeded changelog entries newest-first with filtering by version "
            "range and category that genuinely works, plus summary counts."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "version": {"type": "string", "description": "Exact version filter."},
                "from_version": {"type": "string", "description": "From version (inclusive)."},
                "to_version": {"type": "string", "description": "To version (inclusive)."},
                "category": {
                    "type": "string",
                    "enum": ["added", "changed", "deprecated", "removed", "fixed", "security"],
                    "description": "Category filter.",
                },
                "author": {"type": "string", "description": "Author filter."},
                "limit": {"type": "integer", "default": 50, "minimum": 1, "maximum": 500},
            },
            "required": [],
        },
    ),
    Tool(
        name="generate_release_notes",
        description=(
            "Aggregate changelog entries in a version range into real release notes: grouped by "
            "category, breaking changes called out first, contributors listed, entry counts, "
            "and a rendered markdown release-notes document."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "from_version": {
                    "type": "string",
                    "description": "From version (inclusive).",
                },
                "to_version": {
                    "type": "string",
                    "description": "To version (inclusive).",
                },
            },
            "required": ["from_version", "to_version"],
        },
    ),
]