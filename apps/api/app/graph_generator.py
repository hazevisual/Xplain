from __future__ import annotations

import re

from .schemas import EdgeKind, GraphQuality, NodeLevel, NodeType, ProcessEdge, ProcessGraph, ProcessNode

STEP_SPLIT_RE = re.compile(r"(?:\r?\n|->|=>|→|;|\.)")
NUMBER_PREFIX_RE = re.compile(r"^\s*\d+[\)\.\-:]\s*")

ACTOR_HINTS = {
    "user": "User",
    "client": "Client",
    "manager": "Manager",
    "operator": "Operator",
    "doctor": "Doctor",
    "пользователь": "Пользователь",
    "клиент": "Клиент",
    "менеджер": "Менеджер",
    "оператор": "Оператор",
    "врач": "Врач",
}

DATA_HINTS = {
    "data": "Data",
    "report": "Report",
    "document": "Document",
    "form": "Form",
    "database": "Database",
    "данные": "Данные",
    "отчет": "Отчет",
    "документ": "Документ",
    "форма": "Форма",
    "база": "База данных",
}

COMPONENT_HINTS = {
    "api": "API Service",
    "service": "Application Service",
    "backend": "Backend",
    "frontend": "Frontend",
    "queue": "Queue",
    "cache": "Cache",
    "integration": "Integration Layer",
    "ml": "ML Module",
    "ai": "AI Module",
    "сервис": "Сервис",
    "модуль": "Модуль",
    "интеграци": "Интеграция",
}


def _truncate(text: str, limit: int = 80) -> str:
    value = re.sub(r"\s+", " ", text).strip()
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3].rstrip()}..."


def _extract_source_segments(text: str) -> list[str]:
    chunks = STEP_SPLIT_RE.split(text.strip())
    segments: list[str] = []
    for chunk in chunks:
        cleaned = NUMBER_PREFIX_RE.sub("", chunk).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        if len(cleaned) >= 3:
            segments.append(cleaned)
    return segments


def _extract_steps(text: str) -> list[str]:
    source = text.strip()
    if not source:
        return []

    segments = _extract_source_segments(source)
    steps = [_truncate(segment, 72) for segment in segments]
    if not steps:
        steps = [_truncate(source, 72)]
    return steps[:8]


def _extract_hints(step_text: str) -> list[tuple[NodeType, str]]:
    lower = step_text.lower()
    result: list[tuple[NodeType, str]] = []

    for hint, label in ACTOR_HINTS.items():
        if hint in lower:
            result.append((NodeType.actor, label))
            break

    for hint, label in DATA_HINTS.items():
        if hint in lower:
            result.append((NodeType.data, label))
            break

    for hint, label in COMPONENT_HINTS.items():
        if hint in lower:
            result.append((NodeType.component, label))
            break

    return result


def _compute_quality(source_text: str, nodes: list[ProcessNode], edges: list[ProcessEdge]) -> GraphQuality:
    segments = _extract_source_segments(source_text)
    l2_nodes = [node for node in nodes if node.level == NodeLevel.l2]
    segment_count = max(len(segments), 1)
    coverage_percent = min(100.0, round((len(l2_nodes) / segment_count) * 100, 2))

    connected_node_ids: set[str] = set()
    for edge in edges:
        connected_node_ids.add(edge.from_node)
        connected_node_ids.add(edge.to)
    dangling_nodes = sorted([node.id for node in nodes if node.id not in connected_node_ids])

    normalized_titles = [re.sub(r"\s+", " ", node.title.strip().lower()) for node in nodes if node.title.strip()]
    duplicates = len(normalized_titles) - len(set(normalized_titles))
    naming_consistency_percent = 0.0
    if normalized_titles:
        naming_consistency_percent = round(max(0.0, 100.0 - (duplicates / len(normalized_titles) * 100.0)), 2)

    return GraphQuality(
        coverage_percent=coverage_percent,
        dangling_nodes=dangling_nodes,
        naming_consistency_percent=naming_consistency_percent,
    )


def generate_process_graph(process_id: str, title: str, source_text: str, version: int) -> ProcessGraph:
    steps = _extract_steps(source_text)
    warnings: list[str] = ["Auto-generated graph. Review and edit before final use."]
    if len(steps) <= 1:
        warnings.append("Low decomposition confidence: source text contains too few explicit steps.")

    nodes: list[ProcessNode] = []
    edges: list[ProcessEdge] = []

    root_title = _truncate(title or "Process Map", 64)
    nodes.append(
        ProcessNode(
            id="N0",
            type=NodeType.stage,
            title=root_title,
            level=NodeLevel.l1,
            meta={"generated": True},
        )
    )

    previous_id = "N0"
    edge_idx = 1
    component_idx = 1
    created_support_nodes = 0

    for idx, step in enumerate(steps, start=1):
        step_id = f"S{idx}"
        nodes.append(
            ProcessNode(
                id=step_id,
                type=NodeType.subprocess,
                title=step,
                level=NodeLevel.l2,
                meta={"generated": True, "order": idx},
            )
        )

        edges.append(
            ProcessEdge(
                id=f"E{edge_idx}",
                from_node=previous_id,
                to=step_id,
                kind=EdgeKind.flow,
                meta={"generated": True},
            )
        )
        edge_idx += 1
        previous_id = step_id

        hints = _extract_hints(step)
        for node_type, label in hints:
            support_id = f"C{component_idx}"
            component_idx += 1
            created_support_nodes += 1
            nodes.append(
                ProcessNode(
                    id=support_id,
                    type=node_type,
                    title=label,
                    level=NodeLevel.l3,
                    meta={"generated": True, "stepId": step_id},
                )
            )
            edge_kind = EdgeKind.uses if node_type in (NodeType.component, NodeType.data) else EdgeKind.depends_on
            edges.append(
                ProcessEdge(
                    id=f"E{edge_idx}",
                    from_node=step_id,
                    to=support_id,
                    kind=edge_kind,
                    meta={"generated": True},
                )
            )
            edge_idx += 1

    if created_support_nodes == 0 and steps:
        support_id = "C0"
        step_ref = "S1" if steps else "N0"
        nodes.append(
            ProcessNode(
                id=support_id,
                type=NodeType.component,
                title="Core Component",
                level=NodeLevel.l3,
                meta={"generated": True},
            )
        )
        edges.append(
            ProcessEdge(
                id=f"E{edge_idx}",
                from_node=step_ref,
                to=support_id,
                kind=EdgeKind.uses,
                meta={"generated": True},
            )
        )

    quality = _compute_quality(source_text=source_text, nodes=nodes, edges=edges)
    if quality.coverage_percent < 65:
        warnings.append("Coverage is low: extracted steps cover less than 65% of source segments.")
    if quality.dangling_nodes:
        warnings.append("Graph contains dangling nodes without connections.")
    if quality.naming_consistency_percent < 70:
        warnings.append("Naming consistency is low: too many duplicate or unstable node titles.")

    return ProcessGraph(
        processId=process_id,
        version=max(version, 1),
        nodes=nodes,
        edges=edges,
        warnings=warnings,
        sourceRefs=["generated:rule-based:v2"],
        quality=quality,
    )

