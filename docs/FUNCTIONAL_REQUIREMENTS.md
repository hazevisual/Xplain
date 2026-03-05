# Functional Requirements

## 1. Process Management

- Create processes manually.
- Import processes from text/documents.
- Store process versions and change history.
- Clone a process as a template.

## 2. Visualization

- Display processes as graphs.
- Support detail levels:
  - L1: high-level map;
  - L2: subprocesses;
  - L3: steps and components.
- Filter by node types (stages, systems, roles, data).
- Drill-down and backward navigation (breadcrumb).

## 3. Infographics and Analytics

- Auto-generated insight blocks:
  - stage duration;
  - bottlenecks;
  - critical dependencies;
  - role x stage matrix.
- Export report to PDF/PNG.

## 4. AI Processing

- Parse input and extract entities.
- Decompose into subprocesses.
- Build visual spec (JSON).
- Validate consistency and produce warnings.

## 5. Moderation Workflow

- Draft -> In Review -> Approved.
- Reviewer comments on nodes/edges.
- Manual edits before publication.

## 6. Roles and Access

- Viewer: view and export.
- Editor: edit processes.
- Reviewer: validate and approve.
- Admin: manage project, users, and settings.

## 7. Non-Functional Requirements (MVP)

- Graph render time for up to 1000 nodes: up to 2 seconds on a typical client device.
- API p95 for process read: up to 600 ms.
- UI accessibility: at least WCAG AA for core screens.
- Audit log: who changed what and when.
