# Architecture and Agents

## 1. Logical Architecture

- Frontend (`Next.js + TypeScript`)
  - Visualization canvas (React Flow / D3)
  - Filter, analytics, and comments panels
- Backend API (`FastAPI`)
  - REST/GraphQL for processes, versions, and roles
  - AI agent call orchestrator
- Storage
  - `PostgreSQL` for processes, versions, and users
  - `pgvector` for semantic search over source descriptions
  - Object storage for attachments and exports
- Async layer
  - `Redis + Celery` for heavy tasks (parsing, generation, export)

## 2. Canonical Data Model

Primary contract between AI and UI: `ProcessGraph`.

```json
{
  "processId": "string",
  "version": 1,
  "nodes": [
    {
      "id": "N1",
      "type": "stage|subprocess|component|data|actor",
      "title": "string",
      "level": "L1|L2|L3",
      "meta": {}
    }
  ],
  "edges": [
    {
      "id": "E1",
      "from": "N1",
      "to": "N2",
      "kind": "flow|depends_on|uses|produces",
      "meta": {}
    }
  ],
  "warnings": [],
  "sourceRefs": []
}
```

## 3. Agent Set

- `Ingestion Agent`
  - Input: file/text
  - Output: cleaned and structured content
- `Decomposition Agent`
  - Input: structured content
  - Output: stages and subprocesses
- `Component Mapping Agent`
  - Input: stages/subprocesses
  - Output: components, roles, data, dependencies
- `Visualization Spec Agent`
  - Input: process model
  - Output: `ProcessGraph` JSON
- `QA Agent`
  - Input: `ProcessGraph`
  - Output: warnings, conflicting links, coverage gaps
- `Narrative Agent` (optional)
  - Input: `ProcessGraph`
  - Output: explanatory text and report summary

## 4. Agent Orchestration

Recommended tool: `LangGraph`.

Why:

- explicit state-machine model;
- easy retry/fallback integration;
- built-in human-in-the-loop step between `QA` and publishing;
- simpler execution traceability.

## 5. Security and Control

- Validate input files and MIME types.
- Enforce uploaded file size limits.
- RBAC for API and UI.
- Audit AI calls and versioned result storage.
