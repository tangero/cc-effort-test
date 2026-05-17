#!/usr/bin/env python3
"""Generate val.town report from results/runs/ directory."""
import json
from pathlib import Path

REPO = Path(__file__).parent.parent
RUNS_DIR = REPO / "results/runs"
OUT = REPO / "results/report.val.ts"

EFFORTS = ["low", "medium", "high", "xhigh", "max"]
COLORS_JS = "{low:'#22c55e',medium:'#3b82f6',high:'#f59e0b',xhigh:'#a855f7',max:'#ef4444'}"
INCOMPLETE_RUNS = 0

TASK_META = {
    "01_rename": {
        "label_cs": "Rename (syntetická)", "label_en": "Rename (synthetic)",
        "desc_cs": "Přejmenovat userId→accountId v TypeScript. 57 výskytů. Verify: 7 checks.",
        "desc_en": "Rename userId→accountId in TypeScript. 57 occurrences. Verify: 7 checks.",
        "type": "synthetic",
    },
    "02_implement_ico": {
        "label_cs": "Implement IČO (syntetická)", "label_en": "Implement IČO (synthetic)",
        "desc_cs": "Implementovat český algoritmus IČO validace. Verify: 5 checks + hidden tests.",
        "desc_en": "Implement Czech IČO validation algorithm. Verify: 5 checks + hidden tests.",
        "type": "synthetic",
    },
    "03_debug_order": {
        "label_cs": "Debug Order (syntetická)", "label_en": "Debug Order (synthetic)",
        "desc_cs": "Najít 2 záměrné bugy v OrderService. Bug B záměrně skrytý v názvech.",
        "desc_en": "Find 2 intentional bugs in OrderService. Bug B deliberately hidden in naming.",
        "type": "synthetic",
    },
    "05_find_validation_gaps": {
        "label_cs": "Find Validation Gaps (syntetická)", "label_en": "Find Validation Gaps (synthetic)",
        "desc_cs": "Najít a opravit mezery ve validaci dat. 5 checks.",
        "desc_en": "Find and fix data validation gaps. 5 checks.",
        "type": "synthetic",
    },
    "06_strict_scope": {
        "label_cs": "Strict Scope (syntetická)", "label_en": "Strict Scope (synthetic)",
        "desc_cs": "Přidat validaci pouze do create.ts, neměnit ostatní soubory.",
        "desc_en": "Add validation only to create.ts, don't modify other files.",
        "type": "synthetic",
    },
    "07_security_audit": {
        "label_cs": "Security Audit (syntetická)", "label_en": "Security Audit (synthetic)",
        "desc_cs": "Najít a opravit bezpečnostní chyby v Express API. 5 checks (SQLi, XSS, exposure).",
        "desc_en": "Find and fix security bugs in Express API. 5 checks (SQLi, XSS, exposure).",
        "type": "synthetic",
    },
    "08_async_bugs": {
        "label_cs": "Async Bugs (syntetická)", "label_en": "Async Bugs (synthetic)",
        "desc_cs": "Najít a opravit 4–5 async/Promise bugů v TypeScript pipeline.",
        "desc_en": "Find and fix 4–5 async/Promise bugs in TypeScript pipeline.",
        "type": "synthetic",
    },
    "swe_sympy__sympy-24909": {
        "label_cs": "SWE: sympy milli prefix", "label_en": "SWE: sympy milli prefix",
        "desc_cs": "milli*W == 1 vrací True místo False. SWE-bench Lite #24909.",
        "desc_en": "milli*W == 1 returns True instead of False. SWE-bench Lite #24909.",
        "type": "swe",
    },
    "swe_django__django-16910": {
        "label_cs": "SWE: django only()+select_related", "label_en": "SWE: django only()+select_related",
        "desc_cs": "only() nefunguje se select_related() na reverse OneToOneField. SWE-bench #16910.",
        "desc_en": "only() doesn't work with select_related() on reverse OneToOneField. SWE-bench #16910.",
        "type": "swe",
    },
    "swe_django__django-17051": {
        "label_cs": "SWE: django bulk_create", "label_en": "SWE: django bulk_create",
        "desc_cs": "bulk_create(update_conflicts=True) nevrací IDs. SWE-bench #17051.",
        "desc_en": "bulk_create(update_conflicts=True) doesn't return IDs. SWE-bench #17051.",
        "type": "swe",
    },
    "swe_django__django-16379": {
        "label_cs": "SWE: django cache race", "label_en": "SWE: django cache race",
        "desc_cs": "FileBasedCache.has_key race condition. SWE-bench #16379.",
        "desc_en": "FileBasedCache.has_key race condition. SWE-bench #16379.",
        "type": "swe",
    },
    "swe_django__django-16408": {
        "label_cs": "SWE: django FilteredRelation", "label_en": "SWE: django FilteredRelation",
        "desc_cs": "Multi-level FilteredRelation + select_related. SWE-bench #16408.",
        "desc_en": "Multi-level FilteredRelation + select_related. SWE-bench #16408.",
        "type": "swe",
    },
    "swe_django__django-16820": {
        "label_cs": "SWE: django migrations", "label_en": "SWE: django migrations",
        "desc_cs": "Migration squashing index_together → indexes. SWE-bench #16820.",
        "desc_en": "Migration squashing index_together → indexes. SWE-bench #16820.",
        "type": "swe",
    },
    "swe_django__django-14016": {
        "label_cs": "SWE: django 14016", "label_en": "SWE: django 14016",
        "desc_cs": "Django SWE-bench instance #14016.",
        "desc_en": "Django SWE-bench instance #14016.",
        "type": "swe",
    },
    "swe_sympy__sympy-22840": {
        "label_cs": "SWE: sympy cse() MatrixSymbol", "label_en": "SWE: sympy cse() MatrixSymbol",
        "desc_cs": "cse() extrahuje MatrixSymbol jako common subexpression. Multi-aspect bug. SWE-bench #22840.",
        "desc_en": "cse() extracts MatrixSymbol as common subexpression. Multi-aspect bug. SWE-bench #22840.",
        "type": "swe",
    },
    "swe_sympy__sympy-11400": {
        "label_cs": "SWE: sympy ccode sinc", "label_en": "SWE: sympy ccode sinc",
        "desc_cs": "ccode(sinc(x)) nefunguje. SWE-bench #11400.",
        "desc_en": "ccode(sinc(x)) doesn't work. SWE-bench #11400.",
        "type": "swe",
    },
    "swe_sympy__sympy-21612": {
        "label_cs": "SWE: sympy latex fractions", "label_en": "SWE: sympy latex fractions",
        "desc_cs": "Latex parsing frakcí vrací špatný výraz. SWE-bench #21612.",
        "desc_en": "Latex parsing of fractions yields wrong expression. SWE-bench #21612.",
        "type": "swe",
    },
    "swe_astropy__astropy-12907": {
        "label_cs": "SWE: astropy separability matrix", "label_en": "SWE: astropy separability matrix",
        "desc_cs": "separability_matrix nepočítá správně pro nested CompoundModels. SWE-bench #12907.",
        "desc_en": "separability_matrix doesn't compute correctly for nested CompoundModels. SWE-bench #12907.",
        "type": "swe",
    },
}


