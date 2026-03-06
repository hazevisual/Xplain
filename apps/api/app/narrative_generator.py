from __future__ import annotations

from collections import defaultdict

from .schemas import (
    EdgeKind,
    NarrativeDependency,
    NarrativeReference,
    NarrativeStep,
    NodeLevel,
    ProcessDetails,
    ProcessNarrative,
)


def _plural(value: int, singular: str, plural: str) -> str:
    return singular if value == 1 else plural


def _node_order(node_index: int, raw_order: object) -> tuple[int, int]:
    if isinstance(raw_order, int):
        return raw_order, node_index
    return 10_000 + node_index, node_index


def _select_breakdown_nodes(process: ProcessDetails) -> list[tuple[int, str, str]]:
    l2_nodes: list[tuple[int, str, str, object]] = []
    fallback_nodes: list[tuple[int, str, str, object]] = []
    for idx, node in enumerate(process.graph.nodes):
        if node.level == NodeLevel.l2:
            l2_nodes.append((idx, node.id, node.title, node.meta.get("order")))
        elif node.level != NodeLevel.l1:
            fallback_nodes.append((idx, node.id, node.title, node.meta.get("order")))

    raw = l2_nodes if l2_nodes else fallback_nodes
    ordered = sorted(raw, key=lambda item: _node_order(item[0], item[3]))
    return [(item[0], item[1], item[2]) for item in ordered[:8]]


def _build_summary(process: ProcessDetails) -> str:
    graph = process.graph
    main_steps = len([node for node in graph.nodes if node.level == NodeLevel.l2])
    if main_steps == 0:
        main_steps = len([node for node in graph.nodes if node.level != NodeLevel.l1])
    dependency_count = len([edge for edge in graph.edges if edge.kind == EdgeKind.depends_on])
    actor_count = len([node for node in graph.nodes if node.type.value == "actor"])
    data_count = len([node for node in graph.nodes if node.type.value == "data"])
    coverage = round(graph.quality.coverage_percent)
    naming = round(graph.quality.naming_consistency_percent)

    return (
        f"{process.title}: {main_steps} {_plural(main_steps, 'main step', 'main steps')}, "
        f"{dependency_count} {_plural(dependency_count, 'critical dependency', 'critical dependencies')}, "
        f"{actor_count} {_plural(actor_count, 'actor', 'actors')}, "
        f"and {data_count} {_plural(data_count, 'data node', 'data nodes')}. "
        f"Graph quality is {coverage}% coverage and {naming}% naming consistency."
    )


def _build_step_details(process: ProcessDetails, steps: list[tuple[int, str, str]]) -> list[NarrativeStep]:
    node_by_id = {node.id: node for node in process.graph.nodes}
    outgoing_by_node: dict[str, list] = defaultdict(list)
    for edge in process.graph.edges:
        outgoing_by_node[edge.from_node].append(edge)

    result: list[NarrativeStep] = []
    for _, node_id, title in steps:
        outgoing = outgoing_by_node.get(node_id, [])
        relations: list[str] = []
        for edge in outgoing:
            target = node_by_id.get(edge.to)
            target_title = target.title if target else edge.to
            if edge.kind == EdgeKind.depends_on:
                relations.append(f"depends on {target_title}")
            elif edge.kind == EdgeKind.uses:
                relations.append(f"uses {target_title}")
            elif edge.kind == EdgeKind.produces:
                relations.append(f"produces {target_title}")

        if relations:
            detail = "; ".join(relations[:3]) + "."
        elif outgoing:
            next_node = node_by_id.get(outgoing[0].to)
            next_title = next_node.title if next_node else outgoing[0].to
            detail = f"Continues to {next_title}."
        else:
            detail = "Executes as part of the primary flow."

        result.append(NarrativeStep(id=node_id, title=title, detail=detail))
    return result


def _build_key_dependencies(process: ProcessDetails) -> list[NarrativeDependency]:
    node_by_id = {node.id: node for node in process.graph.nodes}
    edges = [edge for edge in process.graph.edges if edge.kind == EdgeKind.depends_on]
    if not edges:
        edges = [edge for edge in process.graph.edges if edge.kind in {EdgeKind.uses, EdgeKind.produces}]

    dependencies: list[NarrativeDependency] = []
    for edge in edges[:6]:
        from_title = node_by_id.get(edge.from_node).title if edge.from_node in node_by_id else edge.from_node
        to_title = node_by_id.get(edge.to).title if edge.to in node_by_id else edge.to
        dependencies.append(
            NarrativeDependency(
                fromNodeId=edge.from_node,
                fromTitle=from_title,
                toNodeId=edge.to,
                toTitle=to_title,
                relation=edge.kind,
            )
        )
    return dependencies


def _build_references(process: ProcessDetails, steps: list[NarrativeStep]) -> list[NarrativeReference]:
    refs: list[NarrativeReference] = [
        NarrativeReference(label="Process Version", ref=f"process:{process.id}:v{process.version}")
    ]
    seen = {refs[0].ref}

    for source_ref in process.graph.source_refs:
        if source_ref in seen:
            continue
        refs.append(NarrativeReference(label="Source", ref=source_ref))
        seen.add(source_ref)

    for step in steps[:3]:
        step_ref = f"node:{step.id}"
        if step_ref in seen:
            continue
        refs.append(NarrativeReference(label="Step Node", ref=step_ref))
        seen.add(step_ref)

    return refs


def generate_process_narrative(process: ProcessDetails) -> ProcessNarrative:
    steps_source = _select_breakdown_nodes(process)
    steps = _build_step_details(process, steps_source)
    dependencies = _build_key_dependencies(process)
    references = _build_references(process, steps)

    return ProcessNarrative(
        processId=process.id,
        version=process.version,
        summary=_build_summary(process),
        steps=steps,
        keyDependencies=dependencies,
        references=references,
        qualityNotes=process.graph.warnings[:6],
        sourceRefs=process.graph.source_refs,
        generatedBy="generated:rule-based:narrative:v1",
    )
