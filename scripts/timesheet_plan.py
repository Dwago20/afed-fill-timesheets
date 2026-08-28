#!/usr/bin/env python3
"""Validate an AFED timesheet plan and render a visual approval report."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from collections.abc import Iterable
from datetime import date, datetime, time, timedelta
from datetime import timezone as dt_timezone
from pathlib import Path
from typing import Any

CONFIDENCE_LEVELS = {
    "direct",
    "corroborated",
    "shared-confirmed",
    "user-supplied",
    "inferred",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a timesheet plan JSON and optionally render HTML."
    )
    parser.add_argument("plan", type=Path, help="Path to the plan JSON")
    parser.add_argument("--html", type=Path, help="Write the visual review HTML")
    parser.add_argument("--audit-json", type=Path, help="Write the audit result JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 1 when audit errors are present",
    )
    return parser.parse_args()


def load_plan(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Plan file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON at line {exc.lineno}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise TypeError("Plan root must be a JSON object.")
    return data


def parse_date(value: Any, label: str) -> date:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a YYYY-MM-DD string.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a valid YYYY-MM-DD date.") from exc


def parse_time(value: Any, label: str) -> time:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be an HH:MM string.")
    try:
        parsed = time.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a valid HH:MM time.") from exc
    return parsed.replace(second=0, microsecond=0)


def parse_datetime(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a local ISO date-time string.")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a valid local ISO date-time.") from exc
    if parsed.tzinfo is not None:
        raise ValueError(f"{label} must be local time without a timezone suffix.")
    return parsed.replace(second=0, microsecond=0)


def date_range(start: date, end: date) -> Iterable[date]:
    cursor = start
    while cursor <= end:
        yield cursor
        cursor += timedelta(days=1)


def minutes(delta: timedelta) -> int:
    return int(delta.total_seconds() // 60)


def format_minutes(value: int) -> str:
    sign = "-" if value < 0 else ""
    value = abs(value)
    return f"{sign}{value // 60}:{value % 60:02d}"


def format_clock(value: datetime) -> str:
    return value.strftime("%-I:%M %p")


def intervals_overlap(
    left_start: datetime,
    left_end: datetime,
    right_start: datetime,
    right_end: datetime,
) -> bool:
    return left_start < right_end and right_start < left_end


def merge_intervals(
    intervals: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    if not intervals:
        return []
    ordered = sorted(intervals)
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        previous_start, previous_end = merged[-1]
        if start <= previous_end:
            merged[-1] = (previous_start, max(previous_end, end))
        else:
            merged.append((start, end))
    return merged


def subtract_intervals(
    base: list[tuple[datetime, datetime]],
    covered: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    remaining: list[tuple[datetime, datetime]] = []
    merged_covered = merge_intervals(covered)
    for base_start, base_end in base:
        cursor = base_start
        for covered_start, covered_end in merged_covered:
            if covered_end <= cursor or covered_start >= base_end:
                continue
            if covered_start > cursor:
                remaining.append((cursor, min(covered_start, base_end)))
            cursor = max(cursor, covered_end)
            if cursor >= base_end:
                break
        if cursor < base_end:
            remaining.append((cursor, base_end))
    return remaining


def blocked_match(project: str, blocked_projects: list[str]) -> str | None:
    normalized = " ".join(project.casefold().split())
    for blocked in blocked_projects:
        candidate = " ".join(blocked.casefold().split())
        if normalized == candidate or normalized.startswith(candidate + " ("):
            return blocked
    return None


def issue(
    issues: list[dict[str, Any]],
    severity: str,
    code: str,
    message: str,
    *,
    entry: int | None = None,
    day: str | None = None,
) -> None:
    item: dict[str, Any] = {
        "severity": severity,
        "code": code,
        "message": message,
    }
    if entry is not None:
        item["entry"] = entry
    if day is not None:
        item["day"] = day
    issues.append(item)


def audit_plan(plan: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    period = plan.get("period")
    policy = plan.get("policy")
    raw_entries = plan.get("entries")

    if not isinstance(plan.get("employee"), str) or not plan["employee"].strip():
        issue(issues, "error", "employee", "Employee name is required.")
    if not isinstance(period, dict):
        issue(issues, "error", "period", "Period object is required.")
        period = {}
    if not isinstance(policy, dict):
        issue(issues, "error", "policy", "Policy object is required.")
        policy = {}
    if not isinstance(raw_entries, list):
        issue(issues, "error", "entries", "Entries must be an array.")
        raw_entries = []

    try:
        period_start = parse_date(period.get("start"), "period.start")
        period_end = parse_date(period.get("end"), "period.end")
        if period_end < period_start:
            raise ValueError("period.end must not be before period.start.")
    except (TypeError, ValueError) as exc:
        issue(issues, "error", "period-date", str(exc))
        period_start = datetime.now(dt_timezone.utc).date()
        period_end = period_start

    timezone_name = period.get("timezone")
    if not isinstance(timezone_name, str) or not timezone_name.strip():
        issue(issues, "warning", "timezone", "Period timezone is missing.")

    try:
        workday_start = parse_time(policy.get("workday_start"), "policy.workday_start")
        workday_end = parse_time(policy.get("workday_end"), "policy.workday_end")
        if workday_end <= workday_start:
            raise ValueError("policy.workday_end must be after workday_start.")
    except (TypeError, ValueError) as exc:
        issue(issues, "error", "workday-time", str(exc))
        workday_start = time(8, 30)
        workday_end = time(18, 0)

    workdays = policy.get("workdays", [0, 1, 2, 3, 4])
    if not isinstance(workdays, list) or any(
        not isinstance(day, int) or day < 0 or day > 6 for day in workdays
    ):
        issue(
            issues,
            "error",
            "workdays",
            "policy.workdays must contain integers from 0 to 6.",
        )
        workdays = [0, 1, 2, 3, 4]

    try:
        minimum_work_minutes = int(policy.get("minimum_work_minutes", 0))
        if minimum_work_minutes < 0:
            raise ValueError
    except (TypeError, ValueError):
        issue(
            issues,
            "error",
            "minimum-work",
            "policy.minimum_work_minutes must be a non-negative integer.",
        )
        minimum_work_minutes = 0

    breaks: list[dict[str, Any]] = []
    raw_breaks = policy.get("breaks", [])
    if not isinstance(raw_breaks, list):
        issue(issues, "error", "breaks", "policy.breaks must be an array.")
        raw_breaks = []
    for index, raw_break in enumerate(raw_breaks):
        try:
            if not isinstance(raw_break, dict):
                raise TypeError(f"policy.breaks[{index}] must be an object.")
            start = parse_time(raw_break.get("start"), f"policy.breaks[{index}].start")
            end = parse_time(raw_break.get("end"), f"policy.breaks[{index}].end")
            if end <= start:
                raise ValueError(f"policy.breaks[{index}] end must be after start.")
            breaks.append(
                {
                    "start": start,
                    "end": end,
                    "label": str(raw_break.get("label", "Break")),
                }
            )
        except (TypeError, ValueError) as exc:
            issue(issues, "error", "break", str(exc))

    def parse_date_set(field: str) -> set[date]:
        values = policy.get(field, [])
        if not isinstance(values, list):
            issue(issues, "error", field, f"policy.{field} must be an array.")
            return set()
        result: set[date] = set()
        for index, value in enumerate(values):
            try:
                result.add(parse_date(value, f"policy.{field}[{index}]"))
            except (TypeError, ValueError) as exc:
                issue(issues, "error", field, str(exc))
        return result

    leave_dates = parse_date_set("leave_dates")
    holiday_dates = parse_date_set("holiday_dates")
    blocked_projects = policy.get("blocked_projects", [])
    if not isinstance(blocked_projects, list) or any(
        not isinstance(value, str) for value in blocked_projects
    ):
        issue(
            issues,
            "error",
            "blocked-projects",
            "policy.blocked_projects must be an array of strings.",
        )
        blocked_projects = []

    entries: list[dict[str, Any]] = []
    signatures: dict[tuple[str, str, str, str], int] = {}

    for index, raw in enumerate(raw_entries):
        if not isinstance(raw, dict):
            issue(
                issues,
                "error",
                "entry-object",
                f"Entry {index + 1} must be an object.",
                entry=index,
            )
            continue
        try:
            start = parse_datetime(raw.get("start"), f"entries[{index}].start")
            end = parse_datetime(raw.get("end"), f"entries[{index}].end")
            if end <= start:
                raise ValueError(f"Entry {index + 1} end must be after start.")
        except (TypeError, ValueError) as exc:
            issue(issues, "error", "entry-time", str(exc), entry=index)
            continue

        project = raw.get("project")
        task = raw.get("task")
        notes = raw.get("notes")
        activity = raw.get("activity")
        for field, value in (
            ("project", project),
            ("task", task),
            ("notes", notes),
            ("activity", activity),
        ):
            if not isinstance(value, str) or not value.strip():
                issue(
                    issues,
                    "error",
                    f"entry-{field}",
                    f"Entry {index + 1} requires {field}.",
                    entry=index,
                )
        project = project.strip() if isinstance(project, str) else ""
        task = task.strip() if isinstance(task, str) else ""
        notes = notes.strip() if isinstance(notes, str) else ""
        activity = activity.strip() if isinstance(activity, str) else ""

        if len(notes) < 30:
            issue(
                issues,
                "warning",
                "short-note",
                f"Entry {index + 1} note is unusually short.",
                entry=index,
            )

        confidence = raw.get("confidence")
        if confidence not in CONFIDENCE_LEVELS:
            issue(
                issues,
                "error",
                "confidence",
                f"Entry {index + 1} has an invalid confidence grade.",
                entry=index,
            )
        if confidence == "inferred":
            issue(
                issues,
                "warning",
                "inferred",
                f"Entry {index + 1} is inferred and must be resolved before entry.",
                entry=index,
            )
        if (
            confidence == "shared-confirmed"
            and raw.get("participation_confirmed") is not True
        ):
            issue(
                issues,
                "error",
                "shared-unconfirmed",
                f"Entry {index + 1} shared work lacks participation confirmation.",
                entry=index,
            )

        evidence = raw.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            issue(
                issues,
                "warning",
                "missing-evidence",
                f"Entry {index + 1} has no evidence metadata.",
                entry=index,
            )
            evidence = []

        blocked = blocked_match(project, blocked_projects)
        if blocked:
            issue(
                issues,
                "error",
                "blocked-project",
                f"Entry {index + 1} uses blocked project {project!r}.",
                entry=index,
            )

        if start.date() < period_start or start.date() > period_end:
            issue(
                issues,
                "error",
                "outside-period",
                f"Entry {index + 1} starts outside the review period.",
                entry=index,
            )

        allow_non_workday = raw.get("allow_non_workday") is True
        if (
            start.date().weekday() not in workdays
            or start.date() in leave_dates
            or start.date() in holiday_dates
        ) and not allow_non_workday:
            issue(
                issues,
                "error",
                "non-workday",
                f"Entry {index + 1} starts on a weekend, leave day, or holiday.",
                entry=index,
                day=start.date().isoformat(),
            )

        duration = minutes(end - start)
        if duration > 24 * 60:
            issue(
                issues,
                "warning",
                "long-entry",
                f"Entry {index + 1} is longer than 24 hours.",
                entry=index,
            )

        signature = (start.isoformat(), end.isoformat(), project, notes.casefold())
        if signature in signatures:
            issue(
                issues,
                "error",
                "duplicate",
                f"Entry {index + 1} duplicates entry {signatures[signature] + 1}.",
                entry=index,
            )
        else:
            signatures[signature] = index

        parsed = dict(raw)
        parsed.update(
            {
                "_index": index,
                "_start": start,
                "_end": end,
                "_duration_minutes": duration,
                "project": project,
                "task": task,
                "notes": notes,
                "activity": activity,
                "confidence": confidence,
                "evidence": evidence,
            }
        )
        entries.append(parsed)

    ordered = sorted(entries, key=lambda item: item["_start"])
    for left_index, left in enumerate(ordered):
        for right in ordered[left_index + 1 :]:
            if right["_start"] >= left["_end"]:
                break
            if intervals_overlap(
                left["_start"], left["_end"], right["_start"], right["_end"]
            ):
                issue(
                    issues,
                    "error",
                    "overlap",
                    (
                        f"Entries {left['_index'] + 1} and "
                        f"{right['_index'] + 1} overlap."
                    ),
                )

    for entry in entries:
        for day in date_range(entry["_start"].date(), entry["_end"].date()):
            for work_break in breaks:
                break_start = datetime.combine(day, work_break["start"])
                break_end = datetime.combine(day, work_break["end"])
                if intervals_overlap(
                    entry["_start"], entry["_end"], break_start, break_end
                ):
                    issue(
                        issues,
                        "error",
                        "break-overlap",
                        (
                            f"Entry {entry['_index'] + 1} overlaps "
                            f"{work_break['label']} on {day.isoformat()}."
                        ),
                        entry=entry["_index"],
                        day=day.isoformat(),
                    )

    daily: list[dict[str, Any]] = []
    for day in date_range(period_start, period_end):
        day_type = "workday"
        if day in leave_dates:
            day_type = "leave"
        elif day in holiday_dates:
            day_type = "holiday"
        elif day.weekday() not in workdays:
            day_type = "weekend"

        work_start = datetime.combine(day, workday_start)
        work_end = datetime.combine(day, workday_end)
        break_intervals = [
            (datetime.combine(day, item["start"]), datetime.combine(day, item["end"]))
            for item in breaks
        ]
        expected_segments = subtract_intervals(
            [(work_start, work_end)], break_intervals
        )
        expected_minutes = sum(minutes(end - start) for start, end in expected_segments)

        covering: list[tuple[datetime, datetime]] = []
        for entry in entries:
            for segment_start, segment_end in expected_segments:
                start = max(entry["_start"], segment_start)
                end = min(entry["_end"], segment_end)
                if start < end:
                    covering.append((start, end))
        merged_covering = merge_intervals(covering)
        covered_minutes = sum(minutes(end - start) for start, end in merged_covering)
        gaps = subtract_intervals(expected_segments, merged_covering)

        anchored = [entry for entry in entries if entry["_start"].date() == day]
        logged_minutes = sum(entry["_duration_minutes"] for entry in anchored)
        required_minutes = minimum_work_minutes if day_type == "workday" else 0
        complete = covered_minutes >= required_minutes

        if day_type == "workday" and not complete:
            issue(
                issues,
                "error",
                "coverage-gap",
                (
                    f"{day.isoformat()} covers {format_minutes(covered_minutes)} "
                    f"of required {format_minutes(required_minutes)}."
                ),
                day=day.isoformat(),
            )

        daily.append(
            {
                "date": day.isoformat(),
                "day_name": day.strftime("%A"),
                "type": day_type,
                "expected_minutes": expected_minutes if day_type == "workday" else 0,
                "required_minutes": required_minutes,
                "covered_minutes": covered_minutes,
                "logged_minutes": logged_minutes,
                "complete": complete,
                "gaps": [
                    {
                        "start": start.isoformat(timespec="minutes"),
                        "end": end.isoformat(timespec="minutes"),
                        "minutes": minutes(end - start),
                    }
                    for start, end in gaps
                ]
                if day_type == "workday"
                else [],
                "entry_indexes": [entry["_index"] for entry in anchored],
            }
        )

    total_logged = sum(entry["_duration_minutes"] for entry in entries)
    errors = sum(item["severity"] == "error" for item in issues)
    warnings = sum(item["severity"] == "warning" for item in issues)
    complete_workdays = sum(
        item["type"] == "workday" and item["complete"] for item in daily
    )
    workday_count = sum(item["type"] == "workday" for item in daily)

    public_entries = []
    for entry in entries:
        public_entries.append(
            {key: value for key, value in entry.items() if not key.startswith("_")}
            | {
                "index": entry["_index"],
                "duration_minutes": entry["_duration_minutes"],
            }
        )

    return {
        "ok": errors == 0,
        "summary": {
            "employee": plan.get("employee", ""),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "timezone": timezone_name or "",
            "entry_count": len(entries),
            "total_logged_minutes": total_logged,
            "total_logged": format_minutes(total_logged),
            "workday_count": workday_count,
            "complete_workdays": complete_workdays,
            "errors": errors,
            "warnings": warnings,
        },
        "evidence_coverage": plan.get("evidence_coverage", {}),
        "issues": issues,
        "daily": daily,
        "entries": public_entries,
    }


def color_class(project: str) -> str:
    digest = hashlib.sha256(project.encode("utf-8")).digest()
    return f"project-{digest[0] % 6}"


def render_html(plan: dict[str, Any], audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    entries_by_index = {entry["index"]: entry for entry in audit["entries"]}
    evidence_coverage = audit.get("evidence_coverage")
    coverage_items = []
    if isinstance(evidence_coverage, dict):
        for source, status in evidence_coverage.items():
            coverage_items.append(
                f'<span class="coverage-chip">{html.escape(str(source).replace("_", " ").title())}: '
                f"{html.escape(str(status))}</span>"
            )

    issue_rows = []
    for item in audit["issues"]:
        context = []
        if "day" in item:
            context.append(item["day"])
        if "entry" in item:
            context.append(f"Entry {item['entry'] + 1}")
        issue_rows.append(
            '<li class="issue {severity}"><strong>{code}</strong>'
            "<span>{message}</span><small>{context}</small></li>".format(
                severity=html.escape(item["severity"]),
                code=html.escape(item["code"]),
                message=html.escape(item["message"]),
                context=html.escape(" / ".join(context)),
            )
        )
    if not issue_rows:
        issue_rows.append(
            '<li class="issue clear"><strong>Audit clear</strong>'
            "<span>No structural, routing, overlap, break, or coverage issues.</span>"
            "<small>Ready for user review</small></li>"
        )

    day_sections = []
    for day in audit["daily"]:
        anchored_entries = [entries_by_index[index] for index in day["entry_indexes"]]
        entry_rows = []
        for entry in anchored_entries:
            start = datetime.fromisoformat(entry["start"])
            end = datetime.fromisoformat(entry["end"])
            time_label = f"{format_clock(start)} - {format_clock(end)}"
            if start.date() != end.date():
                time_label = (
                    f"{start.strftime('%d %b')} {format_clock(start)} - "
                    f"{end.strftime('%d %b')} {format_clock(end)}"
                )
            evidence_items = []
            for evidence in entry.get("evidence", []):
                if not isinstance(evidence, dict):
                    continue
                line = " | ".join(
                    str(value)
                    for value in (
                        evidence.get("timestamp", ""),
                        evidence.get("source", ""),
                        evidence.get("subject", ""),
                    )
                    if value
                )
                if line:
                    evidence_items.append(f"<li>{html.escape(line)}</li>")
            evidence_html = (
                "<details><summary>Evidence</summary><ul>"
                + "".join(evidence_items)
                + "</ul></details>"
                if evidence_items
                else '<span class="no-evidence">No evidence metadata</span>'
            )
            entry_rows.append(
                """
                <article class="entry">
                  <div class="entry-time">
                    <strong>{time}</strong>
                    <span>{duration}</span>
                  </div>
                  <div class="entry-body">
                    <div class="entry-heading">
                      <span class="project {project_class}">{project}</span>
                      <span class="task">{task}</span>
                      <span class="confidence">{confidence}</span>
                    </div>
                    <h3>{activity}</h3>
                    <p>{notes}</p>
                    {evidence}
                  </div>
                </article>
                """.format(
                    time=html.escape(time_label),
                    duration=html.escape(format_minutes(entry["duration_minutes"])),
                    project_class=color_class(entry["project"]),
                    project=html.escape(entry["project"]),
                    task=html.escape(entry["task"]),
                    confidence=html.escape(str(entry.get("confidence", ""))),
                    activity=html.escape(entry["activity"]),
                    notes=html.escape(entry["notes"]),
                    evidence=evidence_html,
                )
            )
        if not entry_rows:
            entry_rows.append(
                '<p class="empty-day">No entries anchored to this date.</p>'
            )

        gap_text = ", ".join(
            f"{format_clock(datetime.fromisoformat(gap['start']))}-"
            f"{format_clock(datetime.fromisoformat(gap['end']))}"
            for gap in day["gaps"]
        )
        status = (
            "complete" if day["type"] != "workday" or day["complete"] else "incomplete"
        )
        coverage = (
            f"Coverage {format_minutes(day['covered_minutes'])} / "
            f"{format_minutes(day['required_minutes'])}"
            if day["type"] == "workday"
            else day["type"].title()
        )
        if gap_text:
            coverage += f" | Gaps: {gap_text}"

        parsed_day = date.fromisoformat(day["date"])
        day_sections.append(
            """
            <section class="day {status}">
              <header>
                <div>
                  <p class="date-kicker">{date}</p>
                  <h2>{day_name}</h2>
                </div>
                <div class="day-metrics">
                  <span>{coverage}</span>
                  <strong>Logged {logged}</strong>
                </div>
              </header>
              {entries}
            </section>
            """.format(
                status=status,
                date=html.escape(parsed_day.strftime("%d %B %Y")),
                day_name=html.escape(day["day_name"]),
                coverage=html.escape(coverage),
                logged=html.escape(format_minutes(day["logged_minutes"])),
                entries="".join(entry_rows),
            )
        )

    status_label = "Audit clear" if audit["ok"] else "Needs correction"
    generated = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AFED Timesheet Review</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #172033;
      --muted: #667085;
      --line: #d9dee8;
      --panel: #ffffff;
      --surface: #f4f6f9;
      --accent: #8a2be2;
      --good: #087a55;
      --warn: #9a6700;
      --bad: #b42318;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--surface);
      color: var(--ink);
      font: 14px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
      letter-spacing: 0;
    }}
    main {{ width: min(1180px, calc(100% - 32px)); margin: 32px auto 64px; }}
    .masthead {{
      display: flex; justify-content: space-between; gap: 24px; align-items: end;
      padding: 0 0 24px; border-bottom: 2px solid var(--ink);
    }}
    h1, h2, h3, p {{ margin-top: 0; }}
    h1 {{ margin-bottom: 6px; font-size: clamp(28px, 4vw, 44px); line-height: 1.05; }}
    .subtitle, .generated {{ color: var(--muted); margin-bottom: 0; }}
    .status {{ text-align: right; }}
    .status strong {{ display: block; font-size: 18px; color: {status_color}; }}
    .summary {{
      display: grid; grid-template-columns: repeat(5, minmax(0, 1fr));
      border-bottom: 1px solid var(--line); background: var(--panel);
    }}
    .metric {{ padding: 18px; border-right: 1px solid var(--line); }}
    .metric:last-child {{ border-right: 0; }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; }}
    .metric strong {{ display: block; margin-top: 4px; font-size: 24px; }}
    .coverage {{ display: flex; flex-wrap: wrap; gap: 8px; padding: 16px 0; }}
    .coverage-chip, .task, .confidence {{
      display: inline-flex; align-items: center; min-height: 24px; padding: 2px 8px;
      border: 1px solid var(--line); background: var(--panel); font-size: 12px;
    }}
    .audit {{ margin: 18px 0 28px; }}
    .audit h2 {{ font-size: 18px; }}
    .issue-list {{ display: grid; gap: 6px; padding: 0; list-style: none; }}
    .issue {{
      display: grid; grid-template-columns: 150px 1fr auto; gap: 12px;
      align-items: center; padding: 10px 12px; background: var(--panel);
      border-left: 4px solid var(--line);
    }}
    .issue.error {{ border-left-color: var(--bad); }}
    .issue.warning {{ border-left-color: var(--warn); }}
    .issue.clear {{ border-left-color: var(--good); }}
    .issue small {{ color: var(--muted); }}
    .day {{ margin-top: 16px; background: var(--panel); border: 1px solid var(--line); }}
    .day.incomplete {{ border-left: 4px solid var(--bad); }}
    .day > header {{
      display: flex; justify-content: space-between; gap: 24px; align-items: center;
      padding: 14px 16px; border-bottom: 1px solid var(--line);
    }}
    .date-kicker {{ margin-bottom: 1px; color: var(--muted); font-size: 12px; }}
    .day h2 {{ margin-bottom: 0; font-size: 18px; }}
    .day-metrics {{ text-align: right; }}
    .day-metrics span {{ display: block; color: var(--muted); font-size: 12px; }}
    .entry {{ display: grid; grid-template-columns: 190px 1fr; border-bottom: 1px solid var(--line); }}
    .entry:last-child {{ border-bottom: 0; }}
    .entry-time {{ padding: 16px; border-right: 1px solid var(--line); }}
    .entry-time strong, .entry-time span {{ display: block; }}
    .entry-time span {{ color: var(--muted); margin-top: 3px; }}
    .entry-body {{ min-width: 0; padding: 16px; }}
    .entry-heading {{ display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }}
    .entry h3 {{ margin: 10px 0 4px; font-size: 15px; }}
    .entry p {{ margin-bottom: 10px; color: #344054; }}
    .project {{
      display: inline-flex; max-width: 100%; padding: 3px 8px; color: #fff;
      overflow-wrap: anywhere; font-size: 12px; font-weight: 650;
    }}
    .project-0 {{ background: #175cd3; }}
    .project-1 {{ background: #087a55; }}
    .project-2 {{ background: #9a3412; }}
    .project-3 {{ background: #7a2e8a; }}
    .project-4 {{ background: #475467; }}
    .project-5 {{ background: #a15c00; }}
    details {{ color: var(--muted); font-size: 12px; }}
    details ul {{ margin: 8px 0 0; padding-left: 20px; }}
    .no-evidence, .empty-day {{ color: var(--muted); font-style: italic; }}
    .empty-day {{ margin: 0; padding: 16px; }}
    @media (max-width: 760px) {{
      main {{ width: min(100% - 20px, 1180px); margin-top: 18px; }}
      .masthead, .day > header {{ align-items: flex-start; flex-direction: column; }}
      .status, .day-metrics {{ text-align: left; }}
      .summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .metric {{ border-bottom: 1px solid var(--line); }}
      .entry {{ grid-template-columns: 1fr; }}
      .entry-time {{ border-right: 0; border-bottom: 1px solid var(--line); }}
      .issue {{ grid-template-columns: 1fr; gap: 3px; }}
    }}
    @media print {{
      body {{ background: #fff; }}
      main {{ width: 100%; margin: 0; }}
      .day, .entry {{ break-inside: avoid; }}
      details {{ display: block; }}
    }}
  </style>
</head>
<body>
<main>
  <header class="masthead">
    <div>
      <h1>AFED Timesheet Review</h1>
      <p class="subtitle">{employee} | {period_start} to {period_end} | {timezone}</p>
    </div>
    <div class="status">
      <strong>{status_label}</strong>
      <p class="generated">Generated {generated}</p>
    </div>
  </header>
  <section class="summary" aria-label="Summary">
    <div class="metric"><span>Entries</span><strong>{entry_count}</strong></div>
    <div class="metric"><span>Total logged</span><strong>{total_logged}</strong></div>
    <div class="metric"><span>Covered workdays</span><strong>{complete_days}/{workdays}</strong></div>
    <div class="metric"><span>Errors</span><strong>{errors}</strong></div>
    <div class="metric"><span>Warnings</span><strong>{warnings}</strong></div>
  </section>
  <div class="coverage">{coverage}</div>
  <section class="audit">
    <h2>Audit</h2>
    <ul class="issue-list">{issues}</ul>
  </section>
  <section class="schedule" aria-label="Schedule">
    {days}
  </section>
</main>
</body>
</html>
""".format(
        status_color="var(--good)" if audit["ok"] else "var(--bad)",
        employee=html.escape(str(summary["employee"])),
        period_start=html.escape(summary["period_start"]),
        period_end=html.escape(summary["period_end"]),
        timezone=html.escape(summary["timezone"]),
        status_label=status_label,
        generated=generated,
        entry_count=summary["entry_count"],
        total_logged=html.escape(summary["total_logged"]),
        complete_days=summary["complete_workdays"],
        workdays=summary["workday_count"],
        errors=summary["errors"],
        warnings=summary["warnings"],
        coverage="".join(coverage_items),
        issues="".join(issue_rows),
        days="".join(day_sections),
    )


def main() -> int:
    args = parse_args()
    try:
        plan = load_plan(args.plan)
        audit = audit_plan(plan)
    except (TypeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.audit_json:
        args.audit_json.parent.mkdir(parents=True, exist_ok=True)
        args.audit_json.write_text(
            json.dumps(audit, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(render_html(plan, audit), encoding="utf-8")

    summary = audit["summary"]
    print(
        f"{summary['entry_count']} entries | "
        f"{summary['total_logged']} logged | "
        f"{summary['complete_workdays']}/{summary['workday_count']} workdays covered | "
        f"{summary['errors']} errors | {summary['warnings']} warnings"
    )
    for item in audit["issues"]:
        print(
            f"{item['severity'].upper()}: {item['code']}: {item['message']}",
            file=sys.stderr if item["severity"] == "error" else sys.stdout,
        )

    if args.strict and not audit["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
