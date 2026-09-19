"""Shared styling and presentational components."""
from __future__ import annotations

import html

import streamlit as st


def esc(value) -> str:
    """HTML-escape a value. Note 0 and False are real values, not blanks."""
    if value is None:
        return ""
    return html.escape(str(value))


def inject_css(primary="#7B1E3C", accent="#C9A227"):
    st.html(
        f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Jost:wght@300;400;500;600&display=swap');
:root {{
  --ink:#241a1d; --muted:#6d5f63; --line:#e7dcd2;
  --primary:{primary}; --accent:{accent};
  --cream:#fdf8f3; --card:#ffffff;
}}
html, body, [class*="css"], .stApp {{ font-family:'Jost',system-ui,sans-serif; }}
.stApp {{ background:
    radial-gradient(1100px 520px at 12% -12%, rgba(201,162,39,.14), transparent 60%),
    radial-gradient(900px 480px at 92% 4%, rgba(123,30,60,.12), transparent 60%),
    var(--cream); color:var(--ink); }}
[data-testid="stHeader"] {{ background:transparent; }}
#MainMenu, footer {{ visibility:hidden; }}
.block-container {{ padding-top:1.1rem; padding-bottom:3rem; max-width:1180px; }}

h1,h2,h3,h4, .disp {{ font-family:'Cormorant Garamond',Georgia,serif; letter-spacing:.2px; }}
h1 {{ font-weight:700; }}
a {{ color:var(--primary); }}

/* ---------- brand bar ---------- */
.brandbar {{ display:flex; align-items:center; gap:.9rem; padding:.2rem 0 .9rem; }}
.brandmark {{ width:48px;height:48px;border-radius:50%;flex:0 0 48px;
  background:linear-gradient(140deg,var(--primary),#b8355f 55%,var(--accent));
  display:flex;align-items:center;justify-content:center;color:#fff;
  font-family:'Cormorant Garamond',serif;font-size:1.5rem;
  box-shadow:0 6px 18px rgba(123,30,60,.28); }}
.brandname {{ font-family:'Cormorant Garamond',serif;font-size:1.6rem;line-height:1.1;
  font-weight:700;color:var(--primary); }}
.brandtag {{ font-size:.78rem;letter-spacing:.22em;text-transform:uppercase;color:var(--muted); }}

/* ---------- hero ---------- */
.hero {{ position:relative;overflow:hidden;border-radius:26px;padding:3.4rem 2.6rem;
  background:linear-gradient(135deg,#5d1430 0%,var(--primary) 42%,#a33455 100%);
  color:#fff;box-shadow:0 24px 60px rgba(93,20,48,.32); }}
.hero:before {{ content:"";position:absolute;inset:auto -80px -140px auto;width:380px;height:380px;
  border-radius:50%;background:radial-gradient(circle,rgba(201,162,39,.45),transparent 62%); }}
.hero:after {{ content:"";position:absolute;top:-70px;right:-40px;width:240px;height:240px;
  border:1px solid rgba(255,255,255,.22);border-radius:50%; }}
.hero-eyebrow {{ letter-spacing:.32em;text-transform:uppercase;font-size:.72rem;
  color:var(--accent);margin-bottom:.9rem; }}
.hero h1 {{ font-size:3.15rem;line-height:1.08;margin:0 0 1rem;color:#fff; }}
.hero p {{ font-size:1.06rem;max-width:44rem;color:rgba(255,255,255,.88);margin:0; }}
.hero-meta {{ display:flex;gap:2.2rem;flex-wrap:wrap;margin-top:2rem;
  border-top:1px solid rgba(255,255,255,.2);padding-top:1.3rem;position:relative;z-index:2; }}
.hero-meta div span {{ display:block; }}
.hm-num {{ font-family:'Cormorant Garamond',serif;font-size:1.8rem;color:var(--accent);line-height:1; }}
.hm-lab {{ font-size:.74rem;letter-spacing:.16em;text-transform:uppercase;color:rgba(255,255,255,.7);margin-top:.35rem; }}

/* ---------- section headings ---------- */
.sec {{ margin:2.6rem 0 1.1rem; }}
.sec .eyebrow {{ letter-spacing:.28em;text-transform:uppercase;font-size:.72rem;color:var(--accent);font-weight:600; }}
.sec h2 {{ font-size:2.15rem;margin:.25rem 0 .2rem;color:var(--primary); }}
.sec p.lead {{ color:var(--muted);margin:0;max-width:46rem; }}
.rule {{ height:2px;width:72px;margin:.55rem 0 0;
  background:linear-gradient(90deg,var(--accent),transparent); }}

/* ---------- cards ---------- */
.card {{ background:var(--card);border:1px solid var(--line);border-radius:18px;
  padding:1.4rem 1.5rem;height:100%;
  box-shadow:0 2px 10px rgba(36,26,29,.05);transition:.22s; }}
.card:hover {{ transform:translateY(-3px);box-shadow:0 14px 34px rgba(123,30,60,.14);
  border-color:rgba(201,162,39,.55); }}
.card h4 {{ margin:.5rem 0 .45rem;color:var(--primary);font-size:1.3rem; }}
.card p {{ color:var(--muted);font-size:.93rem;margin:0;line-height:1.6; }}
.card .glyph {{ font-size:1.6rem;color:var(--accent); }}

.batch {{ background:var(--card);border:1px solid var(--line);border-left:4px solid var(--accent);
  border-radius:16px;padding:1.4rem 1.5rem;margin-bottom:1rem;
  box-shadow:0 2px 10px rgba(36,26,29,.05); }}
.batch h4 {{ margin:0 0 .2rem;color:var(--primary);font-size:1.35rem; }}
.batch .lvl {{ display:inline-block;font-size:.68rem;letter-spacing:.16em;text-transform:uppercase;
  background:rgba(123,30,60,.09);color:var(--primary);padding:.22rem .6rem;border-radius:999px; }}
.batch .meta {{ color:var(--muted);font-size:.88rem;margin:.7rem 0 0;
  display:flex;gap:1.3rem;flex-wrap:wrap; }}
.batch .price {{ font-family:'Cormorant Garamond',serif;font-size:1.65rem;color:var(--primary); }}

.quote {{ background:var(--card);border:1px solid var(--line);border-radius:18px;padding:1.5rem;height:100%; }}
.quote p {{ font-family:'Cormorant Garamond',serif;font-size:1.16rem;font-style:italic;
  color:var(--ink);line-height:1.55;margin:0 0 .9rem; }}
.quote .who {{ font-size:.82rem;letter-spacing:.1em;text-transform:uppercase;color:var(--accent); }}
.quote .rel {{ font-size:.82rem;color:var(--muted); }}

.eventrow {{ display:flex;gap:1.2rem;background:var(--card);border:1px solid var(--line);
  border-radius:16px;padding:1.1rem 1.3rem;margin-bottom:.8rem;align-items:flex-start; }}
.evdate {{ flex:0 0 74px;text-align:center;background:linear-gradient(160deg,var(--primary),#a33455);
  color:#fff;border-radius:12px;padding:.55rem .2rem; }}
.evdate .d {{ font-family:'Cormorant Garamond',serif;font-size:1.6rem;line-height:1; }}
.evdate .m {{ font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;opacity:.85; }}
.eventrow h4 {{ margin:0 0 .25rem;color:var(--primary);font-size:1.2rem; }}
.eventrow p {{ margin:0;color:var(--muted);font-size:.9rem; }}

.pill {{ display:inline-block;padding:.24rem .7rem;border-radius:999px;font-size:.72rem;
  letter-spacing:.08em;text-transform:uppercase;font-weight:600; }}
.pill.ok {{ background:#e7f4ec;color:#1d6b3f; }}
.pill.warn {{ background:#fdf1dc;color:#8a6212; }}
.pill.bad {{ background:#fbe9e9;color:#9b2c2c; }}
.pill.info {{ background:#eaeef8;color:#2f4a86; }}

.kpi {{ background:var(--card);border:1px solid var(--line);border-radius:16px;padding:1.1rem 1.25rem; }}
.kpi .n {{ font-family:'Cormorant Garamond',serif;font-size:2.1rem;color:var(--primary);line-height:1; }}
.kpi .l {{ font-size:.74rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-top:.35rem; }}

.note {{ background:#fff8e8;border:1px solid rgba(201,162,39,.45);border-left:4px solid var(--accent);
  border-radius:12px;padding:.85rem 1.1rem;color:#6b5312;font-size:.92rem; }}

.footer {{ margin-top:3rem;padding:2rem 0 1rem;border-top:1px solid var(--line);
  color:var(--muted);font-size:.87rem; }}
.footer .fname {{ font-family:'Cormorant Garamond',serif;font-size:1.3rem;color:var(--primary); }}

/* ---------- streamlit widgets ---------- */
.stButton>button, .stFormSubmitButton>button {{
  border-radius:999px;border:1px solid var(--primary);background:var(--primary);color:#fff;
  font-weight:500;letter-spacing:.02em;padding:.5rem .9rem;transition:.18s;
  white-space:nowrap;overflow:visible; }}
.stButton>button p, .stFormSubmitButton>button p {{ white-space:nowrap; }}
.stButton>button:hover, .stFormSubmitButton>button:hover {{
  background:#5d1430;border-color:#5d1430;color:#fff;transform:translateY(-1px); }}
.stButton>button[kind="secondary"] {{ background:transparent;color:var(--primary); }}
div[data-testid="stTabs"] button[role="tab"] {{ font-family:'Jost',sans-serif;font-weight:500; }}
div[data-testid="stTabs"] button[aria-selected="true"] {{ color:var(--primary); }}
section[data-testid="stSidebar"] {{ background:#fffdfa;border-right:1px solid var(--line); }}
input, textarea, .stSelectbox div[data-baseweb="select"] > div {{ border-radius:10px !important; }}
hr {{ border-color:var(--line); }}
.stDataFrame {{ border-radius:12px;overflow:hidden; }}
@media (max-width:640px) {{
  .hero {{ padding:2.2rem 1.4rem; }} .hero h1 {{ font-size:2.1rem; }}
  .sec h2 {{ font-size:1.7rem; }}
}}
</style>"""
    )


def brandbar(site):
    initial = esc(site.get("academy_name", "N"))[:1] or "N"
    st.html(
        f"""<div class="brandbar">
  <div class="brandmark">{initial}</div>
  <div><div class="brandname">{esc(site.get('academy_name'))}</div>
  <div class="brandtag">{esc(site.get('tagline'))}</div></div>
</div>"""
    )


def section(eyebrow, heading, lead=""):
    st.html(
        f"""<div class="sec"><div class="eyebrow">{esc(eyebrow)}</div>
<h2>{esc(heading)}</h2><div class="rule"></div>
{f'<p class="lead">{esc(lead)}</p>' if lead else ''}</div>"""
    )


def card(glyph, title, text):
    st.html(
        f"""<div class="card"><div class="glyph">{esc(glyph)}</div>
<h4>{esc(title)}</h4><p>{esc(text)}</p></div>"""
    )


def kpi(number, label):
    st.html(
        f"""<div class="kpi"><div class="n">{esc(number)}</div>
<div class="l">{esc(label)}</div></div>"""
    )


def pill(text, kind="info"):
    return f'<span class="pill {kind}">{esc(text)}</span>'


def footer(site):
    bits = []
    if site.get("phone"):
        bits.append(esc(site["phone"]))
    if site.get("email"):
        bits.append(esc(site["email"]))
    if site.get("address"):
        bits.append(esc(site["address"]))
    links = []
    for label, key in (("Instagram", "guru_instagram"), ("YouTube", "youtube"),
                       ("Facebook", "facebook"), ("WhatsApp", "whatsapp")):
        if site.get(key):
            links.append(f'<a href="{esc(site[key])}" target="_blank">{label}</a>')
    st.html(
        f"""<div class="footer">
<div class="fname">{esc(site.get('academy_name'))}</div>
<div style="margin:.45rem 0">{' &nbsp;·&nbsp; '.join(bits)}</div>
<div style="margin:.45rem 0">{' &nbsp;·&nbsp; '.join(links)}</div>
<div style="margin-top:.8rem;opacity:.8">{esc(site.get('footer_note'))}</div>
</div>"""
    )
