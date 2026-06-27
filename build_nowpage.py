#!/usr/bin/env python3
"""
build_nowpage.py — Prototype of strategy_factory/generation/html_generator.py

Reads the factory's generated markdown deliverables and renders ONE self-contained,
branded NowPage-style HTML deliverable with three live-swappable themes
(ASAP Mastery / Zeus Jones / Deloitte) and client-side mermaid rendering.

This is a proof of the themeable HTML output layer for ai-strategy-factory.
"""
import re, html, pathlib, sys

SLUG = "steve-cunningham"
COMPANY = "Steve Cunningham"
SUBTITLE = ("AI Strategy &amp; Implementation Blueprint — an operating system for the "
            "<strong>Humans+Agents Economy</strong>.")
BASE = pathlib.Path(__file__).parent / "output" / SLUG
MD_DIR = BASE / "markdown"
OUT = BASE / f"nowpage-{SLUG}.html"

try:
    import markdown
except ImportError:
    sys.exit("markdown package missing — pip install markdown")

SECTION_KICKER = {  # short label per deliverable id prefix
    "01": "Assessment", "02": "Assessment", "03": "Architecture", "04": "Assessment",
    "05": "Roadmap", "06": "Roadmap", "07": "Vendors", "08": "Vendors",
    "09": "Economics", "10": "Governance", "11": "Governance", "12": "Enablement",
    "13": "Reference", "14": "Enablement", "15": "Enablement",
}

def split_frontmatter(text):
    title = None
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm = text[3:end]
            m = re.search(r'title:\s*"?([^"\n]+)"?', fm)
            if m: title = m.group(1).strip()
            text = text[end + 4:]
    return title, text.lstrip("\n")

def extract_mermaid(md_text):
    """Pull ```mermaid blocks out before MD conversion; return (text_with_tokens, [code])."""
    blocks = []
    def repl(m):
        blocks.append(m.group(1).strip())
        return f"\n@@MERMAID{len(blocks)-1}@@\n"
    md_text = re.sub(r"```mermaid\s*\n(.*?)```", repl, md_text, flags=re.S)
    return md_text, blocks

def md_to_html(md_text):
    md_text, mermaids = extract_mermaid(md_text)
    # drop the first H1 (we render our own section header)
    md_text = re.sub(r"^#\s+.*\n", "", md_text, count=1)
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists", "attr_list"])
    # re-inject mermaid as render targets
    for i, code in enumerate(mermaids):
        token = f"@@MERMAID{i}@@"
        div = f'<div class="mermaid-wrap"><pre class="mermaid">{html.escape(code)}</pre></div>'
        body = body.replace(f"<p>{token}</p>", div).replace(token, div)
    return body

