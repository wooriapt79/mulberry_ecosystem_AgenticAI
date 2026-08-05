# Luna–AI Inje Tokenizer Integration v0.2

Status: Draft / Human review required  
Scope: A-1 and A-2 only

## Purpose

The AI Inje L4 lexicon seed is derived from Luna Open Reception's governed `food-desert-v1` Domain Pack. This PR does not collect resident utterances, enable production routing, or authorize deployment.

## Governed flow

```
Luna Domain Pack
→ structural policy snapshot
→ Inje L4 seed
→ field verification (later, explicit consent required)
```

The sync check compares the complete policy structure:

- request types
- required competencies
- required permissions
- maximum risk
- supervision level
- junior eligibility
- Domain Pack and Matching policy versions

Any value change fails validation until the mirror and generated lexicon are reviewed and updated.

## Privacy and safety boundaries

- `surface_forms` remains empty and `verified=false` until field verification.
- No resident utterance, identity, address, contact detail, or reception log is stored in the lexicon.
- Language contribution is opt-in only and belongs in a separately authorized data path.
- Withdrawal, retention, access control, and Participation Passport linkage must be approved before collection.
- Default operating modes remain `dry_run` and `recommendation_only`.
- Deployment, external effects, and merging require separate Human approval.

## Implemented in this Draft PR

- A-1: Domain Pack → lexicon seed generation
- A-2: schema and repository location
- structural drift detection using Python AST without executing policy source
- invariant tests for privacy, provenance, empty surface forms, and generated output

## Explicitly out of scope

- B-series consent and utterance collection
- C-series tokenizer performance measurement
- production deployment, payment, messaging, or external API effects

## Merge gate

1. Structural sync and lexicon tests pass.
2. No personal-data fields appear in generated entries.
3. Generated JSON matches the reviewed generator.
4. Human reviewers confirm scope and governance boundaries.
5. PR remains Draft until the representative authorizes readiness.

SIL Eum / CSA KeBin review baseline
