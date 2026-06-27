"""
html_generator.py — L4 presentation layer. Renders a Substrate through a VIEW.

A view is a pure function of the Substrate (L2). Views differ STRUCTURALLY, not
by color (see docs/view-structural-dna.md + the Anti-Recolor Test). Branding (L5)
is a per-client override on the NowPage house tokens — one accent swap + logo +
sticky name/title.

Implemented:
  * "traditional" (View D / "Mark's") — plain, elegant, FULL DEPTH: every section
    linearly, house tables, diagrams, sources appendix. The anchor view.

Pending (own render fns): "dossier" (A), "visual" (B), "decision" (C).

Design tokens are the real NowPage house system extracted from the nowpages:
cream #EDE8DF + ink #1A1612 + amber #B85C18, Bebas Neue / DM Sans / DM Mono.
`--accent` defaults to amber and is the single per-client swap.
"""
from __future__ import annotations
import re, html, pathlib
from typing import Optional

try:
    import markdown
except ImportError:
    markdown = None

from ..substrate import Substrate, Brand, from_state


# ─────────────────────────────────────────────────────────────────────────────
# markdown + mermaid helpers (shared by all views)
# ─────────────────────────────────────────────────────────────────────────────
def _md(md_text: str) -> str:
    """Markdown → HTML, with ```mermaid blocks pulled to client-side render targets."""
    blocks = []
    def grab(m):
        blocks.append(m.group(1).strip()); return f"\n@@MMD{len(blocks)-1}@@\n"
    md_text = re.sub(r"```mermaid\s*\n(.*?)```", grab, md_text, flags=re.S)
    md_text = re.sub(r"^#\s+.*\n", "", md_text, count=1)   # drop the section's own H1
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists"])
    for i, code in enumerate(blocks):
        div = f'<div class="mermaid-wrap"><pre class="mermaid">{html.escape(code)}</pre></div>'
        body = body.replace(f"<p>@@MMD{i}@@</p>", div).replace(f"@@MMD{i}@@", div)
    return body


def _esc(s: str) -> str:
    return html.escape(s or "")


def _plain(md_text: str, limit: int = 240) -> str:
    """Strip markdown to plain text (kills '## ' / '**' bleed-through)."""
    t = md_text or ""
    t = re.sub(r"`+", "", t)
    t = re.sub(r"^\s*#{1,6}\s*", "", t, flags=re.M)
    t = re.sub(r"\*\*|\*|__|_", "", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:limit].rstrip() + ("…" if len(t) > limit else "")


def _clean_subtitle(sub: Substrate) -> str:
    """A correct, clean cover subtitle. Prefer SYNTHESIS (section 01's first
    paragraph) over the raw research profile, which the entity gate may have
    flagged as wrong-entity (e.g. Steve's polluted 1990-UK-company blurb)."""
    if sub.sections:
        body = sorted(sub.sections, key=lambda s: s.order)[0].body_md
        for para in re.split(r"\n\s*\n", body):
            p = para.strip()
            if p and not p.startswith("#") and not p.startswith("|") and len(p) > 60:
                return _plain(p, 240)
    return _plain(sub.profile_summary, 240)


