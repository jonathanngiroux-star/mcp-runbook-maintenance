#!/usr/bin/env python3
"""MCP server for runbook-maintenance - Runbook & Changelog Maintenance"""

import json
import os
from datetime import datetime
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("mcp-runbook-maintenance")

RUNBOOKS = {
    "rb-001": {
        "id": "rb-001",
        "agent_id": "agent-001",
        "title": "Trading Bot Alpha Runbook",
        "version": "2.3",
        "status": "active",
        "last_updated": "2024-12-20T10:00:00",
        "sections": [
            {"id": "overview", "title": "Overview", "content": "High-frequency trading bot for ETH/USDC pairs"},
            {"id": "architecture", "title": "Architecture", "content": "Microservices: signal-gen, risk-mgr, execution-engine"},
            {"id": "deployment", "title": "Deployment", "content": "K8s cluster us-east-1, blue-green deployments"},
            {"id": "monitoring", "title": "Monitoring", "content": "Prometheus + Grafana, alerts on P99 latency > 100ms"},
            {"id": "incident-response", "title": "Incident Response", "content": "Runbook: INC-TRADING-001 through INC-TRADING-005"}
        ],
        "owner": "trading-team"
    },
    "rb-002": {
        "id": "rb-002",
        "agent_id": "agent-002",
        "title": "Monitoring Agent Runbook",
        "version": "1.1",
        "status": "active",
        "last_updated": "2024-12-01T10:00:00",
        "sections": [
            {"id": "overview", "title": "Overview", "content": "Infrastructure monitoring and alerting agent"},
            {"id": "architecture", "title": "Architecture", "content": "Single binary, SQLite backend, MCP server interface"},
            {"id": "deployment", "title": "Deployment", "content": "Systemd service on monitoring VPS"},
            {"id": "monitoring", "title": "Self-Monitoring", "content": "Health endpoint /health, logs to journald"}
        ],
        "owner": "platform-team"
    }
}

CHANGELOG = [
    {
        "id": "cl-001",
        "runbook_id": "rb-001",
        "type": "update",
        "title": "Updated failover procedure for new backup endpoint",
        "description": "Added secondary backup endpoint us-west-2, updated DNS failover TTL to 30s",
        "author": "engineer-1",
        "timestamp": "2024-12-20T10:00:00",
        "version_after": "2.3"
    },
    {
        "id": "cl-002",
        "runbook_id": "rb-001",
        "type": "update",
        "title": "Increased position size limits per new risk policy",
        "description": "Max position size increased from 50 to 75 ETH per trade",
        "author": "risk-manager-1",
        "timestamp": "2024-11-15T10:00:00",
        "version_after": "2.2"
    },
    {
        "id": "cl-003",
        "runbook_id": "rb-002",
        "type": "create",
        "title": "Initial runbook creation",
        "description": "Created runbook for monitoring agent v1.0",
        "author": "engineer-2",
        "timestamp": "2024-12-01T10:00:00",
        "version_after": "1.0"
    }
]

app = Server("mcp-runbook-maintenance")

TOOLS = [
    Tool(
        name="create_changelog_entry",
        description="Create a new changelog entry for a runbook",
        inputSchema={
            "type": "object",
            "properties": {
                "runbook_id": {"type": "string", "description": "Runbook ID"},
                "type": {"type": "string", "enum": ["create", "update", "deprecate", "archive"], "description": "Change type"},
                "title": {"type": "string", "description": "Change title"},
                "description": {"type": "string", "description": "Detailed description"},
                "author": {"type": "string", "description": "Author name"},
                "version_after": {"type": "string", "description": "Version after change"}
            },
            "required": ["runbook_id", "type", "title", "description", "author", "version_after"]
        }
    ),
    Tool(
        name="get_runbook_status",
        description="Get runbook status and details",
        inputSchema={
            "type": "object",
            "properties": {
                "runbook_id": {"type": "string", "description": "Runbook ID (optional, returns all if not provided)"},
                "agent_id": {"type": "string", "description": "Filter by agent ID"}
            }
        }
    ),
    Tool(
        name="update_runbook",
        description="Update a runbook section",
        inputSchema={
            "type": "object",
            "properties": {
                "runbook_id": {"type": "string", "description": "Runbook ID"},
                "section_id": {"type": "string", "description": "Section ID to update"},
                "content": {"type": "string", "description": "New content"},
                "author": {"type": "string", "description": "Author name"}
            },
            "required": ["runbook_id", "section_id", "content", "author"]
        }
    ),
    Tool(
        name="get_changelog_history",
        description="Get changelog history for a runbook",
        inputSchema={
            "type": "object",
            "properties": {
                "runbook_id": {"type": "string", "description": "Runbook ID (optional)"},
                "limit": {"type": "integer", "default": 50, "description": "Max entries"}
            }
        }
    )
]

