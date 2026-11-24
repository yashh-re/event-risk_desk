# Blindspot

**The risks no one else is watching: pricing hedges for events insurance won't cover.**

Some of the biggest risks a company faces don't fit insurance or futures: a snowstorm that shuts New York's airports, a calm year for a wind farm, a superhero sequel that opens soft. Event contracts, which pay $1 if an event happens and $0 if it doesn't, can hedge them.

This project sizes and prices those hedges for four real companies and writes a one-page exposure memo for each CFO.

| Company | Event | Revenue at risk | Probability |
|---|---|---|---|
| JetBlue | A weather shutdown day in New York | $12.4M | 50% |
| CoreWeave | H100 GPU rental prices fall 25%+ | $25.7M | 30% |
| Clearway Energy | A low-wind year (5% shortfall) | $30.3M | 20% |
| Paramount / DC Studios | *Man of Tomorrow* opens below $100M | $99.0M | 25% |

## How it works

1. **Research:** each exposure is built from SEC filings (10-Ks), federal flight data, GPU price indexes and box office comps.
2. **Probability:** estimated from historical data, then adjusted with judgment. For JetBlue, 10 winters of Bureau of Transportation Statistics flight data (`jfk_storms.py`) found weather shutdowns in 5 of 10 winters.
3. **Pricing:** `pricer.py` sizes the hedge: one $1 contract per $1 protected, priced at probability plus a market-maker spread, at several coverage levels.
4. **Memos:** `memo_agent.py` sends the numbers, facts and reasoning to Claude, which drafts a CFO memo using only those inputs. Each memo is then reviewed and edited by hand.
5. **App:** `app.py` (Streamlit) shows each company's memo, the payoff chart and "what if" sliders for probability and coverage.

## Run it

```
pip install -r requirements.txt
streamlit run app.py
```

To generate memos (needs an Anthropic API key set as `ANTHROPIC_API_KEY`):

```
python memo_agent.py DC --dry-run   # shows the prompt, free
python memo_agent.py DC             # writes memos/DC.md
```

## Limits

These are sample memos built from public data, not trading advice or offers to trade. Probabilities are estimates from small samples, and a real contract would need a precisely defined, measurable trigger.

---
Built by Yashna | Finance and Informatics @ Indiana University.