def build():
    sections, toc = [], []
    for f in sorted(MD_DIR.glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        title, body_md = split_frontmatter(raw)
        did = f.name[:2]
        title = title or f.stem
        anchor = f"s-{did}"
        kicker = SECTION_KICKER.get(did, "Section")
        body_html = md_to_html(body_md)
        toc.append(f'<a href="#{anchor}"><span class="toc-num">{did}</span>{html.escape(title)}</a>')
        sections.append(f"""
        <section class="section" id="{anchor}">
          <div class="section-label">{kicker} <span class="sl-num">/ {did}</span></div>
          <h2>{html.escape(title)}</h2>
          <div class="prose">{body_html}</div>
        </section>""")
    page = TEMPLATE.format(
        company=html.escape(COMPANY), subtitle=SUBTITLE,
        toc="\n".join(toc), sections="\n".join(sections),
        count=len(sections),
    )
    OUT.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT}  ({len(page)//1024} KB, {len(sections)} sections)")

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="asap">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{company} — AI Strategy Blueprint</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{
  --maxw:1180px; --radius:10px;
}}
/* ============ THEME: ASAP MASTERY ============ */
[data-theme="asap"]{{
  --font-head:'Space Grotesk',system-ui,sans-serif; --font-body:'Inter',system-ui,sans-serif; --font-mono:'JetBrains Mono',monospace;
  --bg:#F6F7F7; --glow:rgba(238,124,11,0.09); --panel:#FFFFFF; --panel-2:#FBFBFA;
  --ink:#1A171A; --muted:#3A3F45; --faint:#9AA2A9; --line:#E6E8EA;
  --accent:#EE7C0B; --accent-d:#9A460B; --accent2:#739392; --accent2-d:#3D4C52;
  --header-bg:#3D4C52; --header-ink:#FFFFFF; --gold:#F1E5AE; --badge-bg:#EE7C0B; --badge-ink:#fff;
  --hero-grad:linear-gradient(120deg,rgba(26,23,26,0.93),rgba(61,76,82,0.80));
  --head-upper:none; --head-spacing:-0.02em; --head-weight:500; --radius:10px;
}}
/* ============ THEME: ZEUS JONES ============ */
[data-theme="zeus"]{{
  --font-head:'Bebas Neue',system-ui,sans-serif; --font-body:'DM Sans',system-ui,sans-serif; --font-mono:'DM Mono',monospace;
  --bg:#F7F4EF; --glow:rgba(184,92,24,0.08); --panel:#FFFFFF; --panel-2:#FBF9F5;
  --ink:#1A1612; --muted:#4A4339; --faint:#9B9082; --line:#D9D0C3;
  --accent:#B85C18; --accent-d:#8f4612; --accent2:#2D7A4F; --accent2-d:#1f5637;
  --header-bg:#1A1612; --header-ink:#F7F4EF; --gold:#D9D0C3; --badge-bg:#B85C18; --badge-ink:#fff;
  --hero-grad:linear-gradient(120deg,rgba(26,22,18,0.90),rgba(45,122,79,0.55));
  --head-upper:uppercase; --head-spacing:0.01em; --head-weight:400; --radius:3px;
}}
[data-theme="zeus"] .hero h1{{font-size:74px;letter-spacing:0.005em}}
[data-theme="zeus"] h2{{font-size:38px}}
/* ============ THEME: DELOITTE ============ */
[data-theme="deloitte"]{{
  --font-head:'Helvetica Neue',Arial,sans-serif; --font-body:'Helvetica Neue',Arial,sans-serif; --font-mono:'JetBrains Mono',monospace;
  --bg:#FFFFFF; --glow:rgba(134,188,37,0.07); --panel:#FFFFFF; --panel-2:#F4F6F4;
  --ink:#000000; --muted:#43484d; --faint:#75787B; --line:#D0D0CE;
  --accent:#86BC25; --accent-d:#046A38; --accent2:#046A38; --accent2-d:#000000;
  --header-bg:#000000; --header-ink:#FFFFFF; --gold:#86BC25; --badge-bg:#86BC25; --badge-ink:#000;
  --hero-grad:linear-gradient(120deg,rgba(0,0,0,0.92),rgba(4,106,56,0.70));
  --head-upper:none; --head-spacing:-0.01em; --head-weight:700; --radius:0px;
}}

*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{margin:0;font-family:var(--font-body);background:radial-gradient(1200px 700px at 18% 0%,var(--glow),transparent 55%),var(--bg);
  color:var(--ink);font-size:15px;line-height:1.65;-webkit-font-smoothing:antialiased}}
a{{color:var(--accent);text-decoration:none}} a:hover{{text-decoration:underline}}
h1,h2,h3,h4{{font-family:var(--font-head);font-weight:var(--head-weight);letter-spacing:var(--head-spacing);color:var(--ink)}}

/* header */
.appbar{{position:sticky;top:0;z-index:50;background:var(--header-bg);color:var(--header-ink);
  display:flex;align-items:center;justify-content:space-between;padding:14px 28px;border-bottom:1px solid rgba(255,255,255,.08)}}
