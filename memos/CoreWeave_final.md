**To:** CFO, CoreWeave (CRWV)  |  **From:** Yashna  |  **Date:** November 24, 2026
**Re:** H100 rental price index falls 25% or more over the next 12 months

Your contracts already hedge 98% of this risk. Here's the 2% they don't. A 25% drop in H100 rental prices could still cost CoreWeave $25.7M in revenue.

**The exposure**
Only the ~2% on-demand slice of revenue (~$103M of $5.1B) reprices with the market right away. A 25% price drop on that slice is about **$25.7M** of lost revenue. The committed contracts, backed by $60.7B of remaining performance obligations, don't move with spot prices.

**How likely it is**
We estimate **30%**. History points to about 65%, since the H100 index fell from about $8/hr in early 2024 to about $2.00 in Dec 2025. But those drops came from post-shortage normalization. The index has since recovered to about $3.10, and capacity is sold out, so we weight the historical rate down.

**The hedge**
Event contracts pay $1 if the event happens. The price is $0.32 (30% probability plus a 2c spread).

| Cover | Contracts | Cost | Net if event | Net if no event |
|---|---|---|---|---|
| None | n/a | $0 | -$25.7M | $0 |
| 25% | 6,413,750 | $2.1M | -$21.3M | -$2.1M |
| 50% | 12,827,500 | $4.1M | -$16.9M | -$4.1M |
| 100% | 25,655,000 | $8.2M | -$8.2M | -$8.2M |

**Recommended: Cover 25%.** The exposure is a small slice of revenue and the event is more likely not to happen, so the smallest premium ($2.1M) gives some protection at the lowest cost. Cover 100% turns the outcome into a certain -$8.2M either way.

**What this doesn't cover**
- **Bigger risks than price.** Microsoft was 67% of 2025 revenue, and you carry $1.2B of annual interest expense on debt partly backed by GPUs. This hedge does nothing for customer concentration or debt.
- **Index mismatch.** The contract settles on the H100 rental index, not your own realized prices, so payouts may not match your actual loss.
- **Renewals.** When committed contracts expire, they renew at market prices, so a lasting price drop would also hit future revenue. This hedge only covers the next 12 months.

**Next step**
Tell me which coverage level you want to consider, and I'll get firm quotes from the exchange.

---
Sample memo prepared by Yashna using public filings and market price data. Not an offer to trade