#!/usr/bin/env python3
"""Real business logic for mcp-runbook-maintenance handlers."""

import hashlib
import json
import os
import re
import statistics
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------
# Persistence
# --------------------------------------------------------------------------

def _state_dir() -> Path:
    override = os.environ.get("MCP_RUNBOOK_MAINTENANCE_STATE_DIR")
    path = Path(override) if override else Path(__file__).resolve().parent / "state"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _state_path() -> Path:
    return _state_dir() / "runbook_state.json"


def _default_state() -> dict[str, Any]:
    return {
        "version": "1.0.0",
        "changelog_entries": [],
        "runbooks": {},
        "sequence": 2000,
    }


def load_state() -> dict[str, Any]:
    path = _state_path()
    if not path.exists():
        state = _default_state()
        save_state(state)
        return state
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        state = _default_state()
    base = _default_state()
    base.update(state)
    for key, default in _default_state().items():
        if key not in base:
            base[key] = default
    return state


def save_state(state: dict[str, Any]) -> None:
    path = _state_path()
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".runbook-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


# --------------------------------------------------------------------------
# Domain data
# --------------------------------------------------------------------------

SEED_CHANGELOG: list[dict[str, Any]] = [
    {
        "id": "cl-2001",
        "version": "v2.1.0",
        "category": "added",
        "summary": "FR/EN compliance digest cadence",
        "body": "Added weekly MiCA digest and AMF national-level interpretation endpoints to mcp-frcompliance.",
        "author": "sm-001",
        "created_at": "2026-09-15T10:00:00Z",
        "breaking": False,
        "affected_components": ["mcp-frcompliance"],
        "runbook_link": "rb-frcompliance",
    },
    {
        "id": "cl-2002",
        "version": "v2.1.0",
        "category": "changed",
        "summary": "SLA credit self-execution threshold lowered",
        "body": "Desk-tier recovery window reduced from 60 to 45 minutes.",
        "author": "sm-002",
        "created_at": "2026-09-18T14:30:00Z",
        "breaking": False,
        "affected_components": ["mcp-agent-sla"],
        "runbook_link": "rb-agent-sla",
    },
    {
        "id": "cl-2003",
        "version": "v2.0.0",
        "category": "security",
        "summary": "Rotated on-chain attestation signing key",
        "body": "Rotated the HMAC signing key used for mcp-onchain-proof attestations.",
        "author": "eng-001",
        "created_at": "2026-08-20T09:00:00Z",
        "breaking": False,
        "affected_components": ["mcp-onchain-proof"],
        "runbook_link": "rb-onchain-proof",
    },
    {
        "id": "cl-2004",
        "version": "v1.9.0",
        "category": "removed",
        "summary": "Deprecated v1 onboarding flow retired",
        "body": "Removed the legacy one-off onboarding flow in favor of the concierge.",
        "author": "pm-001",
        "created_at": "2026-07-05T11:00:00Z",
        "breaking": True,
        "affected_components": ["mcp-onboarding-concierge"],
        "runbook_link": "rb-onboarding",
    },
    {
        "id": "cl-2005",
        "version": "v2.0.0",
        "category": "fixed",
        "summary": "Regression watcher drift threshold false positives",
        "body": "Fixed false-positive drift alerts in mcp-regression-watch p95 latency metric.",
        "author": "eng-002",
        "created_at": "2026-08-10T16:45:00Z",
        "breaking": False,
        "affected_components": ["mcp-regression-watch"],
        "runbook_link": "rb-regression-watch",
    },
]

REQUIRED_SECTIONS: list[str] = [
    "Overview",
    "Architecture",
    "Deployment",
    "Monitoring",
    "Incident Response",
    "Rollback",
    "Contacts",
]

