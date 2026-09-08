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

    def test_replacement_reviewer_continues_the_same_bounded_round(self) -> None:
        skill = (SKILLS / "eng-bounded-delivery" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        review = (
            SKILLS / "eng-bounded-delivery" / "assets" / "review.md"
        ).read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", f"{skill} {review}".lower())

        for phrase in (
            "same reviewer is preferred",
            "genuinely unavailable",
            "one replacement reviewer",
            "same verification round",
            "review round",
            "repair budget",
            "existing findings",
            "acceptance criteria",
            "reviewed target",
            "severity rules",
            "did not implement the current repair",
            "read-only",
            "not a second review layer",
            "current exact head",
        ):
            self.assertIn(phrase, normalized)
        self.assertIn("REPLACEMENT_BLOCKER_VERIFICATION", review)

    def test_normal_task_reuses_knowledge_without_recovery_or_duplicate_write(self) -> None:
        start = (SKILLS / "eng-task-start/SKILL.md").read_text()
        close = (SKILLS / "eng-verified-closeout/SKILL.md").read_text()
        core = (ROOT / "docs/apg-v1-contract.md").read_text()
        for phrase in ("RETRIEVAL_USED=YES|NO", "REUSED_KNOWLEDGE=<references or NONE>"):
            self.assertIn(phrase, start)
        self.assertIn("REUSED_KNOWLEDGE=NONE", start)
        self.assertIn("KNOWLEDGE_WRITE=SKIPPED", close)
        self.assertIn("RECOVERY_ARTIFACT_REQUIRED=NO", core)
        for template in ("AGENTS.md", "AGENTS-existing-project.md"):
            text = (SKILLS / "project-bootstrap/assets" / template).read_text()
            self.assertNotIn("Give every main agent", text)
            self.assertIn("only", text)
            self.assertIn("NEW_KNOWLEDGE=YES", text)

    def test_learning_is_conditional_after_acceptance_and_promotion_requires_reuse(self) -> None:
        text = (SKILLS / "eng-verified-closeout/SKILL.md").read_text()
        self.assertIn("after task acceptance", text)
        self.assertIn("NEW_KNOWLEDGE=YES", text)
        self.assertIn("UPDATE_NEEDED=YES", text)
        self.assertIn("actual reuse", text)
        self.assertIn("Do not create a completion report", text)

    def test_every_skill_local_markdown_link_resolves(self) -> None:
        for skill in SKILLS.glob("*/SKILL.md"):
            for relative in re.findall(r"\]\(([^)]+)\)", skill.read_text(encoding="utf-8")):
                if "://" not in relative:
                    self.assertTrue((skill.parent / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