def load_runs():
    global INCOMPLETE_RUNS
    by = {}
    for d in RUNS_DIR.iterdir():
        if not d.is_dir():
            continue
        try:
            r = json.loads((d / "run_meta.json").read_text())
            v = json.loads((d / "verify_result.json").read_text())
            m = json.loads((d / "metrics.json").read_text())
        except Exception:
            INCOMPLETE_RUNS += 1
            continue
        provider = r.get("provider", "claude")
        model_label = f"{provider}:{r['model']}"
        key = (model_label, r["task"], r["effort"])
        by.setdefault(key, []).append({
            "t": r.get("wall_clock_ms", 0) // 1000,
            "c": round(m.get("total_cost_usd") or 0, 3),
            "tc": m.get("tool_call_count", 0),
            "score": v.get("score", 0),
            "fs": v.get("functional_score", v.get("score", 0)),
            "ss": v.get("scope_score", None),
            "ok": v.get("success", False),
            "in": m.get("input_tokens", 0),
            "out": m.get("output_tokens", 0),
            "cr": m.get("cache_read_input_tokens", 0),
            "cc": m.get("cache_creation_input_tokens", 0),
            "th": m.get("thinking_tokens", 0),
            "it": m.get("num_turns", 0),
        })
    return by


def build_data_js(runs_by):
    models = sorted(set(m for (m, t, e) in runs_by))
    out = ["const DATA={"]
    for model in models:
        out.append(json.dumps(model) + ":{")
        tasks = [t for t in TASK_META if any(k[0] == model and k[1] == t for k in runs_by)]
        for task in tasks:
            out.append(json.dumps(task) + ":{")
            for effort in EFFORTS:
                runs = runs_by.get((model, task, effort), [])
                if not runs:
                    continue
                rows = []
                for r in runs:
                    # packed: [t,c,tc,score,ok,in,out,cr,cc,th,it,functional_score,scope_score]
                    ok_val = "1" if r["ok"] else "0"
                    scope_val = "null" if r["ss"] is None else str(r["ss"])
                    rows.append("[" + ",".join(str(r[k]) for k in ["t","c","tc","score"]) + "," + ok_val + "," + ",".join(str(r[k]) for k in ["in","out","cr","cc","th","it","fs"]) + "," + scope_val + "]")
                out.append(effort + ":{runs:[" + ",".join(rows) + "]},")
            out.append("},")
        out.append("},")
    out.append("};")
    return "".join(out)


def build_checks_js(runs_by):
    # Aggregate check pass rates per (task, effort)
    checks = {}
    for (model, task, effort), runs in runs_by.items():
        check_names = set()
        for d in RUNS_DIR.iterdir():
            if not d.is_dir():
                continue
            try:
                r = json.loads((d / "run_meta.json").read_text())
                model_label = f"{r.get('provider', 'claude')}:{r['model']}"
                if model_label == model and r["task"] == task and r["effort"] == effort:
                    v = json.loads((d / "verify_result.json").read_text())
                    check_names.update(v.get("checks", {}).keys())
            except:
                pass
        if not check_names:
            continue
        task_checks = checks.setdefault(task, {})
        effort_checks = task_checks.setdefault(effort, {})
        for cn in check_names:
            passed = 0
            total = 0
            for d in RUNS_DIR.iterdir():
                if not d.is_dir():
                    continue
                try:
                    r = json.loads((d / "run_meta.json").read_text())
                    model_label = f"{r.get('provider', 'claude')}:{r['model']}"
                    if model_label == model and r["task"] == task and r["effort"] == effort:
                        v = json.loads((d / "verify_result.json").read_text())
                        c = v.get("checks", {}).get(cn, {})
                        if "passed" in c:
                            passed += 1 if c["passed"] else 0
                            total += 1
                except:
                    pass
            if total > 0:
                effort_checks[cn] = round(passed / total * 100)
    return "const CHECKS = " + json.dumps(checks, ensure_ascii=False).replace("\\", "\\\\") + ";"


def build_tools_js(runs_by):
    # Aggregate tool counts per (task, effort)
    tools = {}
    for (model, task, effort), runs in runs_by.items():
        tool_agg = {}
        for d in RUNS_DIR.iterdir():
            if not d.is_dir():
                continue
            try:
                r = json.loads((d / "run_meta.json").read_text())
                model_label = f"{r.get('provider', 'claude')}:{r['model']}"
                if model_label == model and r["task"] == task and r["effort"] == effort:
                    m = json.loads((d / "metrics.json").read_text())
                    for k, v in m.get("tool_call_count_by_type", {}).items():
                        tool_agg[k] = tool_agg.get(k, 0) + v
            except:
                pass
        if tool_agg:
            tools.setdefault(task, {})[effort] = dict(sorted(tool_agg.items(), key=lambda x: -x[1])[:8])
    return "const TOOLS = " + json.dumps(tools, ensure_ascii=False).replace("\\", "\\\\") + ";"