SEED_RUNBOOKS: dict[str, dict[str, Any]] = {
    "rb-agent-sla": {
        "runbook_id": "rb-agent-sla",
        "title": "Agent SLA Runbook",
        "sections": {
            "Overview": "Agent failure-recovery SLA runbook for mcp-agent-sla.",
            "Architecture": "Watcher + evaluator + credit executor.",
            "Deployment": "Blue/green deploy with canary.",
            "Monitoring": "Heartbeat + adversarial tests.",
            "Incident Response": "Triage, mitigate, post-mortem.",
            "Rollback": "Revert to last known good baseline.",
            "Escalation": "Escalate to on-call retainer after missed SLA windows.",
            "Contacts": "oncall@katsironni.com",
        },
        "cadence_target_days": 30,
        "last_reviewed": "2026-09-20T00:00:00Z",
        "last_modified": "2026-09-20T00:00:00Z",
        "revision": 3,
        "history": [],
    },
    "rb-oncall": {
        "runbook_id": "rb-oncall",
        "title": "Incident On-Call Runbook",
        "sections": {
            "Overview": "On-call escalation and incident response runbook.",
            "Architecture": "Pager + rotation + escalation ladder.",
            "Deployment": "Pager duty rotation schedule.",
            "Monitoring": "Pager responsiveness tracking.",
            "Incident Response": "Named responder owns triage and post-mortem.",
            "Rollback": "Stand down escalation once resolved.",
            "Contacts": "oncall@katsironni.com",
        },
        "cadence_target_days": 30,
        "last_reviewed": "2026-09-25T00:00:00Z",
        "last_modified": "2026-09-25T00:00:00Z",
        "revision": 2,
        "history": [],
    },
    "rb-frcompliance": {
        "runbook_id": "rb-frcompliance",
        "title": "Francophone Compliance Runbook",
        "sections": {
            "Overview": "MiCA digest + AMF interpretation runbook.",
            "Architecture": "Glossary engine + content service.",
            "Deployment": "Weekly digest cadence.",
        },
        "cadence_target_days": 14,
        "last_reviewed": "2026-08-01T00:00:00Z",
        "last_modified": "2026-08-01T00:00:00Z",
        "revision": 2,
        "history": [],
    },
}

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_ts(value: str) -> datetime:
    text = str(value).strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


SEMVER_RE = re.compile(r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-])*))?)?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$")


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _diff_lines(old_text: str, new_text: str) -> dict[str, int]:
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    added = max(0, len(new_lines) - len(old_lines))
    removed = max(0, len(old_lines) - len(new_lines))
    return {"added": added, "removed": removed, "total": len(new_lines)}


# --------------------------------------------------------------------------
# Handlers
# --------------------------------------------------------------------------

def _handler_create_changelog_entry(arguments: dict) -> dict[str, Any]:
    version = str(arguments.get("version", "")).strip()
    category = str(arguments.get("category", "")).strip()
    summary = str(arguments.get("summary", "")).strip()
    body = str(arguments.get("body", "")).strip()
    author = str(arguments.get("author", "")).strip()
    affected_components = arguments.get("affected_components") or []
    persist = bool(arguments.get("persist", True))

    if not version:
        return {"status": "error", "error": "version is required"}
    if not SEMVER_RE.match(version):
        return {"status": "error", "error": f"invalid semver: {version}", "example": "v2.1.0"}
    valid_categories = {"added", "changed", "deprecated", "removed", "fixed", "security"}
    if category not in valid_categories:
        return {"status": "error", "error": f"invalid category: {category}", "valid_categories": sorted(valid_categories)}
    if not summary or not body or not author:
        return {"status": "error", "error": "summary, body, and author are required"}

    state = load_state()
    sequence = int(state.get("sequence", 2000)) + 1
    state["sequence"] = sequence

    breaking = category in ("removed", "deprecated")
    entry_id = f"cl-{sequence}"
    entry = {
        "id": entry_id,
        "version": version,
        "category": category,
        "summary": summary,
        "body": body,
        "author": author,
        "affected_components": affected_components,
        "created_at": _fmt(_now()),
        "breaking": breaking,
        "runbook_link": f"rb-{'-'.join(affected_components[:1])}" if affected_components else None,
    }

    if persist:
        state.setdefault("changelog_entries", []).insert(0, entry)
        save_state(state)

    return {
        "entry": entry,
        "breaking_change": breaking,
    }


