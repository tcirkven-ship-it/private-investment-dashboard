# Price-gated overlay — decision

2 gated model(s) pass the 15/30 overlap gate:
- A3 G3_QVETO: 21/30 overlap
- B2 G3_QVETO: 22/30 overlap

## Corrected experiment status

ADDITIVE QVP ARCHITECTURES FAIL PRICE-IDENTITY GATE;
PERFORMANCE EFFECT UNTESTED.

Historical QVP proxy comparison was NOT completed.
The feasibility plan exists but the statement-extraction
infrastructure was not built in this task.

## Decision

**ADOPT A3 G3_QVETO FOR SHADOW MODE**

G3 (Quality veto) retains 21/30 of P100 top 30 while
excluding bottom-10% Quality stocks. This is the only gated model that
both passes the Price-identity gate and materially adds Quality screening.
Historical proxy computation deferred to follow-up task.