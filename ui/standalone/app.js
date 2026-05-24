(function () {
  const h = React.createElement;
  const API_BASE_URL = "http://127.0.0.1:8093";
  const tabs = ["issues", "plan", "code", "agent", "raw"];

  function App() {
    const [dataFile, setDataFile] = React.useState(null);
    const [contractFile, setContractFile] = React.useState(null);
    const [sourceName, setSourceName] = React.useState("uploaded_dataset");
    const [activeTab, setActiveTab] = React.useState("issues");
    const [report, setReport] = React.useState(null);
    const [error, setError] = React.useState("");
    const [loading, setLoading] = React.useState(false);

    const canSubmit = Boolean(dataFile && contractFile && !loading);

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
        const response = await fetch(API_BASE_URL + "/validate", {
          method: "POST",
          body: formData
        });
        const payload = await response.json().catch(function () {
          return {};
        });
        if (!response.ok) {
          throw new Error(payload.detail || "Validation failed");
        }
        setReport(payload);
        setActiveTab("issues");
      } catch (err) {
        setError(err && err.message ? err.message : "Validation failed");
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

    return h(
      "div",
      { className: "app-shell" },
      h(
        "header",
        { className: "topbar" },
        h("div", null, h("p", { className: "eyebrow" }, "DataContract Guard"), h("h1", null, "Contract validation console")),
        h("div", { className: "endpoint-chip", title: "API endpoint" }, h("span", null, API_BASE_URL + " /validate"))
      ),
      h(
        "main",
        { className: "workspace" },
        h(
          "section",
          { className: "input-panel", "aria-label": "Validation form" },
          h(
            "div",
            { className: "panel-heading" },
            h("div", null, h("p", { className: "eyebrow" }, "Request"), h("h2", null, "Validate delivery")),
            h("button", { className: "icon-button", type: "button", onClick: resetForm, title: "Reset" }, "R")
          ),
          h(
            "form",
            { className: "validation-form", onSubmit: submitValidation },
            h("label", { className: "field-label", htmlFor: "source-name" }, "Source name"),
            h("input", {
              id: "source-name",
              value: sourceName,
              onChange: function (event) {
                setSourceName(event.target.value);
              },
              placeholder: "customers"
            }),
            h(FileInput, {
              id: "data-file",
              label: "Data file",
              accept: ".csv,.json,.parquet",
              file: dataFile,
              onChange: setDataFile
            }),
            h(FileInput, {
              id: "contract-file",
              label: "Contract",
              accept: ".yaml,.yml,.json",
              file: contractFile,
              onChange: setContractFile
            }),
            h(
              "button",
              { className: "primary-button", type: "submit", disabled: !canSubmit },
              h("span", null, loading ? "Validating" : "Run validation")
            )
          ),
          error ? h("div", { className: "error-box", role: "alert" }, h("span", null, error)) : null
        ),
        h(
          "section",
          { className: "result-panel", "aria-label": "Validation results" },
          report ? h(ReportView, { report: report, activeTab: activeTab, onTabChange: setActiveTab }) : h(EmptyState, { loading: loading })
        )
      )
    );
  }

  function FileInput(props) {
    return h(
      "div",
      null,
      h("label", { className: "field-label", htmlFor: props.id }, props.label),
      h(
        "label",
        { className: "file-drop", htmlFor: props.id },
        h("input", {
          id: props.id,
          type: "file",
          accept: props.accept,
          onChange: function (event) {
            props.onChange(event.target.files && event.target.files[0] ? event.target.files[0] : null);
          }
        }),
        h("span", null, "File"),
        h(
          "div",
          null,
          h("strong", null, props.file ? props.file.name : "Choose file"),
          h("span", null, props.file ? prettyBytes(props.file.size) : props.accept.replaceAll(",", ", "))
        )
      )
    );
  }

  function ReportView(props) {
    const report = props.report;
    const counts = report.counts || {};
    const code = report.generatedCode || report.generated_code || [];
    const llm = report.llmExplanation || report.llm_explanation || {};

    return h(
      React.Fragment,
      null,
      h(
        "div",
        { className: "summary-strip" },
        h(StatusPill, { status: report.status }),
        h(Metric, { label: "Failures", value: counts.FAIL || 0 }),
        h(Metric, { label: "Warnings", value: counts.WARN || 0 }),
        h(Metric, { label: "Source", value: report.source || "-", wide: true }),
        h(Metric, { label: "Elapsed", value: (report.trace && report.trace.elapsedMs ? report.trace.elapsedMs : 0) + " ms" })
      ),
      h(
        "div",
        { className: "explanation-band " + statusToClass(report.status) },
        h("div", null, h("p", { className: "eyebrow" }, "Engine status"), h("h2", null, report.analysis && report.analysis.summary ? report.analysis.summary : "Validation complete")),
        h("p", null, llm.explanation || "No explanation returned.")
      ),
      h(
        "div",
        { className: "tabbar", role: "tablist", "aria-label": "Report sections" },
        tabs.map(function (tab) {
          return h(
            "button",
            {
              key: tab,
              className: props.activeTab === tab ? "tab-button active" : "tab-button",
              type: "button",
              onClick: function () {
                props.onTabChange(tab);
              }
            },
            tabLabel(tab)
          );
        })
      ),
      props.activeTab === "issues" ? h(IssuesTable, { issues: report.issues || [] }) : null,
      props.activeTab === "plan" ? h(PlanView, { report: report }) : null,
      props.activeTab === "code" ? h(CodeView, { snippets: code }) : null,
      props.activeTab === "agent" ? h(AgentView, { agent: report.agent, trace: report.trace, cost: report.cost }) : null,
      props.activeTab === "raw" ? h(RawView, { report: report }) : null
    );
  }

  function StatusPill(props) {
    return h("div", { className: "status-pill " + statusToClass(props.status) }, h("span", null, props.status || "UNKNOWN"));
  }

  function Metric(props) {
    return h("div", { className: props.wide ? "metric wide" : "metric" }, h("span", null, props.label), h("strong", null, props.value));
  }

  function IssuesTable(props) {
    if (!props.issues.length) {
      return h("div", { className: "empty-inline" }, "No issues detected.");
    }

    return h(
      "div",
      { className: "table-wrap" },
      h(
        "table",
        null,
        h("thead", null, h("tr", null, ["Severity", "Check", "Column", "Expected", "Actual", "Message"].map(function (item) {
          return h("th", { key: item }, item);
        }))),
        h(
          "tbody",
          null,
          props.issues.map(function (issue, index) {
            return h(
              "tr",
              { key: issue.check + issue.column + index },
              h("td", null, h("span", { className: "severity " + statusToClass(issue.severity) }, issue.severity)),
              h("td", null, issue.check),
              h("td", null, issue.column),
              h("td", null, formatCell(issue.expected)),
              h("td", null, formatCell(issue.actual)),
              h(
                "td",
                null,
                h("div", { className: "message-cell" }, h("strong", null, issue.message), issue.row ? h("span", null, "Row " + issue.row) : null, issue.impact ? h("span", null, issue.impact) : null)
              )
            );
          })
        )
      )
    );
  }

  function PlanView(props) {
    const report = props.report;
    const recommendations = report.recommendations || (report.analysis && report.analysis.correctionPlan) || [];
    const corrections = report.corrections || [];
    return h(
      "div",
      { className: "two-column" },
      h("section", { className: "plain-section" }, h("h3", null, "Recommendations"), h("ul", { className: "action-list" }, recommendations.map(function (item, index) {
        return h("li", { key: item + index }, item);
      }))),
      h("section", { className: "plain-section" }, h("h3", null, "Corrections"), h("div", { className: "correction-list" }, corrections.map(function (correction, index) {
        return h("div", { className: "correction-item", key: correction.action + correction.target + index }, h("span", null, correction.action), h("strong", null, correction.target), h("p", null, correction.suggestion));
      })))
    );
  }

  function CodeView(props) {
    if (!props.snippets.length) {
      return h("div", { className: "empty-inline" }, "No generated code returned.");
    }
    return h("div", { className: "code-list" }, props.snippets.map(function (snippet, index) {
      return h("section", { className: "code-block", key: snippet.title + index }, h("div", { className: "code-header" }, h("div", null, h("span", null, snippet.language), h("h3", null, snippet.title)), h("button", { className: "icon-button", type: "button", title: "Copy code", onClick: function () { copyText(String(snippet.code || "")); } }, "C")), h("pre", null, h("code", null, snippet.code)));
    }));
  }

  function AgentView(props) {
    const steps = props.agent && props.agent.steps ? props.agent.steps : [];
    return h(
      "div",
      { className: "agent-grid" },
      h("section", { className: "plain-section" }, h("h3", null, "Execution trace"), h("div", { className: "timeline" }, steps.map(function (step, index) {
        return h("div", { className: "timeline-item", key: step.name + index }, h("span", null), h("div", null, h("strong", null, step.name), h("p", null, step.summary)));
      }))),
      h("section", { className: "plain-section" }, h("h3", null, "Runtime"), h("dl", { className: "definition-list" }, definitionRows([
        ["Trace ID", props.trace && props.trace.traceId ? props.trace.traceId : "-"],
        ["Estimated units", props.cost && props.cost.estimatedUnits !== undefined ? props.cost.estimatedUnits : "-"],
        ["Rows", props.cost && props.cost.dataRows !== undefined ? props.cost.dataRows : "-"],
        ["Columns", props.cost ? (props.cost.sourceColumns + " source / " + props.cost.contractColumns + " contract") : "-"]
      ])))
    );
  }

  function RawView(props) {
    const raw = JSON.stringify(props.report, null, 2);
    return h("section", { className: "code-block" }, h("div", { className: "code-header" }, h("div", null, h("span", null, "json"), h("h3", null, "Response payload")), h("button", { className: "icon-button", type: "button", title: "Copy JSON", onClick: function () { copyText(raw); } }, "C")), h("pre", null, h("code", null, raw)));
  }

  function EmptyState(props) {
    return h("div", { className: "empty-state" }, h("h2", null, props.loading ? "Running validation" : "Ready for a delivery"), h("p", null, "Upload a data file and a contract to inspect schema drift, quality issues, and generated remediation code."));
  }

  function definitionRows(rows) {
    return rows.flatMap(function (row) {
      return [h("dt", { key: row[0] + "-term" }, row[0]), h("dd", { key: row[0] + "-desc" }, row[1])];
    });
  }

  function tabLabel(tab) {
    return tab.charAt(0).toUpperCase() + tab.slice(1);
  }

  function prettyBytes(bytes) {
    if (!Number.isFinite(bytes)) {
      return "-";
    }
    if (bytes < 1024) {
      return bytes + " B";
    }
    if (bytes < 1024 * 1024) {
      return (bytes / 1024).toFixed(1) + " KB";
    }
    return (bytes / 1024 / 1024).toFixed(1) + " MB";
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

  function copyText(value) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(value);
    }
  }

  ReactDOM.createRoot(document.getElementById("root")).render(h(App));
})();