def _handler_get_runbook_status(arguments: dict) -> dict[str, Any]:
    runbook_id = str(arguments.get("runbook_id", "")).strip()
    if not runbook_id:
        return {"status": "error", "error": "runbook_id is required"}

    state = load_state()
    runbook = state.get("runbooks", {}).get(runbook_id)
    if not runbook:
        runbook = dict(SEED_RUNBOOKS.get(runbook_id, {}))
    if not runbook:
        return {"status": "error", "error": f"runbook not found: {runbook_id}", "valid_runbooks": list(state.get("runbooks", {}).keys()) + list(SEED_RUNBOOKS.keys())}

    sections = runbook.get("sections", {})
    present_sections = set(sections.keys())
    missing = [s for s in REQUIRED_SECTIONS if s not in present_sections]
    coverage_pct = round(len(present_sections & set(REQUIRED_SECTIONS)) / len(REQUIRED_SECTIONS) * 100.0, 2)

    last_modified = _parse_ts(runbook.get("last_modified", runbook.get("last_reviewed", "2020-01-01T00:00:00Z")))
    days_since_modified = (datetime.now(timezone.utc) - last_modified).days
    cadence_target = runbook.get("cadence_target_days", 30)
    cadence_compliant = days_since_modified <= cadence_target

    # Staleness score: 0 = fresh, 100 = fully stale
    age_factor = min(days_since_modified / max(cadence_target, 1), 2.0)  # cap at 2x cadence
    coverage_factor = 1.0 - (coverage_pct / 100.0)
    staleness_score = round((age_factor * 0.6 + coverage_factor * 0.4) * 100, 2)

    if staleness_score < 25:
        rot_risk = "low"
    elif staleness_score < 60:
        rot_risk = "medium"
    else:
        rot_risk = "high"

    return {
        "runbook_id": runbook_id,
        "title": runbook.get("title", runbook_id),
        "sections": sections,
        "required_sections": REQUIRED_SECTIONS,
        "missing_sections": missing,
        "coverage_pct": coverage_pct,
        "last_modified": runbook.get("last_modified"),
        "last_reviewed": runbook.get("last_reviewed"),
        "days_since_modified": days_since_modified,
        "cadence_target_days": cadence_target,
        "cadence_compliant": cadence_compliant,
        "revision": runbook.get("revision", 0),
        "staleness_score": staleness_score,
        "rot_risk": rot_risk,
    }


def _handler_update_runbook(arguments: dict) -> dict[str, Any]:
    runbook_id = str(arguments.get("runbook_id", "")).strip()
    section = str(arguments.get("section", "")).strip()
    content = str(arguments.get("content", "")).strip()
    author = str(arguments.get("author", "system") or "system").strip()
    persist = bool(arguments.get("persist", True))

    if not runbook_id or not section or not content:
        return {"status": "error", "error": "runbook_id, section, and content are required"}

    state = load_state()
    runbooks = state.setdefault("runbooks", {})
    if runbook_id not in runbooks:
        seed = dict(SEED_RUNBOOKS.get(runbook_id, {}))
        if not seed:
            return {"status": "error", "error": f"runbook not found: {runbook_id}", "valid_runbooks": list(runbooks.keys()) + list(SEED_RUNBOOKS.keys())}
        runbooks[runbook_id] = seed

    runbook = runbooks[runbook_id]
    sections = runbook.setdefault("sections", {})
    if section not in sections:
        return {
            "status": "error",
            "error": f"unknown section {section!r} for runbook {runbook_id}",
            "valid_sections": sorted(sections.keys()),
        }

    previous_content = sections.get(section, "")

    diff = _diff_lines(previous_content, content)
    sections[section] = content
    runbook["last_modified"] = _fmt(_now())
    runbook["revision"] = runbook.get("revision", 0) + 1

    history_entry = {
        "revision": runbook["revision"],
        "section": section,
        "author": author,
        "changed_at": _fmt(_now()),
        "previous_content_hash": _content_hash(previous_content) if previous_content else None,
        "new_content_hash": _content_hash(content),
        "diff": diff,
    }
    runbook.setdefault("history", []).insert(0, history_entry)

    if persist:
        save_state(state)

    return {
        "runbook_id": runbook_id,
        "section": section,
        "revision": runbook["revision"],
        "diff": diff,
        "history_entry": history_entry,
        "last_modified": runbook["last_modified"],
    }


