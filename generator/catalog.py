"""The fictional company's IT program catalog.

Kestrel Health is a made-up consumer wearables company. Every program, person and
number here is synthetic. Format per line:  name | why it matters | tier | alias
Tier 1 = business-critical, 3 = discretionary. Alias is how people refer to the
program in chat and meeting notes (it is what makes entity resolution hard).
"""

TEAMS = {
    "ERP": "ERP",
    "SCT": "Supply Chain Technology",
    "COM": "Commercial Systems",
    "CX": "CX Technology",
    "WPT": "Workplace Technology",
    "EAI": "Enterprise Architecture & AI",
}

# Where each team actually keeps its status today (six versions of the truth).
TEAM_SOURCE = {
    "ERP": "jira",        # Jira epic export (CSV)
    "SCT": "sheet",       # hand-maintained tracker spreadsheet (CSV)
    "COM": "confluence",  # one Confluence page per program (Markdown)
    "CX": "status_doc",   # a weekly status doc (Markdown)
    "WPT": "slack",       # nothing written down; it lives in Slack
    "EAI": "steering",    # steering-committee meeting notes
}

_RAW = {
"ERP": """
Core financials ERP cutover | Single ledger for all entities; retires three legacy finance tools | 1 | the ERP go-live
Order-to-cash redesign | Cuts invoice-to-cash from 41 to 25 days | 1 | O2C
Procure-to-pay automation | Removes manual PO matching for ~2,000 invoices a month | 2 | P2P
Fixed assets module | Replaces spreadsheet depreciation schedules | 3 | fixed assets
Multi-entity consolidation | Needed to add the new EU entity next fiscal year | 1 | consolidation
Revenue recognition automation (ASC 606) | Subscription revenue is booked by hand today | 1 | rev rec
Bank reconciliation automation | Frees ~3 FTE-days per close | 3 | bank rec
Indirect tax engine integration | Audit exposure on US sales tax | 2 | tax engine
Inventory costing rework | Standard-cost errors distort gross margin | 2 | inventory costing
Intercompany eliminations | Manual eliminations add 2 days to close | 2 | intercompany
Close acceleration (10 to 6 days) | Board asked for faster monthly reporting | 2 | fast close
Chart of accounts redesign | Prerequisite for reporting by product line | 2 | CoA
ERP reporting data mart | Finance self-serve reporting | 3 | finance mart
Vendor master data cleanup | Duplicate vendors cause double payments | 2 | vendor cleanup
Expense management integration | Card spend lands in the ledger a month late | 3 | expenses
FP&A planning tool integration | Plan-vs-actual is rebuilt in spreadsheets | 3 | FP&A integration
SOX ITGC remediation (ERP access) | Open audit findings on ERP access; must close before year-end audit | 1 | SOX ITGC
""",
"SCT": """
Demand planning platform | Replaces the spreadsheet forecast for 40+ SKUs | 1 | demand planning
EU 3PL warehouse integration | New EU fulfilment centre opens in Q1 | 1 | EU 3PL
US 3PL EDI modernization | EDI failures stall ~3% of orders | 2 | US EDI
Device serialization & traceability | Needed for warranty and recall readiness | 1 | serialization
Returns & refurbishment tracking | Refurbished inventory is invisible to planning | 2 | refurb tracking
Supplier portal | Suppliers email POs and ASNs today | 3 | supplier portal
Inbound logistics visibility | No ETA on inbound components | 2 | inbound visibility
Carrier rate shopping | Estimated 6% outbound freight savings | 3 | rate shopping
Contract manufacturer data feed | Daily yield data arrives as PDFs | 2 | CM feed
Component shortage early warning | Two stockouts last year started as silent shortages | 2 | shortage alerts
Inventory allocation engine | Allocates constrained stock across channels | 2 | allocation engine
Customs & trade compliance automation | Every new SKU is classified by hand | 3 | customs automation
Warranty replacement fulfillment | Replacements ship in 9 days against a 3-day target | 2 | warranty fulfilment
S&OP dashboard | Monthly S&OP runs on stale data | 3 | S&OP dashboard
Packaging BOM management | Packaging changes break costing | 3 | packaging BOM
Forecast accuracy analytics | Forecast error is not measured today | 3 | forecast accuracy
Retail replenishment (EDI 852) | Retail partners require sell-through feeds | 2 | EDI 852
""",
"COM": """
B2B CPQ for enterprise wellness | Enterprise deals are quoted in spreadsheets | 2 | CPQ
CRM org consolidation | Two CRM orgs since the last acquisition | 1 | CRM consolidation
E-commerce checkout replatform | Checkout conversion and holiday resilience | 1 | checkout
Subscription billing migration | Legacy billing vendor contract ends in March | 1 | billing migration
Partner portal | Channel partners are onboarded by email | 3 | partner portal
Pricing & promotions engine | Every campaign's promotions are hand-coded | 2 | promo engine
Retail POS integration | Retail sales are invisible until month-end | 3 | POS integration
Consent & preference center | Regulators expect granular consent | 1 | consent center
Customer data platform | One customer profile for marketing and CX | 2 | CDP
Lead routing automation | Inbound B2B leads wait ~2 days | 3 | lead routing
Membership entitlement service | Single source of truth for who has a paid membership | 1 | entitlements
Gift card & store credit | Needed for holiday promotions and CX goodwill credits | 3 | gift cards
Checkout tax calculation | Tax errors on international orders | 2 | checkout tax
B2B invoicing | Enterprise invoices are built by hand | 2 | B2B invoicing
Affiliate tracking replacement | Current vendor is being sunset | 3 | affiliate tracking
JP/KR storefront localization | APAC growth target for next year | 2 | APAC storefronts
Sales commission tooling | Commission disputes every quarter | 3 | commissions
""",
"CX": """
Contact center telephony migration | Legacy telephony contract ends in January | 1 | telephony
Knowledge base rebuild | Agents can't find answers; deflection is low | 2 | KB rebuild
AI agent assist for support | Target: 20% lower handle time | 2 | agent assist
Returns self-service portal | Returns are the #2 contact reason | 1 | returns portal
Order status bot | "Where is my order" is the #1 contact reason | 2 | WISMO bot
Warranty claim automation | Claims are reviewed by hand; 5-day backlog | 2 | warranty claims
Support QA scoring | QA samples under 2% of conversations | 3 | QA scoring
CSAT & NPS pipeline | Survey data lands in three tools | 3 | CSAT pipeline
Device diagnostics log upload | Agents ask customers for screenshots | 2 | diagnostics upload
Omnichannel routing | Chat, email and voice are routed separately | 2 | omnichannel
Support workforce management | Staffing is planned in spreadsheets | 3 | WFM
Community forum migration | Forum vendor is end-of-life | 3 | forum migration
Ticket taxonomy redesign | Contact reasons are unreliable for product teams | 3 | taxonomy
APAC BPO onboarding | 24/7 coverage for the APAC launch | 1 | APAC BPO
Voice of customer analytics | Product feedback is buried in tickets | 3 | VoC
Support tool SSO & access review | Audit finding: shared agent logins | 1 | support SSO
Proactive shipping-delay outreach | Cuts inbound contacts during carrier delays | 2 | delay outreach
""",
"WPT": """
Identity lifecycle automation (JML) | Leavers keep access for days; open SOX finding | 1 | JML
Laptop refresh FY27 | 30% of the fleet is out of warranty | 2 | laptop refresh
MDM consolidation | Two MDM tools with inconsistent policy | 2 | MDM
SF HQ conference room refresh | Rooms fail about one meeting in five | 3 | room refresh
Austin office network upgrade | Office switches are end-of-support | 3 | Austin network
ITSM platform rollout | Service requests are tracked in email and Slack | 1 | ITSM
Workspace DLP policies | Sensitive files are shared externally without controls | 2 | DLP
Zero-trust network access | Replaces the legacy VPN | 2 | ZTNA
Printer fleet retirement | Cost reduction | 3 | printers
New-hire onboarding kit automation | Day-one readiness for 40+ hires a month | 2 | onboarding kits
SaaS license reclamation | Estimated $400k a year in unused licenses | 2 | license reclamation
Service desk chatbot | Deflects password and access requests | 3 | desk bot
Endpoint patch compliance | Patch compliance is 78% against a 95% target | 1 | patching
Badge system integration | Badge access is not tied to HR status | 2 | badges
Asset inventory reconciliation | Asset records don't match reality | 3 | asset recon
SF office Wi-Fi upgrade | Capacity for twice the headcount | 3 | Wi-Fi
""",
"EAI": """
Integration platform (iPaaS) migration | Every ERP, bank and 3PL integration routes through it | 1 | iPaaS
Enterprise data warehouse modernization | Current warehouse can't scale past next year | 1 | EDW
Product master data management | Product data is defined differently in five systems | 1 | product MDM
AI gateway & model governance | All LLM use must route through approved controls | 1 | AI gateway
API catalog | Teams rebuild integrations that already exist | 3 | API catalog
Order event bus | Real-time order events for CX and logistics | 2 | event bus
Architecture review board refresh | Reviews take 3+ weeks and get skipped | 3 | ARB
SSO for tier-1 applications | 11 tier-1 apps still use local passwords | 1 | SSO rollout
Privacy data deletion automation | Deletion requests are fulfilled by hand across 14 systems | 1 | deletion automation
Employee knowledge assistant (LLM) | Internal Q&A over policies and runbooks | 2 | knowledge assistant
Vendor risk assessment automation | Security reviews gate every new vendor | 2 | vendor risk
Observability platform | Integration failures are found by customers first | 2 | observability
Cloud cost governance | Cloud spend grew 60% year over year | 2 | cloud cost
Secrets management rollout | Credentials live in scripts and wikis | 1 | secrets
EU data residency reference architecture | Needed before the EU entity goes live | 2 | EU residency
Document AI for AP invoices | Automates invoice capture for P2P | 2 | invoice AI
""",
}


