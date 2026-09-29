## Verification log

These are real catches made while building this snapshot, recorded as they happened.

**1. The eval caught a parser bug, not a model bug.** The first run scored the CX status doc at 98%, and three programs came out Amber for "stale". The cause was that owners had edited their sections *after* the doc's week-ending date, and the date parser threw those later dates away. The fix was to resolve dates against the run date. Without the eval, three healthy programs would have shown up as problems in front of leadership.

**2. The eval caught an error in the test data itself.** For meeting-notes programs, the ground truth used update dates the notes couldn't contain, since they only show the meeting date. The pipeline was right and the answer key was wrong. That's a reminder that the answer key gets reviewed too.

**3. The pre-read checker caught stale numbers in Claude's draft.** The headline said 34 Amber and 52 Green. The draft had been written from the snapshot before the parser fix, and the correct counts were 31 and 55. The check failed, and the draft was corrected before it went out.

**4. A human read caught what no script could.** The draft said seven programs "in four teams" sat downstream of iPaaS. It was three *other* teams, because the count had included the root's own team. A recommendation had also picked up a deadline ("by Oct 9") that appears nowhere in the data. Both were fixed. This is why a person reads every pre-read before it is sent.

**Where AI isn't used, on purpose:** reading CSV columns and page tables (code does it exactly), scoring health (it has to be identical and explainable across teams), and the final call on escalations and trade-offs.
