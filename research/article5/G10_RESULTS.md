# ABS-05 Gate G10 Result

**Gate status: PASS**

**Article readiness: READY FOR A FINDINGS OUTLINE WITH RESTRICTIONS**

**Playbook status: PROHIBITED**

G10 completed the final reproducibility audit for the accepted Article 5
analytical package. Every required generator ran successfully twice from empty,
isolated output trees. The two builds produced the same relative file set and
all 44 generated files were byte-identical, with no timestamp or other
exclusions.

## Scope

Each clean run rebuilt, in order:

1. G5 correction values;
2. G6 probability benchmarks;
3. G7 dynamic engine outputs;
4. G8 stability outputs using an independent empty derived-data cache;
5. the bounded G8 objective-scale follow-up; and
6. G9 effect-size and falsification outputs.

The comparison covered 44 files: one independently generated G8 cache file,
five G5 files, seven G6 files, seven G7 files, eight G8 files, eight objective
follow-up files, and eight G9 files. Each tree contained approximately 459 MB
(438 MiB). File names, sizes, SHA-256 values, and bytes all matched.

G0 through G4 were verified from their accepted audit artifacts rather than
regenerated into the repository. The accepted input-audit JSON and report
hashes, all four early gate statuses, 34-file provenance audit, and frozen
preregistration hash reconciled. Protected inputs were unchanged before and
after the paired builds.

## Preserved scientific outcomes

Reproducibility did not convert restricted or failed scientific results into
passes. Both builds independently preserved all of the following:

- G5 correction value: pass;
- G6 computation: pass, with player probability not identified;
- G7 computation: pass, with `deltaW=0` by construction;
- G8 stability: failed, with the playbook prohibited;
- G8 win-probability follow-up: model rejected, original failure unchanged;
  and
- G9: numerical upper benchmark passed, deployable policy improvement not
  demonstrated.

This is the intended safeguard behavior: a repeatable model can still be too
assumption-sensitive or insufficiently identified for prescriptive advice.

## Readiness consequence

The research package is ready for the next editorial artifact: a findings
outline that clearly separates measured results, modeled quantities, and
assumptions. It may explain the Challenge Threshold as a decision framework and
report the validation failures as findings.

It may not provide situational challenge recommendations, claim that players or
teams should follow the dynamic benchmark, judge observed decisions, or produce
the Pascal ABS Challenge Playbook. Any future attempt to obtain those products
requires a new reviewed research plan that resolves the decision-time
information, counterfactual game-path, objective-scale, stability, and
strategic-response limitations.

## Verification

- All 12 generator invocations returned success.
- All 11 G10 conditions passed.
- All 40 focused Article 5 unit tests passed.
- No generated file differed across the two clean builds.
- No protected input changed.

The broader repository suite was not rerun as a G10 acceptance condition. G9
already recorded its legacy Sprint 3 manifest test issue and verified the two
affected downstream Sprint 4 tests after restoring the accepted backup. G10
used the focused Article 5 suite so it would not rewrite that ignored historical
fixture.

## Summary artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| `VALIDATION.md` | `dc17d000d29213ddc33a919595ba4ce4f6175d3c68baf6cd76600ce8f4e0e2e2` |
| `commands.json` | `6c489fe79a6a367eadeb07ddcb0ce7f4962269d34d5cea61564e5dc0c03a46ed` |
| `comparison.csv` | `25074475f625d53f59d6f84ec529ed197af089a0f3f690540aa1654e85d518b9` |
| `validation.json` | `2466b15041e9a93eb6f942ec46c0dc929376dea3c815907b18862faf6e53029a` |

## Commands and resources

Each run used the repository's `.venv-article5/bin/python` interpreter with an
explicit `--root` and isolated `--output`; G8 also received its own isolated
`--cache`. The focused test command was:

```text
.venv-article5/bin/python -m unittest discover -s tests -p 'test_article5*.py'
```

The audit used only the locked local snapshot and local computation. It
consumed no live data, paid source, GitHub Actions, Vercel, Supabase, Odds API,
hosted database, production system, Google Drive operation, or additional
Claude exchange.
