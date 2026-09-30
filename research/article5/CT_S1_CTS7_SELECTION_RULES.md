# CT-S1 CTS7 Mechanical Contrast Rules

## Purpose and limitation

This file makes the frozen contrast families executable. The family names and
acceptance conditions were frozen in `CT_SUCCESSOR_VALIDATION_PLAN.md` before
confirmation acquisition. The plan did not specify every pairing and tie-break
detail below. These details therefore clarify implementation; they do not add
a new scientific gate.

To prevent confirmation-result shopping, the generator enumerates every
eligible pair in the first three families. Selection of the small `ordinary`
representative set uses development-period reference values only. Confirmation
thresholds, confirmation separation, and eligibility never select or replace a
pair.

## Shared eligibility

Both members must be present in the confirmation candidate grid and supported
under the validated common hierarchy. Pairing uses public decision-time state
fields. Member A and member B retain stable scenario identifiers. Every pair is
expanded to both periods and all eight core implementations; a missing or
nonfinite cell fails rather than disappearing.

## Pair families

### Early versus late

Hold original call, side, count, outs, bases, half-inning, score bucket, team
role, and inventory fixed. Pair innings 1 with 7, 2 with 8, and 3 with 9.
Member A is early and member B is late. Extra innings are not substituted.

### One versus two challenge units

Hold every public state field fixed. Member A has one unit and member B has two
units.

### Ordinary versus terminal count

Hold every non-count public state field fixed. For an original `BALL`, preserve
strikes and pair each balls value 0, 1, or 2 with balls 3. For an original
`STRIKE`, preserve balls and pair strikes 0 or 1 with strikes 2. Member A is the
ordinary count and member B is the terminal count.

## Ordinary representatives

Within each of the three families, restrict to pairs whose members have bases
empty and no outs. Compute each pair's midpoint from its two development-period
reference thresholds. Select the pair whose midpoint is nearest the median
finite development-period reference threshold across the supported candidate
grid. Ties break lexicographically by stable contrast identifier.

The resulting three pairs are copied into the `ordinary` contrast class with
their source family retained. These are the only rows that can satisfy the
frozen requirement that at least one ordinary contrast survive. A failed
ordinary representative is preserved and is not replaced by the next-best
confirmation result.

## Acceptance

A contrast is article-eligible only when all core cells are present and finite,
the sign of `CT_B - CT_A` is the same and nonzero in both periods and all core
implementations, and absolute reference separation is at least 0.05 in both
periods. CTS7 passes only if at least one of the three mechanically selected
`ordinary` representatives is article-eligible.