.brand{{font-family:var(--font-head);font-size:21px;letter-spacing:var(--head-spacing);display:flex;align-items:center;gap:14px}}
.brand .mk{{color:var(--gold)}}
.brand .tag{{font-family:var(--font-mono);font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:rgba(255,255,255,.65);
  padding-left:14px;border-left:1px solid rgba(255,255,255,.3)}}
.doc-badge{{font-family:var(--font-mono);font-size:10.5px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  background:var(--badge-bg);color:var(--badge-ink);padding:7px 14px;border-radius:4px}}

/* theme switcher */
.theme-switch{{position:fixed;right:18px;bottom:18px;z-index:90;display:flex;gap:6px;background:var(--panel);
  border:1px solid var(--line);border-radius:999px;padding:6px;box-shadow:0 8px 24px rgba(0,0,0,.14)}}
.theme-switch button{{font-family:var(--font-mono);font-size:11px;letter-spacing:.04em;border:none;cursor:pointer;
  padding:8px 14px;border-radius:999px;background:transparent;color:var(--muted);transition:all .2s}}
.theme-switch button.active{{background:var(--accent);color:#fff}}
.theme-switch .dot{{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:6px;vertical-align:-1px}}

/* hero */
.hero{{background:var(--hero-grad),linear-gradient(135deg,#222,#333);background-size:cover;color:#fff;padding:74px 60px 64px}}
.hero .kick{{font-family:var(--font-mono);font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:rgba(255,255,255,.7);margin-bottom:18px}}
.hero h1{{font-size:54px;line-height:1.05;margin:0 0 18px;color:#fff;text-transform:var(--head-upper)}}
.hero h1 .accent{{color:var(--accent)}}
.hero p{{font-size:18px;max-width:720px;color:rgba(255,255,255,.86);line-height:1.7;margin:0}}
.hero .meta{{margin-top:30px;display:flex;gap:28px;flex-wrap:wrap;font-family:var(--font-mono);font-size:12px;color:rgba(255,255,255,.72)}}
.hero .meta b{{color:#fff;font-weight:600}}

/* layout */
.shell{{max-width:var(--maxw);margin:0 auto;display:grid;grid-template-columns:248px 1fr;gap:40px;padding:44px 28px 100px}}
.toc{{position:sticky;top:78px;align-self:start;max-height:calc(100vh - 100px);overflow:auto}}
.toc-title{{font-family:var(--font-mono);font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--faint);margin:0 0 14px;padding-left:4px}}
.toc a{{display:flex;gap:10px;align-items:baseline;padding:7px 10px;border-radius:7px;color:var(--muted);font-size:13px;line-height:1.4;border:1px solid transparent}}
.toc a:hover{{background:var(--panel);border-color:var(--line);text-decoration:none;color:var(--ink)}}
.toc a.active{{background:var(--panel);border-color:var(--line);color:var(--ink);font-weight:600}}
.toc-num{{font-family:var(--font-mono);font-size:11px;color:var(--accent);flex:none}}

main{{min-width:0}}
.section{{margin-bottom:54px;scroll-margin-top:82px}}
.section-label{{font-family:var(--font-mono);font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--accent2);
  font-weight:600;display:flex;align-items:center;gap:12px;margin-bottom:12px}}
.section-label::before{{content:"";width:26px;height:2px;background:var(--accent2)}}
.section-label .sl-num{{color:var(--faint)}}
.section>h2{{font-size:30px;margin:0 0 22px;line-height:1.18;text-transform:var(--head-upper)}}

.prose{{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:30px 34px;box-shadow:0 1px 2px rgba(0,0,0,.03)}}
.prose h1,.prose h2{{font-size:22px;margin:30px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--line)}}
.prose h3{{font-size:17px;margin:24px 0 10px;color:var(--accent2-d)}}
.prose h4{{font-size:14px;margin:18px 0 8px;font-family:var(--font-body);font-weight:700;color:var(--muted)}}
.prose p{{margin:0 0 14px;color:var(--muted)}}
.prose ul,.prose ol{{margin:0 0 16px;padding-left:22px}} .prose li{{margin:0 0 7px;color:var(--muted)}}
.prose strong{{color:var(--ink)}}
.prose code{{font-family:var(--font-mono);font-size:12.5px;background:var(--panel-2);border:1px solid var(--line);border-radius:4px;padding:1px 6px}}
.prose pre{{background:var(--panel-2);border:1px solid var(--line);border-radius:var(--radius);padding:14px;overflow:auto;font-family:var(--font-mono);font-size:12.5px}}
.prose pre code{{border:none;background:none;padding:0}}
.prose table{{width:100%;border-collapse:collapse;margin:16px 0;font-size:13.5px;display:block;overflow-x:auto}}
.prose th{{background:var(--accent2-d);color:#fff;text-align:left;padding:10px 13px;font-family:var(--font-mono);font-size:11px;letter-spacing:.04em;text-transform:uppercase;font-weight:600;white-space:nowrap}}
.prose td{{padding:10px 13px;border-bottom:1px solid var(--line);vertical-align:top;color:var(--muted)}}
.prose tr:nth-child(even) td{{background:var(--panel-2)}}
.prose blockquote{{border-left:3px solid var(--accent);margin:16px 0;padding:4px 0 4px 16px;color:var(--muted);font-style:italic}}
.prose hr{{border:none;border-top:1px solid var(--line);margin:24px 0}}
.mermaid-wrap{{background:var(--panel-2);border:1px solid var(--line);border-radius:var(--radius);padding:20px;margin:18px 0;overflow:auto}}
.mermaid{{font-family:var(--font-body)!important}}
.mmd-fallback{{font-family:var(--font-body);color:var(--muted);font-size:13.5px}}
.mmd-fallback .tag{{font-family:var(--font-mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent2);display:block;margin-bottom:8px}}
.mmd-fallback details{{margin-top:10px}} .mmd-fallback summary{{cursor:pointer;color:var(--accent);font-family:var(--font-mono);font-size:12px}}
.mmd-fallback pre{{margin-top:10px;font-size:11.5px;line-height:1.5}}

footer{{max-width:var(--maxw);margin:0 auto;padding:26px 28px 50px;border-top:1px solid var(--line);
  display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;color:var(--faint);font-family:var(--font-mono);font-size:11.5px}}

@media(max-width:900px){{
  .shell{{grid-template-columns:1fr}} .toc{{position:static;max-height:none;margin-bottom:20px}}
  .hero{{padding:54px 26px 44px}} .hero h1{{font-size:38px}}
}}
@media print{{.theme-switch,.appbar{{position:static}} .toc{{display:none}} .shell{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
  <div class="appbar">
    <div class="brand"><span>ASAP<span class="mk"> Mastery</span></span><span class="tag">AI Strategy Factory</span></div>
    <div class="doc-badge">Confidential · Strategy Blueprint</div>
  </div>

  <header class="hero">
    <div class="kick">AI Strategy &amp; Implementation</div>
    <h1>{company} <span class="accent">·</span> AI&nbsp;Blueprint</h1>
    <p>{subtitle}</p>
    <div class="meta">
      <span><b>{count}</b> deliverables</span>
      <span>Mode <b>quick</b></span>
      <span>Engine <b>Perplexity + Gemini</b></span>
      <span>Prepared <b>2026-06-27</b></span>
    </div>
  </header>

  <div class="shell">
    <nav class="toc">
      <p class="toc-title">Contents</p>
      {toc}
    </nav>
    <main>
      {sections}
    </main>
  </div>

  <footer>
    <span>ASAP Mastery · AI Strategy Factory — themeable output prototype</span>
    <span>Switch theme ↘</span>
  </footer>

  <div class="theme-switch" id="sw">
    <button data-t="asap" class="active"><span class="dot" style="background:#EE7C0B"></span>ASAP</button>
    <button data-t="zeus"><span class="dot" style="background:#B85C18"></span>Zeus Jones</button>
    <button data-t="deloitte"><span class="dot" style="background:#86BC25"></span>Deloitte</button>
  </div>

<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
  const MERMAID_THEME = {{
    asap:{{primaryColor:'#F1E5AE',primaryBorderColor:'#3D4C52',primaryTextColor:'#1A171A',lineColor:'#739392',secondaryColor:'#F3A24C',tertiaryColor:'#F6F7F7'}},
    zeus:{{primaryColor:'#EDE8DF',primaryBorderColor:'#1A1612',primaryTextColor:'#1A1612',lineColor:'#2D7A4F',secondaryColor:'#B85C18',tertiaryColor:'#F7F4EF'}},
    deloitte:{{primaryColor:'#E8F3D6',primaryBorderColor:'#000000',primaryTextColor:'#000000',lineColor:'#046A38',secondaryColor:'#86BC25',tertiaryColor:'#F4F6F4'}}
  }};
  // stash raw mermaid source so we can re-render on theme change
  const DIAGS=[...document.querySelectorAll('pre.mermaid')].map((p,i)=>{{p.dataset.src=p.textContent;return {{el:p,src:p.textContent,id:i}};}});
  // repair the most common Gemini mermaid defects: idless quoted subgraphs + unquoted labels w/ special chars
  function sanitizeMermaid(src){{
    let n=0;
    src=src.replace(/subgraph\s+"([^"]*)"/g,(m,t)=>`subgraph zg${{++n}}["${{t}}"]`);
    const q=t=>'"'+t.replace(/"/g,"'").trim()+'"';
    src=src.replace(/\[([^\[\]"|]*[(){{}}:,;][^\[\]"|]*)\]/g,(m,t)=>'['+q(t)+']');
    src=src.replace(/\{{([^{{}}"|]*[(),:;][^{{}}"|]*)\}}/g,(m,t)=>'{{'+q(t)+'}}');
    return src;
  }}
  async function renderMermaid(theme){{
    mermaid.initialize({{startOnLoad:false,securityLevel:'loose',theme:'base',themeVariables:MERMAID_THEME[theme],fontFamily:'inherit'}});
    let ok=0,fb=0;
    for(const d of DIAGS){{
      const src=sanitizeMermaid(d.src);
      try{{
        await mermaid.parse(src);
        const {{svg}}=await mermaid.render('zmmd-'+d.id+'-'+Math.floor(performance.now()),src);
        d.el.className='mermaid'; d.el.innerHTML=svg; ok++;
      }}catch(e){{
        d.el.className='mmd-fallback';
        d.el.innerHTML='<span class="tag">◇ Diagram — source needs repair</span>The generated source for this diagram has syntax the renderer rejects (a known factory defect: malformed mermaid from the synthesis model). <details><summary>view source</summary><pre>'+d.src.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</pre></details>';
        fb++;
      }}
    }}
    console.info('mermaid:',ok,'rendered,',fb,'fallback');
  }}
  function setTheme(t){{
    document.documentElement.setAttribute('data-theme',t);
    document.querySelectorAll('#sw button').forEach(b=>b.classList.toggle('active',b.dataset.t===t));
    renderMermaid(t);
    try{{localStorage.setItem('nowpage-theme',t);}}catch(e){{}}
  }}
  document.querySelectorAll('#sw button').forEach(b=>b.addEventListener('click',()=>setTheme(b.dataset.t)));
  // scrollspy
  const links=[...document.querySelectorAll('.toc a')], secs=links.map(a=>document.querySelector(a.getAttribute('href')));
  const obs=new IntersectionObserver(es=>{{es.forEach(e=>{{if(e.isIntersecting){{const i=secs.indexOf(e.target);links.forEach(l=>l.classList.remove('active'));if(links[i])links[i].classList.add('active');}}}});}},{{rootMargin:'-20% 0px -70% 0px'}});
  secs.forEach(s=>s&&obs.observe(s));
  // init
  const saved=(()=>{{try{{return localStorage.getItem('nowpage-theme')}}catch(e){{return null}}}})();
  setTheme(saved||'asap');
</script>
</body>
</html>"""

if __name__ == "__main__":
    build()
