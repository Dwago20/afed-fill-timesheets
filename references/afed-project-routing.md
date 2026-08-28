# AFED Project Routing

Treat the live timesheet dropdown as authoritative. This reference captures the
known AFED taxonomy and routing rules, but labels may change.

## Contents

- [Routing Hierarchy](#routing-hierarchy)
- [User-Controlled Restrictions](#user-controlled-restrictions)
- [High-Signal Mappings](#high-signal-mappings)
- [Known Live Project Labels](#known-live-project-labels)
- [Task Type](#task-type)

## Routing Hierarchy

1. Use an explicit client, product, JDA, application, or deliverable named in the
   request.
2. Identify the requester and their department from the message, signature, or
   directory context.
3. Match the actual system or environment involved.
4. Confirm the exact project label exists in the live dropdown.
5. Ask the employee when ownership remains ambiguous.

Do not route solely from words such as "cloud", "Azure", "Alibaba", "support",
or "meeting". Those words occur across many projects.

## User-Controlled Restrictions

No project is blocked by default. Treat every label in the live dropdown,
including the following, as available when the evidence supports it:

- `DEFA Cloud (AFED HOLDINGS)`
- `DEFA Hub (DEFA Digital)`

Only add a project to `policy.blocked_projects` when the current user explicitly
requests that restriction. A correction made during the post-entry category
check is authoritative for the affected entries and the rest of the current
review.

Do not substitute `CTO OFFICE PROJECTS (CTO OFFICE)` for work owned by a named
product. CTO projects are allowed when the requester and deliverable genuinely
belong to CTO Office.

## High-Signal Mappings

| Evidence context | Project |
| --- | --- |
| AI SEEK, JDA1 production PoC, AI SEEK cost report, JDA1 readiness | `JDA 1 - AI SEEK (TRICIPTA)` |
| GEB work | `JDA 1 - GEB (TRICIPTA)` |
| Basin AI, its containers, Redis, Service Bus, or Key Vault | `JDA 2 - Basin AI (TRICIPTA)` |
| Geosciences Companion | `JDA 2 - Geosciences Companion (TRICIPTA)` |
| Production Analytics, IGM, or Netop | `JDA 2 - Production Analytics AI & IGM Netop (TRICIPTA)` |
| Production Companion, Petronas SSO, Entra application registration | `JDA 2 -Production Companion (TRICIPTA)` |
| JobGiga application, database, deployment, access, or cost work | `Jobgiga (JOBGIGA)` |
| AVC product or its Alibaba infrastructure | `AVC (CTO OFFICE)` |
| Beicip-Franlab Asia environment | `Beicip-Franlab Asia (EDAFY)` |
| General EDAFY platform work | `EDAFY (EDAFY)` |
| SKK Migas work | `SKK MIGAS (EDAFY)` |
| CoPlace8 office migration or readiness | `CoPlace8 (CP8) Project - New AFED Office (AFED DIGITAL)` |
| Dynect product or routing | `Dynect (DYNECTUS)` |
| AFED Digital website | `AFED Digital (Website) (AFED DIGITAL)` |
| AFED Holdings website | `AFED Holdings (Website) (AFED HOLDINGS)` |

An Alibaba Cloud PoC, API budget, Azure account, or AI subscription task is not
automatically internal. For example, when those resources support the JDA1
production PoC, route the work to `JDA 1 - AI SEEK (TRICIPTA)`, not
`General Activities & Sales Support (INTERNAL)`.

Use `General Activities & Sales Support (INTERNAL)` only for company-wide
administration, sales support, or coordination with no attributable client,
product, application, or delivery program.

## Known Live Project Labels

Use exact spelling and punctuation from the live dropdown:

- `AFED Digital (Website) (AFED DIGITAL)`
- `AFED Holdings (Website) (AFED HOLDINGS)`
- `AFED HOLDINGS GRATZELS (AFED HOLDINGS)`
- `AI KLASS (AI KLASS)`
- `AVC (CTO OFFICE)`
- `Beicip-Franlab Asia (EDAFY)`
- `CAI Office Projects (CAI OFFICE)`
- `CoPlace8 (CP8) Project - New AFED Office (AFED DIGITAL)`
- `Cravee (DYNECTUS)`
- `CTO OFFICE PROJECTS (CTO OFFICE)`
- `Cyberview15 (Magic) Project - New AFED Office (AFED HOLDINGS)`
- `DEFA Cloud (AFED HOLDINGS)`
- `DEFA Core - IT Managed Services & Support (AFED HOLDINGS)`
- `DEFA Core - IT Managed Services & Support (AFED DIGITAL)`
- `DEFA Digital Website (DEFA Digital)`
- `DEFA Hub (DEFA Digital)`
- `Dynect (DYNECTUS)`
- `DYNECTUS (WEBSITE) (DYNECTUS)`
- `EDAFY (EDAFY)`
- `General Activities & Sales Support (INTERNAL)`
- `Gratzels (DYNECTUS)`
- `JDA 1 - AI SEEK (TRICIPTA)`
- `JDA 1 - GEB (TRICIPTA)`
- `JDA 2 - Basin AI (TRICIPTA)`
- `JDA 2 - Geosciences Companion (TRICIPTA)`
- `JDA 2 - Production Analytics AI & IGM Netop (TRICIPTA)`
- `JDA 2 -Production Companion (TRICIPTA)`
- `Jobgiga (JOBGIGA)`
- `MCDynect (DYNECTUS)`
- `Mineral Water (AFED HOLDINGS)`
- `MPM - Celebal Tech (DEFA Digital)`
- `POS SYSTEM (DYNECTUS)`
- `QSHE & Others (to specify in Notes) (AFED HOLDINGS)`
- `SKK MIGAS (EDAFY)`
- `Structura (CTO OFFICE)`
- `Tricipta Structura (DYNECTUS)`

## Task Type

Never assume a universal task type. Select the project first and inspect the
enabled task options.

Observed examples:

- most client work: `Project`;
- AVC product work: `Product Development`;
- genuine internal coordination: `Administrative`.

Use the live option when it differs from this baseline.