# ─────────────────────────────────────────────────────────────────────────────
# View D — "traditional" (plain, elegant, full depth)
# ─────────────────────────────────────────────────────────────────────────────
def render_traditional(sub: Substrate, brand: Optional[Brand] = None) -> str:
    if markdown is None:
        raise RuntimeError("markdown package required: pip install markdown")
    b = brand or sub.brand
    accent = b.accent or "#B85C18"
    accent2 = b.accent_2 or "#2D7A4F"
    name = b.name or sub.meta.subject_name
    title = b.title or ""
    producer = b.producer_name or "ASAP AI"
    # LEFT corner = the firm PRODUCING the report (FROM); the target goes on the right.
    logo = (f'<img class="logo-img" src="{_esc(b.producer_logo_url)}" alt="logo">'
            if b.producer_logo_url else f'<span class="logo-wm">{_esc(producer)}</span>')
    report_title = {
        "ai_strategy": "AI Strategy Blueprint",
        "intelligence_brief": "Expert Intelligence Brief",
        "idea_validator": "Idea Validation Report",
    }.get(sub.meta.report_type.value, "Strategic Report")

    # entity-gate banner (transparency: show data-trust state on the artifact)
    e = sub.entity
    gate_banner = ""
    if e.status.value != "match":
        tone = "#A0403F" if e.blocking else accent
        label = "DATA INTEGRITY: BLOCK" if e.blocking else "DATA INTEGRITY: REVIEW"
        gate_banner = (f'<div class="gate" style="border-color:{tone};color:{tone}">'
                       f'<b>{label}</b> · entity confidence {e.confidence:.2f} — '
                       f'{_esc(e.evidence[0] if e.evidence else "")}</div>')

    # TOC + sections (full depth)
    toc, sections = [], []
    for s in sorted(sub.sections, key=lambda x: x.order):
        anchor = f"sec-{s.id}"
        num = s.id[:2] if s.id[:2].isdigit() else f"{s.order+1:02d}"
        toc.append(f'<a href="#{anchor}"><span class="tnum">{num}</span>{_esc(s.title)}</a>')
        sections.append(f"""
      <section class="sec" id="{anchor}">
        <div class="kick">Section <span>{num}</span></div>
        <h2>{_esc(s.title)}</h2>
        <div class="prose">{_md(s.body_md)}</div>
      </section>""")

    # sources appendix
    cites = ""
    if sub.citations:
        items = "\n".join(f'<li><a href="{_esc(c.url)}" target="_blank" rel="noopener">{_esc(c.url)}</a></li>'
                          for c in sub.citations[:60])
        cites = f"""
      <section class="sec" id="sec-sources">
        <div class="kick">Appendix <span>S</span></div>
        <h2>Sources</h2>
        <ol class="sources">{items}</ol>
      </section>"""

    meta = sub.meta
    return TRADITIONAL_TMPL.format(
        accent=accent, accent2=accent2,
        doc_title=f"{_esc(name)} — {report_title}",
        report_title=report_title.upper(),
        logo=logo, name=_esc(name), title=_esc(title) or "—",
        subject=_esc(meta.subject_name),
        prepared_date=_esc(meta.generated_at[:10] or "2026"),
        mode=_esc(meta.mode or "—"),
        subtitle=_esc(_clean_subtitle(sub)),
        gate_banner=gate_banner, toc="\n".join(toc),
        sections="\n".join(sections), cites=cites,
        n_sections=len(sub.sections),
        title_sep=" · " if title else "",
    )


