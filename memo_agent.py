"""
Exposure memo agent.

Takes a company's numbers and reasoning (companies.json), prices the hedge
(pricer.py), and asks Claude to write a one-page exposure memo for the CFO.

Setup (once):
    pip install anthropic
    Set your API key as an environment variable (never paste it into code):
        Mac/Linux:  export ANTHROPIC_API_KEY="your-key"
        Windows:    setx ANTHROPIC_API_KEY "your-key"   (then reopen the terminal)

Usage:
    python memo_agent.py DC            -> writes memos/DC.md
    python memo_agent.py all           -> writes all four
    python memo_agent.py DC --dry-run  -> shows the prompt, no API call, no cost
"""

import json
import os
import sys
from datetime import date

from pricer import price_hedge, money

AUTHOR = "Yash"                 # your name on every memo
MODEL = "claude-sonnet-5-5"     # good writing at a low cost (~2 cents per memo)
COVERAGES = (0.25, 0.50, 1.00)  # hedge sizes to show the CFO


def load_companies():
    with open("companies.json", encoding="utf-8") as f:
        return json.load(f)


def build_numbers(c):
    """Run the pricer and turn the results into plain text for the prompt."""
    lines = [
        f"{c.get('revenue_label', 'Annual revenue (2025)')}: {money(c['revenue'])}",
        f"Revenue at risk if the event happens: {money(c['revenue_at_risk'])}",
        f"Estimated probability: {c['probability']:.0%}",
        "Hedge options (event contracts pay $1 if the event happens; price = probability + 2c spread):",
    ]
    for cov in COVERAGES:
        h = price_hedge(c["revenue_at_risk"], c["probability"], coverage=cov)
        lines.append(
            f"  Cover {cov:.0%}: {h['contracts']:,.0f} contracts at ${h['price']:.2f} = cost {money(h['cost'])}; "
            f"if event: net {money(h['net_if_event'])} (vs {money(h['unhedged_if_event'])} unhedged); "
            f"if no event: {money(h['net_if_no_event'])}"
        )
    return "\n".join(lines)


def build_prompt(name, c):
    facts = "\n".join(f"- {f}" for f in c["key_facts"])
    reasoning = "\n".join(f"- {r}" for r in c["reasoning"])
    return f"""You are writing a one-page exposure memo for the CFO of {c['client']}.
The memo is from a broker that arranges event-contract hedges on CFTC-regulated exchanges.

EVENT: {c['event']}

NUMBERS (use exactly these; do not invent or change any figure):
{build_numbers(c)}

KEY FACTS (from filings and data; use only these facts):
{facts}

ANALYST REASONING:
{reasoning}

Write the memo in Markdown, under 400 words.
Start with this header, exactly:
**To:** CFO, {c['client']}  |  **From:** {AUTHOR}  |  **Date:** {date.today():%B %d, %Y}
**Re:** {c['event']}

Then these sections:
1. A one-sentence hook that makes the risk vivid using one fact above.
2. **The exposure**: what happens and what it costs.
3. **How likely it is**: the probability and where it comes from.
4. **The hedge**: a small table of the three coverage options, then a recommended option with one sentence of why.
5. **What this doesn't cover**: one or two honest limits.
6. **Next step**: one line.

Tone: direct, plain English, no hype. A busy CFO should get it in two minutes.
Do not give investment advice beyond describing the hedge options."""


def write_memo(name, c, dry_run=False):
    prompt = build_prompt(name, c)
    if dry_run:
        print(prompt)
        return

    import anthropic  # imported here so --dry-run works without the package

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. See the setup notes at the top of this file.")

    client = anthropic.Anthropic()  # reads the key from the environment variable
    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,                 # room for thinking + the memo
        messages=[{"role": "user", "content": prompt}],
    )
    # The reply can include a "thinking" block before the memo; keep only the text blocks
    memo = "".join(block.text for block in response.content if block.type == "text")

    if response.stop_reason == "max_tokens":
        print("Warning: the reply hit the length limit, so the memo may be cut off.")
    if not memo.strip():
        sys.exit("The reply had no memo text. Try running again.")

    os.makedirs("memos", exist_ok=True)
    path = os.path.join("memos", f"{name}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(memo)
    print(f"Wrote {path}  ({response.usage.input_tokens} in / {response.usage.output_tokens} out tokens)")


if __name__ == "__main__":
    companies = load_companies()
    if len(sys.argv) < 2:
        sys.exit(f"Usage: python memo_agent.py <{'|'.join(companies)}|all> [--dry-run]")

    target = sys.argv[1]
    dry = "--dry-run" in sys.argv
    names = list(companies) if target == "all" else [target]
    for n in names:
        if n not in companies:
            sys.exit(f"Unknown company '{n}'. Choose from: {', '.join(companies)}")
        write_memo(n, companies[n], dry_run=dry)
