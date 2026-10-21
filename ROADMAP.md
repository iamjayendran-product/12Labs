# 12Labs — Q1 2027 Product Roadmap

_Generated 2026-10-21T11:33:20Z · derived from 51 voice of customer, 32 crm, 10 fireflies, 42 nps / support, 6 commitment_

**How this was built.** Contractual commitments are pinned first, earliest deadline first. Everything else is ranked by RICE (Reach × Impact × Confidence ÷ Effort) and fills the remaining squad capacity. Reach is computed from the ARR-weighted accounts that asked for the item.

## At a glance

| Month | Theme | Committed | RICE-ranked | Capacity used |
|---|---|---|---|---|
| January 2027 | Enterprise readiness | 5 | 1 | 46/48 pw |
| February 2027 | Enterprise readiness | 0 | 4 | 45/48 pw |
| March 2027 | Developer platform | 1 | 6 | 46/48 pw |

## January 2027 — Enterprise readiness

Capacity: Voice Quality 14/16 pw · Platform & SDK 16/16 pw · Growth & Enterprise 16/16 pw

### Committed (pinned)

- **P1 support response SLA and priority queue** — RICE 4.22 · Growth & Enterprise · 4 pw · **Committed — due 2027-01-15**
  A nine-hour first reply during an outage cost Clearline trust; several accounts now ask for a written response-time commitment and free-tier delays make evaluators doubt paid support.
  _7 accounts · $370k ARR · 11 quotes_
  > “They want a written support SLA with a 1 hour response on P1 tickets.” — Clearline Support Co. (CRM)
  > “support took over 24 hours to raise it” — Meridian Legal Docs (Voice of customer)
  > “Friday night on-sale broke and the ticket sat in the queue for hours. Need a response SLA for events.” — Turnstile Ticketing (NPS / support)

- **SAML SSO and SOC 2 Type II** — RICE 2.04 · Growth & Enterprise · 10 pw · **Committed — due 2027-01-31**
  Enterprise buyers will not add a vendor that sits outside their identity provider or lacks a SOC 2 Type II report; Vantage's 300k expansion is gated on both, and three more security-led prospects stalled on the same ask.
  _6 accounts · $638k ARR · 11 quotes_
  > “SSO/SAML took an extra round of back-and-forth with your team to configure correctly” — Vantage Enterprise Systems (Voice of customer)
  > “Our IT team needs SAML SSO via Okta before more attorneys can be added.” — Meridian Legal Docs (NPS / support)
  > “SSO required by their own customers' security review.” — Ironclad Security Training (CRM)

- **VPC / private-cloud deployment** — RICE 0.82 · Platform & SDK · 20 pw · **Committed — due 2027-03-15** · ships 2027-02
  Healthcare, banking and public-sector buyers cannot send audio through a shared multi-tenant endpoint; Solace's renewal is gated on a HIPAA-ready VPC deployment by mid-March.
  _7 accounts · $722k ARR · 11 quotes_
  > “Legal wants a VPC deployment with a BAA.” — Solace Health (CRM)
  > “a Germany-resident deployment option” — Berlin Transit Authority (NPS / support)
  > “Only if it is in our cloud account. HIPAA review is strict.” — Pulse Telehealth (Voice of customer)

- **Android SDK streaming parity with iOS** — RICE 0.75 · Platform & SDK · 12 pw · **Committed — due 2027-02-15**
  The Android SDK has no streaming playback, so Android-heavy customers pre-render audio or delay features; Junction renewed on a promise of parity.
  _4 accounts · $246k ARR · 9 quotes_
  > “The Android SDK, though, is noticeably behind” — Junction Mobile (Voice of customer)
  > “Half their users are on Android.” — TrueNorth Fitness App (CRM)
  > “Android streaming for offline-first guides?” — Alpine Trail Guides (NPS / support)

- **Natural Modern Standard and Gulf-dialect Arabic voices** — RICE 0.57 · Voice Quality · 14 pw · **Committed — due 2027-02-28**
  Existing Arabic voices sound robotic and diacritics are handled inconsistently; Beacon's three-year deal is conditional on both MSA and Gulf-dialect voices.
  _3 accounts · $248k ARR · 7 quotes_
  > “diacritics handling is inconsistent” — Beacon Arabic Media (Voice of customer)
  > “Arabic could be a second wish.” — Baraza News (NPS / support)
  > “then Arabic for Gulf plants” — Vega Robotics (Voice of customer)

### Prioritised by RICE

- **Multiple billing contacts per account** — RICE 0.25 · Growth & Enterprise · 2 pw
  Only one contact receives invoice emails; a missed payment triggered a service-pause warning.
  _1 account · $35k ARR · 1 quote_
  > “our account has two different billing contacts and only one of them receives the invoice emails” — Skyline Property Management (Voice of customer)

## February 2027 — Enterprise readiness

Capacity: Voice Quality 16/16 pw · Platform & SDK 16/16 pw · Growth & Enterprise 13/16 pw

### Prioritised by RICE

