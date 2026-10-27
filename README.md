# mcp-runbook-maintenance

MCP server for Runbook & Changelog Maintenance - create changelog entries, get runbook status, update runbooks, view history.

## Tools

### create_changelog_entry
Create a new changelog entry for a runbook.

**Parameters:**
- `runbook_id` (string, required): Runbook ID
- `type` (string, required): "create", "update", "deprecate", or "archive"
- `title` (string, required): Change title
- `description` (string, required): Detailed description
- `author` (string, required): Author name
- `version_after` (string, required): Version after change

### get_runbook_status
Get runbook status and details.

**Parameters:**
- `runbook_id` (string, optional): Runbook ID
- `agent_id` (string, optional): Filter by agent ID

### update_runbook
Update a runbook section (auto-creates changelog entry).

**Parameters:**
- `runbook_id` (string, required): Runbook ID
- `section_id` (string, required): Section ID to update
- `content` (string, required): New content
- `author` (string, required): Author name

### get_changelog_history
Get changelog history for a runbook.

**Parameters:**
- `runbook_id` (string, optional): Runbook ID
- `limit` (integer, optional): Max entries (default: 50)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Connecting to Claude Desktop

```json
{
  "mcpServers": {
    "runbook-maintenance": {
      "command": "python",
      "args": ["/path/to/mcp-runbook-maintenance/main.py"],
      "cwd": "/path/to/mcp-runbook-maintenance"
    }
  }
}
```

## License

MIT