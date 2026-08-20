# Recurring-charge engine (v2.4)

## Problem

Subscripz-Buster is a pile of near-duplicate scanners that grep Apple Mail
**subject lines** for words like `payment` and `plan`. That is why the product
grew a 17-option menu, a 1000-domain "fraud" blacklist, and still cannot answer
the only question that matters:

> What is charging me on a cadence, how much, and what should I cancel?

Keyword hits are recall. Recurrence is the product. Rocket Money / Truebill
win because they detect **the same merchant taking a similar amount on a
regular interval**, then rank actions. This repo never computed that.

## Constraints

- Stay **100% local**. No bank linking, no telemetry, no DNS "fraud" lookups.
- Apple Mail Envelope Index remains the default source (subjects, senders,
  dates; snippet when the column exists).
- Must be testable on Linux without Apple Mail (fixture messages + synthetic
  Envelope Index via `--mail-db`).
- Legacy scanners stay in the repo. They are not the product surface.

## Approaches considered

1. **More scanners / keywords / blacklists** — already tried; more false
   positives and more menu options. Rejected.
2. **Gmail API as the leap** — Google client libs are already unused
   dependencies. Expands TAM but still keyword-greps if the engine stays
   the same. Deferred.
3. **Recurrence engine + one CLI + in-process MCP** — recommended. Changes
   what the product computes. Mail source becomes an adapter.

## Architecture

```
source adapter  →  Message
extract         →  Charge (merchant, amount, hints)
cluster         →  Series (cadence, confidence)
actions         →  ranked cancel / consolidate / review / keep
report          →  text or JSON
```

Units:

- `subscripz.sources.apple_mail` — Envelope Index → `Message`
- `subscripz.sources.messages` — JSON fixture → `Message`
- `subscripz.merchants` — domain / alias / subject → merchant identity
- `subscripz.extract` — amount + status hints from subject/snippet/body
- `subscripz.recurrence` — interval inference from charge dates
- `subscripz.actions` — action plan from series
- `subscripz.engine` — pipeline; injectable `now` for tests
- `subscripz.cli` — `python -m subscripz scan`

A series is a subscription when cadence is detected **or** (explicit
subscription language + amount) **or** (known merchant + billing language
+ amount). A single Amazon "your order shipped" is not a subscription.

## Action rules

- `cancel_unused` — inferred cycle, last charge older than 1.6 cycles, not cancelled
- `consolidate` — same merchant, two or more real recipient accounts
- `review_price_hike` — latest amount ≥ 20% over earlier median
- `review_trial` — trial language, no later paid cadence
- `keep` — recent, consistent, one account

## Surfaces

- CLI: `python -m subscripz scan [--days] [--mail-db] [--output-json] [--format json|text] [--quiet] [--dry-run]`
- MCP: `hunt_recurring_charges`, `subscription_action_plan` (in-process)
- Menu option 18 in `scan_subscriptions_now.py`

## Out of scope (next slices)

- Gmail / IMAP adapters
- `.emlx` body parsing
- Cancel-link extraction
- Web dashboard
- Deleting legacy scanners
