import json
import os

import altair as alt
import pandas as pd
import streamlit as st

from pricer import price_hedge, money

st.set_page_config(page_title="Event Risk Desk", layout="wide")

HEDGED, UNHEDGED = "#2a78d6", "#eb6834"   # validated colorblind-safe pair


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

# ---------------- Sidebar: pick a company, adjust assumptions ----------------
st.sidebar.title("Event Risk Desk")
st.sidebar.caption("Hedging the risks no one else covers")
name = st.sidebar.radio("Company", list(companies), format_func=lambda n: companies[n]["client"])
c = companies[name]

st.sidebar.divider()
st.sidebar.subheader("What if?")
prob = st.sidebar.slider("Probability of the event", 0.05, 0.90, float(c["probability"]), 0.05, format="%.2f")
coverage = st.sidebar.slider("Share of the loss to hedge", 0.0, 1.0, 0.5, 0.05, format="%.2f")
st.sidebar.caption(f"Base case for this memo: {c['probability']:.0%} probability.")

h = price_hedge(c["revenue_at_risk"], prob, coverage=coverage)

# ---------------- Header and headline numbers ----------------
st.title(c["client"])
st.markdown(f"**Event:** {c['event']}")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Revenue at risk", money(c["revenue_at_risk"]))
m2.metric("Probability", f"{prob:.0%}")
m3.metric("Hedge cost", money(h["cost"]), help=f"{h['contracts']:,.0f} contracts at ${h['price']:.2f}")
m4.metric("Worst case, hedged", money(h["net_if_event"]),
          delta=f"{money(h['net_if_event'] - h['unhedged_if_event'])} vs unhedged", delta_color="off")

# ---------------- Payoff chart ----------------
st.subheader("Outcome in each scenario")
rows = [
    {"Scenario": "Event happens", "Position": "Unhedged", "Result ($M)": h["unhedged_if_event"] / 1e6},
    {"Scenario": "Event happens", "Position": "Hedged", "Result ($M)": h["net_if_event"] / 1e6},
    {"Scenario": "No event", "Position": "Unhedged", "Result ($M)": 0.0},
    {"Scenario": "No event", "Position": "Hedged", "Result ($M)": h["net_if_no_event"] / 1e6},
]
df = pd.DataFrame(rows)

bars = alt.Chart(df).mark_bar(cornerRadiusBottomLeft=4, cornerRadiusBottomRight=4, size=40).encode(
    x=alt.X("Position:N", title=None, sort=["Unhedged", "Hedged"], axis=alt.Axis(labelAngle=0)),
    y=alt.Y("Result ($M):Q", title="Result ($M)"),
    color=alt.Color("Position:N", scale=alt.Scale(domain=["Unhedged", "Hedged"], range=[UNHEDGED, HEDGED]),
                    legend=alt.Legend(orient="top", title=None)),
    tooltip=["Scenario", "Position", alt.Tooltip("Result ($M):Q", format=",.1f")],
)
labels = alt.Chart(df).mark_text(dy=12, fontSize=12, color="#555").encode(
    x=alt.X("Position:N", sort=["Unhedged", "Hedged"]),
    y="Result ($M):Q",
    text=alt.Text("Result ($M):Q", format=",.1f"),
)
chart = (bars + labels).properties(width=180, height=260).facet(
    column=alt.Column("Scenario:N", title=None, sort=["Event happens", "No event"])
)
st.altair_chart(chart)
st.caption("A hedge turns an uncertain large loss into a known, smaller cost.")

# ---------------- The memo and the research behind it ----------------
tab_memo, tab_why = st.tabs(["Exposure memo", "Why this company & the reasoning"])
with tab_memo:
    memo = load_memo(name)
    if memo:
        st.markdown(memo)
        st.caption("The memo shows the base case. The sliders above are for exploring other assumptions.")
    else:
        st.info(f"No memo yet. Run: python memo_agent.py {name}")
with tab_why:
    st.markdown(f"**Why I picked it:** {c['why_picked']}")
    st.markdown("**Key facts**")
    st.markdown("\n".join(f"- {f}" for f in c["key_facts"]))
    st.markdown("**Reasoning behind the numbers**")
    st.markdown("\n".join(f"- {r}" for r in c["reasoning"]))