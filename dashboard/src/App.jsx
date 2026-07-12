import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Activity, AlertTriangle, Globe2, Network, RefreshCw, Server, ShieldCheck, TerminalSquare } from "lucide-react";
import "./styles.css";

const API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE !== "false";
const demoNow = new Date().toISOString();
const demoData = {
  "/hosts": [
    { host: "edge-01", risk_score: 82 },
    { host: "workstation-14", risk_score: 48 },
    { host: "db-core-02", risk_score: 64 }
  ],
  "/alerts": [
    { id: "alert-1", rule_name: "Suspicious parent process", host: "edge-01", severity: "high", score: 82, ts: demoNow },
    { id: "alert-2", rule_name: "Unusual outbound connection", host: "db-core-02", severity: "medium", score: 64, ts: demoNow }
  ],
  "/timeline": [
    { ts: demoNow, type: "alert", kind: "process_spawn", host: "edge-01" },
    { ts: demoNow, type: "network", kind: "outbound_connection", host: "db-core-02" },
    { ts: demoNow, type: "event", kind: "file_write", host: "workstation-14" }
  ]
};

function riskLabel(score) {
  if (score >= 75) return "critical";
  if (score >= 50) return "high";
  if (score >= 25) return "medium";
  return "low";
}

async function getJson(path) {
  if (DEMO_MODE) {
    if (path.startsWith("/process-tree/")) {
      return {
        processes: [
          { pid: 420, name: "services.exe", children: [{ pid: 942, name: "powershell.exe", children: [{ pid: 1204, name: "curl.exe", children: [] }] }] },
          { pid: 88, name: "agent.exe", children: [] }
        ]
      };
    }
    return demoData[path] || [];
  }
  const response = await fetch(`${API}${path}`);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

function Stat({ icon: Icon, label, value }) {
  return (
    <div className="stat">
      <Icon size={18} />
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

function HostsMap({ hosts, selected, onSelect }) {
  return (
    <section className="panel map-panel">
      <div className="panel-title">
        <Globe2 size={18} />
        <h2>Live hosts map</h2>
      </div>
      <div className="host-map">
        {hosts.map((host, index) => (
          <button
            key={host.host}
            className={`node risk-${riskLabel(host.risk_score)} ${selected === host.host ? "active" : ""}`}
            style={{ "--x": `${18 + (index * 23) % 68}%`, "--y": `${24 + (index * 31) % 54}%` }}
            onClick={() => onSelect(host.host)}
            title={`${host.host}: risk ${host.risk_score}`}
          >
            <Server size={16} />
          </button>
        ))}
      </div>
    </section>
  );
}

function AlertsFeed({ alerts }) {
  return (
    <section className="panel">
      <div className="panel-title">
        <AlertTriangle size={18} />
        <h2>Alerts feed</h2>
      </div>
      <div className="list">
        {alerts.map((alert) => (
          <article className={`alert severity-${alert.severity}`} key={alert.id}>
            <div>
              <strong>{alert.rule_name}</strong>
              <span>{alert.host} - {new Date(alert.ts).toLocaleString()}</span>
            </div>
            <b>{alert.score}</b>
          </article>
        ))}
        {alerts.length === 0 && <p className="empty">No data yet.</p>}
      </div>
    </section>
  );
}

function Timeline({ items }) {
  return (
    <section className="panel">
      <div className="panel-title">
        <Activity size={18} />
        <h2>Attack timeline</h2>
      </div>
      <div className="timeline">
        {items.map((item, index) => (
          <div className={item.type} key={`${item.type}-${index}-${item.ts}`}>
            <time>{new Date(item.ts).toLocaleTimeString()}</time>
            <strong>{item.kind}</strong>
            <span>{item.host}</span>
          </div>
        ))}
        {items.length === 0 && <p className="empty">No data yet.</p>}
      </div>
    </section>
  );
}

function TreeNode({ node }) {
  return (
    <li>
      <div className="process">
        <TerminalSquare size={15} />
        <span>{node.name}</span>
        <small>pid {node.pid}</small>
      </div>
      {node.children?.length > 0 && (
        <ul>
          {node.children.map((child) => <TreeNode node={child} key={child.pid} />)}
        </ul>
      )}
    </li>
  );
}

function ProcessTree({ tree, selected }) {
  return (
    <section className="panel">
      <div className="panel-title">
        <Network size={18} />
        <h2>Process tree</h2>
      </div>
      <div className="tree-host">{selected || "No host selected"}</div>
      <ul className="process-tree">
        {(tree?.processes || []).map((node) => <TreeNode node={node} key={node.pid} />)}
      </ul>
      {(!tree || tree.processes?.length === 0) && <p className="empty">No data yet.</p>}
    </section>
  );
}

function App() {
  const [hosts, setHosts] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [selectedHost, setSelectedHost] = useState("");
  const selectedHostRef = useRef("");
  const [tree, setTree] = useState(null);
  const [error, setError] = useState("");

  function selectHost(host) {
    selectedHostRef.current = host;
    setSelectedHost(host);
  }

  async function refresh() {
    try {
      setError("");
      const [hostData, alertData, timelineData] = await Promise.all([
        getJson("/hosts"),
        getJson("/alerts"),
        getJson("/timeline"),
      ]);
      setHosts(hostData);
      setAlerts(alertData);
      setTimeline(timelineData);
      const knownHosts = new Set(hostData.map((host) => host.host));
      const nextHost = knownHosts.has(selectedHostRef.current) ? selectedHostRef.current : hostData[0]?.host || "";
      selectHost(nextHost);
      if (nextHost) setTree(await getJson(`/process-tree/${encodeURIComponent(nextHost)}`));
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 5000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!selectedHost) return;
    getJson(`/process-tree/${encodeURIComponent(selectedHost)}`).then(setTree).catch(() => {});
  }, [selectedHost]);

  const maxRisk = useMemo(() => hosts.reduce((max, host) => Math.max(max, host.risk_score), 0), [hosts]);

  return (
    <main>
      <header className="topbar">
        <div className="brand">
          <ShieldCheck size={28} />
          <div>
            <h1>SentinelX</h1>
            <span>EDR/XDR SOC Console</span>
          </div>
        </div>
        <div className="topbar-actions">
          <span className="demo-badge">Demo Mode</span>
          <button className="icon-button" onClick={refresh} title="Refresh">
            <RefreshCw size={18} />
          </button>
        </div>
      </header>

      {error && <div className="error">API unavailable: {error}</div>}

      <section className="stats-row">
        <Stat icon={Server} label="Hosts" value={hosts.length} />
        <Stat icon={AlertTriangle} label="Open alerts" value={alerts.length} />
        <Stat icon={Activity} label="Max risk" value={maxRisk} />
      </section>

      <section className="grid">
        <HostsMap hosts={hosts} selected={selectedHost} onSelect={selectHost} />
        <AlertsFeed alerts={alerts} />
        <Timeline items={timeline} />
        <ProcessTree tree={tree} selected={selectedHost} />
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
// Project version: SentinelX V1.6


