"use client";

import { useEffect, useMemo, useState } from "react";
import { Background, Controls, Edge, Node, ReactFlow } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

type GraphNode = {
  id: string;
  type: "stage" | "subprocess" | "component" | "data" | "actor";
  title: string;
  level: "L1" | "L2" | "L3";
};

type GraphEdge = {
  id: string;
  from: string;
  to: string;
  kind: "flow" | "depends_on" | "uses" | "produces";
};

type ProcessSummary = {
  id: string;
  title: string;
  description: string | null;
  updated_at: string;
  version: number;
  status: ProcessStatus;
};

type ProcessRevisionSummary = {
  version: number;
  created_at: string;
  nodes_count: number;
  edges_count: number;
  warnings_count: number;
  coverage_percent: number;
};

type GraphQuality = {
  coverage_percent: number;
  dangling_nodes: string[];
  naming_consistency_percent: number;
};

type ProcessStatus = "draft" | "in_review" | "approved";

type ProcessDetails = ProcessSummary & {
  created_at: string;
  graph: {
    processId: string;
    version: number;
    nodes: GraphNode[];
    edges: GraphEdge[];
    warnings: string[];
    sourceRefs: string[];
    quality?: GraphQuality;
  };
};

type GraphInsights = {
  criticalDependencies: number;
  actorCount: number;
  dataCount: number;
  topBottlenecks: Array<{ nodeId: string; title: string; score: number }>;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const LEVEL_FILTERS = ["ALL", "L1", "L2", "L3"] as const;
type LevelFilter = (typeof LEVEL_FILTERS)[number];
const NODE_TYPES: GraphNode["type"][] = ["stage", "subprocess", "component", "data", "actor"];
const NODE_TYPE_LABELS: Record<GraphNode["type"], string> = {
  stage: "Stage",
  subprocess: "Subprocess",
  component: "Component",
  data: "Data",
  actor: "Actor",
};
const STATUS_LABEL: Record<ProcessStatus, string> = {
  draft: "Draft",
  in_review: "In Review",
  approved: "Approved",
};
const NEXT_STATUS: Record<ProcessStatus, ProcessStatus | null> = {
  draft: "in_review",
  in_review: "approved",
  approved: null,
};
const NEXT_STATUS_LABEL: Record<ProcessStatus, string | null> = {
  draft: "Send to Review",
  in_review: "Approve",
  approved: null,
};

function getApiErrorMessage(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== "object") return fallback;
  const obj = payload as { error?: { message?: string } };
  return obj.error?.message ?? fallback;
}

