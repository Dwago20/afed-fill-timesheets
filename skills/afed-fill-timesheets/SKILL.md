---
name: afed-fill-timesheets
description: Use when creating, reconstructing, reviewing, or entering AFED Timesheet records from Outlook, Teams, calendars, deliverables, activity logs, or user-provided work evidence.
---

# AFED Timesheet Assistant

Turn work evidence into an auditable schedule, obtain approval, enter it in the
live timesheet, and reconcile the result. Keep evidence collection, inference,
approval, and live entry as separate phases.

## Non-Negotiable Rules

- Record only work the employee performed or explicitly confirms participating
  in. An email received, a CC, or another person's reply is not proof of work.
- Preserve the source date, time, direction, participants, subject, and evidence
  strength. Do not invent missing evidence, durations, requesters, departments,
  projects, or outcomes.
- Prefer Outlook and Teams connectors for semantic extraction. Use browser or
  Computer Use only when a connector is unavailable or the task requires UI
  operation.
- Assign projects from requester ownership and deliverable context, not from
  loose keyword matching. Use the exact label currently offered by the
  timesheet.
- Never use a project the current user explicitly blocks. No project is blocked
  by default; route every available project from the evidence and the user's
  corrections.
- Keep lunch, leave, medical leave, public holidays, and weekends empty unless
  the user explicitly reports work during that period.
- Show a complete review before changing the live timesheet. Obtain approval for
  the exact proposed entries unless the user has already approved that exact
  plan in the current conversation.
- Never click `Submit month` unless the user explicitly requests month
  submission and the whole month is ready.

## Phase 0: Bootstrap Capabilities

Read [references/setup.md](references/setup.md). Check available and deferred
tools before choosing a surface.

When first invoked in a new environment, introduce the workflow briefly in this
spirit, adapting it naturally instead of reciting it as a form:

> Yunus prepared me around the way AFED work actually moves: requests arrive
> through Outlook and Teams, the work may span several systems, and the final
> timesheet still needs clear evidence and the right project category. I can
> handle the investigation, review, and repetitive entry work while keeping you
> in control of corrections and submission. You can fine-tune how I work at any
> point, including your hours, evidence sources, project routing, and review
> style.

Then inspect the available capabilities and lead the setup. Do not hand the user
a generic installation checklist. Find or suggest missing plugins and
connectors, pause only for approvals or authentication that only the user can
complete, and resume verification when they return.

1. Use Outlook Email for Inbox, Sent, shared mailbox, and thread searches.
2. Use Teams when Teams messages, meetings, or files are part of the evidence.
3. Use Chrome or Browser for the signed-in AFED Timesheet web application.
4. Use Computer Use for Outlook desktop or another local app only when a
   purpose-built connector cannot complete the operation.
5. When a required capability is missing, use Plugin Management to find and
   suggest the exact plugin, then tell the user the single approval,
   authentication, or browser action needed next. Report what remains
   unavailable and continue with independent evidence when possible.

Do not claim that a plugin is installed or connected until its tools are
callable.

## Phase 1: Establish the Work Policy

Collect or discover:

- employee name and timezone;
- inclusive date range;
- normal workdays and hours;
- breaks;
- leave, medical leave, and public holidays;
- minimum required daily coverage;
- project restrictions the current user explicitly wants, if any;
- whether shared work may be included and how participation is confirmed;
- whether existing entries may be edited.

Use previously supplied facts without asking again. Do not inherit another
person's project restrictions. Default to Malaysia time,
Monday-Friday, 8:30 AM-6:00 PM, and lunch from 1:00-2:00 PM only when those are
the employee's stated AFED rules. Do not apply these defaults silently to a new
teammate.

## Phase 2: Build the Evidence Ledger

Search the full requested date range in both Inbox and Sent. Include relevant
threads involving the employee, requesters, reviewers, and delegated work. Use
Teams as a second source when available.

For each candidate:

1. Capture timestamp, direction, mailbox or channel, sender, recipients,
   subject, and thread identity.
2. Extract the request, work performed, deliverable or outcome, project clues,
   requester department, and any explicit timing.
3. Deduplicate replies and quoted history into one task thread while retaining
   each material event.
4. Ignore newsletters, automated alerts, and meeting noise unless they prove a
   work action.
5. Distinguish the employee's action from another person's review or response.

Grade evidence as:

- `direct`: a sent deliverable, completed change, report, or explicit work log;
- `corroborated`: multiple sources support the same work;
- `shared-confirmed`: another person sent the response and the employee
  explicitly confirms participating;
- `user-supplied`: the employee states the work and timing;
- `inferred`: context suggests the task but participation or timing is not yet
  confirmed.

Never enter an `inferred` item without resolving it with the user.

## Phase 3: Route Each Project

