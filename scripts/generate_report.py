#!/usr/bin/env python3
"""Generate val.town report from results/runs/ directory."""
import json, statistics
from pathlib import Path

REPO = Path(__file__).parent.parent
RUNS_DIR = REPO / "results/runs"
OUT = REPO / "results/report.val.ts"

EFFORTS = ["low", "medium", "high", "max"]
COLORS_JS = "{low:'#22c55e',medium:'#3b82f6',high:'#f59e0b',max:'#ef4444'}"

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
    "06_strict_scope": {
        "label_cs": "Strict Scope (syntetická)", "label_en": "Strict Scope (synthetic)",
        "desc_cs": "Přidat validaci pouze do create.ts, neměnit ostatní soubory.",
        "desc_en": "Add validation only to create.ts, don't modify other files.",
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
    "swe_sympy__sympy-22840": {
        "label_cs": "SWE: sympy cse() MatrixSymbol", "label_en": "SWE: sympy cse() MatrixSymbol",
        "desc_cs": "cse() extrahuje MatrixSymbol jako common subexpression. Multi-aspect bug. SWE-bench #22840.",
        "desc_en": "cse() extracts MatrixSymbol as common subexpression. Multi-aspect bug. SWE-bench #22840.",
        "type": "swe",
    },
}

def load_runs():
    by = {}
    for d in RUNS_DIR.iterdir():
        if not d.is_dir(): continue
        try:
            r = json.loads((d / "run_meta.json").read_text())
            v = json.loads((d / "verify_result.json").read_text())
            m = json.loads((d / "metrics.json").read_text())
        except Exception:
            continue
        key = (r["model"], r["task"], r["effort"])
        by.setdefault(key, []).append({
            "t": r["wall_clock_ms"] // 1000,
            "c": round(m["total_cost_usd"], 4),
            "tc": m["tool_call_count"],
            "score": v["score"],
            "ok": v["success"],
        })
    return by

def build_data_js(runs_by):
    models = sorted(set(m for (m, t, e) in runs_by))
    out = ["const DATA = {"]
    for model in models:
        out.append("  " + json.dumps(model) + ": {")
        tasks = [t for t in TASK_META if any(k[0] == model and k[1] == t for k in runs_by)]
        for task in tasks:
            out.append("    " + json.dumps(task) + ": {")
            for effort in EFFORTS:
                runs = runs_by.get((model, task, effort), [])
                if not runs: continue
                runs_js = ", ".join(
                    "{t:" + str(r["t"]) + ",c:" + str(r["c"]) + ",tc:" + str(r["tc"])
                    + ",score:" + str(r["score"]) + ",ok:" + ("true" if r["ok"] else "false") + "}"
                    for r in runs
                )
                out.append("      " + effort + ": {runs:[" + runs_js + "]},")
            out.append("    },")
        out.append("  },")
    out.append("};")
    return "\n".join(out)

