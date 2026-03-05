# Frontend Agent

## Branch
`frontend`

## Owns
- UI implementation.
- Process graph rendering and interactions.
- Accessibility and client performance.

## Inputs
- UX/UI requirements.
- API contracts.
- Shared schema updates.

## Outputs
- UI changes.
- Acceptance notes.
- Frontend risks and limitations.

## Non-Negotiable UI Rules
- All primary vertical content blocks (`input`, `graph`, `description`, `error`) must use one shared max-width container and be center-aligned.
- No third-party default widget styling is allowed in production UI (for example, white ReactFlow control blocks on dark theme).
- New UI sections must reuse project theme tokens (`--bg`, `--panel`, `--line`, `--text`) and may not introduce off-theme accent colors by default.
- Vertical rhythm is mandatory: define spacing tokens in CSS and keep consistent breathing room between heading/content and section/section (no ad-hoc micro-spacing).
