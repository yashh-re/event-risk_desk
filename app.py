"""
Blindspot: the risks no one else is watching.
A small web app for four event-hedge exposure memos.

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import json
import os

import altair as alt
import pandas as pd
import streamlit as st

from pricer import price_hedge, money

st.set_page_config(page_title="Blindspot", page_icon="🔷", layout="wide")

ACCENT = "#5aa9ff"
MUTED = "#9fb0d0"
HEDGED, UNHEDGED = "#3987e5", "#d95926"   # chart pair, validated colorblind-safe on navy

# Ticker badges for each company (initials, not company logos)
BADGES = {
    "JetBlue": ("JBLU", "#1e6fd9", "#5aa9ff"),
    "CoreWeave": ("CRWV", "#3b4fd8", "#7f8cff"),
    "Clearway": ("CWEN", "#0f8f9a", "#4fd1d9"),
    "DC": ("PSKY", "#2353b8", "#6c9cff"),
}

# ---------------- Glassmorphism styling ----------------
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stMarkdown, p, li, label {{ font-family: 'Inter', sans-serif; }}

/* Deep navy background with soft blue glows behind the glass */
.stApp {{
  background:
    radial-gradient(circle at 12% 18%, rgba(56, 132, 255, 0.35), transparent 38%),
    radial-gradient(circle at 88% 12%, rgba(90, 169, 255, 0.22), transparent 34%),
    radial-gradient(circle at 70% 85%, rgba(35, 83, 184, 0.35), transparent 40%),
    linear-gradient(160deg, #050a18 0%, #0a1430 55%, #070d1f 100%);
  background-attachment: fixed;
}}
[data-testid="stHeader"] {{ background: transparent; }}

/* Frosted glass sidebar */
[data-testid="stSidebar"] {{
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
  border-right: 1px solid rgba(255, 255, 255, 0.08);
}}

/* Glass cards */
.glass, [data-testid="stMetric"], [data-testid="stVegaLiteChart"], [data-testid="stTabs"] {{
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}}
[data-testid="stMetric"] {{ padding: 16px 18px; }}
[data-testid="stVegaLiteChart"] {{ padding: 18px; }}
[data-testid="stTabs"] {{ padding: 8px 22px 18px; }}

[data-testid="stMetricLabel"] p {{ text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.72rem; color: {MUTED}; }}
[data-testid="stMetricValue"] {{ font-weight: 700; font-size: 2rem; }}

h1 {{ font-weight: 700 !important; letter-spacing: -0.02em; margin: 0 !important; padding: 0 !important; }}
h2, h3 {{ font-weight: 600 !important; letter-spacing: -0.01em; }}

.brand {{ font-weight: 700; font-size: 1.9rem; letter-spacing: -0.02em;
          background: linear-gradient(90deg, #ffffff, {ACCENT}); -webkit-background-clip: text; background-clip: text; color: transparent; }}
.tagline {{ font-size: 0.82rem; color: {MUTED}; margin-bottom: 1.2rem; }}
.label {{ font-size: 0.72rem; letter-spacing: 0.14em; text-transform: uppercase; color: {ACCENT}; margin: 0.6rem 0 0.3rem; }}

.hero {{ display: flex; align-items: center; gap: 18px; padding: 20px 24px; margin-bottom: 18px; }}
.badge {{ width: 64px; height: 64px; border-radius: 18px; display: flex; align-items: center; justify-content: center;
          font-weight: 700; font-size: 0.95rem; letter-spacing: 0.04em; color: #fff; flex-shrink: 0;
          border: 1px solid rgba(255, 255, 255, 0.25); box-shadow: 0 6px 20px rgba(30, 111, 217, 0.45); }}
.hero-sub {{ font-size: 0.8rem; color: {ACCENT}; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 4px; }}
.hero-event {{ color: {MUTED}; font-size: 0.98rem; margin-top: 6px; }}
footer {{ visibility: hidden; }}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_companies():
    with open("companies.json", encoding="utf-8") as f:
        return json.load(f)


def load_memo(name):
    """Prefer your hand-edited memo (NAME_final.md), else the generated one."""
    for path in (f"memos/{name}_final.md", f"memos/{name}.md"):
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return f.read()
    return None


companies = load_companies()
names = list(companies)

# ---------------- Sidebar ----------------
st.sidebar.markdown('<div class="brand">Blindspot</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="tagline">The risks no one else is watching.</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="label">Companies</div>', unsafe_allow_html=True)
name = st.sidebar.radio(
    "Companies", names,
    format_func=lambda n: f"{BADGES[n][0]}  ·  {n}",
    label_visibility="collapsed",
)
c = companies[name]

st.sidebar.divider()
st.sidebar.markdown('<div class="label">What if?</div>', unsafe_allow_html=True)
prob = st.sidebar.slider("Probability of the event", 5, 90, int(round(c["probability"] * 100)), 5, format="%d%%") / 100
coverage = st.sidebar.slider("Share of the loss to hedge", 0, 100, 50, 5, format="%d%%") / 100
st.sidebar.caption(f"Base case for this memo: {c['probability']:.0%} probability.")

h = price_hedge(c["revenue_at_risk"], prob, coverage=coverage)

# ---------------- Header card ----------------
ticker, c1, c2 = BADGES[name]
st.markdown(
    f"""
