# EA & AI steering committee, 2026-09-24

Attendees: Marcus Bell, Sofia Lindqvist, Arjun Rao, Elena Voss, CIO office

## Program round-robin

**iPaaS** (Marcus Bell). Status: Amber. Committee accepted a new date of Dec 11 (baseline was Oct 30). Blocker: Vendor contract amendment unsigned; sitting with Procurement, open since 9/8. Reminder: the ERP go-live (Nov 2) can't happen before the iPaaS cutover. All bank and 3PL integrations route through it. Why: Every ERP, bank and 3PL integration routes through it.

**EDW** (Sofia Lindqvist). Status: Green. Holding Mar 12. Finance's reporting data mart will be built on the new EDW. Why: Current warehouse can't scale past next year.

**product MDM** (Marcus Bell). Status: Green. On plan for Oct 23. The ERP team needs clean product master data before their go-live, and customs automation classifies from it.

**AI gateway** (Arjun Rao). Status: Green. Committee accepted a new date of Dec 18 (baseline was Nov 13). Why: All LLM use must route through approved controls.

**event bus** (Sofia Lindqvist). Status: Green. Holding Oct 30. Why: Real-time order events for CX and logistics.

**ARB** (Marcus Bell). Status: Green. No date agreed yet; still in discovery. Why: Reviews take 3+ weeks and get skipped.

**SSO rollout** (Marcus Bell). Status: Amber. Holding Nov 6. Blocked in practice until Workplace's JML automation ships; accounts are provisioned by it. Why: 11 tier-1 apps still use local passwords.

**deletion automation** (Sofia Lindqvist). Status: Amber. Committee accepted a new date of Dec 25 (baseline was Dec 11). Blocker: Waiting on vendor SOW countersignature, open since 9/23.

**knowledge assistant** (Arjun Rao). Status: Green. On plan for Feb 26. Can't go to production until AI gateway is live. Why: Internal Q&A over policies and runbooks.

**observability** (Arjun Rao). Status: Green. On plan for Jan 1.

**cloud cost** (Marcus Bell). Status: Green. On plan for Nov 13. Why: Cloud spend grew 60% year over year.

**secrets** (Arjun Rao). Status: Green. Committee accepted a new date of Apr 9 (baseline was Mar 19). Blocker: Awaiting legal review of the DPA, open since 9/24.

**EU residency** (Elena Voss). Status: Green. Target moved to Feb 5 from Jan 8. Finance's multi-entity consolidation for the new EU entity is waiting on this reference architecture.

**invoice AI** (Marcus Bell). Status: Green. On plan for Mar 12. Can't go to production until AI gateway is live. Invoice capture from this feeds Procure-to-pay automation on the ERP side. Why: Automates invoice capture for P2P.

## Decisions

- Escalate the iPaaS contract amendment to the CFO's office if unsigned by 10/2.

## Actions

- Marcus to chase Procurement on the iPaaS amendment.
