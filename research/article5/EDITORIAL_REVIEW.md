# ABS-05 Editorial Review

> **Successor notice:** This review predates the failed `CT-2026` build and the
> later CT-S1 confirmation program. Its broad narrative guidance remains useful,
> but `CT_S1_PUBLIC_CLAIMS.json`, `CT_S1_CTS11_RESULTS.md`, and
> `CT_S1_DRAFTING_DECISION.md` now control numerical wording, version identity,
> examples, and prohibitions. Do not follow the `CT-2026` naming or next-gate
> language below.

## Decision

**GO FOR A CHALLENGE THRESHOLD ARTICLE AND REFERENCE EVALUATOR.**

Article 5 should introduce **Challenge Threshold** as a common scale for viewing
an ABS decision: the minimum confidence that a call is wrong required for a
challenge to break even under a declared value model. The metric prices the
situation. It does not estimate a particular player's confidence, perception,
ability, or intent.

That distinction is foundational. Player confidence will always vary, just as
the outcome of a batted ball varies around an expected statistic and recognized
WAR implementations vary around a shared framework. A useful baseball metric
does not need to be definitive. It needs a stable definition, defensible inputs,
transparent assumptions, consistent interpretation, and honest uncertainty.

The preregistration anticipated this result: “The threshold itself is primary
and model-free. Mapping evidence to `p` is a separate secondary layer.” It also
states that failure to identify player probability does not invalidate
model-free threshold tables. The earlier editorial framing placed too much
weight on the missing perception layer and is superseded by this review.

The G8 stop still matters. It prohibits an empirical playbook, evidence-to-action
claims, judgments of observed decisions, and a universal “optimal” policy. It
does **not** prohibit an explicitly assumption-labeled reference evaluator.

## What kind of metric this is

Challenge Threshold belongs to a familiar class of baseball evaluators:

- Expected statistics place an event on a probability scale using a defined set
  of inputs. They are informative without claiming that the estimated outcome
  was destined to occur.
- WAR places performance on a shared value scale even though respected systems
  make different modeling choices and produce different estimates.
- Challenge Threshold places an ABS opportunity on a required-confidence scale.
  It can be useful even though the player alone supplies the final confidence
  judgment and alternative defensible option-value models produce a range.

The proper public statement is therefore:

> **Challenge Threshold tells you how sure you need to be. It does not tell you
> how sure you are.**

This is an evaluator, not an oracle. Broadcasters, coaches, players, journalists,
and fans can use the same number while reaching different decisions because
their evidence and risk preferences differ.

## Editorial scorecard

| Dimension | Result | Editorial judgment |
| --- | --- | --- |
| Mathematical definition | Pass with restriction | The break-even definition is valid under the stated value model; the current G7 implementation has `deltaW=0` by construction. |
| Reference evaluator | Go | Model-free and assumption-labeled thresholds are authorized by the preregistration and G10. |
| Player-confidence estimate | Not identified | This is a separate layer and is not required to publish the evaluator. |
| Empirical playbook | No-go | G8 instability, the rejected win model, and unmodeled strategic response prohibit prescriptive action rules. |
| Industry usefulness | Promising | A percentage scale is intuitive, comparable across situations, and suitable for broadcast and editorial use. |
| Visual discipline | Revise | The threshold spectrum should be the centerpiece; repeated Article 4 charts and the G9 upper benchmark should not be main figures. |
| Conversion path | Revise in site build | Research subscription remains the primary call to action; the AnalytIQ beta invitation remains separate. |

## Locked public framing

### Title

**How Sure Is Sure Enough to Challenge an ABS Call?**

Recommended HTML title:

> ABS Challenge Threshold: How Sure Is Sure Enough? | Pascal Institute

Recommended description:

> Challenge Threshold puts every ABS decision on one scale: the minimum
> confidence required for a challenge to be worth the risk.

Article 2 already uses “The Challenge Threshold” in a behavioral study of what
makes hitters challenge. Article 5 should explicitly connect the two meanings:
Article 2 measured the behavioral threshold; Article 5 defines the value-based
break-even threshold. The site may later use a clarifying subtitle for Article 2,
but its existing URL does not need to change.

### Thesis

The value of the call and the cost of losing inventory determine how confident
a player needs to be. Challenge Threshold measures that required confidence;
the player, catcher, coach, or team determines whether their evidence clears it.

### Reader promise

The reader will be able to interpret a Challenge Threshold percentage correctly,
understand why it changes, and understand why it cannot by itself judge a player.

### Series bridge

Article 4 asked what a challenge was worth. Article 5 turns those values into a
common decision scale. Article 4's correction-value distribution, declining
inventory value, and unused-unit statistics are inputs and context rather than
discoveries to retell at length.

## Challenge Threshold reference standard

Before final prose, create a short, versioned metric specification. The first
publication should be labeled **Challenge Threshold 2026** or **CT-2026**, not
presented as an unchanging law of baseball.

The specification must define:

1. **Unit:** required confidence, expressed as a percentage from 0% to 100%.
2. **Orientation:** lower means less confidence is needed to justify the risk;
   higher means stronger evidence is required.
3. **Immediate value (`V`):** the expected-run gain if an incorrect call is
   corrected, using the named constrained run-expectancy estimator.
4. **Inventory cost (`C`):** the marginal future expected-run value of the
   challenge unit under one named reference opportunity and usage policy.
