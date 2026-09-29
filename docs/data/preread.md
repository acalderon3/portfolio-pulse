# IT portfolio pre-read: week of Sep 28, 2026

**Headline:** Of 100 programs, 11 are Red, 31 Amber, 55 Green and 3 done. 21 programs report a better status than their evidence supports. Most of the Red comes from two blockers outside the programs themselves.

## Decisions needed this week

**1. Get the iPaaS contract amendment signed now instead of waiting for the Oct 2 trigger.** Owner: CIO with the CFO's office.
EAI-01 (Red) has been stuck in Procurement for 20 days and has moved to Dec 11. The ERP go-live, ERP-01 (Red), reports Green in Jira but can't happen before the iPaaS cutover. Seven programs in three other teams sit downstream of it: ERP-01 and ERP-02 (Red), COM-14 (Red), SCT-11 (Red), ERP-09 (Amber), COM-04 (Amber) and SCT-02 (Amber).
*Recommendation:* escalate today. Then ask ERP to re-plan the go-live now. A date after Dec 11 runs into the year-end close freeze (Dec 18 to Jan 8), so realistically the choice is a freeze exception or a January go-live.

**2. Get a date for the HRIS field mapping from the People team.** Owner: Workplace lead with the People team lead.
WPT-01 (Red), the JML automation, has been blocked for 18 days. Downstream: EAI-08 (Red) SSO, CX-16 (Red) support SSO, WPT-14 (Red), WPT-08 (Amber), and two programs that report Green: CX-14 (Red), the APAC BPO launch on Nov 2, and ERP-17 (Amber), SOX remediation ahead of December audit testing.
*Recommendation:* CX decides this week whether APAC launches on Nov 2 with manual account provisioning or moves.

**3. Move the checkout go-live out of the peak-season freeze.** Owner: Commercial Systems lead.
COM-03 (Amber) targets Nov 20, inside the Nov 16 to Dec 1 freeze, and hasn't been updated in 18 days.
*Recommendation:* go live before Nov 16 or after Dec 1. Don't plan on an exception.

## Risks the evidence found that teams haven't reported

- SCT-04 (Amber): the tracker says Green, but in chat the vendor says its API is about three weeks late. Warranty claim automation (CX-06) depends on it.
- SCT-11 (Red): the Dec 4 target lands before its upstream, ERP-09, finishes on Dec 16.
- COM-14 (Red): the Dec 4 invoicing target depends on the ERP go-live.
- CX-16 (Red) and CX-14 (Red): both report Green, and both wait on JML.

## Hygiene before next review

- **No owner:** SCT-06, COM-15, WPT-09
- **No target date:** WPT-12, EAI-07
- **Stale (over 14 days):** ERP-05, SCT-07, COM-03, WPT-04, WPT-12, EAI-05, EAI-11
- **Past due:** CX-12 (Red), forum migration, target was Sep 18
- **Freeze collisions:** ERP-11, ERP-16 (year-end close); COM-03, COM-07, COM-08 (peak season)

## What changed since last week

This is the first snapshot. Week-over-week deltas start next Monday.