function buildInsights(graph: ProcessDetails["graph"] | null): GraphInsights {
  if (!graph) {
    return { criticalDependencies: 0, actorCount: 0, dataCount: 0, topBottlenecks: [] };
  }

  const nodeById = new Map(graph.nodes.map((node) => [node.id, node]));
  const traffic = new Map<string, number>();
  graph.nodes.forEach((node) => traffic.set(node.id, 0));

  graph.edges.forEach((edge) => {
    traffic.set(edge.from, (traffic.get(edge.from) ?? 0) + 1);
    traffic.set(edge.to, (traffic.get(edge.to) ?? 0) + 1);
  });

  const topBottlenecks = graph.nodes
    .filter((node) => node.level === "L2")
    .map((node) => ({
      nodeId: node.id,
      title: node.title,
      score: traffic.get(node.id) ?? 0,
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);

  const criticalDependencies = graph.edges.filter((edge) => edge.kind === "depends_on").length;
  const actorCount = graph.nodes.filter((node) => node.type === "actor").length;
  const dataCount = graph.nodes.filter((node) => node.type === "data").length;

  return {
    criticalDependencies,
    actorCount,
    dataCount,
    topBottlenecks: topBottlenecks.map((item) => ({
      nodeId: item.nodeId,
      title: nodeById.get(item.nodeId)?.title ?? item.title,
      score: item.score,
    })),
  };
}

function toFlow(
  graph: ProcessDetails["graph"] | null,
  levelFilter: LevelFilter,
  typeFilter: Record<GraphNode["type"], boolean>
): { nodes: Node[]; edges: Edge[] } {
  if (!graph) return { nodes: [], edges: [] };

  const grouped = { L1: [] as GraphNode[], L2: [] as GraphNode[], L3: [] as GraphNode[] };
  graph.nodes
    .filter((node) => (levelFilter === "ALL" ? true : node.level === levelFilter))
    .filter((node) => typeFilter[node.type])
    .forEach((n) => grouped[n.level].push(n));

  const xByLevel = { L1: 80, L2: 420, L3: 760 };
  const colorByType: Record<GraphNode["type"], string> = {
    stage: "#d8d8d8",
    subprocess: "#bdbdbd",
    component: "#9f9f9f",
    data: "#868686",
    actor: "#6f6f6f",
  };

  const nodes: Node[] = [];
  (["L1", "L2", "L3"] as const).forEach((level) => {
    grouped[level].forEach((n, idx) => {
      nodes.push({
        id: n.id,
        position: { x: xByLevel[level], y: 60 + idx * 118 },
        data: { label: n.title },
        style: {
          width: 255,
          borderRadius: 12,
          border: `1px solid ${colorByType[n.type]}`,
          background: "#111111",
          color: "#ececec",
          fontSize: 12,
          padding: 10,
          lineHeight: 1.3,
        },
      });
    });
  });

  const visible = new Set(nodes.map((n) => n.id));
  const edgeColor: Record<GraphEdge["kind"], string> = {
    flow: "#cfcfcf",
    depends_on: "#9f9f9f",
    uses: "#7f7f7f",
    produces: "#656565",
  };

  const edges: Edge[] = graph.edges
    .filter((e) => visible.has(e.from) && visible.has(e.to))
    .map((e) => ({
      id: e.id,
      source: e.from,
      target: e.to,
      label: e.kind,
      style: { stroke: edgeColor[e.kind], strokeWidth: 1.5 },
      labelStyle: { fill: "#b3b3b3", fontSize: 11 },
      animated: e.kind === "flow",
    }));

  return { nodes, edges };
}

export default function HomePage() {
  const [inputText, setInputText] = useState("");
  const [processes, setProcesses] = useState<ProcessSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [result, setResult] = useState<ProcessDetails | null>(null);
  const [executing, setExecuting] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [revisions, setRevisions] = useState<ProcessRevisionSummary[]>([]);
  const [compareLeftVersion, setCompareLeftVersion] = useState<number | null>(null);
  const [compareRightVersion, setCompareRightVersion] = useState<number | null>(null);
  const [levelFilter, setLevelFilter] = useState<LevelFilter>("ALL");
  const [typeFilter, setTypeFilter] = useState<Record<GraphNode["type"], boolean>>({
    stage: true,
    subprocess: true,
    component: true,
    data: true,
    actor: true,
  });
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [statusUpdating, setStatusUpdating] = useState(false);

  const flow = useMemo(() => toFlow(result?.graph ?? null, levelFilter, typeFilter), [result?.graph, levelFilter, typeFilter]);
  const insights = useMemo(() => buildInsights(result?.graph ?? null), [result?.graph]);
  const compareStats = useMemo(() => {
    const left = revisions.find((item) => item.version === compareLeftVersion);
    const right = revisions.find((item) => item.version === compareRightVersion);
    if (!left || !right) return null;
    return {
      nodesDelta: left.nodes_count - right.nodes_count,
      edgesDelta: left.edges_count - right.edges_count,
      warningsDelta: left.warnings_count - right.warnings_count,
      coverageDelta: Math.round((left.coverage_percent - right.coverage_percent) * 100) / 100,
    };
  }, [revisions, compareLeftVersion, compareRightVersion]);
  const selectedNodeDetails = useMemo(() => {
    if (!result || !selectedNodeId) return null;
    const node = result.graph.nodes.find((item) => item.id === selectedNodeId);
    if (!node) return null;
    const nodeById = new Map(result.graph.nodes.map((item) => [item.id, item]));
    const linkedEdges = result.graph.edges.filter((edge) => edge.from === selectedNodeId || edge.to === selectedNodeId);
    return {
      node,
      linkedEdges: linkedEdges.map((edge) => ({
        ...edge,
        fromTitle: nodeById.get(edge.from)?.title ?? edge.from,
        toTitle: nodeById.get(edge.to)?.title ?? edge.to,
      })),
    };
  }, [result, selectedNodeId]);

  function toggleTypeFilter(nodeType: GraphNode["type"]): void {
    setTypeFilter((prev) => ({ ...prev, [nodeType]: !prev[nodeType] }));
  }

  function initializeCompareVersions(nextRevisions: ProcessRevisionSummary[]): void {
    if (nextRevisions.length === 0) {
      setCompareLeftVersion(null);
      setCompareRightVersion(null);
      return;
    }

    const left = nextRevisions[0].version;
    const right = nextRevisions[1]?.version ?? left;
    setCompareLeftVersion(left);
    setCompareRightVersion(right);
  }

  async function loadRevisions(processId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/processes/${processId}/revisions`, { cache: "no-store" });
    if (!res.ok) {
      setRevisions([]);
      setCompareLeftVersion(null);
      setCompareRightVersion(null);
      return;
    }
    const data = (await res.json()) as ProcessRevisionSummary[];
    setRevisions(data);
    initializeCompareVersions(data);
  }

  async function loadHistory(): Promise<void> {
    setLoadingHistory(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/processes`, { cache: "no-store" });
      if (!res.ok) throw new Error("Failed to load history");
      const data = (await res.json()) as ProcessSummary[];
      setProcesses(data);
    } finally {
      setLoadingHistory(false);
    }
  }

  async function openProcess(id: string): Promise<void> {
    setSelectedId(id);
    setError(null);
    const res = await fetch(`${API_BASE}/api/v1/processes/${id}`, { cache: "no-store" });
    if (!res.ok) {
      const payload = await res.json().catch(() => null);
      setError(getApiErrorMessage(payload, "Failed to open process"));
      return;
    }
    const details = (await res.json()) as ProcessDetails;
    setResult(details);
    setInputText(details.description ?? details.title);
    setSelectedNodeId(null);
    await loadRevisions(id);
  }

  async function onExecute(): Promise<void> {
    if (result && result.status !== "draft") {
      setError(`Process is ${STATUS_LABEL[result.status].toLowerCase()}. Create a new XPlain to continue editing.`);
      return;
    }

    const source = inputText.trim();
    if (!source) {
      setError("Please provide text first.");
      return;
    }

    setExecuting(true);
    setError(null);
    try {
      let id = selectedId;
      if (!id) {
        const title = source.split(/[.\n]/)[0]?.slice(0, 64) || "Untitled Process";
        const createdRes = await fetch(`${API_BASE}/api/v1/processes`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title, description: source }),
        });
        if (!createdRes.ok) {
          const payload = await createdRes.json().catch(() => null);
          throw new Error(getApiErrorMessage(payload, "Failed to create process."));
        }
        const created = (await createdRes.json()) as ProcessDetails;
        id = created.id;
        setSelectedId(id);
      }

      const genRes = await fetch(`${API_BASE}/api/v1/processes/${id}/generate-graph`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: source }),
      });
      if (!genRes.ok) {
        const payload = await genRes.json().catch(() => null);
        throw new Error(getApiErrorMessage(payload, "Failed to generate visual explanation."));
      }
      const generated = (await genRes.json()) as ProcessDetails;
      setResult(generated);
      setSelectedNodeId(null);
      await loadHistory();
      await loadRevisions(generated.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unexpected error.");
    } finally {
      setExecuting(false);
    }
  }

  async function onTransitionStatus(targetStatus: ProcessStatus): Promise<void> {
    if (!result) return;

    setStatusUpdating(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/processes/${result.id}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ targetStatus }),
      });
      if (!res.ok) {
        const payload = await res.json().catch(() => null);
        throw new Error(getApiErrorMessage(payload, "Failed to update process status."));
      }

      const updated = (await res.json()) as ProcessDetails;
      setResult(updated);
      await loadHistory();
      await loadRevisions(updated.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unexpected error.");
    } finally {
      setStatusUpdating(false);
    }
  }

  useEffect(() => {
    void loadHistory();
  }, []);

  return (
    <main className="shellRoot">
      <div className="appFrame">
        <aside className="sidebar">
          <button
            className="newBtn"
            onClick={() => {
              setSelectedId(null);
              setResult(null);
              setInputText("");
              setError(null);
              setRevisions([]);
              setCompareLeftVersion(null);
              setCompareRightVersion(null);
              setSelectedNodeId(null);
            }}
          >
            + New XPlain
          </button>
          <div className="sideSection">
            <p className="sideTitle">Recent</p>
            {loadingHistory ? <p className="sideMeta">Loading...</p> : null}
            <ul className="historyList">
              {processes.map((p) => (
                <li key={p.id}>
                  <button className={p.id === selectedId ? "historyItem active" : "historyItem"} onClick={() => void openProcess(p.id)}>
                    <span>{p.title}</span>
                    <small>
                      v{p.version} | {STATUS_LABEL[p.status]}
                    </small>
                  </button>
                </li>
              ))}
            </ul>
          </div>
          <div className="sideFooter">
            <p>XPlain Workspace</p>
            <small>Dark Minimal Mode</small>
          </div>
        </aside>

        <section className="mainArea">
          <header className="topBar">
            <div className="brand">XPlain</div>
            <div className="topActions">
              <button className="topAction">Share</button>
              <button className="topAction">Help</button>
            </div>
          </header>

          <section className="composerCard">
            <h1>What need to XPlain?</h1>
            <textarea
              rows={6}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Describe complex process, term, or workflow..."
              disabled={result?.status === "in_review" || result?.status === "approved"}
            />
            <div className="composerFooter">
              <div className="statusGroup">
                <span className="chip">Version 1.0</span>
                {result ? <span className={`statusChip ${result.status}`}>{STATUS_LABEL[result.status]}</span> : null}
              </div>
              <div className="composerActions">
                {result && NEXT_STATUS[result.status] ? (
                  <button
                    className="statusActionBtn"
                    onClick={() => void onTransitionStatus(NEXT_STATUS[result.status] as ProcessStatus)}
                    disabled={statusUpdating}
                  >
                    {statusUpdating ? "Updating..." : NEXT_STATUS_LABEL[result.status]}
                  </button>
                ) : null}
                <button className="xplainBtn" onClick={() => void onExecute()} disabled={executing || (result ? result.status !== "draft" : false)}>
                  {executing ? "XPlaining..." : "XPlain"}
                </button>
              </div>
            </div>
          </section>

          {error ? <p className="error">{error}</p> : null}

          {result ? (
            <div className="resultsStack">
              <section className="resultCard graphCard">
                <div className="resultHead">
                  <h2>Graph</h2>
                  <p>
                    {result.title} | v{result.version} | {flow.nodes.length}/{result.graph.nodes.length} nodes
                  </p>
                </div>
                <div className="graphFilters">
                  <div className="levelFilters">
                    {LEVEL_FILTERS.map((level) => (
                      <button
                        key={level}
                        className={level === levelFilter ? "filterBtn active" : "filterBtn"}
                        onClick={() => setLevelFilter(level)}
                      >
                        {level}
                      </button>
                    ))}
                  </div>
                  <div className="typeFilters">
                    {NODE_TYPES.map((nodeType) => (
                      <button
                        key={nodeType}
                        className={typeFilter[nodeType] ? "typeBtn active" : "typeBtn"}
                        onClick={() => toggleTypeFilter(nodeType)}
                      >
                        {NODE_TYPE_LABELS[nodeType]}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="graphPanel">
                  <ReactFlow
                    nodes={flow.nodes}
                    edges={flow.edges}
                    fitView
                    nodesDraggable={false}
                    nodesConnectable={false}
                    onNodeClick={(_, node) => setSelectedNodeId(node.id)}
                  >
                    <Background color="#262626" />
                    <Controls />
                  </ReactFlow>
                </div>
                <p className="graphHint">Click any node to inspect its details and connections.</p>
                <div className="qualityGrid">
                  <article className="qualityItem">
                    <span>Coverage</span>
                    <strong>{Math.round(result.graph.quality?.coverage_percent ?? 0)}%</strong>
                  </article>
                  <article className="qualityItem">
                    <span>Naming</span>
                    <strong>{Math.round(result.graph.quality?.naming_consistency_percent ?? 0)}%</strong>
                  </article>
                  <article className="qualityItem">
                    <span>Dangling Nodes</span>
                    <strong>{result.graph.quality?.dangling_nodes.length ?? 0}</strong>
                  </article>
                </div>
                {result.graph.warnings.length > 0 ? (
                  <div className="warningBlock">
                    <h3>Warnings</h3>
                    <ul>
                      {result.graph.warnings.map((warning, idx) => (
                        <li key={`${warning}-${idx}`}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {selectedNodeDetails ? (
                  <div className="nodeDetailCard">
                    <h3>Node Detail</h3>
                    <p className="nodeMeta">
                      {selectedNodeDetails.node.title} | {selectedNodeDetails.node.type} | {selectedNodeDetails.node.level}
                    </p>
                    <ul>
                      {selectedNodeDetails.linkedEdges.length > 0 ? (
                        selectedNodeDetails.linkedEdges.map((edge) => (
                          <li key={edge.id}>
                            {edge.fromTitle} {"->"} {edge.toTitle} ({edge.kind})
                          </li>
                        ))
                      ) : (
                        <li>No connected edges.</li>
                      )}
                    </ul>
                  </div>
                ) : null}
              </section>

              <section className="resultCard">
                <h2>Description & Links</h2>
                <div className="insightGrid">
                  <article className="insightCard">
                    <span>Critical Dependencies</span>
                    <strong>{insights.criticalDependencies}</strong>
                  </article>
                  <article className="insightCard">
                    <span>Actors</span>
                    <strong>{insights.actorCount}</strong>
                  </article>
                  <article className="insightCard">
                    <span>Data Nodes</span>
                    <strong>{insights.dataCount}</strong>
                  </article>
                </div>
                <div className="bottleneckCard">
                  <h3>Top Bottlenecks</h3>
                  <ul>
                    {insights.topBottlenecks.length > 0 ? (
                      insights.topBottlenecks.map((item) => (
                        <li key={item.nodeId}>
                          {item.title} ({item.score})
                        </li>
                      ))
                    ) : (
                      <li>No bottlenecks detected yet.</li>
                    )}
                  </ul>
                </div>
                <div className="revisionCard">
                  <h3>Version Compare</h3>
                  <div className="revisionSelectors">
                    <label>
                      Left
                      <select
                        value={compareLeftVersion ?? ""}
                        onChange={(e) => setCompareLeftVersion(Number(e.target.value))}
                        disabled={revisions.length === 0}
                      >
                        {revisions.map((item) => (
                          <option key={`left-${item.version}`} value={item.version}>
                            v{item.version}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Right
                      <select
                        value={compareRightVersion ?? ""}
                        onChange={(e) => setCompareRightVersion(Number(e.target.value))}
                        disabled={revisions.length === 0}
                      >
                        {revisions.map((item) => (
                          <option key={`right-${item.version}`} value={item.version}>
                            v{item.version}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>
                  {compareStats ? (
                    <div className="revisionDeltaGrid">
                      <article className="revisionDelta">
                        <span>Nodes Delta</span>
                        <strong>{compareStats.nodesDelta >= 0 ? `+${compareStats.nodesDelta}` : compareStats.nodesDelta}</strong>
                      </article>
                      <article className="revisionDelta">
                        <span>Edges Delta</span>
                        <strong>{compareStats.edgesDelta >= 0 ? `+${compareStats.edgesDelta}` : compareStats.edgesDelta}</strong>
                      </article>
                      <article className="revisionDelta">
                        <span>Warnings Delta</span>
                        <strong>{compareStats.warningsDelta >= 0 ? `+${compareStats.warningsDelta}` : compareStats.warningsDelta}</strong>
                      </article>
                      <article className="revisionDelta">
                        <span>Coverage Delta</span>
                        <strong>{compareStats.coverageDelta >= 0 ? `+${compareStats.coverageDelta}` : compareStats.coverageDelta}%</strong>
                      </article>
                    </div>
                  ) : (
                    <p className="sideMeta">No revision data yet.</p>
                  )}
                </div>
                <p className="desc">{result.description ?? "No description provided"}</p>
                <div className="columns">
                  <div>
                    <h3>Subprocesses</h3>
                    <ul>
                      {result.graph.nodes
                        .filter((n) => n.level === "L2")
                        .map((n) => (
                          <li key={n.id}>{n.title}</li>
                        ))}
                    </ul>
                  </div>
                  <div>
                    <h3>Connections</h3>
                    <ul>
                      {result.graph.edges.map((e) => (
                        <li key={e.id}>
                          {e.from} {"->"} {e.to} ({e.kind})
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </section>
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );
}

