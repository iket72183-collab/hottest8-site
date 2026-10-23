# FakeCheck: evaluation gate, not an implemented detector

> Follow-up status: the original audit below records the first redesign. See [FOLLOWUP.md](FOLLOWUP.md) for the requested restored signup behavior, Fake Check copy/event, minimal homepage, sync script, and current test results.

The baseline contains a marketing page and shared newsletter embed. There is no classifier, scan backend, evidence store, platform-report integration, labeled evaluation set or reproducible proof for the old “100+ accounts” statement. The page remains **Coming Soon**. No creators were contacted, scans purchased, accounts reported or takedowns attempted.

These **synthetic offline scenarios** define expected handling; they are not human-labeled evaluation results or proof of accuracy:

| Fixture | Available evidence | Safe expected disposition |
|---|---|---|
| Main account | Creator-supplied stable ID | Authorized; no accusation |
| Backup | Linked from authorized main | Authorized; preserve evidence provenance |
| Third authorized alternate | Creator approval despite differing photo/name | Authorized; number of accounts is irrelevant |
| Fan page | Explicit fan disclosure, no creator claim | Fan context; not automatically an impersonator |
| Parody | Explicit parody disclosure | Parody context; no automatic accusation |
| Namesake | Same display name, unrelated biography | Unrelated/uncertain; similarity is insufficient |
| Renamed account | Same stable ID, changed handle | Identity continuity; don't flag old/new handles as duplicates |
| Recycled handle | Changed stable ID | New identity; request review, never inherit authorization |
| Missing photo | No image available | Missing evidence, not positive fraud evidence |
| Similar image | Resemblance without provenance | Uncertain; image confidence is not authorization evidence |
| Alleged impersonator | Synthetic copied claims, no creator review | Candidate for human review only; no public label/report |

Before launch, obtain a permissioned **human-labeled** corpus covering these cases and relevant platforms/languages, with creator authorization records, provenance and review dates. Keep train/tuning and held-out creators separate. Have independent reviewers adjudicate disagreements and honor creator appeals/corrections. Do not label these synthetic examples as a measured benchmark.

Report confusion matrices, precision, recall, false-positive rate (FP / (FP + TN)), sample sizes and uncertainty intervals by scenario/platform. Show abstention/coverage and missed impersonations; missing images must be a separate slice. Define false-positive tolerance and decision thresholds before evaluation with the owner and affected creator reviewers. No threshold or performance figure is established here.

Every candidate needs separate evidence fields (source URL, stable ID, capture date, explicit claim, authorization/disclosure and reviewer decision) and model confidence, if any. Confidence must never replace evidence. Require creator review before any accusation, report or takedown step. Platform reporting rules and data-use permissions must be verified separately. No automatic reporting is included in this branch.
