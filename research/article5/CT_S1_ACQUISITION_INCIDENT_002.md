# CT-S1 Acquisition Incident 002: Final-Day Statcast Publication Lag

## Event

The completed CTS1 pull entered offline preflight at 12:15 a.m. Pacific on
September 28, 2026. September 11--26 contained 57,126 Statcast pitch rows. The
September 27 export was a valid 1,825-byte CSV header with zero data rows and
SHA-256 `c1703bd38919ac5304ed7f1e0f3eb225f385b969203db316cde88adc409462e3`.

Preflight stopped before reconstruction. This is treated as source-publication
latency, not as a zero-pitch baseball day and not as model evidence.

## Bounded response

The original object and receipt remain immutable. A dedicated command may
refresh only the frozen September 27 Statcast URL, with at most two attempts
and the existing 10 MiB response and 450 MiB total-object caps. A populated
replacement is stored by hash and appends a receipt naming the prior hash in
`supersedes_sha256`. Empty retries are preserved as failed receipts and do not
supersede the accepted source view.

Offline preflight accepts a changed successful URL hash only through a complete
supersession chain. It verifies every historical object, counts all retained
objects against the byte ceiling, and uses only the latest successfully
superseding response for source validation.

This correction does not change the date window, expected game set, model,
population, or scientific gates. No reconstruction or confirmation modeling
may begin until the September 27 export is populated and full preflight passes.