5. **Continuation term (`deltaW`):** zero only in the present fixed-path
   implementation; the limitation must travel with every published value.
6. **Reference estimate:** one reproducible CT value under the declared model.
7. **Sensitivity range:** the range across approved alternative estimators and
   policies. Material instability must be visible, not averaged away.
8. **Version:** data window, rules, estimator version, and publication date.
9. **Coverage:** which offense/defense, inventory, inning, count, base-out, and
   score states are supported.

Under the restricted current formulation:

```text
Challenge Threshold = C / (V + C)
```

The general formulation retains `deltaW`:

```text
Challenge Threshold = C / (V + deltaW + C)
```

The reference standard should be recalculated and versioned when the run
environment, ABS rules, challenge allotment, opportunity distribution, or
reference policy materially changes. Historical versions should remain
available so the metric is auditable rather than silently rewritten.

## Required narrative structure

Target **1,900–2,300 words**, excluding the methodology summary and references.

1. **The player has to decide before knowing the answer.** Open on a generic,
   split-second choice. Avoid a historical example that implies a player erred.
2. **Every challenge has three prices.** Briefly recap correction value, failure
   cost, and pass cost from Article 4. Introduce the break-even percentage.
3. **Challenge Threshold puts the decision on one scale.** Show how to read the
   metric and contrast representative low- and high-threshold states under the
   same named assumptions. These are evaluations of the situation, not commands.
4. **The number does not know what the player knows.** Use G6 to separate the
   required threshold from subjective confidence. Challenged pitches succeeded
   53.7% of the time while the public benchmark predicted 24.9%; this shows
   selection on information or processes omitted from the benchmark, not proof
   of skill and not a defect in the threshold definition.
5. **A standard needs uncertainty and versions.** Present the G8 sensitivity
   failure honestly. Where assumptions materially move the threshold, publish a
   range and label the reference policy. Do not convert unstable values into a
   color-coded playbook or a claim that a particular action was correct.
6. **A shared lens, not a final verdict.** Explain how a broadcaster, coach,
   player, journalist, and fan can use the same threshold differently. End on
   the metric's durable purpose: making the price of the decision visible.

Keep the G9 exact-future result in the companion methodology. If the 0.91-run
upper benchmark appears anywhere in public copy, place the shuffled-label
falsification immediately beside it and state that the gain is not achievable.

## Publication figure brief

The main article may use **four figures**:

1. **The Three Prices of a Challenge** — the decision tree and the restricted
   threshold equation.
2. **How to Read Challenge Threshold** — a percentage spectrum with carefully
   selected representative states under one named reference specification.
3. **The Same Threshold, Different Beliefs** — show that a 40% threshold remains
   40% while people with different evidence may estimate their confidence above
   or below it. The confidence values are illustrative, not empirical estimates.
4. **One Metric, a Visible Range** — show the reference estimate and sanctioned
   sensitivity range for representative states, including the G8 stability
   warning where material.

Do not repeat Article 4's correction-value concentration or declining
option-value charts. Do not make G9 a main figure. Do not produce the originally
proposed Pascal ABS Challenge Playbook.

Every figure needs a reproducible source table, plain-language alt text, a
caption stating the permitted interpretation, and labels identifying measured,
modeled, assumed, or illustrative content.

## Site and distribution requirements

The article page should follow the established Pascal insight structure:
eyebrow, title and dek, Subject/Published/Data/Method metadata, ABS-series
navigation, article body, compact methodology summary, companion methodology
link, references, related articles, and footer.

Add two visually distinct calls to action near the conclusion:

1. **Primary:** subscribe for new research, the monthly newsletter, public
   model leaderboards, and competition announcements.
2. **Secondary:** join the AnalytIQ beta without implying that AnalytIQ supplies
   private player confidence or an automated ABS playbook.

The launch message should foreground the metric: “How sure is sure enough?” and
“Challenge Threshold tells you how sure you need to be—not how sure you are.”
The G8 limitations build credibility but should not be marketed as the product.

## Required companion methodology

The methodology page must cover the reference specification, population and
data window, correction-value estimator, inventory-value policy, fixed-path
restriction, sensitivity range, public and selected probability benchmarks,
G8 stability result, rejected win model, G9 upper benchmark and falsification,
reproducibility, version policy, and prohibited interpretations.

Exact estimates, intervals, equations, and diagnostic details belong there.

## Draft acceptance checklist

A draft is ready for fact review only if:

- Challenge Threshold is defined as required confidence, not player confidence;
- a reference value always names its model/version and material sensitivity;
- representative states are evaluations, not commands to challenge or preserve;
- Article 4 material is a bridge rather than the center of the article;
- no modeled probability is labeled as a player's belief;
- no sentence judges an observed player, team, pass, failure, or unused unit;
- the G8 instability is disclosed without being allowed to erase the metric;
- G9 is omitted from the main article or paired with its falsification;
- no empirical playbook or “optimal MLB policy” claim appears;
- all reported numbers map to the claim ledger and reproducible artifacts; and
- the two calls to action remain accurate and separate.

## Next gate

After this review is merged, the next gate is **CT-2026 specification and draft
production**: freeze the reference policy and versioning rules, generate the
model-free/assumption-labeled threshold table, write the article and companion
methodology, and prepare figure-data specifications. Publication graphics and
site implementation should wait until the draft passes factual and claim-ledger
review.