@app.list_tools()
async def list_tools():
    return TOOLS

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "create_changelog_entry":
        entry_id = f"cl-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        entry = {
            "id": entry_id,
            "runbook_id": arguments.get("runbook_id"),
            "type": arguments.get("type"),
            "title": arguments.get("title"),
            "description": arguments.get("description"),
            "author": arguments.get("author"),
            "timestamp": datetime.now().isoformat(),
            "version_after": arguments.get("version_after")
        }
        CHANGELOG.append(entry)
        
        # Update runbook version
        runbook_id = arguments.get("runbook_id")
        if runbook_id in RUNBOOKS:
            RUNBOOKS[runbook_id]["version"] = arguments.get("version_after")
            RUNBOOKS[runbook_id]["last_updated"] = datetime.now().isoformat()
        
        result = {"status": "ok", "tool": "create_changelog_entry", "entry": entry}
        return [TextContent(type="text", text=json.dumps(result))]
    
    elif name == "get_runbook_status":
        runbook_id = arguments.get("runbook_id")
        agent_id = arguments.get("agent_id")
        
        runbooks = list(RUNBOOKS.values())
        if runbook_id:
            runbooks = [r for r in runbooks if r["id"] == runbook_id]
        if agent_id:
            runbooks = [r for r in runbooks if r["agent_id"] == agent_id]
        
        result = {"status": "ok", "tool": "get_runbook_status", "count": len(runbooks), "runbooks": runbooks}
        return [TextContent(type="text", text=json.dumps(result))]
    
    elif name == "update_runbook":
        runbook_id = arguments.get("runbook_id")
        section_id = arguments.get("section_id")
        content = arguments.get("content")
        author = arguments.get("author")
        
        if runbook_id not in RUNBOOKS:
            return [TextContent(type="text", text=json.dumps({"error": f"Runbook not found: {runbook_id}"}))]
        
        runbook = RUNBOOKS[runbook_id]
        section = next((s for s in runbook["sections"] if s["id"] == section_id), None)
        if not section:
            return [TextContent(type="text", text=json.dumps({"error": f"Section not found: {section_id}"}))]
        
        old_content = section["content"]
        section["content"] = content
        runbook["last_updated"] = datetime.now().isoformat()
        
        # Auto-create changelog
        entry_id = f"cl-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        CHANGELOG.append({
            "id": entry_id,
            "runbook_id": runbook_id,
            "type": "update",
            "title": f"Updated section: {section['title']}",
            "description": f"Changed content from '{old_content[:50]}...' to '{content[:50]}...'",
            "author": author,
            "timestamp": datetime.now().isoformat(),
            "version_after": runbook["version"]
        })
        
        result = {"status": "ok", "tool": "update_runbook", "runbook_id": runbook_id, "section_id": section_id, "updated": True}
        return [TextContent(type="text", text=json.dumps(result))]
    
    elif name == "get_changelog_history":
        runbook_id = arguments.get("runbook_id")
        limit = arguments.get("limit", 50)
        
        entries = CHANGELOG
        if runbook_id:
            entries = [e for e in entries if e["runbook_id"] == runbook_id]
        
        entries.sort(key=lambda x: x["timestamp"], reverse=True)
        
        result = {"status": "ok", "tool": "get_changelog_history", "count": len(entries), "entries": entries[:limit]}
        return [TextContent(type="text", text=json.dumps(result))]
    
    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def serve():
        reader, writer = await stdio_server()
        await app.run(reader, writer)
    
    asyncio.run(serve())