- **Pronunciation dictionary / shared lexicon** — RICE 2.40 · Voice Quality · 6 pw
  Names, acronyms and terminology are mispronounced and the fix does not persist, so teams re-record or maintain manual overrides.
  _9 accounts · $995k ARR · 14 quotes_
  > “a few of our stations get mispronounced and we've had to add manual overrides.” — Berlin Transit Authority (Voice of customer)
  > “Also wants a custom pronunciation lexicon so product names are read correctly every time.” — Zenith Translation Services (CRM)
  > “Add words once, and every voice respects them.” — Fenwick Games (Fireflies)

- **Usage analytics dashboard and API** — RICE 1.50 · Growth & Enterprise · 10 pw · pulled forward for usage-based-pricing
  Customers cannot see minutes used per project, campaign, property or program, so finance rebuilds reports by hand; the existing usage view also lags billing by a day.
  _7 accounts · $527k ARR · 13 quotes_
  > “Wants a usage dashboard with per-project breakdown and CSV export.” — Northwind Media (CRM)
  > “Want a usage API to pull minutes and cost into our BI tool.” — Insight Analytics (NPS / support)
  > “The usage dashboard lags behind actual billing by about a day” — Legacy Radio Network (Voice of customer)

- **Sub-300 ms time-to-first-byte streaming tier** — RICE 1.49 · Voice Quality · 20 pw · ships 2027-03
  Real-time voice agents, live dubbing and phone ordering need first audio under 300 ms; measured 600-1200 ms today. Chatterbox already delayed its launch waiting for a promised low-latency tier.
  _9 accounts · $612k ARR · 15 quotes_
  > “That is too slow. Passengers are already walking away by the time the voice starts.” — Berlin Transit Authority (Fireflies)
  > “latency is far too high for live use” — Hanbit Streaming (NPS / support)
  > “Ship the low-latency streaming tier and a volume pricing plan” — Insight Analytics (Voice of customer)

- **Volume discounts and annual-prepay option** — RICE 0.99 · Growth & Enterprise · 3 pw
  Finance teams at scaling accounts want volume tiers or an annual discount; this partly conflicts with the push for pure pay-as-you-go.
  _5 accounts · $371k ARR · 5 quotes_
  > “rough pricing pain as we scale” — Insight Analytics (Voice of customer)
  > “Volume discounts past a certain threshold, or a flat monthly tier for high-usage studios” — Fenwick Games (Voice of customer)
  > “The character pricing didn't help” — Lumen Publishing (Voice of customer)

### Continuing from earlier months

- **VPC / private-cloud deployment** — continues from 2027-01 (16 pw this month, ships 2027-02)

## March 2027 — Developer platform

Capacity: Voice Quality 14/16 pw · Platform & SDK 16/16 pw · Growth & Enterprise 16/16 pw

### Committed (pinned)

- **Reliable webhooks: retries, signing, delivery log** — RICE 2.32 · Platform & SDK · 6 pw · **Committed — due 2027-03-31**
  Failed webhooks are dropped silently with no retry or log, so customers find out from their own users; Rapidfire's renewal carries a credit if guarantees are not live by end of March.
  _5 accounts · $385k ARR · 11 quotes_
  > “We found out from our customers, not from you.” — Clearline Support Co. (Fireflies)
  > “A retry-with-backoff on your end would fix this for us.” — Rapidfire Logistics (Voice of customer)
  > “Webhook failures are also invisible.” — Insight Analytics (NPS / support)

### Prioritised by RICE

- **Usage-based (pay-as-you-go) pricing tier** — RICE 2.41 · Growth & Enterprise · 8 pw
  The flat seat plan is wrong for spiky or small workloads; prospects want per-minute billing with overage caps and cost that scales with usage.
  _11 accounts · $383k ARR · 14 quotes_
  > “pay-as-you-go per-minute pricing would let them start immediately” — Hanbit Streaming (CRM)
  > “Flat plan is wasteful for a small show. Want pay-as-you-go per-minute pricing.” — Nightshift Podcast Network (NPS / support)
  > “A per-minute pay-as-you-go plan is the only way our model works.” — Kite Education (Voice of customer)

- **Streaming/websocket docs, SDK examples and SSO setup guide** — RICE 1.17 · Platform & SDK · 3 pw
  Docs for websocket streaming, SDK examples and SSO configuration trail the REST docs.
  _3 accounts · $910k ARR · 4 quotes_
  > “the self-serve docs for SSO setup are thinner than the rest of the docs” — Vantage Enterprise Systems (Voice of customer)
  > “The Python SDK examples are a bit behind” — Solace Health (Voice of customer)
  > “the websocket streaming docs are thinner than the REST docs” — Pixelforge Studio (Voice of customer)

- **Recorded voice-clone consent workflow** — RICE 0.67 · Growth & Enterprise · 8 pw
  Clone creation already verifies consent at a single point, but agencies, studios and narrators need an auditable per-voice consent record they can show their clients and talent.
  _6 accounts · $335k ARR · 9 quotes_
  > “Their compliance team also wants documented consent from any person whose voice is cloned, before the clone can be used.” — Meridian Legal Docs (CRM)
  > “A consent workflow that records permission would help.” — Whisperwind Games (NPS / support)
  > “Narrators want written consent before any voice clone is created.” — Mosaic Audiobooks (Voice of customer)