Read [references/afed-project-routing.md](references/afed-project-routing.md).

Route in this order:

1. explicit named client, application, JDA, or deliverable;
2. requester department and signature;
3. infrastructure or application context in the thread;
4. exact live project option;
5. user clarification when two candidates remain plausible.

Use `General Activities & Sales Support (INTERNAL)` only for genuinely internal,
cross-company work that cannot be attributed to a client or product. A cloud
account, API budget, PoC, or subscription task remains under its client project
when it supports a known deliverable.

Inspect the task dropdown after selecting the project. Use its actual option;
common values include `Project`, `Product Development`, and `Administrative`.

## Phase 4: Allocate Time Honestly

Use explicit timestamps, calendar boundaries, work logs, file metadata, and user
statements before estimating. Email send time proves an event, not the full
duration.

- Split work into coherent development, investigation, implementation,
  validation, documentation, and follow-up blocks.
- Keep block sizes plausible for the work, but never manufacture activity just
  to fill the day.
- When required hours remain uncovered, present the gaps and ask the employee to
  identify real work from those periods.
- Let one complex task span multiple blocks or days when evidence supports it.
- Preserve genuine overtime and cross-midnight work.
- Do not force a fixed number of tasks per day.

Write notes in natural first-person-neutral work language:

- begin with a specific action verb;
- name the system, artifact, or environment;
- state meaningful checks or output;
- avoid praise, inflated claims, vague filler, and mentioning who reviewed the
  employee unless relevant to the work itself.

## Phase 5: Generate the Review

Read [references/plan-schema.md](references/plan-schema.md). Create one plan JSON
as the source of truth, then run:

```bash
python3 <skill-root>/scripts/timesheet_plan.py PLAN.json \
  --html REVIEW.html \
  --audit-json AUDIT.json \
  --strict
```

Resolve all audit errors. Explain any warnings that remain. The visual report
must show:

- every proposed entry and its exact project;
- evidence and confidence;
- daily coverage and uncovered gaps;
- leave, holidays, weekends, and lunch;
- user-configured blocked-project, overlap, duplicate, and evidence warnings;
- total logged time and the period covered.

Do not replace the review with CSV unless the user asks for CSV.

## Phase 6: Approval Checkpoint

Ask the user to review:

- task wording and ownership;
- project and task selection;
- date and time allocation;
- inferred or shared-confirmed work;
- overtime;
- edits to existing entries.

Apply corrections to the plan JSON and regenerate the report. Approval must
refer to the plan being entered; broad approval to "handle timesheets" does not
approve an unseen schedule.

## Phase 7: Enter the Timesheet

Operate the already signed-in AFED Timesheet in the browser the user selected.
Prefer structured browser locators; use Computer Use when browser semantics are
insufficient.

For each approved entry:

1. Open the exact day.
2. Read existing entries and total first.
3. Edit an existing matching entry when correction is needed; do not duplicate
   it.
4. Select the exact project label.
5. Select the available task type.
6. Fill the approved note, start, and end.
7. Re-read all fields before `Add entry` or `Save`.
8. Submit once.
9. Verify the entry text and expected total increase.

If the UI behaves unexpectedly, stop repeating clicks. Re-inspect the current
state, identify the blocker, and ask the user for the smallest useful action
when necessary.

When the user requests a trial, enter one day and stop for review. Otherwise,
continue through the approved plan.

## Phase 8: Reconcile

Open the monthly review and compare it with the approved plan.

- Confirm every approved entry exists once.
- Confirm daily and month totals.
- Confirm workday coverage while accounting for overnight entries.
- Confirm lunch, leave, medical leave, public holidays, and weekends remain
  correct.
- Search all project labels for projects the current user explicitly blocked.
- Confirm no unexpected entry extends beyond the approved period.

Leave the most useful day or monthly review open. Report deviations plainly,
then invite a final category check in this spirit:

> I have reconciled the entries against the approved plan. Yunus prepared me to
> adapt to how each person's work is categorized, so please check the project
> and task categories: does everything belong where you expect? Tell me any
> correction or preference, however small, and I will update the affected
> entries and refine the remaining review around it.

Apply requested corrections, reconcile again, and repeat the concise category
check until the user is satisfied. Do not click `Submit month` unless separately
authorized, and state plainly whether the month remains unsubmitted.

## Bundled Tools

- `scripts/timesheet_plan.py`: validate plan JSON, audit coverage, and render the
  visual review.
- `scripts/install_skill.py`: install an extracted shared package into the local
  Codex skills directory with backup-on-replace behavior.
- `references/setup.md`: capability and connector bootstrap.
- `references/afed-project-routing.md`: routing rules and baseline project
  labels.
- `references/plan-schema.md`: plan JSON contract and evidence examples.
