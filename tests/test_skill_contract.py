from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class SharedSkillContractTests(unittest.TestCase):
    def test_no_project_is_blocked_by_default(self) -> None:
        skill = read("SKILL.md")
        routing = read("references/afed-project-routing.md")
        schema = read("references/plan-schema.md")

        self.assertNotIn("blocked by default", skill.casefold())
        self.assertNotIn("## Default Blocks", routing)

        example_match = re.search(r"```json\n(.*?)\n```", schema, re.DOTALL)
        self.assertIsNotNone(example_match)
        example = json.loads(example_match.group(1))
        self.assertEqual(example["policy"]["blocked_projects"], [])

    def test_first_run_introduction_is_warm_and_adaptable(self) -> None:
        skill = read("SKILL.md")

        self.assertIn("Yunus prepared me", skill)
        self.assertIn("fine-tune", skill.casefold())
        self.assertIn("Outlook", skill)
        self.assertIn("Teams", skill)

    def test_capability_bootstrap_guides_only_required_user_actions(self) -> None:
        setup = read("references/setup.md")

        self.assertIn("Plugin Management", setup)
        self.assertIn("install", setup.casefold())
        self.assertIn("authenticate", setup.casefold())
        self.assertIn("verify", setup.casefold())
        self.assertIn("only the user", setup.casefold())

    def test_reconciliation_invites_project_category_corrections(self) -> None:
        skill = read("SKILL.md")
        reconciliation = skill.split("## Phase 8: Reconcile", maxsplit=1)[1]
        reconciliation_text = " ".join(
            reconciliation.casefold().replace(">", "").split()
        )

        self.assertIn("project and task categories", reconciliation_text)
        self.assertIn("correction", reconciliation_text)
        self.assertIn("Yunus prepared me", reconciliation)
        self.assertIn("Do not click `Submit month`", reconciliation)

    def test_onboarding_is_not_written_for_a_specific_role(self) -> None:
        skill = read("SKILL.md")
        onboarding = skill.split("## Phase 0: Bootstrap Capabilities", maxsplit=1)[1]
        onboarding = onboarding.split("## Phase 1:", maxsplit=1)[0]

        self.assertNotIn("manager", onboarding.casefold())
        self.assertNotIn("senior", onboarding.casefold())


if __name__ == "__main__":
    unittest.main()
