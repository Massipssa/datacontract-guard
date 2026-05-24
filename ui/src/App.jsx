import { useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Braces,
  CheckCircle2,
  Clipboard,
  Code2,
  FileCode2,
  FileText,
  Loader2,
  Play,
  RotateCcw,
  Server,
  ShieldAlert,
  UploadCloud,
  XCircle
} from "lucide-react";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

const tabs = [
  { id: "issues", label: "Issues", icon: AlertTriangle },
  { id: "plan", label: "Plan", icon: CheckCircle2 },
  { id: "code", label: "Code", icon: Code2 },
  { id: "agent", label: "Agent", icon: Activity },
  { id: "raw", label: "Raw", icon: Braces }
];

function App() {
  const [dataFile, setDataFile] = useState(null);
  const [contractFile, setContractFile] = useState(null);
  const [sourceName, setSourceName] = useState("uploaded_dataset");
  const [activeTab, setActiveTab] = useState("issues");
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const canSubmit = dataFile && contractFile && !loading;

  async function submitValidation(event) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }

    setLoading(true);
    setError("");
    setReport(null);

    const formData = new FormData();
    formData.append("data_file", dataFile);
    formData.append("contract_file", contractFile);
    formData.append("source_name", sourceName.trim() || "uploaded_dataset");

    try {
      const response = await fetch(`${API_BASE_URL}/validate`, {
        method: "POST",
        body: formData
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.detail || payload.error?.message || "Validation failed");
      }
      setReport(payload);
      setActiveTab("issues");
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : "Validation failed");
    } finally {
      setLoading(false);
    }
  }

  function resetForm() {
    setDataFile(null);
    setContractFile(null);
    setSourceName("uploaded_dataset");
    setReport(null);
    setError("");
    setActiveTab("issues");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">DataContract Guard</p>
          <h1>Contract validation console</h1>
        </div>
        <div className="endpoint-chip" title="API endpoint">
          <Server size={16} />
          <span>{API_BASE_URL || "Vite proxy"} /validate</span>
        </div>
      </header>

      <main className="workspace">
        <section className="input-panel" aria-label="Validation form">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Request</p>
              <h2>Validate delivery</h2>
            </div>
            <button className="icon-button" type="button" onClick={resetForm} title="Reset">
              <RotateCcw size={18} />
            </button>
          </div>

          <form className="validation-form" onSubmit={submitValidation}>
            <label className="field-label" htmlFor="sourceName">
              Source name
            </label>
            <input
              id="sourceName"
              value={sourceName}
              onChange={(event) => setSourceName(event.target.value)}
              placeholder="customers"
            />

            <FileDrop
              label="Data file"
              accept=".csv,.json,.parquet"
              file={dataFile}
              onChange={setDataFile}
              icon={FileText}
            />

            <FileDrop
              label="Contract"
              accept=".yaml,.yml,.json"
              file={contractFile}
              onChange={setContractFile}
              icon={FileCode2}
            />

            <button className="primary-button" type="submit" disabled={!canSubmit}>
              {loading ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
              <span>{loading ? "Validating" : "Run validation"}</span>
            </button>
          </form>

          {error ? (
            <div className="error-box" role="alert">
              <ShieldAlert size={18} />
              <span>{error}</span>
            </div>
          ) : null}
        </section>

        <section className="result-panel" aria-label="Validation results">
          {report ? (
            <ReportView report={report} activeTab={activeTab} onTabChange={setActiveTab} />
          ) : (
            <EmptyState loading={loading} />
          )}
        </section>
      </main>
    </div>
  );
}

function FileDrop({ label, accept, file, onChange, icon: Icon }) {
  const inputId = useMemo(() => `${label.replace(/\s+/g, "-").toLowerCase()}-input`, [label]);

  return (
    <div>
      <label className="field-label" htmlFor={inputId}>
        {label}
      </label>
      <label
        className="file-drop"
        htmlFor={inputId}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          const droppedFile = event.dataTransfer.files?.[0];
          if (droppedFile) {
            onChange(droppedFile);
          }
        }}
      >
        <input
          id={inputId}
          type="file"
          accept={accept}
          onChange={(event) => onChange(event.target.files?.[0] || null)}
        />
        <Icon size={22} />
        <div>
          <strong>{file ? file.name : "Choose file"}</strong>
          <span>{file ? prettyBytes(file.size) : accept.replaceAll(",", ", ")}</span>
        </div>
      </label>
    </div>
  );
}

function ReportView({ report, activeTab, onTabChange }) {
  const counts = report.counts || {};
  const generatedCode = report.generatedCode || report.generated_code || [];
  const llmExplanation = report.llmExplanation || report.llm_explanation || {};
  const statusClass = statusToClass(report.status);

  return (
    <>
      <div className="summary-strip">
        <StatusPill status={report.status} />
        <Metric label="Failures" value={counts.FAIL ?? 0} />
        <Metric label="Warnings" value={counts.WARN ?? 0} />
        <Metric label="Source" value={report.source || "-"} wide />
        <Metric label="Elapsed" value={`${report.trace?.elapsedMs ?? 0} ms`} />
      </div>

      <div className={`explanation-band ${statusClass}`}>
        <div>
          <p className="eyebrow">Engine status</p>
          <h2>{report.analysis?.summary || "Validation complete"}</h2>
        </div>
        <p>{llmExplanation.explanation || "No explanation returned."}</p>
      </div>

      <div className="tabbar" role="tablist" aria-label="Report sections">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              className={activeTab === tab.id ? "tab-button active" : "tab-button"}
              type="button"
              onClick={() => onTabChange(tab.id)}
              role="tab"
              aria-selected={activeTab === tab.id}
              title={tab.label}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {activeTab === "issues" ? <IssuesTable issues={report.issues || []} /> : null}
      {activeTab === "plan" ? <PlanView report={report} /> : null}
      {activeTab === "code" ? <CodeView snippets={generatedCode} /> : null}
      {activeTab === "agent" ? <AgentView agent={report.agent} trace={report.trace} cost={report.cost} /> : null}
      {activeTab === "raw" ? <RawView report={report} /> : null}
    </>
  );
}

