"""
report_generator.py
-------------------
Generates human-readable hiring reports from candidate + match data.
Supports plain-text and Markdown formats.
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# ReportGenerator
# ---------------------------------------------------------------------------
class ReportGenerator:
    """
    Build a professional hiring report.

    Parameters
    ----------
    candidate : dict   – output from ResumeParser.parse()
    match     : dict   – output from ResumeMatcher.match()
    job_title : str    – job role being hired for
    company   : str    – hiring company name
    """

    def __init__(
        self,
        candidate: dict,
        match: dict,
        job_title: str = "the position",
        company: str = "",
    ) -> None:
        self.candidate = candidate
        self.match = match
        self.job_title = job_title
        self.company = company
        self.generated_at = datetime.now().strftime("%d %B %Y, %H:%M")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_text(self) -> str:
        """Return a plain-text hiring report."""
        lines = []
        w = lines.append

        w("=" * 64)
        w("       INTELLIGENT RESUME ANALYZER – HIRING REPORT")
        w("=" * 64)
        w(f"Generated : {self.generated_at}")
        if self.company:
            w(f"Company   : {self.company}")
        w(f"Role      : {self.job_title}")
        w("")

        # --- Candidate snapshot ---
        w("-" * 64)
        w("CANDIDATE PROFILE")
        w("-" * 64)
        w(f"Name          : {self.candidate.get('name', 'N/A')}")
        w(f"Email         : {self.candidate.get('email', 'N/A')}")
        w(f"Phone         : {self.candidate.get('phone', 'N/A')}")
        w(f"Experience    : {self.candidate.get('total_experience_years', 0)} years")

        edu = self.candidate.get("education", [])
        if edu:
            w(f"Education     : {edu[0].get('degree', '')} {edu[0].get('year','')}")

        summary = self.candidate.get("summary")
        if summary:
            w("")
            w("Summary:")
            w(self._wrap(summary, width=60, indent="  "))

        # --- Scores ---
        w("")
        w("-" * 64)
        w("MATCH SCORES")
        w("-" * 64)
        w(f"Overall Score     : {self.match.get('overall_score', 0):>6.1f} / 100")
        w(f"Skill Match       : {self.match.get('skill_score', 0):>6.1f} / 100  (weight 50%)")
        w(f"Experience Fit    : {self.match.get('experience_score', 0):>6.1f} / 100  (weight 30%)")
        w(f"Education Score   : {self.match.get('education_score', 0):>6.1f} / 100  (weight 20%)")
        w("")
        verdict = self.match.get("verdict", "N/A")
        w(f"VERDICT : {verdict}")
        w(f"ACTION  : {self.match.get('recommendation', '')}")

        # --- Skills breakdown ---
        w("")
        w("-" * 64)
        w("SKILLS BREAKDOWN")
        w("-" * 64)

        matched = self.match.get("matched_skills", [])
        missing = self.match.get("missing_skills", [])
        all_skills = self.candidate.get("skills", [])

        if matched:
            w(f"Matched ({len(matched)})  : {', '.join(matched)}")
        if missing:
            w(f"Missing ({len(missing)})  : {', '.join(missing)}")
        if all_skills:
            w(f"All Extracted   : {', '.join(all_skills)}")

        # --- Experience entries ---
        exp = self.candidate.get("experience", [])
        if exp:
            w("")
            w("-" * 64)
            w("WORK EXPERIENCE")
            w("-" * 64)
            for entry in exp:
                w(f"  • {entry.get('title', '')} | {entry.get('company', '')}  [{entry.get('duration', '')}]")

        # --- Education entries ---
        if edu:
            w("")
            w("-" * 64)
            w("EDUCATION")
            w("-" * 64)
            for entry in edu:
                w(f"  • {entry.get('degree', '')}  {entry.get('year', '')}")
                if entry.get("institution"):
                    w(f"    {entry['institution']}")

        w("")
        w("=" * 64)
        w("END OF REPORT")
        w("=" * 64)

        return "\n".join(lines)

    def generate_markdown(self) -> str:
        """Return a Markdown-formatted hiring report."""
        c = self.candidate
        m = self.match
        lines = []
        w = lines.append

        w(f"# Hiring Report — {self.job_title}")
        w(f"*Generated: {self.generated_at}*")
        if self.company:
            w(f"*Company: {self.company}*")
        w("")

        w("## Candidate Profile")
        w(f"| Field | Value |")
        w(f"|---|---|")
        w(f"| **Name** | {c.get('name','N/A')} |")
        w(f"| **Email** | {c.get('email','N/A')} |")
        w(f"| **Phone** | {c.get('phone','N/A')} |")
        w(f"| **Experience** | {c.get('total_experience_years',0)} years |")
        edu = c.get("education", [])
        if edu:
            w(f"| **Education** | {edu[0].get('degree','')} {edu[0].get('year','')} |")
        w("")

        if c.get("summary"):
            w(f"**Summary:** {c['summary']}")
            w("")

        w("## Match Scores")
        w("")
        overall = m.get("overall_score", 0)
        bar = self._progress_bar(overall)
        w(f"**Overall Score: {overall} / 100**  {bar}")
        w("")
        w("| Category | Score | Weight |")
        w("|---|---|---|")
        w(f"| Skill Match | {m.get('skill_score',0):.1f} | 50% |")
        w(f"| Experience | {m.get('experience_score',0):.1f} | 30% |")
        w(f"| Education | {m.get('education_score',0):.1f} | 20% |")
        w("")
        w(f"**Verdict:** {m.get('verdict','N/A')}")
        w(f"**Recommendation:** {m.get('recommendation','')}")
        w("")

        matched = m.get("matched_skills", [])
        missing = m.get("missing_skills", [])

        if matched or missing:
            w("## Skills Breakdown")
            if matched:
                w(f"**Matched ({len(matched)}):** " + " ".join(f"`{s}`" for s in matched))
            if missing:
                w(f"**Missing ({len(missing)}):** " + " ".join(f"`{s}`" for s in missing))
            w("")

        exp = c.get("experience", [])
        if exp:
            w("## Work Experience")
            for e in exp:
                w(f"- **{e.get('title','')}** | {e.get('company','')} _{e.get('duration','')}_")
            w("")

        if edu:
            w("## Education")
            for e in edu:
                w(f"- {e.get('degree','')} {e.get('year','')}  \n  _{e.get('institution','')}_")
            w("")

        return "\n".join(lines)

    def save(self, filepath: str | Path, fmt: str = "text") -> str:
        """
        Save the report to disk.

        Parameters
        ----------
        filepath : str | Path   – destination path (without extension)
        fmt      : "text" | "markdown"

        Returns
        -------
        str : actual path written
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "markdown":
            content = self.generate_markdown()
            full_path = path.with_suffix(".md")
        else:
            content = self.generate_text()
            full_path = path.with_suffix(".txt")

        full_path.write_text(content, encoding="utf-8")
        return str(full_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _wrap(text: str, width: int = 60, indent: str = "") -> str:
        """Simple word-wrap."""
        words = text.split()
        lines, current = [], ""
        for word in words:
            if len(current) + len(word) + 1 > width and current:
                lines.append(indent + current.rstrip())
                current = word + " "
            else:
                current += word + " "
        if current:
            lines.append(indent + current.rstrip())
        return "\n".join(lines)

    @staticmethod
    def _progress_bar(score: float, length: int = 20) -> str:
        filled = int((score / 100) * length)
        return "[" + "█" * filled + "░" * (length - filled) + "]"