- **Bulk-job status and per-item failure reporting** — RICE 0.40 · Platform & SDK · 4 pw
  Batch jobs do not say which files or chapters failed, so teams check outputs manually.
  _2 accounts · $80k ARR · 2 quotes_
  > “when we submit 50 files at once, we can't easily see which ones failed” — Nightshift Podcast Network (Voice of customer)
  > “If one chapter fails mid-batch, the whole batch doesn't tell you which chapter failed in the response” — Lantern Library Services (Voice of customer)

- **Predictable rate-limit windows and self-serve raises** — RICE 0.34 · Platform & SDK · 3 pw
  Limits reset unpredictably at midnight UTC and a limit hit during a deadline took more than a day to raise.
  _2 accounts · $110k ARR · 2 quotes_
  > “We hit our rate limit during a compliance deadline crunch” — Meridian Legal Docs (Voice of customer)
  > “The rate limits reset unpredictably around midnight UTC rather than a clear rolling window” — Overdrive Motorsports Media (Voice of customer)

- **Consistent reading of times, numbers and dates** — RICE 0.06 · Voice Quality · 4 pw
  Times such as 3:45 PM are read inconsistently so every announcement is hand-checked.
  _1 account · $40k ARR · 2 quotes_
  > “sometimes comes out with an odd pause” — Turnstile Ticketing (Voice of customer)

### Continuing from earlier months

- **Sub-300 ms time-to-first-byte streaming tier** — continues from 2027-02 (10 pw this month, ships 2027-03)

## Below the line

Ranked by RICE but no squad capacity left this quarter (or blocked by a dependency).

| Item | Squad | Effort | RICE | Reach | Why not |
|---|---|---|---|---|---|
| Hindi voices | Voice Quality | 12 pw | 0.91 | 6 accounts · $230k | no voice-quality capacity left this quarter |
| Unity and Unreal engine plugins | Platform & SDK | 8 pw | 0.45 | 4 accounts · $250k | no platform-sdk capacity left this quarter |
| Clean interruption (barge-in) handling for voice agents | Voice Quality | 8 pw | 0.12 | 1 account · $140k | no voice-quality capacity left this quarter |
| Production-grade Swedish, Finnish and Japanese | Voice Quality | 12 pw | 0.12 | 2 accounts · $130k | no voice-quality capacity left this quarter |
| Dashboard transcript search and dark mode | Growth & Enterprise | 5 pw | 0.08 | 2 accounts · $38k | no growth capacity left this quarter |
| Automated migration of voice presets | Platform & SDK | 3 pw | 0.07 | 1 account · $25k | no platform-sdk capacity left this quarter |
| Faster voice-marketplace approval | Growth & Enterprise | 4 pw | 0.06 | 1 account · $0k | no growth capacity left this quarter |
| Inline emotion tags in the API | Platform & SDK | 6 pw | 0.05 | 1 account · $85k | no platform-sdk capacity left this quarter |
| Multi-speaker dialogue in one generation call | Voice Quality | 10 pw | 0.05 | 1 account · $75k | no voice-quality capacity left this quarter |
| Broadcast-grade MP3 export | Platform & SDK | 3 pw | 0.04 | 1 account · $52k | no platform-sdk capacity left this quarter |
| Swahili voices | Voice Quality | 10 pw | 0.03 | 1 account · $28k | no voice-quality capacity left this quarter |
| Salesforce connector | Growth & Enterprise | 8 pw | 0.02 | 1 account · $22k | no growth capacity left this quarter |

## Risks and flags

- **Larger than one squad-month** (spans months; consider splitting): streaming-latency, vpc-deployment

## Commitment register

| ID | Account | Commitment | Due | ARR at risk | Scheduled |
|---|---|---|---|---|---|
| com_002 | Clearline Support Co. | Contractual 1-hour P1 support response SLA. | 2027-01-15 | $140k | 2027-01 → 2027-01 |
| com_001 | Vantage Enterprise Systems | Deliver SAML SSO and a SOC 2 Type II report to Vantage. | 2027-01-31 | $480k | 2027-01 → 2027-01 |
| com_003 | Junction Mobile | Ship Android SDK with streaming playback parity with iOS. | 2027-02-15 | $190k | 2027-01 → 2027-01 |
| com_004 | Beacon Arabic Media | Deliver Modern Standard and Gulf-dialect Arabic voices. | 2027-02-28 | $220k | 2027-01 → 2027-01 |
| com_005 | Solace Health | Offer VPC deployment with BAA for HIPAA workloads. | 2027-03-15 | $360k | 2027-01 → 2027-02 |
| com_006 | Rapidfire Logistics | Webhook delivery guarantees: retries, signing, delivery log. | 2027-03-31 | $120k | 2027-03 → 2027-03 |
