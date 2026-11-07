# Labelling guidelines

## Unit of analysis

The unit is **one news article**, represented by its headline plus the lead text
available for it (the paraphrased summary for the 15 seed articles; the publisher's
teaser or RSS description for collected articles, or the headline alone if the
source shows none). Each article gets exactly one label: its **primary** event, or
**No Risk Event**. Sentence-level or multi-event labelling is not used, because the
collected sources provide only a headline and a short teaser, so there are no
sentences to split, and because one label per article keeps the classifier,
evaluation and dashboard on the same unit. A secondary event may be noted in
`gold_secondary_event` for error analysis but is never scored.

Label the primary event: the development the headline and first sentence are about,
not every event mentioned. Labels are assigned by reading each article independently
of the rule output.

## No Risk Event

Use **No Risk Event** (risk category and severity "None") when the article reports
none of the events below. Typical cases: project launches and unveilings, progress or
milestone updates with no problem reported, product and equipment news, trade shows
and conferences (including a show being postponed), appointments, tenders and
shortlists before any award, partnerships and land deals, opinion or explainer
pieces that discuss risks in general without a specific event, and M&A.

## Event types and their risk category

| Event type | Risk category | Use when |
|---|---|---|
| Project Suspension | Operational | work paused, suspended, put on hold, re-scoped or scaled back |
| Contract Cancellation | Operational | a contract is terminated or cancelled |
| Project Delay | Operational | schedule slips, postponements, deadlines judged unrealistic |
| Supply Chain Disruption | Operational | shipping, materials, lead times, import dependence |
| Workforce Change | Operational | headcount cuts, relocations, labour shortages as the main story |
| Cost Overrun | Financial | budget growth or cost escalation on a project |
| Payment Risk | Financial | late/stretched payments, cash-flow and payment-term risk |
| Financial Result | Financial | company earnings, revenue, profit |
| Contract Award | Market | a named company wins/is awarded a contract |
| Market Trend | Market | sector-level statistics or outlooks (award volumes, forecasts) |
| Regulatory Change | Regulatory | new rules, permits, enforcement, compliance |
| No Risk Event | None | none of the above (see above) |

## Severity rubric

- **High**: work on a named project or contract has stopped, been cancelled or
  materially cut, a large budget increase on a named project, or an acute,
  sector-wide disruption.
- **Medium**: a risk is materialising (delay, dispute, cost/payment pressure,
  supply or labour constraint, regulatory tightening) but work continues.
- **Low**: positive or neutral news (awards, results, outlooks), descriptions of
  standard practice, or a trivial/short-lived issue (e.g. a three-day delay).

## Ambiguous items

Mark `ambiguous = yes` when two labels are defensible, and say why in `note`.
Results are reported with and without ambiguous items.

## Label status and review

A label is only gold standard after a person has read the source article and accepted
or corrected it. The real-world set's labels start as drafts (`label_status = draft`,
`annotator = claude-draft`). Review happens in `label_review.xlsx`; `apply_review.py`
sets `verified`, `corrected` or `excluded`. Reports must say how many labels were
reviewed and must not call draft labels gold.

Headline-only items (no teaser) are labelled from the headline, because that is all the
classifiers see. If the full article tells a different story, keep the headline-based
label and record the difference in the comment, so the error can be analysed later.
