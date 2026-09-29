You are drafting the one-page pre-read for this week's IT portfolio review. The reader is the CIO and six team leads. They have five minutes before the meeting starts.

Input: `docs/data/portfolio.json`. It holds every program's evidence-based health, the rules that fired, dependency chains, and each team's self-reported status.

Write Markdown with these sections, in this order:

1. **Headline**: one sentence with the Red, Amber and Green counts and how many programs report better than their evidence.
2. **Decisions needed this week**: at most three. Each one names the decision, who has to make it, by when, and what happens if nobody does. Start with the dependency chains that have the largest blast radius. A decision is a choice someone in the room can make. It is not a status update.
3. **Risks the evidence found that teams haven't reported**: programs whose self-reported status is better than their evidence. Give one line each and say why.
4. **Hygiene**: missing owners, missing dates, stale updates, past-due items and freeze collisions, as compact lists of IDs.
5. **What changed since last week**: the deltas, or say this is the first snapshot.

Conventions the checker enforces (`python -m pipeline.verify_preread`):
- Refer to programs by ID, e.g. `EAI-01`. When you state a program's health, write it as `EAI-01 (Red)` right after the ID.
- Every Red program must appear somewhere.
- Counts in the headline must match the data exactly.
- Do not invent dates, owners or numbers. If a fact isn't in the input, leave it out.

Mark every recommendation as a recommendation. A person decides. Keep it to one page, about 450 words.