def _handler_get_changelog_history(arguments: dict) -> dict[str, Any]:
    version = arguments.get("version")
    from_version = arguments.get("from_version")
    to_version = arguments.get("to_version")
    category = arguments.get("category")
    author = arguments.get("author")
    limit = int(arguments.get("limit", 50))

    state = load_state()
    entries = list(state.get("changelog_entries", [])) + [dict(e) for e in SEED_CHANGELOG]

    # Deduplicate by id (seeded + persisted)
    seen = set()
    deduped = []
    for e in entries:
        if e["id"] not in seen:
            seen.add(e["id"])
            deduped.append(e)
    entries = deduped

    if version:
        entries = [e for e in entries if e["version"] == version]
    if from_version:
        entries = [e for e in entries if _ver_compare(e["version"], from_version) >= 0]
    if to_version:
        entries = [e for e in entries if _ver_compare(e["version"], to_version) <= 0]
    if category:
        entries = [e for e in entries if e["category"] == category]
    if author:
        entries = [e for e in entries if e["author"] == author]

    entries.sort(key=lambda e: e["created_at"], reverse=True)
    total = len(entries)
    entries = entries[:limit]

    category_counts: dict[str, int] = {}
    for e in entries:
        category_counts[e["category"]] = category_counts.get(e["category"], 0) + 1

    return {
        "count": len(entries),
        "total_matching": total,
        "filters": {"version": version, "from_version": from_version, "to_version": to_version, "category": category, "author": author},
        "category_counts": category_counts,
        "entries": entries,
    }


def _ver_compare(a: str, b: str) -> int:
    """Compare two semver strings. Returns -1, 0, or 1."""

    def parse(v: str):
        v = v.lstrip("v")
        parts = v.split("-")[0].split(".")
        return tuple(int(p) for p in parts[:3])

    pa, pb = parse(a), parse(b)
    return (pa > pb) - (pa < pb)


def _handler_generate_release_notes(arguments: dict) -> dict[str, Any]:
    from_version = str(arguments.get("from_version", "")).strip()
    to_version = str(arguments.get("to_version", "")).strip()
    if not from_version or not to_version:
        return {"status": "error", "error": "from_version and to_version are required"}

    state = load_state()
    entries = list(state.get("changelog_entries", [])) + [dict(e) for e in SEED_CHANGELOG]
    seen = set()
    deduped = []
    for e in entries:
        if e["id"] not in seen:
            seen.add(e["id"])
            deduped.append(e)
    entries = deduped

    entries = [e for e in entries if _ver_compare(e["version"], from_version) >= 0 and _ver_compare(e["version"], to_version) <= 0]
    entries.sort(key=lambda e: (_ver_compare(e["version"], "v0.0.0"), e["created_at"]))

    grouped: dict[str, list[dict[str, Any]]] = {}
    for e in entries:
        grouped.setdefault(e["category"], []).append(e)

    breaking = [e for e in entries if e.get("breaking")]
    contributors = sorted(set(e["author"] for e in entries))

    category_order = ["security", "added", "changed", "fixed", "deprecated", "removed"]
    category_labels = {
        "security": "### Security",
        "added": "### Added",
        "changed": "### Changed",
        "fixed": "### Fixed",
        "deprecated": "### Deprecated",
        "removed": "### Removed",
    }

    md_lines = [f"# Release Notes: {from_version} -> {to_version}", ""]
    md_lines.append(f"Generated: {_fmt(_now())}")
    md_lines.append(f"Entries: {len(entries)} | Contributors: {', '.join(contributors) if contributors else 'none'}")
    md_lines.append("")
    if breaking:
        md_lines.append("## Breaking Changes")
        for e in breaking:
            md_lines.append(f"- **{e['version']}** {e['summary']} ({e['id']})")
        md_lines.append("")
    for cat in category_order:
        if cat in grouped:
            md_lines.append(category_labels[cat])
            for e in grouped[cat]:
                md_lines.append(f"- **{e['version']}** {e['summary']} — {e['body']} ({e['id']})")
            md_lines.append("")
    markdown = "\n".join(md_lines)

    return {
        "from_version": from_version,
        "to_version": to_version,
        "generated_at": _fmt(_now()),
        "entry_count": len(entries),
        "breaking_changes": len(breaking),
        "contributors": contributors,
        "grouped_by_category": {cat: len(v) for cat, v in grouped.items()},
        "markdown": markdown,
        "content_hash": _content_hash(markdown),
    }


HANDLERS = {
    "create_changelog_entry": _handler_create_changelog_entry,
    "get_runbook_status": _handler_get_runbook_status,
    "update_runbook": _handler_update_runbook,
    "get_changelog_history": _handler_get_changelog_history,
    "generate_release_notes": _handler_generate_release_notes,
}