def programs():
    out = []
    for team, block in _RAW.items():
        for i, line in enumerate([l for l in block.strip().splitlines() if l.strip()], 1):
            name, why, tier, alias = [x.strip() for x in line.split("|")]
            out.append({"id": f"{team}-{i:02d}", "team": team, "name": name,
                        "why": why, "tier": int(tier), "alias": alias})
    return out


# Downstream <- upstream. "where" says which artifact records the dependency.
# "hidden" ones are never in a structured field: they only surface in free text
# (chat, meeting notes) - this is the quiet cross-team coupling the job is about.
DEPENDENCIES = [
    # (downstream, upstream, where)
    ("ERP-01", "EAI-01", "steering"),   # hidden: ERP go-live needs the iPaaS cutover
    ("ERP-01", "EAI-03", "steering"),
    ("ERP-01", "ERP-14", "jira"),
    ("ERP-02", "ERP-01", "jira"),
    ("ERP-09", "ERP-01", "jira"),
    ("ERP-05", "ERP-12", "jira"),
    ("ERP-05", "EAI-15", "steering"),
    ("ERP-03", "EAI-16", "steering"),
    ("ERP-13", "EAI-02", "steering"),
    ("ERP-06", "COM-04", "jira"),
    ("ERP-17", "WPT-01", "slack"),      # hidden: SOX remediation needs JML
    ("COM-04", "ERP-01", "confluence"),
    ("COM-04", "ERP-08", "confluence"),
    ("COM-14", "ERP-01", "confluence"),
    ("COM-03", "COM-13", "confluence"),
    ("COM-03", "COM-06", "confluence"),
    ("COM-16", "COM-03", "confluence"),
    ("COM-09", "COM-08", "confluence"),
    ("COM-09", "EAI-09", "confluence"),
    ("COM-01", "COM-02", "confluence"),
    ("SCT-11", "ERP-09", "sheet"),
    ("SCT-01", "EAI-02", "sheet"),
    ("SCT-14", "SCT-01", "sheet"),
    ("SCT-13", "CX-06", "sheet"),
    ("SCT-17", "SCT-03", "sheet"),
    ("SCT-12", "EAI-03", "sheet"),
    ("SCT-02", "EAI-01", "slack"),      # hidden: EU 3PL needs new iPaaS connectors
    ("CX-06", "SCT-04", "status_doc"),
    ("CX-04", "SCT-05", "status_doc"),
    ("CX-04", "COM-11", "status_doc"),
    ("CX-03", "EAI-04", "status_doc"),
    ("CX-03", "CX-02", "status_doc"),
    ("CX-16", "EAI-08", "status_doc"),
    ("CX-14", "CX-16", "status_doc"),
    ("CX-14", "WPT-01", "slack"),       # hidden: BPO agents can't get accounts until JML
    ("CX-05", "EAI-06", "status_doc"),
    ("CX-17", "EAI-06", "status_doc"),
    ("CX-17", "SCT-07", "status_doc"),
    ("CX-10", "CX-01", "status_doc"),
    ("CX-11", "CX-01", "status_doc"),
    ("EAI-10", "EAI-04", "steering"),
    ("EAI-16", "EAI-04", "steering"),
    ("EAI-08", "WPT-01", "steering"),
    ("WPT-08", "WPT-01", "slack"),
    ("WPT-02", "WPT-03", "slack"),
    ("WPT-12", "WPT-06", "slack"),
    ("WPT-14", "WPT-01", "slack"),
]

# Change freezes by team. A target date inside one needs an exception or a re-plan.
FREEZES = [
    {"team": "COM", "name": "Peak-season code freeze", "start": "2026-11-16", "end": "2026-12-01"},
    {"team": "ERP", "name": "Year-end close freeze", "start": "2026-12-18", "end": "2027-01-08"},
]

PEOPLE = {
    "ERP": ["Dana Whitfield", "Rahul Mehta", "Grace Okafor", "Tomasz Nowak"],
    "SCT": ["Luis Ortega", "Mei Tanaka", "Sam Adeyemi"],
    "COM": ["Nina Petrova", "Jordan Blake", "Aisha Karim", "Ben Castillo"],
    "CX": ["Priya Natarajan", "Owen Hughes", "Lena Fischer"],
    "WPT": ["Chris Duarte", "Hannah Lee", "Marco Rossi"],
    "EAI": ["Marcus Bell", "Sofia Lindqvist", "Arjun Rao", "Elena Voss"],
}