def main():
    runs_by = load_runs()
    data_js = build_data_js(runs_by)
    task_meta_js = json.dumps(
        {tid: {k: v for k, v in m.items()} for tid, m in TASK_META.items()},
        ensure_ascii=False, indent=2
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
  .container{max-width:1100px;margin:0 auto;padding:0 1.5rem;}
  header h1{font-size:2rem;font-weight:700;color:#fff;}
  .badge{display:inline-block;background:var(--accent);color:#fff;font-size:.75rem;font-weight:600;padding:.2rem .6rem;border-radius:99px;margin-left:.5rem;vertical-align:middle;}
  .controls{float:right;margin-top:.3rem;display:flex;gap:.5rem;}
  .controls button{background:var(--card);border:1px solid var(--border);color:var(--muted);padding:.3rem .8rem;border-radius:6px;cursor:pointer;font-size:.85rem;transition:.2s;}
  .controls button.active,.controls button:hover{background:var(--accent);color:#fff;border-color:var(--accent);}
  section{padding:2.5rem 0;border-bottom:1px solid var(--border);}
  h2{font-size:1.4rem;font-weight:700;margin-bottom:1rem;color:#fff;}
  h3{font-size:1.1rem;font-weight:600;margin-bottom:.6rem;color:#e2e8f0;}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;}
  .grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;}
  @media(max-width:700px){.grid2,.grid4{grid-template-columns:1fr 1fr;}}
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
  .chart-wrap{position:relative;height:240px;}
  footer{padding:1.5rem 0;border-top:1px solid var(--border);} footer p{color:var(--muted);font-size:.85rem;}
"""

    body = (
        '<header><div class="container">'
        '<div class="controls"><button onclick="setLang(\'cs\')" id="btn-cs" class="active">CS</button>'
        '<button onclick="setLang(\'en\')" id="btn-en">EN</button></div>'
        '<h1>Claude Code Effort Benchmark <span class="badge">Phase 1+SWE</span></h1>'
        '<p id="hdr-sub">Empirické měření dopadu parametru --effort &middot; claude-opus-4-7</p>'
        '</div></header>'
        '<div class="container">'

        # KPI
        '<section><div class="grid4">'
        '<div class="card kpi"><div class="num">' + str(total_runs) + '</div><div class="label" data-i18n="kpi_runs">celkem run&#367;</div></div>'
        '<div class="card kpi"><div class="num">' + str(unique_tasks) + '</div><div class="label" data-i18n="kpi_tasks">&uacute;lohy</div></div>'
        '<div class="card kpi"><div class="num">' + str(total_pass) + '/' + str(total_runs) + '</div><div class="label" data-i18n="kpi_pass">verify pass</div></div>'
        '<div class="card kpi"><div class="num">$' + f"{total_cost:.1f}" + '</div><div class="label" data-i18n="kpi_cost">celkem n&aacute;klady</div></div>'
        '</div></section>'

        # Overview table
        '<section><h2 data-i18n="overview_h">P&#345;ehled v&yacute;sledk&#367;</h2>'
        '<div class="card" style="overflow-x:auto;">'
        '<table><thead><tr>'
        '<th data-i18n="ov_task">&Uacute;loha</th>'
        '<th>low</th><th>medium</th><th>high</th><th>max</th>'
        '<th data-i18n="ov_signal">Effort gradient</th>'
        '</tr></thead><tbody id="overview-tbody"></tbody></table>'
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

        # Django detail
        '<section><h2 data-i18n="django_h">Django-16910: detail effort gradientu</h2>'
        '<p style="color:var(--muted);margin-bottom:1rem;font-size:.9rem" data-i18n="django_desc">'
        'only()+select_related() na reverse OneToOneField. Nejsilnějš&iacute; effort gradient v benchmarku.</p>'
        '<div class="grid2">'
        '<div class="card"><h3 data-i18n="django_pass_h">Pass rate per effort</h3>'
        '<div class="chart-wrap"><canvas id="c-django-pass"></canvas></div></div>'
        '<div class="card"><h3 data-i18n="django_cost_h">Průměrná cena per effort</h3>'
        '<div class="chart-wrap"><canvas id="c-django-cost"></canvas></div></div>'
        '</div>'
        '<div class="card" style="margin-top:1rem;overflow-x:auto;">'
        '<table><thead><tr>'
        '<th>Effort</th><th data-i18n="col_n">n</th><th data-i18n="col_pass">Pass%</th>'
        '<th data-i18n="col_score">Avg score</th><th data-i18n="col_cost">Avg cost</th>'
        '<th data-i18n="col_wall">Avg wall</th><th data-i18n="col_tools">Avg tools</th>'
        '</tr></thead><tbody id="django-detail-tbody"></tbody></table>'
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

const SWE_FINDINGS = {
  cs: {
    'swe_sympy__sympy-24909': 'Low selhal, medium+ opravil. One-file fix.',
    'swe_django__django-16910': 'Low/medium selhávají, high uspívá.',
    'swe_django__django-17051': 'I low opravil. Příliš snadné.',
    'swe_django__django-16379': 'Cache race condition — snadné, low občas stačí.',
    'swe_django__django-16408': 'Ostrý práh: low 25%, medium+ 100%. Multi-level ORM bug.',
    'swe_django__django-16820': 'Ostrý práh: low 25%, medium+ ~100%. Migration squashing.',
    'swe_sympy__sympy-22840': 'Pozvolný gradient — 2-aspect bug, max 60% full fix, medium/high stuck na 2/3.',
  },
  en: {
    'swe_sympy__sympy-24909': 'Low failed, medium+ fixed. One-file fix.',
    'swe_django__django-16910': 'Low/medium fail, high succeeds.',
    'swe_django__django-17051': 'Even low fixed it. Too easy.',
    'swe_django__django-16379': 'Cache race condition — easy, low sometimes works.',
    'swe_django__django-16408': 'Sharp threshold: low 25%, medium+ 100%. Multi-level ORM bug.',
    'swe_django__django-16820': 'Sharp threshold: low 25%, medium+ ~100%. Migration squashing.',
    'swe_sympy__sympy-22840': 'Gradual gradient — 2-aspect bug, max 60% full fix, medium/high stuck at 2/3.',
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
    swe_h:'SWE-bench výsledky', swe_desc:'Reálné bugy z open-source projektů.',
    swe_instance:'Instance', swe_finding:'Finding',
    django_h:'Django-16910: detail effort gradientu',
    django_desc:'only()+select_related() na reverse OneToOneField.',
    django_pass_h:'Pass rate per effort', django_cost_h:'Průměrná cena per effort',
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
    col_wall:'Avg wall', col_tools:'Avg tools',
    hdr_sub:'Empirické měření dopadu parametru --effort · claude-opus-4-7',
  },
  en: {
    kpi_runs:'total runs', kpi_tasks:'tasks', kpi_pass:'verify pass', kpi_cost:'total cost',
    overview_h:'Results Overview', ov_task:'Task', ov_signal:'Effort gradient',
    swe_h:'SWE-bench Results', swe_desc:'Real bugs from open-source projects.',
    swe_instance:'Instance', swe_finding:'Finding',
    django_h:'Django-16910: effort gradient detail',
    django_desc:'only()+select_related() on reverse OneToOneField.',
    django_pass_h:'Pass rate per effort', django_cost_h:'Avg cost per effort',
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
    col_wall:'Avg wall', col_tools:'Avg tools',
    hdr_sub:'Empirical measurement of --effort parameter · claude-opus-4-7',
  },
};

let lang = navigator.language.startsWith('en') ? 'en' : 'cs';
const charts = {};
const model = 'claude-opus-4-7';

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

function makeBar(id, labels, vals, colors, yLabel, yMax) {
  if (charts[id]) charts[id].destroy();
  const ctx = document.getElementById(id);
  if (!ctx) return;
  charts[id] = new Chart(ctx.getContext('2d'), {
    type:'bar',
    data:{labels,datasets:[{data:vals,backgroundColor:colors.map(c=>c+'bb'),borderColor:colors,borderWidth:2,borderRadius:6}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false}},
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
    const tag = meta.type==='swe' ? '&#128300;' : '&#129514;';
    tbody.innerHTML += '<tr><td><strong>'+tag+' '+meta['label_'+lang]+'</strong>'
      +'<br><small style="color:var(--muted)">'+meta['desc_'+lang]+'</small></td>'
      +cells.join('')+'<td>'+gradient+'</td></tr>';
  });
}

function renderSWE() {
  const d = DATA[model] || {};
  const tbody = document.getElementById('swe-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  const SWE_TASKS = ['swe_sympy__sympy-24909','swe_django__django-16910','swe_django__django-17051','swe_django__django-16379','swe_django__django-16408','swe_django__django-16820','swe_sympy__sympy-22840'];
  SWE_TASKS.forEach(tid => {
    if (!d[tid]) return;
    const meta = TASK_META[tid];
    const cells = EFFORTS.map(e => {
      const runs = (d[tid][e]||{}).runs||[];
      if (!runs.length) return '<td style="color:var(--muted)">—</td>';
      const p = pct(runs.map(r=>r.ok));
      return '<td><span style="color:'+passColor(p)+';font-weight:700">'+p+'%</span>'
           + ' <small style="color:var(--muted)">n='+runs.length+'</small></td>';
    });
    const finding = (SWE_FINDINGS[lang]||{})[tid]||'';
    tbody.innerHTML += '<tr><td><strong>'+meta['label_'+lang]+'</strong></td>'
      +cells.join('')+'<td style="color:#94a3b8;font-size:.85rem">'+finding+'</td></tr>';
  });
}

function renderDjangoDetail() {
  const d = (DATA[model]||{})['swe_django__django-16910'];
  if (!d) return;
  const tbody = document.getElementById('django-detail-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  const passVals=[], costVals=[];
  EFFORTS.forEach(e => {
    const runs = (d[e]||{}).runs||[];
    if (!runs.length) { passVals.push(0); costVals.push(0); return; }
    const p = pct(runs.map(r=>r.ok));
    const ac = avg(runs.map(r=>r.c));
    const aw = avg(runs.map(r=>r.t));
    const at = avg(runs.map(r=>r.tc));
    const as_ = avg(runs.map(r=>r.score));
    passVals.push(p); costVals.push(ac);
    tbody.innerHTML += '<tr>'
      +'<td>'+effortBadge(e)+'</td>'
      +'<td>'+runs.length+'</td>'
      +'<td><strong style="color:'+passColor(p)+'">'+p+'%</strong></td>'
      +'<td>'+as_.toFixed(2)+'</td>'
      +'<td>$'+ac.toFixed(3)+'</td>'
      +'<td>'+Math.round(aw)+'s</td>'
      +'<td>'+Math.round(at)+'</td>'
      +'</tr>';
  });
  makeBar('c-django-pass', EFFORTS, passVals, EFFORTS.map(e=>COLORS[e]), 'pass %', 100);
  makeBar('c-django-cost', EFFORTS, costVals, EFFORTS.map(e=>COLORS[e]), 'USD', null);
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
  renderOverview(); renderSWE(); renderDjangoDetail(); renderSynthCharts(); renderRec();
  document.querySelectorAll('[data-i18n]').forEach(el=>{const k=el.dataset.i18n;if(i18n[lang][k])el.innerHTML=i18n[lang][k];});
}

document.addEventListener('DOMContentLoaded', ()=>{ setLang(lang); });
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
        "  const html = String.raw`" + html.replace("`", "\\`") + "`;\n"
        "  return new Response(html, { headers: {'content-type': 'text/html;charset=utf-8'} });\n"
        "}\n"
    )

    OUT.write_text(val_ts, encoding="utf-8")
    print(f"✓ Report written to {OUT}")
    print(f"  {total_runs} runs | {unique_tasks} tasks | ${total_cost:.2f} total cost")
    print(f"  Django-16910 runs per effort:")
    for e in EFFORTS:
        runs = runs_by.get(("claude-opus-4-7", "swe_django__django-16910", e), [])
        if runs:
            p = sum(1 for r in runs if r["ok"])
            print(f"    {e}: {p}/{len(runs)} pass")

if __name__ == "__main__":
    main()