function StatusPill({ status }) {
  const Icon = status === "PASS" ? CheckCircle2 : status === "WARN" ? AlertTriangle : XCircle;
  return (
    <div className={`status-pill ${statusToClass(status)}`}>
      <Icon size={18} />
      <span>{status || "UNKNOWN"}</span>
    </div>
  );
}

function Metric({ label, value, wide = false }) {
  return (
    <div className={wide ? "metric wide" : "metric"}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function IssuesTable({ issues }) {
  if (!issues.length) {
    return <div className="empty-inline">No issues detected.</div>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Severity</th>
            <th>Check</th>
            <th>Column</th>
            <th>Expected</th>
            <th>Actual</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          {issues.map((issue, index) => (
            <tr key={`${issue.check}-${issue.column}-${index}`}>
              <td>
                <span className={`severity ${statusToClass(issue.severity)}`}>{issue.severity}</span>
              </td>
              <td>{issue.check}</td>
              <td>{issue.column}</td>
              <td>{formatCell(issue.expected)}</td>
              <td>{formatCell(issue.actual)}</td>
              <td>
                <div className="message-cell">
                  <strong>{issue.message}</strong>
                  {issue.row ? <span>Row {issue.row}</span> : null}
                  {issue.impact ? <span>{issue.impact}</span> : null}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PlanView({ report }) {
  const corrections = report.corrections || [];
  const recommendations = report.recommendations || report.analysis?.correctionPlan || [];

  return (
    <div className="two-column">
      <section className="plain-section">
        <h3>Recommendations</h3>
        <ul className="action-list">
          {recommendations.map((item, index) => (
            <li key={`${item}-${index}`}>{item}</li>
          ))}
        </ul>
      </section>
      <section className="plain-section">
        <h3>Corrections</h3>
        <div className="correction-list">
          {corrections.map((correction, index) => (
            <div className="correction-item" key={`${correction.action}-${correction.target}-${index}`}>
              <span>{correction.action}</span>
              <strong>{correction.target}</strong>
              <p>{correction.suggestion}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function CodeView({ snippets }) {
  if (!snippets.length) {
    return <div className="empty-inline">No generated code returned.</div>;
  }

  return (
    <div className="code-list">
      {snippets.map((snippet, index) => (
        <section className="code-block" key={`${snippet.title}-${index}`}>
          <div className="code-header">
            <div>
              <span>{snippet.language}</span>
              <h3>{snippet.title}</h3>
            </div>
            <button
              className="icon-button"
              type="button"
              title="Copy code"
              onClick={() => navigator.clipboard?.writeText(String(snippet.code || ""))}
            >
              <Clipboard size={18} />
            </button>
          </div>
          <pre><code>{snippet.code}</code></pre>
        </section>
      ))}
    </div>
  );
}

function AgentView({ agent, trace, cost }) {
  const steps = agent?.steps || [];
  return (
    <div className="agent-grid">
      <section className="plain-section">
        <h3>Execution trace</h3>
        <div className="timeline">
          {steps.map((step, index) => (
            <div className="timeline-item" key={`${step.name}-${index}`}>
              <span />
              <div>
                <strong>{step.name}</strong>
                <p>{step.summary}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
      <section className="plain-section">
        <h3>Runtime</h3>
        <dl className="definition-list">
          <dt>Trace ID</dt>
          <dd>{trace?.traceId || "-"}</dd>
          <dt>Estimated units</dt>
          <dd>{cost?.estimatedUnits ?? "-"}</dd>
          <dt>Rows</dt>
          <dd>{cost?.dataRows ?? "-"}</dd>
          <dt>Columns</dt>
          <dd>{cost?.sourceColumns ?? "-"} source / {cost?.contractColumns ?? "-"} contract</dd>
        </dl>
      </section>
    </div>
  );
}

function RawView({ report }) {
  return (
    <section className="code-block">
      <div className="code-header">
        <div>
          <span>json</span>
          <h3>Response payload</h3>
        </div>
        <button
          className="icon-button"
          type="button"
          title="Copy JSON"
          onClick={() => navigator.clipboard?.writeText(JSON.stringify(report, null, 2))}
        >
          <Clipboard size={18} />
        </button>
      </div>
      <pre><code>{JSON.stringify(report, null, 2)}</code></pre>
    </section>
  );
}

function EmptyState({ loading }) {
  return (
    <div className="empty-state">
      {loading ? <Loader2 className="spin" size={34} /> : <UploadCloud size={38} />}
      <h2>{loading ? "Running validation" : "Ready for a delivery"}</h2>
      <p>Upload a data file and a contract to inspect schema drift, quality issues, and generated remediation code.</p>
    </div>
  );
}

function prettyBytes(bytes) {
  if (!Number.isFinite(bytes)) {
    return "-";
  }
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function statusToClass(status) {
  const normalized = String(status || "").toLowerCase();
  if (normalized === "pass" || normalized === "ok") {
    return "pass";
  }
  if (normalized === "warn") {
    return "warn";
  }
  if (normalized === "fail") {
    return "fail";
  }
  return "neutral";
}

function formatCell(value) {
  if (value === undefined || value === null || value === "") {
    return "-";
  }
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  return String(value);
}

export default App;
