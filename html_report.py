"""
HTML rendering for dependency analysis reports.
"""

import html
import json


def resolve_initial_focus(initial_focus, report_data):
    libraries = report_data["libraries"]
    if not libraries:
        return None
    if not initial_focus:
        return libraries[0]
    return report_data["lookup"].get(initial_focus, libraries[0])


def render_html_report(report_data, initial_focus=None):
    resolved_focus = resolve_initial_focus(initial_focus, report_data)
    payload = json.dumps(report_data, ensure_ascii=False)
    initial_focus_json = json.dumps(resolved_focus, ensure_ascii=False)
    title = "Shared Library Dependency Report"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --bg: #f4f0e8;
      --panel: rgba(255, 252, 247, 0.08);
      --panel-strong: rgba(255, 253, 250, 0.16);
      --line: rgba(159, 74, 25, 0.08);
      --grid: rgba(108, 88, 61, 0.08);
      --text: #1f2933;
      --muted: #6b7280;
      --accent: #9f4a19;
      --selected: #fff1e6;
      --selected-stroke: #b95d2b;
      --cycle: #fff2ea;
      --cycle-stroke: #b9462a;
      --shadow: 0 10px 24px rgba(64, 45, 22, 0.08);
      --status-bg: rgba(34, 30, 25, 0.68);
      --status-line: rgba(255, 255, 255, 0.1);
      --status-text: rgba(255, 245, 230, 0.78);
      --status-muted: rgba(255, 241, 222, 0.46);
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      color: var(--text);
      font-family: "Noto Sans SC", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(255,255,255,0.72), transparent 35%),
        linear-gradient(135deg, #efe1ca 0%, #f7f4ee 42%, #ebe1d3 100%);
      width: 100vw;
      height: 100vh;
      overflow: hidden;
    }}

    .page {{
      position: relative;
      width: 100vw;
      height: 100vh;
      overflow: hidden;
    }}

    .toolbar {{
      position: absolute;
      top: 12px;
      left: 16px;
      z-index: 10;
      display: grid;
      grid-template-columns: minmax(200px, 280px) minmax(78px, 96px) auto auto;
      gap: 6px;
      padding: 3px 6px;
      align-items: end;
      width: min(640px, calc(100vw - 32px));
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 12px;
      box-shadow: none;
      backdrop-filter: blur(10px);
    }}

    label {{
      display: grid;
      gap: 2px;
      font-size: 9px;
      color: rgba(31, 41, 51, 0.48);
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }}

    select {{
      width: 100%;
      border: 1px solid rgba(159, 74, 25, 0.08);
      background: rgba(255, 255, 255, 0.08);
      border-radius: 7px;
      padding: 4px 7px;
      color: rgba(31, 41, 51, 0.86);
      font-size: 11px;
      backdrop-filter: blur(8px);
    }}

    .toolbar-actions {{
      display: flex;
      gap: 6px;
      align-items: center;
      justify-content: flex-end;
    }}

    .switch {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 9px;
      color: rgba(31, 41, 51, 0.5);
      white-space: nowrap;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      padding: 4px 7px;
      border-radius: 7px;
      border: 1px solid rgba(159, 74, 25, 0.08);
      background: rgba(255, 255, 255, 0.08);
      backdrop-filter: blur(8px);
    }}

    .switch input {{
      position: absolute;
      opacity: 0;
      width: 0;
      height: 0;
      pointer-events: none;
    }}

    .switch-track {{
      position: relative;
      width: 24px;
      height: 14px;
      border-radius: 999px;
      background: rgba(76, 58, 39, 0.18);
      border: 1px solid rgba(159, 74, 25, 0.12);
      transition: background 0.18s ease;
    }}

    .switch-track::after {{
      content: "";
      position: absolute;
      top: 1px;
      left: 1px;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: rgba(255, 252, 247, 0.96);
      box-shadow: 0 1px 4px rgba(31, 41, 51, 0.18);
      transition: transform 0.18s ease;
    }}

    .switch input:checked + .switch-track {{
      background: rgba(185, 93, 43, 0.44);
    }}

    .switch input:checked + .switch-track::after {{
      transform: translateX(10px);
    }}

    .action-btn {{
      border: 1px solid rgba(159, 74, 25, 0.08);
      background: rgba(255, 255, 255, 0.08);
      border-radius: 7px;
      padding: 4px 8px;
      color: rgba(31, 41, 51, 0.86);
      font-size: 10px;
      cursor: pointer;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      backdrop-filter: blur(8px);
    }}

    .canvas-panel {{
      position: absolute;
      inset: 0;
      overflow: hidden;
      background: transparent;
    }}

    .graph-wrap {{
      position: absolute;
      inset: 0;
      overflow: auto;
      background:
        linear-gradient(var(--grid) 1px, transparent 1px),
        linear-gradient(90deg, var(--grid) 1px, transparent 1px),
        rgba(255,255,255,0.44);
      background-size: 32px 32px;
      padding: 62px 72px 52px;
    }}

    #graph-host {{
      min-width: 100%;
      min-height: 100%;
    }}

    #graph-host svg {{
      display: block;
      margin: 0 auto;
      max-width: 100%;
      width: auto;
      height: auto;
    }}

    .statusbar {{
      position: absolute;
      left: 0;
      right: 0;
      bottom: 0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      z-index: 9;
      pointer-events: auto;
      min-height: 28px;
      background: var(--status-bg);
      border: 1px solid var(--status-line);
      padding: 0 8px;
      box-shadow: 0 -6px 20px rgba(34, 24, 17, 0.18);
      backdrop-filter: blur(12px);
    }}

    .status-group {{
      min-width: 0;
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .status-sep {{
      flex: 0 0 auto;
      width: 1px;
      height: 12px;
      background: rgba(255, 255, 255, 0.12);
    }}

    .status-label {{
      flex: 0 0 auto;
      font-size: 9px;
      color: var(--status-muted);
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }}

    .status-value {{
      min-width: 0;
      font-family: "JetBrains Mono", monospace;
      font-size: 11px;
      color: var(--status-text);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .empty {{
      padding: 24px;
      color: var(--muted);
      background: rgba(255,255,255,0.8);
      border-radius: 20px;
      box-shadow: var(--shadow);
    }}

    @media (max-width: 1080px) {{
      .toolbar {{
        grid-template-columns: 1fr 1fr;
        width: min(500px, calc(100vw - 24px));
      }}

      .graph-wrap {{
        padding-top: 110px;
      }}

      .statusbar {{
        flex-wrap: wrap;
        gap: 10px;
        padding-top: 6px;
        padding-bottom: 6px;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <section class="toolbar">
      <label>
        目标动态库
        <select id="library-select"></select>
      </label>
      <label>
        最大层级
        <select id="depth-select">
          <option value="99">全部</option>
          <option value="1" selected>1 层</option>
          <option value="2">2 层</option>
          <option value="3">3 层</option>
          <option value="4">4 层</option>
          <option value="5">5 层</option>
          <option value="6">6 层</option>
        </select>
      </label>
      <div class="toolbar-actions">
        <label class="switch">
          <input id="dashed-toggle" type="checkbox" checked>
          <span class="switch-track"></span>
          虚线
        </label>
      </div>
      <div class="toolbar-actions">
        <button id="export-svg" class="action-btn" type="button">导出 SVG</button>
      </div>
    </section>

    <section class="canvas-panel">
      <div class="graph-wrap">
        <div id="graph-host"></div>
      </div>
      <div class="statusbar">
        <div class="status-group">
          <span class="status-label">未解析依赖</span>
          <div class="status-value" id="unresolved-status">None</div>
        </div>
        <div class="status-sep"></div>
        <div class="status-group">
          <span class="status-label">当前分析</span>
          <div class="status-value" id="basic-info">None</div>
        </div>
      </div>
    </section>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <script>
    const REPORT = {payload};
    const INITIAL_FOCUS = {initial_focus_json};

    const elements = {{
      librarySelect: document.getElementById("library-select"),
      depthSelect: document.getElementById("depth-select"),
      dashedToggle: document.getElementById("dashed-toggle"),
      exportSvg: document.getElementById("export-svg"),
      basicInfo: document.getElementById("basic-info"),
      unresolvedStatus: document.getElementById("unresolved-status"),
      graphHost: document.getElementById("graph-host"),
    }};

    const state = {{
      selected: INITIAL_FOCUS || REPORT.libraries[0] || null,
      maxDepth: 1,
      showDashed: true,
    }};

    let currentSvg = "";

    function escapeHtml(value) {{
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }}

    function mermaidLabel(value) {{
      return String(value)
        .replaceAll('"', "&quot;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
    }}

    function comparePaths(aPath, bPath) {{
      const a = REPORT.nodes[aPath];
      const b = REPORT.nodes[bPath];
      return a.basename.localeCompare(b.basename) || a.path.localeCompare(b.path);
    }}

    function refreshLibraryOptions() {{
      const options = REPORT.libraries.slice().sort(comparePaths);
      elements.librarySelect.innerHTML = options.map((path) => {{
        const node = REPORT.nodes[path];
        const selected = path === state.selected ? " selected" : "";
        return `<option value="${{escapeHtml(path)}}"${{selected}}>${{escapeHtml(node.basename)}}</option>`;
      }}).join("");

      if (!options.includes(state.selected)) {{
        state.selected = options[0] || null;
      }}
      if (state.selected) {{
        elements.librarySelect.value = state.selected;
      }}
    }}

    function buildSubgraph(root) {{
      if (!root || !REPORT.nodes[root]) return null;

      const queue = [[root, 0]];
      const depthMap = new Map([[root, 0]]);
      const included = new Set([root]);
      const edges = [];

      while (queue.length) {{
        const [current, depth] = queue.shift();
        const node = REPORT.nodes[current];
        const dependencies = node.dependencies.slice().sort(comparePaths);

        for (const dep of dependencies) {{
          edges.push({{ source: current, target: dep }});
          if (depth >= state.maxDepth) {{
            continue;
          }}
          const nextDepth = depth + 1;
          const prevDepth = depthMap.get(dep);
          if (prevDepth === undefined || nextDepth < prevDepth) {{
            depthMap.set(dep, nextDepth);
          }}
          if (!included.has(dep) && nextDepth <= state.maxDepth) {{
            included.add(dep);
            queue.push([dep, nextDepth]);
          }}
        }}
      }}

      const nodes = Array.from(included).sort(comparePaths);
      return {{
        root,
        nodes,
        depthMap,
        edges: edges.filter((edge) => included.has(edge.source) && included.has(edge.target)),
      }};
    }}

    function buildMermaidGraph(subgraph) {{
      const idMap = new Map();
      subgraph.nodes.forEach((path, index) => {{
        idMap.set(path, `n${{index}}`);
      }});

      const cycleNodes = new Set(REPORT.cycles.flat().filter((path) => idMap.has(path)));
      const lines = [
        "flowchart TD",
        "classDef selected fill:#fff1e6,stroke:#b95d2b,stroke-width:3px,color:#1f2933;",
        "classDef cycle fill:#fff2ea,stroke:#b9462a,stroke-width:2px,color:#1f2933;",
        "classDef normal fill:#fffdfa,stroke:#bda68b,stroke-width:1.5px,color:#1f2933;",
      ];

      let visibleEdgeIndex = 0;
      subgraph.nodes.forEach((path) => {{
        const nodeId = idMap.get(path);
        const name = mermaidLabel(REPORT.nodes[path].basename);
        lines.push(`${{nodeId}}["${{name}}"]`);
        if (path === subgraph.root) {{
          lines.push(`class ${{nodeId}} selected`);
        }} else if (cycleNodes.has(path)) {{
          lines.push(`class ${{nodeId}} cycle`);
        }} else {{
          lines.push(`class ${{nodeId}} normal`);
        }}
      }});

      subgraph.edges.forEach((edge) => {{
        const sourceId = idMap.get(edge.source);
        const targetId = idMap.get(edge.target);
        const sourceDepth = subgraph.depthMap.get(edge.source) ?? 0;
        const targetDepth = subgraph.depthMap.get(edge.target) ?? 0;
        const isCycleEdge = targetDepth <= sourceDepth;

        if (isCycleEdge && !state.showDashed) {{
          return;
        }}

        lines.push(`${{sourceId}} --> ${{targetId}}`);
        if (isCycleEdge) {{
          lines.push(`linkStyle ${{visibleEdgeIndex}} stroke:#b9462a,stroke-width:2.5px,stroke-dasharray:7 5;`);
        }}
        visibleEdgeIndex += 1;
      }});

      subgraph.nodes.forEach((path) => {{
        lines.push(`click ${{idMap.get(path)}} callback "${{encodeURIComponent(path)}}"`);
      }});

      return lines.join("\\n");
    }}

    async function renderMermaid(subgraph) {{
      if (!subgraph || !subgraph.nodes.length) {{
        elements.graphHost.innerHTML = '<div class="empty">没有可展示的依赖关系。</div>';
        currentSvg = "";
        return;
      }}

      if (typeof mermaid === "undefined") {{
        elements.graphHost.innerHTML = '<div class="empty">未加载到 Mermaid。请在可访问 CDN 的环境中打开此 HTML，或者改成本地静态资源。</div>';
        currentSvg = "";
        return;
      }}

      mermaid.initialize({{
        startOnLoad: false,
        securityLevel: "loose",
        theme: "base",
        themeVariables: {{
          primaryColor: "#fffdfa",
          primaryBorderColor: "#bda68b",
          primaryTextColor: "#1f2933",
          lineColor: "#c17a4f",
          secondaryColor: "#fff1e6",
          tertiaryColor: "#fff2ea",
          fontFamily: "Noto Sans SC, Segoe UI, sans-serif",
          fontSize: "22px",
        }},
        flowchart: {{
          useMaxWidth: false,
          htmlLabels: true,
          curve: "basis",
          rankSpacing: state.maxDepth <= 1 ? 140 : 110,
          nodeSpacing: state.maxDepth <= 1 ? 70 : 50,
          padding: 18,
        }},
      }});

      const definition = buildMermaidGraph(subgraph);
      const renderId = `mermaid_${{Date.now()}}`;

      try {{
        const rendered = await mermaid.render(renderId, definition);
        currentSvg = rendered.svg;
        elements.graphHost.innerHTML = rendered.svg;
        fitGraphToViewport();
      }} catch (error) {{
        elements.graphHost.innerHTML = `<div class="empty">Mermaid 渲染失败: ${{escapeHtml(error.message || String(error))}}</div>`;
        currentSvg = "";
      }}
    }}

    function fitGraphToViewport() {{
      const wrap = elements.graphHost.parentElement;
      const svg = elements.graphHost.querySelector("svg");
      if (!wrap || !svg) {{
        return;
      }}

      const graphWidth = svg.viewBox.baseVal && svg.viewBox.baseVal.width
        ? svg.viewBox.baseVal.width
        : svg.getBBox().width;
      const graphHeight = svg.viewBox.baseVal && svg.viewBox.baseVal.height
        ? svg.viewBox.baseVal.height
        : svg.getBBox().height;

      if (!graphWidth || !graphHeight) {{
        return;
      }}

      const availableWidth = Math.max(320, wrap.clientWidth - 32);
      const availableHeight = Math.max(240, wrap.clientHeight - 32);
      const scale = Math.min(availableWidth / graphWidth, availableHeight / graphHeight, 1);

      svg.style.width = `${{Math.floor(graphWidth * scale)}}px`;
      svg.style.height = `${{Math.floor(graphHeight * scale)}}px`;
      wrap.scrollTo(0, 0);
    }}

    function renderMeta(node, reachableCount) {{
      const unresolvedText = node.unresolved_needed.length
        ? node.unresolved_needed.join(", ")
        : "None";
      const soname = node.soname || "N/A";

      elements.unresolvedStatus.textContent = unresolvedText;
      elements.basicInfo.textContent = `${{node.basename}} | soname ${{soname}} | 直接依赖 ${{node.dependencies.length}} | 可达 ${{reachableCount}} | 反向依赖 ${{node.dependents.length}}`;
    }}

    function exportSvg() {{
      if (!currentSvg) {{
        window.alert("当前没有可导出的 SVG。");
        return;
      }}
      const blob = new Blob([currentSvg], {{ type: "image/svg+xml;charset=utf-8" }});
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${{(state.selected || "dependency_graph").replaceAll("/", "_")}}.svg`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    }}

    async function render() {{
      refreshLibraryOptions();

      if (!state.selected || !REPORT.nodes[state.selected]) {{
        elements.basicInfo.textContent = "没有匹配的动态库";
        elements.unresolvedStatus.textContent = "None";
        elements.graphHost.innerHTML = '<div class="empty">没有匹配的动态库。</div>';
        currentSvg = "";
        return;
      }}

      const subgraph = buildSubgraph(state.selected);
      renderMeta(REPORT.nodes[state.selected], Math.max(0, subgraph.nodes.length - 1));
      await renderMermaid(subgraph);
    }}

    window.callback = (encodedPath) => {{
      const nextFocus = decodeURIComponent(encodedPath);
      if (!REPORT.nodes[nextFocus]) {{
        return;
      }}
      state.selected = nextFocus;
      elements.librarySelect.value = nextFocus;
      render();
    }};

    elements.librarySelect.addEventListener("change", (event) => {{
      state.selected = event.target.value;
      render();
    }});

    elements.depthSelect.addEventListener("change", (event) => {{
      state.maxDepth = Number(event.target.value);
      render();
    }});

    elements.dashedToggle.addEventListener("change", (event) => {{
      state.showDashed = event.target.checked;
      render();
    }});

    elements.exportSvg.addEventListener("click", () => {{
      exportSvg();
    }});

    window.addEventListener("resize", () => {{
      fitGraphToViewport();
    }});

    render();
  </script>
</body>
</html>
"""
