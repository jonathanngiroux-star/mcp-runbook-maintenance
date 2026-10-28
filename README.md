# mcp-runbook-maintenance

MCP server for **Runbook & Changelog Maintenance Subscription** - fixed-cadence upkeep of
protocol change logs, runbooks, status communication, and version-governance records — including
operator-published NAMED amendments (v1.x/v2.1 changelogs) that buyers verified clause-by-clause.

Pricing: $99-250/mo. Docs positioned as "your first investor pitch, your onboarding funnel, AND
your SEO moat."

## Tools

### `create_changelog_entry`
Create and PERSIST a real changelog entry.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `version` | string | **required** | Semantic version (e.g. v2.1.0) |
| `category` | string enum | **required** | added/changed/deprecated/removed/fixed/security |
| `summary` | string | **required** | One-line summary |
| `body` | string | **required** | Full changelog body text |
| `author` | string | **required** | Author of the entry |
| `affected_components` | array of string | - | Components affected |
| `persist` | boolean | `true` | Persist to state |

Validates semver format and category enum. Returns the entry with breaking-change flag,
affected components, and runbook link.

### `get_runbook_status`
Return real staleness/rot metrics for a runbook.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `runbook_id` | string | **required** | Runbook identifier |

Returns last-modified date, days since last review vs cadence target, cadence compliance,
per-section coverage, missing sections vs required-section template, staleness score (0-100),
and a rot_risk verdict (low/medium/high).

### `update_runbook`
Apply and PERSIST a real section update.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `runbook_id` | string | **required** | Runbook identifier |
| `section` | string | **required** | Section to update |
| `content` | string | **required** | New section content |
| `author` | string | **required** | Author of the update |
| `persist` | boolean | `true` | Persist to state |

Bumps the runbook revision, records a versioned history entry (who, when, what changed,
previous content hash), updates staleness, returns diff summary (added/removed line counts,
revision number).

### `get_changelog_history`
Return changelog entries newest-first with filtering.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `version` | string | - | Exact version filter |
| `from_version` | string | - | From version (inclusive) |
| `to_version` | string | - | To version (inclusive) |
| `category` | string enum | - | Category filter |
| `author` | string | - | Author filter |
| `limit` | integer | 50 | Max entries (1-500) |

Returns entries with summary counts and category counts.

### `generate_release_notes`
Aggregate changelog entries into release notes.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `from_version` | string | **required** | From version (inclusive) |
| `to_version` | string | **required** | To version (inclusive) |

Returns grouped-by-category markdown release notes, breaking changes called out first,
contributors, entry counts, content hash.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

State persisted in `./state/runbook_state.json`. Override with
`MCP_RUNBOOK_MAINTENANCE_STATE_DIR`.

## Connecting to an MCP client

```json
{
  "mcpServers": {
    "runbook-maintenance": {
      "command": "python3",
      "args": ["/tmp/v3-services/mcp-runbook-maintenance/main.py"]
    }
  }
}
```

## License

MIT