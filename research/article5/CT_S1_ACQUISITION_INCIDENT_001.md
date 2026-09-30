# CT-S1 Acquisition Incident 001: Duplicate Postponed-Game Listing

## Event

The first authorized CTS1 execution began on September 28, 2026. The schedule
request succeeded, after which acquisition stopped before any game feed,
Statcast, team ABS, or dashboard request because the response contained a
duplicate game ID.

The cached schedule object has SHA-256
`9dc7cbd394eef335eda035036249111f0688576b6ad67f7d3c712a82a071fb52`.
It contains 231 in-window regular-season listings representing 230 unique game
IDs. The sole duplicate is `gamePk 824785`:

- one listing appears under September 22 with official date September 23 and
  detailed state `Postponed`;
- one appears under September 23 with the same official date and feed link and
  detailed state `Final`.

Both use the same teams and the schedule API labels both with abstract state
`Final`. No pitch, challenge, model, or outcome table was inspected.

## Targeted correction

The acquisition parser may collapse duplicate schedule listings only when all
listings agree on game ID, official date, regular-season game type, feed link,
home team, and away team, and exactly one listing has detailed state `Final`.
That completed representation is retained once.

Conflicting identity fields, no completed representation, or more than one
completed representation remain hard failures. The 275-game and 326-request
caps are unchanged. Resumption uses the verified cached schedule object and
does not spend another network request on it.

## Classification

This is a bounded source-representation correction after an evidenced CTS1
failure. It does not alter the date window, population, model, thresholds,
support rules, confirmation outcomes, or scientific acceptance gates.
