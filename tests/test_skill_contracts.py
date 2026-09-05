from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
EXPECTED_SKILLS = {
    "context-governance",
    "eng-bounded-delivery",
    "eng-task-start",
    "eng-verified-closeout",
    "project-bootstrap",
}
NEW_SKILLS = EXPECTED_SKILLS - {"context-governance", "project-bootstrap"}


class SkillContractTests(unittest.TestCase):
    def test_exactly_five_approved_skill_entrypoints_are_distributed(self) -> None:
        actual = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
        self.assertEqual(actual, EXPECTED_SKILLS)
        self.assertNotIn("eng-context-handoff", actual)

    def test_new_skills_are_explicit_only_and_define_non_trigger_cases(self) -> None:
        for name in NEW_SKILLS:
            skill = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
            agent = (SKILLS / name / "agents" / "openai.yaml").read_text(
                encoding="utf-8"
            )
            self.assertIn("## Do not use when", skill, name)
            self.assertRegex(
                agent,
                r"(?ms)^policy:\s*\n\s+allow_implicit_invocation:\s*false\s*$",
                name,
            )

    def test_context_governance_is_the_only_handoff_store(self) -> None:
        skill = (SKILLS / "context-governance" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        normalized = re.sub(r"\s+", " ", skill.lower())
        handoff = SKILLS / "context-governance" / "assets" / "handoff.md"
        self.assertTrue(handoff.is_file())
        for phrase in (
            "original blocker",
            "review rounds already used",
            "known uncommitted work",
            "next bounded action",
        ):
            self.assertIn(phrase, normalized)

    def test_every_skill_local_markdown_link_resolves(self) -> None:
        for skill in SKILLS.glob("*/SKILL.md"):
            for relative in re.findall(r"\]\(([^)]+)\)", skill.read_text(encoding="utf-8")):
                if "://" not in relative:
                    self.assertTrue((skill.parent / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