TRADITIONAL_TMPL = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{doc_title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{{
    --accent:{accent}; --accent2:{accent2};
    --cream:#EDE8DF; --ink:#1A1612; --white:#F7F4EF; --mid:#6B5F52; --pale:#D9D0C3;
    --head:'Bebas Neue',system-ui,sans-serif; --body:'DM Sans',system-ui,sans-serif; --mono:'DM Mono',monospace;
    --maxw:1080px;
  }}
  *{{box-sizing:border-box}} html{{scroll-behavior:smooth}}
  body{{margin:0;font-family:var(--body);background:var(--cream);color:var(--ink);font-size:15.5px;line-height:1.65;font-weight:300;-webkit-font-smoothing:antialiased}}
  a{{color:var(--accent);text-decoration:none}} a:hover{{text-decoration:underline}}
  h1,h2,h3{{font-family:var(--head);font-weight:400;letter-spacing:.02em}}

  /* sticky appbar with HIGHLIGHTED name + title */
  .bar{{position:sticky;top:0;z-index:50;background:var(--ink);color:var(--cream);display:flex;align-items:center;
    justify-content:space-between;padding:11px 28px;gap:18px}}
  .bar .who{{display:flex;align-items:center;gap:14px;min-width:0}}
  .logo-img{{height:26px;width:auto;display:block}}
  .logo-wm{{font-family:var(--head);font-size:19px;letter-spacing:.04em;color:var(--cream)}}
  .nt{{display:flex;flex-direction:column;line-height:1.15;padding-left:14px;border-left:1px solid rgba(255,255,255,.25)}}
  .nt .pf{{font-family:var(--mono);font-size:8.5px;letter-spacing:.18em;text-transform:uppercase;color:rgba(255,255,255,.5);margin-bottom:2px}}
  .nt .n{{font-family:var(--head);font-size:18px;letter-spacing:.03em;color:#fff}}
  .nt .n b{{color:var(--accent)}}
  .nt .t{{font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:rgba(255,255,255,.7)}}
  .bar .badge{{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;background:var(--accent);color:#fff;padding:6px 12px;border-radius:3px;white-space:nowrap}}

  /* cover */
  .cover{{background:var(--ink);color:var(--cream);padding:70px 60px 52px}}
  .cover .cls{{font-family:var(--mono);font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:var(--accent);margin-bottom:20px}}
  .cover h1{{font-size:clamp(44px,7vw,82px);line-height:.98;color:#fff;margin:0 0 14px;letter-spacing:.01em}}
  .cover .sub{{font-family:var(--body);font-size:17px;font-weight:300;color:rgba(255,255,255,.8);max-width:680px;line-height:1.6}}
  .cover .rule{{width:64px;height:3px;background:var(--accent);margin:26px 0}}
  .cover .meta{{display:flex;flex-wrap:wrap;gap:38px}}
  .cover .meta .f{{font-family:var(--mono);font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:rgba(255,255,255,.55)}}
  .cover .meta .f b{{display:block;font-family:var(--body);font-size:14px;font-weight:600;letter-spacing:0;text-transform:none;color:#fff;margin-top:4px}}

  .gate{{max-width:var(--maxw);margin:0 auto;transform:translateY(-22px);background:var(--white);border:1px solid;border-left-width:4px;
    border-radius:4px;padding:11px 16px;font-size:13px;box-shadow:0 6px 18px rgba(0,0,0,.06)}}

  .shell{{max-width:var(--maxw);margin:0 auto;display:grid;grid-template-columns:230px 1fr;gap:44px;padding:30px 28px 90px}}
  .toc{{position:sticky;top:74px;align-self:start;max-height:calc(100vh - 96px);overflow:auto}}
  .toc .h{{font-family:var(--mono);font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--mid);margin:0 0 12px}}
  .toc a{{display:flex;gap:10px;padding:6px 9px;border-radius:5px;color:var(--mid);font-size:13px;line-height:1.4;border-left:2px solid transparent}}
  .toc a:hover,.toc a.on{{color:var(--ink);border-left-color:var(--accent);background:var(--white);text-decoration:none}}
  .tnum{{font-family:var(--mono);font-size:11px;color:var(--accent);flex:none}}

  main{{min-width:0}}
  .sec{{margin-bottom:48px;scroll-margin-top:78px}}
  .kick{{font-family:var(--mono);font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--mid);margin-bottom:8px}}
  .kick span{{color:var(--accent)}}
  .sec>h2{{font-size:clamp(26px,3.4vw,38px);line-height:1.08;margin:0 0 18px;border-bottom:2px solid var(--ink);padding-bottom:12px}}
  .prose p{{margin:0 0 13px;color:#2c2620}}
  .prose h1,.prose h2{{font-family:var(--head);font-size:24px;margin:26px 0 12px;letter-spacing:.02em}}
  .prose h3{{font-family:var(--body);font-weight:700;font-size:16px;margin:20px 0 8px;color:var(--ink)}}
  .prose h4{{font-family:var(--body);font-weight:600;font-size:14px;margin:16px 0 6px;color:var(--mid)}}
  .prose ul,.prose ol{{margin:0 0 14px;padding-left:22px}} .prose li{{margin:0 0 6px;color:#2c2620}}
  .prose strong{{color:var(--ink);font-weight:600}}
  .prose code{{font-family:var(--mono);font-size:12.5px;background:var(--white);border:1px solid var(--pale);border-radius:3px;padding:1px 5px}}
  .prose table{{width:100%;border-collapse:collapse;margin:16px 0;font-size:13.5px;display:block;overflow-x:auto}}
  .prose th{{background:var(--ink);color:var(--cream);text-align:left;padding:9px 12px;font-family:var(--mono);font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;font-weight:500;white-space:nowrap}}
  .prose td{{padding:9px 12px;border-bottom:1px solid var(--pale);vertical-align:top;color:#2c2620}}
  .prose tr:nth-child(even) td{{background:var(--white)}}
  .prose blockquote{{border-left:3px solid var(--accent);margin:14px 0;padding:4px 0 4px 15px;color:var(--mid);font-style:italic}}
  .prose hr{{border:none;border-top:1px solid var(--pale);margin:22px 0}}
  .mermaid-wrap{{background:var(--white);border:1px solid var(--pale);border-radius:4px;padding:18px;margin:16px 0;overflow:auto}}
  .sources{{font-family:var(--mono);font-size:12px;color:var(--mid);columns:2;column-gap:34px}}
  .sources li{{margin:0 0 6px;break-inside:avoid}}

  footer{{max-width:var(--maxw);margin:0 auto;padding:22px 28px 50px;border-top:1px solid var(--pale);color:var(--mid);font-family:var(--mono);font-size:11px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}}
  @media(max-width:860px){{.shell{{grid-template-columns:1fr}}.toc{{position:static;max-height:none;margin-bottom:18px}}.cover{{padding:48px 24px}}.sources{{columns:1}}}}
  @media print{{.bar,.toc{{position:static}}.shell{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
  <div class="bar">
    <div class="who">{logo}
      <div class="nt"><span class="pf">Prepared for</span><span class="n"><b>{name}</b></span><span class="t">{title}</span></div>
    </div>
    <span class="badge">Confidential · {report_title}</span>
  </div>

  <header class="cover">
    <div class="cls">Prepared exclusively for {subject}</div>
    <h1>{report_title}</h1>
    <div class="rule"></div>
    <p class="sub">{subtitle}</p>
    <div class="meta" style="margin-top:30px">
      <span class="f">Prepared for<b>{name}{title_sep}{title}</b></span>
      <span class="f">Date<b>{prepared_date}</b></span>
      <span class="f">Mode<b>{mode}</b></span>
      <span class="f">Sections<b>{n_sections}</b></span>
    </div>
  </header>
  {gate_banner}

  <div class="shell">
    <nav class="toc"><p class="h">Contents</p>{toc}</nav>
    <main>{sections}{cites}</main>
  </div>
  <footer><span>{name} · {report_title} — generated by the report engine</span><span>NowPage house · View D (Traditional)</span></footer>

<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
  const DIAGS=[...document.querySelectorAll('pre.mermaid')].map((p,i)=>({{el:p,src:p.textContent,id:i}}));
  function sani(src){{
    let n=0;
    src=src.replace(/subgraph\s+"([^"]*)"/g,(m,t)=>`subgraph zg${{++n}}["${{t}}"]`);
    const q=t=>'"'+t.replace(/"/g,"'").trim()+'"';
    src=src.replace(/\[([^\[\]"|]*[(){{}}:,;][^\[\]"|]*)\]/g,(m,t)=>'['+q(t)+']');
    return src;
  }}
  async function go(){{
    mermaid.initialize({{startOnLoad:false,securityLevel:'loose',theme:'base',
      themeVariables:{{primaryColor:'#F7F4EF',primaryBorderColor:'#1A1612',primaryTextColor:'#1A1612',lineColor:'{accent}',secondaryColor:'#EDE8DF',tertiaryColor:'#EDE8DF'}},fontFamily:'inherit'}});
    for(const d of DIAGS){{
      try{{ await mermaid.parse(sani(d.src));
        const {{svg}}=await mermaid.render('zd'+d.id,sani(d.src)); d.el.className='mermaid'; d.el.innerHTML=svg;
      }}catch(e){{ d.el.outerHTML='<div style="font-family:var(--mono);font-size:12px;color:var(--mid)">◇ diagram source needs repair</div>'; }}
    }}
  }}
  const links=[...document.querySelectorAll('.toc a')],secs=links.map(a=>document.querySelector(a.getAttribute('href')));
  new IntersectionObserver(es=>es.forEach(e=>{{if(e.isIntersecting){{const i=secs.indexOf(e.target);links.forEach(l=>l.classList.remove('on'));if(links[i])links[i].classList.add('on');}}}}),{{rootMargin:'-15% 0px -75% 0px'}}).observe&&secs.forEach(s=>s&&new IntersectionObserver(es=>es.forEach(e=>{{if(e.isIntersecting){{const i=secs.indexOf(e.target);links.forEach(l=>l.classList.remove('on'));if(links[i])links[i].classList.add('on');}}}}),{{rootMargin:'-15% 0px -75% 0px'}}).observe(s));
  go();
</script>
</body>
</html>"""


# view registry (A/B/C to be added)
VIEWS = {"traditional": render_traditional}


def render(sub: Substrate, view: str = "traditional", brand: Optional[Brand] = None) -> str:
    if view not in VIEWS:
        raise ValueError(f"unknown view '{view}'. available: {list(VIEWS)}")
    return VIEWS[view](sub, brand)


if __name__ == "__main__":
    import sys
    run_dir = sys.argv[1] if len(sys.argv) > 1 else "output/steve-cunningham"
    view = sys.argv[2] if len(sys.argv) > 2 else "traditional"
    sub = from_state(run_dir)
    # demo brand for Steve (per-client override; logo slot left to RP-11 extraction)
    sub.brand = Brand(name=sub.meta.subject_name, title="Business Transformation Advisor",
                      accent="#B85C18", seed_url="https://stevecunningham.ai/")
    out = pathlib.Path(run_dir) / f"view-{view}.html"
    out.write_text(render(sub, view, sub.brand), encoding="utf-8")
    print(f"Wrote {out}  ({len(out.read_text(encoding='utf-8'))//1024} KB, view={view})")
