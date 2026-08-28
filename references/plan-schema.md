# Timesheet Plan Schema

Use one JSON file as the source of truth for review and live entry.

## Contents

- [Example](#example)
- [Required Top-Level Fields](#required-top-level-fields)
- [Policy Fields](#policy-fields)
- [Entry Fields](#entry-fields)
- [Evidence Fields](#evidence-fields)
- [Audit Command](#audit-command)

## Example

```json
{
  "employee": "Employee Name",
  "period": {
    "start": "2026-07-20",
    "end": "2026-07-24",
    "timezone": "Asia/Kuala_Lumpur"
  },
  "policy": {
    "workdays": [0, 1, 2, 3, 4],
    "workday_start": "08:30",
    "workday_end": "18:00",
    "breaks": [
      {"start": "13:00", "end": "14:00", "label": "Lunch"}
    ],
    "minimum_work_minutes": 510,
    "leave_dates": [],
    "holiday_dates": [],
    "blocked_projects": []
  },
  "evidence_coverage": {
    "outlook_inbox": "searched",
    "outlook_sent": "searched",
    "teams": "not-connected"
  },
  "entries": [
    {
      "start": "2026-07-20T16:30",
      "end": "2026-07-21T09:30",
      "project": "JDA 1 - AI SEEK (TRICIPTA)",
      "task": "Project",
      "activity": "TriCipta cloud cost analysis",
      "notes": "Reviewed the Azure billing records, separated required infrastructure from reducible costs, validated the scoped resources, and prepared the monthly cost reports.",
      "confidence": "direct",
      "participation_confirmed": true,
      "status": "proposed",
      "evidence": [
        {
          "source": "Outlook Sent",
          "timestamp": "2026-07-21T09:34:00+08:00",
          "direction": "sent",
          "subject": "TriCipta cloud cost analysis",
          "kind": "direct"
        }
      ]
    }
  ]
}
```

## Required Top-Level Fields

- `employee`: display name.
- `period.start` and `period.end`: inclusive `YYYY-MM-DD` dates.
- `period.timezone`: IANA timezone name.
- `policy`: work schedule and exclusions.
- `entries`: proposed or approved entry array.

## Policy Fields

- `workdays`: integers where Monday is `0` and Sunday is `6`.
- `workday_start`, `workday_end`: local `HH:MM`.
- `breaks`: local recurring breaks with `start`, `end`, and optional `label`.
- `minimum_work_minutes`: required covered working minutes per ordinary day.
- `leave_dates`, `holiday_dates`: `YYYY-MM-DD` arrays.
- `blocked_projects`: exact live project labels or unambiguous blocked prefixes
  explicitly requested by the current user; use an empty array by default.

## Entry Fields

- `start`, `end`: local ISO date-times without a timezone suffix. `end` may be
  on the next day.
- `project`: exact timesheet project label.
- `task`: exact task option available for that project.
- `activity`: short review heading.
- `notes`: text to enter in the timesheet.
- `confidence`: `direct`, `corroborated`, `shared-confirmed`,
  `user-supplied`, or `inferred`.
- `participation_confirmed`: required as `true` for `shared-confirmed` work.
- `status`: normally `proposed` or `approved`.
- `evidence`: one or more evidence objects.
- `allow_non_workday`: optional `true` only for confirmed weekend, leave, or
  holiday work.

## Evidence Fields

- `source`: mailbox, Teams channel, document, activity log, or user statement.
- `timestamp`: source event time with timezone where available.
- `direction`: `sent`, `received`, `meeting`, `file`, `log`, or
  `user-statement`.
- `subject`: message subject, meeting name, file name, or concise description.
- `kind`: one of the confidence grades.
- `requester`: optional requester name.
- `requester_department`: optional department used in project routing.
- `thread_id`: optional stable connector thread identity.

Store concise evidence metadata, not unnecessary full email bodies.

## Audit Command

```bash
python3 scripts/timesheet_plan.py PLAN.json \
  --html REVIEW.html \
  --audit-json AUDIT.json \
  --strict
```

`--strict` exits unsuccessfully when audit errors remain. Warnings still require
review but do not make the plan structurally invalid.