<div class="glass hero">
  <div class="badge" style="background: linear-gradient(135deg, {c1}, {c2});">{ticker}</div>
  <div>
    <div class="hero-sub">{c['sector']}</div>
    <h1>{c['client']}</h1>
    <div class="hero-event">{c['event']}</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Revenue at risk", money(c["revenue_at_risk"]))
m2.metric("Probability", f"{prob:.0%}")
m3.metric("Hedge cost", money(h["cost"]), help=f"{h['contracts']:,.0f} contracts at ${h['price']:.2f}")
m4.metric("Worst case, hedged", money(h["net_if_event"]),
          delta=f"saves {money(h['net_if_event'] - h['unhedged_if_event'])}", delta_color="normal")

# ---------------- Payoff chart ----------------
st.markdown("### Outcome in each scenario")
rows = [
    {"Scenario": "Event happens", "Position": "Unhedged", "Result ($M)": h["unhedged_if_event"] / 1e6},
    {"Scenario": "Event happens", "Position": "Hedged", "Result ($M)": h["net_if_event"] / 1e6},
    {"Scenario": "No event", "Position": "Unhedged", "Result ($M)": 0.0},
    {"Scenario": "No event", "Position": "Hedged", "Result ($M)": h["net_if_no_event"] / 1e6},
]
df = pd.DataFrame(rows)
order = ["Unhedged", "Hedged"]

bars = alt.Chart(df).mark_bar(cornerRadiusBottomLeft=4, cornerRadiusBottomRight=4, size=40).encode(
    x=alt.X("Position:N", title=None, sort=order, axis=alt.Axis(labelAngle=0)),
    y=alt.Y("Result ($M):Q", title="Result ($M)"),
    color=alt.Color("Position:N", scale=alt.Scale(domain=order, range=[UNHEDGED, HEDGED]),
                    legend=alt.Legend(orient="top", title=None)),
    tooltip=["Scenario", "Position", alt.Tooltip("Result ($M):Q", format=",.1f")],
)
labels = alt.Chart(df).mark_text(dy=12, fontSize=12, color="#c9d4ec").encode(
    x=alt.X("Position:N", sort=order),
    y="Result ($M):Q",
    text=alt.Text("Result ($M):Q", format=",.1f"),
)
chart = (
    (bars + labels)
    .properties(width=200, height=260)
    .facet(column=alt.Column("Scenario:N", title=None, sort=["Event happens", "No event"]))
    .configure(background="transparent")
    .configure_view(stroke=None)
    .configure_axis(labelColor="#c9d4ec", titleColor="#c9d4ec", gridColor="rgba(255,255,255,0.08)",
                    domainColor="rgba(255,255,255,0.2)")
    .configure_header(labelColor="#e8eefc", labelFontSize=13)
    .configure_legend(labelColor="#e8eefc")
)
st.altair_chart(chart)
st.caption("A hedge turns an uncertain large loss into a known, smaller cost.")

# ---------------- The data behind the probability (if the company has a history) ----------------
hist = c.get("history")
if hist:
    st.markdown(f"### {hist['title']}")
    st.markdown(f'<div class="hero-event" style="margin-top:-8px;margin-bottom:10px;">{hist["subtitle"]}</div>',
                unsafe_allow_html=True)
    hdf = pd.DataFrame(hist["rows"])
    measure = hist["measure"]
    hdf = hdf.rename(columns={"period": "Winter", "value": measure, "detail": "What happened"})

    base = alt.Chart(hdf).encode(x=alt.X("Winter:N", title=None, sort=None, axis=alt.Axis(labelAngle=0)))
    hbars = base.mark_bar(color=HEDGED, cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=34).encode(
        y=alt.Y(f"{measure}:Q", title=measure, axis=alt.Axis(tickMinStep=1)),
        tooltip=["Winter", alt.Tooltip(f"{measure}:Q"), "What happened"],
    )
    # Label only the winters that had shutdown days
    hlabels = base.transform_filter(f"datum['{measure}'] > 0").mark_text(
        dy=-8, fontSize=12, color="#e8eefc").encode(y=f"{measure}:Q", text=f"{measure}:Q")
    hchart = (
        (hbars + hlabels)
        .properties(height=240)
        .configure(background="transparent")
        .configure_view(stroke=None)
        .configure_axis(labelColor="#c9d4ec", titleColor="#c9d4ec", gridColor="rgba(255,255,255,0.08)",
                        domainColor="rgba(255,255,255,0.2)")
    )
    st.altair_chart(hchart, use_container_width=True)
    st.markdown(f"**{hist['takeaway']}**")
    st.caption(hist["source"] + " Hover a bar to see the storm dates.")
    with st.expander("Show the data as a table"):
        st.dataframe(hdf, hide_index=True, use_container_width=True)

# ---------------- The memo and the research ----------------
tab_memo, tab_why = st.tabs(["Exposure memo", "Research & reasoning"])
with tab_memo:
    memo = load_memo(name)
    if memo:
        st.markdown(memo)
        st.caption("The memo shows the base case. Use the What if? sliders to explore other assumptions.")
    else:
        st.info(f"No memo yet. Run: python memo_agent.py {name}")
with tab_why:
    st.markdown("#### Why I picked it")
    st.markdown(c["why_picked"])
    st.markdown("#### Key facts")
    st.markdown("\n".join(f"- {f}" for f in c["key_facts"]))
    st.markdown("#### Reasoning behind the numbers")
    st.markdown("\n".join(f"- {r}" for r in c["reasoning"]))
