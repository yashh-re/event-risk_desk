"""
Event-hedge pricer.

An event contract pays $1 if the event happens and $0 if it doesn't.
To protect $X of revenue, you buy X contracts. Each one costs about
the probability of the event, plus a small spread for the market maker.

Usage:
    python pricer.py
"""

# ---------------------------------------------------------------
# 1. The four companies, with the numbers from the research Sheet
# ---------------------------------------------------------------
COMPANIES = {
    "JetBlue": {
        "event": "Weather shutdown day in New York (>50% of NY flights cancelled)",
        "revenue": 9_062_000_000,
        "revenue_at_risk": 12_413_699,
        "probability": 0.50,
    },
    "CoreWeave": {
        "event": "H100 rental price index falls 25%+ in the next 12 months",
        "revenue": 5_131_000_000,
        "revenue_at_risk": 25_655_000,
        "probability": 0.30,
    },
    "Clearway": {
        "event": "Low-wind year (5% wind shortfall)",
        "revenue": 1_429_000_000,
        "revenue_at_risk": 30_326_695,
        "probability": 0.20,
    },
    "DC / Paramount": {
        "event": "Man of Tomorrow opens below $100M domestic",
        "revenue": 12_619_000_000,
        "revenue_at_risk": 98_992_000,
        "probability": 0.25,
    },
}


# ---------------------------------------------------------------
# 2. The pricing math
# ---------------------------------------------------------------
def price_hedge(revenue_at_risk, probability, coverage=1.0, spread=0.02):
    """
    revenue_at_risk : dollars lost if the event happens
    probability     : chance of the event (0 to 1)
    coverage        : share of the loss to protect (1.0 = all of it)
    spread          : extra cents per contract the market maker charges
    """
    contracts = revenue_at_risk * coverage          # one $1 contract per $1 protected
    fair_price = probability                        # fair price = chance of paying out
    price = min(fair_price + spread, 0.99)          # what the client actually pays
    cost = contracts * price

    payout_if_event = contracts * 1.0
    # Net result for the company in each scenario (loss + hedge)
    net_if_event = -revenue_at_risk + payout_if_event - cost
    net_if_no_event = -cost

    return {
        "contracts": contracts,
        "fair_price": fair_price,
        "price": price,
        "cost": cost,
        "payout_if_event": payout_if_event,
        "net_if_event": net_if_event,
        "net_if_no_event": net_if_no_event,
        "unhedged_if_event": -revenue_at_risk,
    }


def money(x):
    """Format dollars as $12.4M."""
    sign = "-" if x < 0 else ""
    if abs(x) >= 1e9:
        return f"{sign}${abs(x) / 1e9:,.1f}B"
    return f"{sign}${abs(x) / 1e6:,.1f}M"


# ---------------------------------------------------------------
# 3. Print a summary for each company
# ---------------------------------------------------------------
if __name__ == "__main__":
    for name, c in COMPANIES.items():
        h = price_hedge(c["revenue_at_risk"], c["probability"])
        print(f"=== {name} ===")
        print(f"Event: {c['event']}")
        print(f"  Revenue at risk:        {money(c['revenue_at_risk'])}")
        print(f"  Probability:            {c['probability']:.0%}")
        print(f"  Contracts to buy:       {h['contracts']:,.0f}  at ${h['price']:.2f} each "
              f"(fair ${h['fair_price']:.2f} + spread)")
        print(f"  Hedge cost:             {money(h['cost'])}  ({h['cost'] / c['revenue']:.2%} of revenue)")
        print(f"  If the event happens:   unhedged {money(h['unhedged_if_event'])}  ->  "
              f"hedged {money(h['net_if_event'])}")
        print(f"  If it doesn't happen:   hedged costs {money(h['net_if_no_event'])}")
        print()

    # Coverage choices for one company, to show the CFO the tradeoff
    name = "DC / Paramount"
    c = COMPANIES[name]
    print(f"=== {name}: how much to cover? ===")
    for cov in (0.25, 0.50, 0.75, 1.00):
        h = price_hedge(c["revenue_at_risk"], c["probability"], coverage=cov)
        print(f"  Cover {cov:>4.0%}: cost {money(h['cost']):>8}   "
              f"worst case {money(h['net_if_event']):>9}   no-event cost {money(h['net_if_no_event']):>8}")
