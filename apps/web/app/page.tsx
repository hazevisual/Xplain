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
};

type GraphQuality = {
  coverage_percent: number;
  dangling_nodes: string[];
  naming_consistency_percent: number;
};

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
  const [levelFilter, setLevelFilter] = useState<LevelFilter>("ALL");
  const [typeFilter, setTypeFilter] = useState<Record<GraphNode["type"], boolean>>({
    stage: true,
    subprocess: true,
    component: true,
    data: true,
    actor: true,
  });

  const flow = useMemo(() => toFlow(result?.graph ?? null, levelFilter, typeFilter), [result?.graph, levelFilter, typeFilter]);

  function toggleTypeFilter(nodeType: GraphNode["type"]): void {
    setTypeFilter((prev) => ({ ...prev, [nodeType]: !prev[nodeType] }));
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
      setError("Failed to open process");
      return;
    }
    const details = (await res.json()) as ProcessDetails;
    setResult(details);
    setInputText(details.description ?? details.title);
  }

  async function onExecute(): Promise<void> {
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
        if (!createdRes.ok) throw new Error("Failed to create process.");
        const created = (await createdRes.json()) as ProcessDetails;
        id = created.id;
        setSelectedId(id);
      }

      const genRes = await fetch(`${API_BASE}/api/v1/processes/${id}/generate-graph`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: source }),
      });
      if (!genRes.ok) throw new Error("Failed to generate visual explanation.");
      const generated = (await genRes.json()) as ProcessDetails;
      setResult(generated);
      await loadHistory();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unexpected error.");
    } finally {
      setExecuting(false);
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
                    <small>v{p.version}</small>
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
            />
            <div className="composerFooter">
              <span className="chip">Version 1.0</span>
              <button className="xplainBtn" onClick={() => void onExecute()} disabled={executing}>
                {executing ? "XPlaining..." : "XPlain"}
              </button>
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
                  <ReactFlow nodes={flow.nodes} edges={flow.edges} fitView nodesDraggable={false} nodesConnectable={false}>
                    <Background color="#262626" />
                    <Controls />
                  </ReactFlow>
                </div>
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
              </section>

              <section className="resultCard">
                <h2>Description & Links</h2>
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

