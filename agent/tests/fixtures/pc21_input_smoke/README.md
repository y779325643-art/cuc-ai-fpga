# PC 2.1 input smoke fixture

`design.json` is a minimal schema-valid model proposal for the public PC input
command. It exercises strict JSON decoding, registered schema validation, and
controller-owned source-byte binding only (research plan v2.2 §4.1 and code
architecture v2.1 §6.1–6.2).

The empty structural module is deliberately not an AI task, a semantically
validated architecture, a buildable RTL project, or a reference algorithm.
There are no requirement-boundary semantics or oracle answers in this fixture.
Any accompanying source bytes used by a smoke run establish byte identity only;
they do not establish task readiness. Parser size/depth limits are explicit
engineering resource policy, not a frozen research budget.