def main():
    runs_by = load_runs()
    data_js = build_data_js(runs_by)
    checks_js = build_checks_js(runs_by)
    tools_js = build_tools_js(runs_by)
    # Strip cs labels to save space; keep only en + type
    task_meta_js = json.dumps(
        {tid: {"l":m.get("label_en",""),"d":m.get("desc_en",""),"y":m.get("type","")} for tid, m in TASK_META.items()},
        ensure_ascii=False
    )
    task_order_js = json.dumps(list(TASK_META.keys()))

    all_runs = [r for runs in runs_by.values() for r in runs]
    total_runs = len(all_runs)
    total_pass = sum(1 for r in all_runs if r["ok"])
    total_cost = sum(r["c"] for r in all_runs)
    unique_tasks = len(set(t for (m, t, e) in runs_by))

    css = """
  :root{--low:#22c55e;--medium:#3b82f6;--high:#f59e0b;--max:#ef4444;--bg:#0f172a;--card:#1e293b;--border:#334155;--text:#f1f5f9;--muted:#94a3b8;--accent:#6366f1;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;line-height:1.6;}
  header{background:linear-gradient(135deg,#1e1b4b 0%,#0f172a 100%);border-bottom:1px solid var(--border);padding:2rem 0;}
  .container{max-width:1200px;margin:0 auto;padding:0 1.5rem;}
  header h1{font-size:2rem;font-weight:700;color:#fff;}
  .badge{display:inline-block;background:var(--accent);color:#fff;font-size:.75rem;font-weight:600;padding:.2rem .6rem;border-radius:99px;margin-left:.5rem;vertical-align:middle;}
  .controls{float:right;margin-top:.3rem;display:flex;gap:.5rem;}
  .controls button{background:var(--card);border:1px solid var(--border);color:var(--muted);padding:.3rem .8rem;border-radius:6px;cursor:pointer;font-size:.85rem;transition:.2s;}
  .controls button.active,.controls button:hover{background:var(--accent);color:#fff;border-color:var(--accent);}
  section{padding:2.5rem 0;border-bottom:1px solid var(--border);}
  h2{font-size:1.4rem;font-weight:700;margin-bottom:1rem;color:#fff;}
  h3{font-size:1.1rem;font-weight:600;margin-bottom:.6rem;color:#e2e8f0;}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;}
  .grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1.5rem;}
  .grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;}
  @media(max-width:900px){.grid2,.grid3{grid-template-columns:1fr 1fr;}}
  @media(max-width:700px){.grid2,.grid3,.grid4{grid-template-columns:1fr 1fr;}}
  @media(max-width:450px){.grid4{grid-template-columns:1fr;}}
  .card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.25rem 1.5rem;}
  .kpi{text-align:center;} .kpi .num{font-size:2.2rem;font-weight:800;color:var(--accent);}
  .kpi .label{font-size:.8rem;color:var(--muted);margin-top:.2rem;}
  .effort-label{display:inline-block;padding:.15rem .55rem;border-radius:6px;font-size:.78rem;font-weight:700;}
  .eff-low{background:#14532d;color:#86efac;} .eff-medium{background:#1e3a5f;color:#93c5fd;}
  .eff-high{background:#451a03;color:#fcd34d;} .eff-max{background:#450a0a;color:#fca5a5;}
  table{width:100%;border-collapse:collapse;font-size:.88rem;}
  th{background:#0f172a;color:var(--muted);font-weight:600;text-align:left;padding:.55rem .8rem;border-bottom:1px solid var(--border);}
  td{padding:.5rem .8rem;border-bottom:1px solid #1e293b;}
  tr:last-child td{border-bottom:none;} tr:hover td{background:rgba(99,102,241,.06);}
  .chart-wrap{position:relative;height:260px;}
  footer{padding:1.5rem 0;border-top:1px solid var(--border);} footer p{color:var(--muted);font-size:.85rem;}
  .task-row{cursor:pointer;}
  .task-row:hover td{background:rgba(99,102,241,.12);}
  .detail-panel{display:none;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.5rem;margin-top:1rem;}
  .detail-panel.active{display:block;}
  .close-btn{float:right;background:var(--card);border:1px solid var(--border);color:var(--muted);padding:.2rem .6rem;border-radius:6px;cursor:pointer;font-size:.85rem;}
  .close-btn:hover{background:var(--accent);color:#fff;border-color:var(--accent);}
  .tool-tag{display:inline-block;background:#0f172a;color:#94a3b8;padding:.1rem .4rem;border-radius:4px;font-size:.75rem;margin-right:.3rem;margin-bottom:.2rem;}
  .check-pass{color:#22c55e;font-weight:700;}
  .check-fail{color:#ef4444;font-weight:700;}
  .scatter-dot{transition:r .2s;}
"""

    body = (
        '<header><div class="container">'
        '<div class="controls"><button onclick="setLang(\'cs\')" id="btn-cs" class="active">CS</button>'
        '<button onclick="setLang(\'en\')" id="btn-en">EN</button></div>'
        '<h1>Agent Effort Benchmark <span class="badge">Phase 1+SWE</span></h1>'
        '<p id="hdr-sub">Empirické měření dopadu reasoning effort napříč providery a modely</p>'
        '</div></header>'
        '<div class="container">'

        # KPI
        '<section><div class="grid4">'
        '<div class="card kpi"><div class="num">' + str(total_runs) + '</div><div class="label" data-i18n="kpi_runs">celkem run&#367;</div></div>'
        '<div class="card kpi"><div class="num">' + str(unique_tasks) + '</div><div class="label" data-i18n="kpi_tasks">&uacute;lohy</div></div>'
        '<div class="card kpi"><div class="num">' + str(total_pass) + '/' + str(total_runs) + '</div><div class="label" data-i18n="kpi_pass">verify pass</div></div>'
        '<div class="card kpi"><div class="num">$' + f"{total_cost:.1f}" + '</div><div class="label" data-i18n="kpi_cost">celkem n&aacute;klady</div></div>'
        '<div class="card kpi"><div class="num">' + str(INCOMPLETE_RUNS) + '</div><div class="label">nekompletn&iacute; runy</div></div>'
        '</div></section>'

        # Overview table
        '<section><h2 data-i18n="overview_h">P&#345;ehled v&yacute;sledk&#367;</h2>'
        '<div class="card" style="overflow-x:auto;">'
        '<table><thead><tr>'
        '<th data-i18n="ov_task">&Uacute;loha</th>'
        '<th>low</th><th>medium</th><th>high</th><th>max</th>'
        '<th data-i18n="ov_signal">Effort gradient</th>'
        '</tr></thead><tbody id="overview-tbody"></tbody></table>'
        '</div>'
        # Dynamic detail panel
        '<div id="task-detail" class="detail-panel">'
        '<button class="close-btn" onclick="hideTaskDetail()">&times; ' + ("Zavřít") + '</button>'
        '<h2 id="detail-title"></h2>'
        '<p id="detail-desc" style="color:var(--muted);margin-bottom:1rem;font-size:.9rem"></p>'
        '<div class="grid2">'
        '<div class="card"><h3 data-i18n="detail_pass_h">Pass rate per effort</h3>'
        '<div class="chart-wrap"><canvas id="c-detail-pass"></canvas></div></div>'
        '<div class="card"><h3 data-i18n="detail_cost_h">Průměrná cena per effort</h3>'
        '<div class="chart-wrap"><canvas id="c-detail-cost"></canvas></div></div>'
        '</div>'
        '<div class="grid2" style="margin-top:1rem;">'
        '<div class="card"><h3 data-i18n="detail_tokens_h">Tokeny per effort</h3>'
        '<div class="chart-wrap"><canvas id="c-detail-tokens"></canvas></div></div>'
        '<div class="card"><h3 data-i18n="detail_iter_h">Iterace (turns) per effort</h3>'
        '<div class="chart-wrap"><canvas id="c-detail-iter"></canvas></div></div>'
        '</div>'
        '<div id="detail-checks-wrap" style="margin-top:1rem;display:none;">'
        '<div class="card"><h3 data-i18n="detail_checks_h">Per-check breakdown</h3>'
        '<div class="chart-wrap"><canvas id="c-detail-checks"></canvas></div></div>'
        '</div>'
        '<div class="card" style="margin-top:1rem;overflow-x:auto;">'
        '<table><thead><tr>'
        '<th>Effort</th><th data-i18n="col_n">n</th><th data-i18n="col_pass">Pass%</th>'
        '<th data-i18n="col_score">Avg score</th><th data-i18n="col_cost">Avg cost</th>'
        '<th data-i18n="col_wall">Avg wall</th><th data-i18n="col_tools">Avg tools</th>'
        '<th data-i18n="col_iter">Avg iter</th>'
        '<th data-i18n="col_tokens">Tokens</th>'
        '<th data-i18n="col_tools_breakdown">Tool breakdown</th>'
        '</tr></thead><tbody id="detail-tbody"></tbody></table>'
        '</div>'
        '</div></section>'

        # Pareto / Efficiency section
        '<section><h2 data-i18n="pareto_h">Efektivita: cena vs. kvalita</h2>'
        '<p style="color:var(--muted);margin-bottom:1rem;font-size:.9rem" data-i18n="pareto_desc">'
        'Každý bod = jeden run. Osy: cena (USD) vs. skóre (0–1). Ideální bod = levý horní roh (levné a kvalitní). Pareto frontier = zelená čára.</p>'
        '<div class="card"><div class="chart-wrap" style="height:400px;"><canvas id="c-pareto"></canvas></div></div>'
        '</section>'

        # Token analysis section
        '<section><h2 data-i18n="token_h">Tokeny a iterace napříč úlohami</h2>'
        '<div class="grid2">'
        '<div class="card"><h3 data-i18n="token_stack_h">Token consumption per effort (stacked)</h3>'
        '<div class="chart-wrap"><canvas id="c-token-stack"></canvas></div></div>'
        '<div class="card"><h3 data-i18n="iter_h">Průměrné iterace per effort</h3>'
        '<div class="chart-wrap"><canvas id="c-iter"></canvas></div></div>'
        '</div></section>'

        # Time & Efficiency section
        '<section><h2 data-i18n="time_h">Čas a efektivita</h2>'
        '<div class="grid3">'
        '<div class="card"><h3 data-i18n="wall_h">Průměrný wall time per effort</h3>'
        '<div class="chart-wrap"><canvas id="c-wall"></canvas></div></div>'
        '<div class="card"><h3 data-i18n="eff_h">Cena per úspěšný run</h3>'
        '<div class="chart-wrap"><canvas id="c-eff"></canvas></div></div>'
        '<div class="card"><h3 data-i18n="sr_h">Success rate podle typu úlohy</h3>'
        '<div class="chart-wrap"><canvas id="c-sr-type"></canvas></div></div>'
        '</div></section>'

        # SWE section
        '<section><h2 data-i18n="swe_h">SWE-bench v&yacute;sledky</h2>'
        '<p style="color:var(--muted);margin-bottom:1rem;font-size:.9rem" data-i18n="swe_desc">Re&aacute;ln&eacute; bugy z open-source projekt&#367;.</p>'
        '<div class="card" style="overflow-x:auto;">'
        '<table><thead><tr>'
        '<th data-i18n="swe_instance">Instance</th>'
        '<th>low</th><th>medium</th><th>high</th><th>max</th>'
        '<th data-i18n="swe_finding">Finding</th>'
        '</tr></thead><tbody id="swe-tbody"></tbody></table>'
        '</div></section>'

        # Synthetic
        '<section><h2 data-i18n="synth_h">Syntetick&eacute; &uacute;lohy</h2>'
        '<p style="color:var(--muted);margin-bottom:1rem;font-size:.9rem" data-i18n="synth_desc">'
        'Na dob&#345;e specifikovan&yacute;ch &uacute;loh&aacute;ch jsou v&scaron;echny effort &uacute;rovn&#283; funk&#269;n&#283; ekvivalentn&iacute;.</p>'
        '<div class="grid2">'
        '<div class="card"><h3 data-i18n="synth_scope_h">Pass rate &mdash; 06_strict_scope</h3>'
        '<div class="chart-wrap"><canvas id="c-scope-pass"></canvas></div></div>'
        '<div class="card"><h3 data-i18n="synth_cost_h">Průměrná cena &mdash; 01_rename</h3>'
        '<div class="chart-wrap"><canvas id="c-rename-cost"></canvas></div></div>'
        '</div></section>'

        # Findings
        '<section><h2 data-i18n="findings_h">Kl&iacute;&#269;ov&aacute; zji&scaron;t&#283;n&iacute;</h2>'
        '<div class="grid2">'
        '<div class="card"><h3>&#128161; <span data-i18n="f1_h">SWE-bench diferenciuje effort</span></h3>'
        '<p style="color:#cbd5e1;font-size:.88rem" data-i18n="f1_p">Na re&aacute;ln&yacute;ch bugech (django-16910) low/medium konzistentn&#283; sel&aacute;vaj&iacute;, high usp&iacute;v&aacute;. Na jednoduch&yacute;ch bugech i low sta&#269;&iacute;.</p></div>'
        '<div class="card"><h3>&#128161; <span data-i18n="f2_h">Max &ne; lep&scaron;&iacute; v&yacute;sledek</span></h3>'
        '<p style="color:#cbd5e1;font-size:.88rem" data-i18n="f2_p">Max effort stoj&iacute; 2&ndash;4&times; v&iacute;ce ne&#382; high, ale v&yacute;sledek je stejn&yacute;. High je sweet spot pro re&aacute;ln&eacute; bugy.</p></div>'
        '<div class="card"><h3>&#9888;&#65039; <span data-i18n="f3_h">Debug bez testu = nulov&yacute; efekt</span></h3>'
        '<p style="color:#cbd5e1;font-size:.88rem" data-i18n="f3_p">03_debug_order Bug B nebyl nalezen ani max effortem. Failing testy jsou nezbytn&yacute; guidance.</p></div>'
        '<div class="card"><h3>&#9888;&#65039; <span data-i18n="f4_h">Python 3.14 limituje SWE-bench</span></h3>'
        '<p style="color:#cbd5e1;font-size:.88rem" data-i18n="f4_p">Pre-2022 projekty jsou nekompatibiln&iacute; (odstra&#328;eny moduly cgi, distutils). Pou&#382;&iacute;vejte Django 4.2+ / Sympy 1.11+.</p></div>'
        '</div></section>'

        # Recommendations
        '<section><h2 data-i18n="rec_h">Doporu&#269;en&iacute;</h2>'
        '<div class="card"><table><thead><tr>'
        '<th data-i18n="rec_uc">Use case</th><th data-i18n="rec_effort">Effort</th><th data-i18n="rec_why">Pro&#269;</th>'
        '</tr></thead><tbody id="rec-tbody"></tbody></table></div></section>'

        '</div>'
        '<footer><div class="container"><p>Claude Code Effort Benchmark &middot; Phase 1+SWE &middot; 2026-05-16 &middot; claude-opus-4-7</p></div></footer>'
    )

    js = """
const EFFORTS = ['low','medium','high','max'];
const COLORS = """ + COLORS_JS + """;
const TASK_META = """ + task_meta_js + """;
const TASK_ORDER = """ + task_order_js + """;
""" + data_js + """
""" + checks_js + """
""" + tools_js + """


const SWE_FINDINGS = {
  cs: {
    'swe_sympy__sympy-24909': 'Low selhal, medium+ opravil. One-file fix.',
    'swe_django__django-16910': 'Low/medium selhávají, high uspívá.',
    'swe_django__django-17051': 'I low opravil. Příliš snadné.',
    'swe_django__django-16379': 'Cache race condition — snadné, low občas stačí.',
    'swe_django__django-16408': 'Ostrý práh: low 25%, medium+ 100%. Multi-level ORM bug.',
    'swe_django__django-16820': 'Ostrý práh: low 25%, medium+ ~100%. Migration squashing.',
    'swe_django__django-14016': 'Jeden run, low selhal.',
    'swe_sympy__sympy-22840': 'Pozvolný gradient — 2-aspect bug, max 60% full fix, medium/high stuck na 2/3.',
    'swe_sympy__sympy-11400': 'Nedostatek dat (n=2).',
    'swe_sympy__sympy-21612': 'Nedostatek dat (n=2).',
    'swe_astropy__astropy-12907': 'C extensions — n=5, všechny selhaly.',
  },
  en: {
    'swe_sympy__sympy-24909': 'Low failed, medium+ fixed. One-file fix.',
    'swe_django__django-16910': 'Low/medium fail, high succeeds.',
    'swe_django__django-17051': 'Even low fixed it. Too easy.',
    'swe_django__django-16379': 'Cache race condition — easy, low sometimes works.',
    'swe_django__django-16408': 'Sharp threshold: low 25%, medium+ 100%. Multi-level ORM bug.',
    'swe_django__django-16820': 'Sharp threshold: low 25%, medium+ ~100%. Migration squashing.',
    'swe_django__django-14016': 'Single run, low failed.',
    'swe_sympy__sympy-22840': 'Gradual gradient — 2-aspect bug, max 60% full fix, medium/high stuck at 2/3.',
    'swe_sympy__sympy-11400': 'Insufficient data (n=2).',
    'swe_sympy__sympy-21612': 'Insufficient data (n=2).',
    'swe_astropy__astropy-12907': 'C extensions — n=5, all failed.',
  },
};

const REC_ROWS = {
  cs: [
    ['Refaktoring, rename, bulk změny','low','100% úspěšnost, nejlevnější, nejrychlejší'],
    ['Implementace dle specifikace','low / medium','Srovnatelné výsledky; low je dobrý default'],
    ['Reálné bugy z codebase','high','Low/medium selhávají; high sweet spot (potvrzen n=3)'],
    ['Scope compliance','max','Konzistentnější dodržení hranic zadání'],
    ['Debugging bez failing testů','—','Žádný effort nepomůže — nejdřív napiš testy'],
  ],
  en: [
    ['Refactoring, rename, bulk changes','low','100% success rate, cheapest, fastest'],
    ['Implementation from spec','low / medium','Comparable results; low is a good default'],
    ['Real bugs from codebase','high','Low/medium fail; high sweet spot (n=3 confirmed)'],
    ['Scope compliance','max','More consistent boundary respect'],
    ['Debugging without failing tests','—','No effort helps — write tests first'],
  ],
};

const i18n = {
  cs: {
    kpi_runs:'celkem runů', kpi_tasks:'úlohy', kpi_pass:'verify pass', kpi_cost:'celkem náklady',
    overview_h:'Přehled výsledků', ov_task:'Úloha', ov_signal:'Effort gradient',
    detail_pass_h:'Pass rate per effort', detail_cost_h:'Průměrná cena per effort',
    detail_tokens_h:'Tokeny per effort', detail_iter_h:'Iterace (turns) per effort',
    detail_checks_h:'Per-check breakdown',
    pareto_h:'Efektivita: cena vs. kvalita', pareto_desc:'Každý bod = jeden run. Ideální = levý horní roh.',
    token_h:'Tokeny a iterace napříč úlohami', token_stack_h:'Token consumption per effort (stacked)',
    iter_h:'Průměrné iterace per effort',
    time_h:'Čas a efektivita', wall_h:'Průměrný wall time (s)', eff_h:'Cena per úspěšný run', sr_h:'Success rate podle typu',
    swe_h:'SWE-bench výsledky', swe_desc:'Reálné bugy z open-source projektů.',
    swe_instance:'Instance', swe_finding:'Finding',
    synth_h:'Syntetické úlohy',
    synth_desc:'Na dobře specifikovaných úlohách jsou všechny effort úrovně funkčně ekvivalentní.',
    synth_scope_h:'Pass rate — 06_strict_scope', synth_cost_h:'Průměrná cena — 01_rename',
    findings_h:'Klíčová zjištění',
    f1_h:'SWE-bench diferenciuje effort',
    f1_p:'Na reálných bugech (django-16910) low/medium konzistentně selhávají, high uspívá.',
    f2_h:'Max ≠ lepší výsledek',
    f2_p:'Max effort stojí 2–4× více než high, ale výsledek je stejný.',
    f3_h:'Debug bez testu = nulový efekt',
    f3_p:'Bug B nebyl nalezen ani max effortem.',
    f4_h:'Python 3.14 limituje SWE-bench',
    f4_p:'Pre-2022 projekty nekompatibilní — volte Django 4.2+ / Sympy 1.11+.',
    rec_h:'Doporučení', rec_uc:'Use case', rec_effort:'Effort', rec_why:'Proč',
    col_n:'n', col_pass:'Pass%', col_score:'Avg score', col_cost:'Avg cost',
    col_wall:'Avg wall', col_tools:'Avg tools', col_iter:'Avg iter', col_tokens:'Tokens',
    col_tools_breakdown:'Nástroje',
    hdr_sub:'Empirické měření dopadu parametru --effort · claude-opus-4-7',
  },
  en: {
    kpi_runs:'total runs', kpi_tasks:'tasks', kpi_pass:'verify pass', kpi_cost:'total cost',
    overview_h:'Results Overview', ov_task:'Task', ov_signal:'Effort gradient',
    detail_pass_h:'Pass rate per effort', detail_cost_h:'Avg cost per effort',
    detail_tokens_h:'Tokens per effort', detail_iter_h:'Iterations per effort',
    detail_checks_h:'Per-check breakdown',
    pareto_h:'Efficiency: cost vs. quality', pareto_desc:'Each dot = one run. Ideal = top-left corner.',
    token_h:'Tokens and iterations across tasks', token_stack_h:'Token consumption per effort (stacked)',
    iter_h:'Avg iterations per effort',
    time_h:'Time and efficiency', wall_h:'Avg wall time (s)', eff_h:'Cost per successful run', sr_h:'Success rate by task type',
    swe_h:'SWE-bench Results', swe_desc:'Real bugs from open-source projects.',
    swe_instance:'Instance', swe_finding:'Finding',
    synth_h:'Synthetic Tasks',
    synth_desc:'On well-specified tasks all effort levels are functionally equivalent.',
    synth_scope_h:'Pass rate — 06_strict_scope', synth_cost_h:'Avg cost — 01_rename',
    findings_h:'Key Findings',
    f1_h:'SWE-bench differentiates effort',
    f1_p:'On real bugs (django-16910) low/medium consistently fail, high succeeds.',
    f2_h:'Max ≠ better result',
    f2_p:'Max effort costs 2–4× more than high with the same result.',
    f3_h:'Debug without tests = zero effect',
    f3_p:'Bug B was not found even at max effort.',
    f4_h:'Python 3.14 limits SWE-bench',
    f4_p:'Pre-2022 projects incompatible — use Django 4.2+ / Sympy 1.11+.',
    rec_h:'Recommendations', rec_uc:'Use case', rec_effort:'Effort', rec_why:'Why',
    col_n:'n', col_pass:'Pass%', col_score:'Avg score', col_cost:'Avg cost',
    col_wall:'Avg wall', col_tools:'Avg tools', col_iter:'Avg iter', col_tokens:'Tokens',
    col_tools_breakdown:'Tools',
    hdr_sub:'Empirical measurement of reasoning effort across providers and models',
  },
};

let lang = navigator.language.startsWith('en') ? 'en' : 'cs';
const charts = {};
const model = Object.keys(DATA)[0];
const _RF=['t','c','tc','score','ok','in','out','cr','cc','th','it','fs','ss'];
function _U(a){return Object.fromEntries(_RF.map((k,i)=>[k,a[i]]));}
for(const M in DATA)for(const T in DATA[M])for(const E in DATA[M][T])
  if(DATA[M][T][E].runs)DATA[M][T][E].runs=DATA[M][T][E].runs.map(_U);

function setLang(l) {
  lang = l;
  document.getElementById('btn-cs').classList.toggle('active', l==='cs');
  document.getElementById('btn-en').classList.toggle('active', l==='en');
  document.getElementById('hdr-sub').textContent = i18n[l].hdr_sub;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const k = el.dataset.i18n; if (i18n[l][k]) el.innerHTML = i18n[l][k];
  });
  renderAll();
}

function t(k) { return i18n[lang][k] || k; }
function avg(a) { return a.length ? a.reduce((s,v)=>s+v,0)/a.length : 0; }
function pct(a) { return a.length ? Math.round(a.filter(v=>v).length/a.length*100) : 0; }
function effortBadge(e) { return '<span class="effort-label eff-'+e+'">'+e+'</span>'; }
function passColor(r) { return r>=80?'#22c55e':r>=40?'#f59e0b':'#ef4444'; }

function makeBar(id, labels, vals, colors, yLabel, yMax, stacked) {
  if (charts[id]) charts[id].destroy();
  const ctx = document.getElementById(id);
  if (!ctx) return;
  const datasets = stacked ? vals : [{data:vals,backgroundColor:colors.map(c=>c+'bb'),borderColor:colors,borderWidth:2,borderRadius:6}];
  charts[id] = new Chart(ctx.getContext('2d'), {
    type:'bar',
    data:{labels,datasets},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:!!stacked, labels:{color:'#94a3b8'}}},
      scales:{
        x:{grid:{color:'#1e293b'},ticks:{color:'#94a3b8'}},
        y:{grid:{color:'#1e293b'},ticks:{color:'#94a3b8'},beginAtZero:true,
          ...(yMax!=null?{max:yMax}:{}),
          ...(yLabel?{title:{display:true,text:yLabel,color:'#64748b'}}:{})
        }
      }
    }
  });
}

function makeLine(id, labels, datasets, yLabel) {
  if (charts[id]) charts[id].destroy();
  const ctx = document.getElementById(id);
  if (!ctx) return;
  charts[id] = new Chart(ctx.getContext('2d'), {
    type:'line',
    data:{labels,datasets},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:true, labels:{color:'#94a3b8'}}},
      scales:{
        x:{grid:{color:'#1e293b'},ticks:{color:'#94a3b8'}},
        y:{grid:{color:'#1e293b'},ticks:{color:'#94a3b8'},beginAtZero:true,
          ...(yLabel?{title:{display:true,text:yLabel,color:'#64748b'}}:{})
        }
      }
    }
  });
}

function makeScatter(id, datasets, xLabel, yLabel) {
  if (charts[id]) charts[id].destroy();
  const ctx = document.getElementById(id);
  if (!ctx) return;
  charts[id] = new Chart(ctx.getContext('2d'), {
    type:'scatter',
    data:{datasets},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:true, labels:{color:'#94a3b8', boxWidth:10}}, tooltip:{callbacks:{label:(c)=>c.dataset.label+' run '+c.dataIndex+': $'+c.parsed.x.toFixed(3)+' / score '+c.parsed.y.toFixed(2)}}},
      scales:{
        x:{grid:{color:'#1e293b'},ticks:{color:'#94a3b8'},
          ...(xLabel?{title:{display:true,text:xLabel,color:'#64748b'}}:{})},
        y:{grid:{color:'#1e293b'},ticks:{color:'#94a3b8'},min:0,max:1.05,
          ...(yLabel?{title:{display:true,text:yLabel,color:'#64748b'}}:{})
        }
      }
    }
  });
}

function renderOverview() {
  const d = DATA[model] || {};
  const tbody = document.getElementById('overview-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  TASK_ORDER.forEach(tid => {
    if (!d[tid]) return;
    const meta = TASK_META[tid];
    const cells = EFFORTS.map(e => {
      const runs = (d[tid][e]||{}).runs||[];
      if (!runs.length) return '<td style="color:var(--muted)">—</td>';
      const p = pct(runs.map(r=>r.ok));
      return '<td><span style="color:'+passColor(p)+';font-weight:700">'+p+'%</span>'
           + '<br><small style="color:var(--muted)">n='+runs.length+'</small></td>';
    });
    const rates = EFFORTS.map(e=>{const rr=(d[tid][e]||{}).runs||[];return rr.length?pct(rr.map(r=>r.ok)):null;}).filter(v=>v!==null);
    const gradient = rates.length>=2 && Math.max(...rates)-Math.min(...rates)>=30 ? '&#128200; gradient' : '&#10134; flat';
    const tag = meta.y==='swe' ? '&#128300;' : '&#129514;';
    tbody.innerHTML += '<tr class="task-row" data-task-id="'+tid+'"><td><strong>'+tag+' '+meta.l+'</strong>'
      +'<br><small style="color:var(--muted)">'+meta.d+'</small></td>'
      +cells.join('')+'<td>'+gradient+'</td></tr>';
  });
  // Delegate click handler (attached once)
  if (!tbody._hasClick) {
    tbody._hasClick = true;
    tbody.addEventListener('click', (e) => {
      const row = e.target.closest('.task-row');
      if (row && row.dataset.taskId) showTaskDetail(row.dataset.taskId);
    });
  }
}

function showTaskDetail(tid) {
  const panel = document.getElementById('task-detail');
  const meta = TASK_META[tid];
  if (!meta) return;
  document.getElementById('detail-title').innerHTML = (meta.y==='swe'?'&#128300; ':'&#129514; ')+meta.l;
  document.getElementById('detail-desc').textContent = meta.d;
  panel.classList.add('active');
  panel.scrollIntoView({behavior:'smooth', block:'start'});
  renderTaskDetail(tid);
}

function hideTaskDetail() {
  document.getElementById('task-detail').classList.remove('active');
}

function renderTaskDetail(tid) {
  const d = (DATA[model]||{})[tid];
  if (!d) return;
  const tbody = document.getElementById('detail-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  const passVals=[], costVals=[], iterVals=[], tokenDatasets=[];
  const tokenColors = ['#6366f1','#22c55e','#3b82f6','#f59e0b','#ef4444'];
  const tokenLabels = ['input','output','cache read','cache creation','thinking'];

  // Per-check analysis from aggregated CHECKS
  const taskChecks = CHECKS[tid] || {};
  const checkNames = new Set();
  EFFORTS.forEach(e => { if (taskChecks[e]) Object.keys(taskChecks[e]).forEach(k=>checkNames.add(k)); });
  const hasChecks = checkNames.size > 0;

  const checkPassRates = {};
  checkNames.forEach(cn => { checkPassRates[cn] = {}; });

  EFFORTS.forEach(e => {
    const runs = (d[e]||{}).runs||[];
    if (!runs.length) { passVals.push(0); costVals.push(0); iterVals.push(0); tokenDatasets.push([0,0,0,0,0]); return; }
    const p = pct(runs.map(r=>r.ok));
    const ac = avg(runs.map(r=>r.c));
    const aw = avg(runs.map(r=>r.t));
    const at = avg(runs.map(r=>r.tc));
    const ai = avg(runs.map(r=>r.it));
    const as_ = avg(runs.map(r=>r.score));
    const aIn = avg(runs.map(r=>r.in));
    const aOut = avg(runs.map(r=>r.out));
    const aCr = avg(runs.map(r=>r.cr));
    const aCc = avg(runs.map(r=>r.cc));
    const aTh = avg(runs.map(r=>r.th));

    // Check pass rates per effort
    checkNames.forEach(cn => {
      checkPassRates[cn][e] = (taskChecks[e] && taskChecks[e][cn] != null) ? taskChecks[e][cn] : null;
    });

    passVals.push(p); costVals.push(ac); iterVals.push(ai);
    tokenDatasets.push([aIn, aOut, aCr, aCc, aTh]);

    const toolAgg = TOOLS[tid] && TOOLS[tid][e] ? TOOLS[tid][e] : {};
    const toolTags = Object.entries(toolAgg)
      .sort((a,b)=>b[1]-a[1])
      .map(([k,v])=>'<span class="tool-tag">'+k+'='+v+'</span>')
      .join('') || '<span style="color:var(--muted)">—</span>';

    const tokensStr = Math.round(aIn+aOut+aCr+aCc+aTh).toLocaleString() + ' total<br><small style="color:var(--muted)">in='+Math.round(aIn)+' out='+Math.round(aOut)+'</small>';

    tbody.innerHTML += '<tr>'
      +'<td>'+effortBadge(e)+'</td>'
      +'<td>'+runs.length+'</td>'
      +'<td><strong style="color:'+passColor(p)+'">'+p+'%</strong></td>'
      +'<td>'+as_.toFixed(2)+'</td>'
      +'<td>$'+ac.toFixed(3)+'</td>'
      +'<td>'+Math.round(aw)+'s</td>'
      +'<td>'+Math.round(at)+'</td>'
      +'<td>'+Math.round(ai)+'</td>'
      +'<td>'+tokensStr+'</td>'
      +'<td>'+toolTags+'</td>'
      +'</tr>';
  });

  makeBar('c-detail-pass', EFFORTS, passVals, EFFORTS.map(e=>COLORS[e]), 'pass %', 100);
  makeBar('c-detail-cost', EFFORTS, costVals, EFFORTS.map(e=>COLORS[e]), 'USD', null);
  makeBar('c-detail-tokens', EFFORTS, tokenLabels.map((_,i)=>({
    label:tokenLabels[i],
    data:tokenDatasets.map(d=>d[i]),
    backgroundColor:tokenColors[i]+'bb',
    borderColor:tokenColors[i],
    borderWidth:1,
    borderRadius:4,
  })), null, 'tokens', null, true);
  makeBar('c-detail-iter', EFFORTS, iterVals, EFFORTS.map(e=>COLORS[e]), 'turns', null);

  // Render checks breakdown if available
  const checksWrap = document.getElementById('detail-checks-wrap');
  if (hasChecks && checkNames.size > 0) {
    checksWrap.style.display = 'block';
    const checkLabels = Array.from(checkNames);
    const checkDatasets = EFFORTS.map(e => ({
      label: e,
      data: checkLabels.map(cn => checkPassRates[cn][e] != null ? checkPassRates[cn][e] : 0),
      backgroundColor: COLORS[e]+'bb',
      borderColor: COLORS[e],
      borderWidth: 1,
      borderRadius: 4,
    }));
    makeBar('c-detail-checks', checkLabels, checkDatasets, null, 'pass %', 100, true);
  } else {
    checksWrap.style.display = 'none';
  }
}

function renderSWE() {
  const d = DATA[model] || {};
  const tbody = document.getElementById('swe-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  const SWE_TASKS = TASK_ORDER.filter(tid => TASK_META[tid].y==='swe' && d[tid]);
  SWE_TASKS.forEach(tid => {
    const meta = TASK_META[tid];
    const cells = EFFORTS.map(e => {
      const runs = (d[tid][e]||{}).runs||[];
      if (!runs.length) return '<td style="color:var(--muted)">—</td>';
      const p = pct(runs.map(r=>r.ok));
      return '<td><span style="color:'+passColor(p)+';font-weight:700">'+p+'%</span>'
           + ' <small style="color:var(--muted)">n='+runs.length+'</small></td>';
    });
    const finding = (SWE_FINDINGS[lang]||{})[tid]||'';
    tbody.innerHTML += '<tr><td><strong>'+meta.l+'</strong></td>'
      +cells.join('')+'<td style="color:#94a3b8;font-size:.85rem">'+finding+'</td></tr>';
  });
}

function renderPareto() {
  const d = DATA[model] || {};
  const datasets = [];
  EFFORTS.forEach(e => {
    const points = [];
    TASK_ORDER.forEach(tid => {
      if (!d[tid] || !d[tid][e]) return;
      (d[tid][e].runs||[]).forEach((r,i) => {
        points.push({x:r.c, y:r.score, task:tid, run:i+1});
      });
    });
    if (points.length) {
      datasets.push({
        label: e,
        data: points,
        backgroundColor: COLORS[e]+'aa',
        borderColor: COLORS[e],
        borderWidth: 1,
        pointRadius: 5,
        pointHoverRadius: 7,
      });
    }
  });
  makeScatter('c-pareto', datasets, 'cost USD', 'score');
}

function renderTokenAnalysis() {
  const d = DATA[model] || {};
  const tokenColors = ['#6366f1','#22c55e','#3b82f6','#f59e0b','#ef4444'];
  const tokenLabels = ['input','output','cache read','cache creation','thinking'];

  // Overall token stacked bar per effort
  const tokenDatasets = tokenLabels.map((_,ti) => ({
    label: tokenLabels[ti],
    data: EFFORTS.map(e => {
      let sum=0, count=0;
      TASK_ORDER.forEach(tid => {
        if (!d[tid] || !d[tid][e]) return;
        (d[tid][e].runs||[]).forEach(r => { sum += r[['in','out','cr','cc','th'][ti]]; count++; });
      });
      return count ? sum/count : 0;
    }),
    backgroundColor: tokenColors[ti]+'bb',
    borderColor: tokenColors[ti],
    borderWidth: 1,
    borderRadius: 4,
  }));
  makeBar('c-token-stack', EFFORTS, tokenDatasets, null, 'avg tokens', null, true);

  // Iterations per effort
  const iterVals = EFFORTS.map(e => {
    let sum=0, count=0;
    TASK_ORDER.forEach(tid => {
      if (!d[tid] || !d[tid][e]) return;
      (d[tid][e].runs||[]).forEach(r => { sum += r.it; count++; });
    });
    return count ? sum/count : 0;
  });
  makeBar('c-iter', EFFORTS, iterVals, EFFORTS.map(e=>COLORS[e]), 'avg turns', null);
}

function renderTimeEfficiency() {
  const d = DATA[model]||{};
  // Wall clock time per effort
  const wallVals = EFFORTS.map(e => {
    let sum=0, count=0;
    TASK_ORDER.forEach(tid => {
      if (!d[tid] || !d[tid][e]) return;
      (d[tid][e].runs||[]).forEach(r => { sum += r.t; count++; });
    });
    return count ? sum/count : 0;
  });
  makeBar('c-wall', EFFORTS, wallVals, EFFORTS.map(e=>COLORS[e]), 'seconds', null);

  // Cost per successful run
  const effVals = EFFORTS.map(e => {
    let costSum=0, successCount=0;
    TASK_ORDER.forEach(tid => {
      if (!d[tid] || !d[tid][e]) return;
      (d[tid][e].runs||[]).forEach(r => { if (r.ok) { costSum += r.c; successCount++; } });
    });
    return successCount ? costSum/successCount : 0;
  });
  makeBar('c-eff', EFFORTS, effVals, EFFORTS.map(e=>COLORS[e]), 'USD', null);

  // Success rate by task type (synthetic vs SWE)
  const typeLabels = ['synthetic', 'swe'];
  const typeDatasets = EFFORTS.map(e => ({
    label: e,
    data: typeLabels.map(t => {
      let passed=0, total=0;
      TASK_ORDER.forEach(tid => {
        if (TASK_META[tid].y !== t) return;
        if (!d[tid] || !d[tid][e]) return;
        (d[tid][e].runs||[]).forEach(r => { if (r.ok) passed++; total++; });
      });
      return total ? Math.round(passed/total*100) : 0;
    }),
    backgroundColor: COLORS[e]+'bb',
    borderColor: COLORS[e],
    borderWidth: 1,
    borderRadius: 4,
  }));
  makeBar('c-sr-type', typeLabels, typeDatasets, null, 'pass %', 100, true);
}

function renderSynthCharts() {
  const d = DATA[model]||{};
  const scope = d['06_strict_scope'];
  if (scope) {
    const v = EFFORTS.map(e=>{const rr=(scope[e]||{}).runs||[];return pct(rr.map(r=>r.ok));});
    makeBar('c-scope-pass', EFFORTS, v, EFFORTS.map(e=>COLORS[e]), 'pass %', 100);
  }
  const rename = d['01_rename'];
  if (rename) {
    const v = EFFORTS.map(e=>{const rr=(rename[e]||{}).runs||[];return avg(rr.map(r=>r.c));});
    makeBar('c-rename-cost', EFFORTS, v, EFFORTS.map(e=>COLORS[e]), 'USD', null);
  }
}

function renderRec() {
  const tbody = document.getElementById('rec-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  (REC_ROWS[lang]||[]).forEach(([uc, eff, why]) => {
    const effHtml = eff==='—' ? '<span style="color:var(--muted)">—</span>'
      : eff.split('/').map(e=>effortBadge(e.trim())).join(' ');
    tbody.innerHTML += '<tr><td>'+uc+'</td><td>'+effHtml+'</td><td style="color:#94a3b8">'+why+'</td></tr>';
  });
}

function renderAll() {
  const errs=[];
  [
    renderOverview, renderSWE, renderPareto, renderTokenAnalysis,
    renderTimeEfficiency, renderSynthCharts, renderRec
  ].forEach(fn=>{ try{fn();}catch(e){errs.push(fn.name+': '+e.message);} });
  document.querySelectorAll('[data-i18n]').forEach(el=>{const k=el.dataset.i18n;if(i18n[lang][k])el.innerHTML=i18n[lang][k];});
  if(errs.length){const d=document.createElement('div');d.style.cssText='position:fixed;top:0;left:0;right:0;background:#450a0a;color:#fca5a5;padding:1rem;z-index:9999;font-family:monospace;white-space:pre-wrap;';d.textContent='JS ERRORS:\n'+errs.join('\n');document.body.appendChild(d);}
}

document.addEventListener('DOMContentLoaded', ()=>{ try{setLang(lang);}catch(e){const d=document.createElement('div');d.style.cssText='position:fixed;top:0;left:0;right:0;background:#450a0a;color:#fca5a5;padding:1rem;z-index:9999;font-family:monospace;';d.textContent='INIT ERROR: '+e.message;document.body.appendChild(d);} });
"""

    html = (
        "<!DOCTYPE html>\n<html lang=\"cs\">\n<head>\n"
        "<meta charset=\"UTF-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        "<title>Claude Code Effort Benchmark</title>\n"
        "<script src=\"https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js\"></script>\n"
        "<style>" + css + "</style>\n"
        "</head>\n<body>\n"
        + body + "\n"
        "<script>\n" + js + "\n</script>\n"
        "</body>\n</html>"
    )

    # Write as val.town HTTP handler
    val_ts = (
        "// Claude Code Effort Benchmark — Phase 1+SWE\n"
        "// Auto-generated by scripts/generate_report.py\n"
        "export default async function(req: Request): Promise<Response> {\n"
        "  const html = `" + html.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$") + "`;\n"
        "  return new Response(html, { headers: {'content-type': 'text/html;charset=utf-8'} });\n"
        "}\n"
    )

    OUT.write_text(val_ts, encoding="utf-8")
    print(f"✓ Report written to {OUT}")
    print(f"  {total_runs} runs | {unique_tasks} tasks | ${total_cost:.2f} total cost")


if __name__ == "__main__":
    main()
