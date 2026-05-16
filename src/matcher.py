"""
matcher.py
----------
Calculates how well a parsed resume matches a job requirement.

Scoring formula (weights are configurable):
  overall = skill_score * 0.50
           + experience_score * 0.30
           + education_score  * 0.20
"""

from __future__ import annotations
import re
from typing import Optional


# ---------------------------------------------------------------------------
# Weight configuration (must sum to 1.0)
# ---------------------------------------------------------------------------
WEIGHTS = {
    "skills":     0.50,
    "experience": 0.30,
    "education":  0.20,
}

# Degree tier values for education scoring
DEGREE_TIERS = {
    "phd": 100, "ph.d": 100, "doctorate": 100,
    "m.tech": 85, "m.e": 85, "m.sc": 85, "m.s": 85,
    "mca": 80, "mba": 80, "m.com": 75,
    "b.tech": 70, "b.e": 70, "b.sc": 65, "b.s": 65,
    "bca": 60, "bba": 60, "b.com": 55,
    "diploma": 45, "associate": 40,
}

VERDICT_THRESHOLDS = [
    (76, "Strong Match"),
    (60, "Good Match"),
    (40, "Partial Match"),
    (0,  "Poor Match"),
]


# ---------------------------------------------------------------------------
# ResumeMatcher
# ---------------------------------------------------------------------------
class ResumeMatcher:
    """
    Match a parsed candidate profile against job requirements.

    Parameters
    ----------
    candidate : dict
        Output from ResumeParser.parse().
    required_skills : list[str]
        Skills the job demands (may also be derived from job_description).
    job_description : str, optional
        Free-text JD. Skills are extracted from it if required_skills is empty.
    min_experience_years : float
        Minimum years of experience the job requires.
    required_degree : str, optional
        E.g. "B.Tech", "M.Sc". Compared loosely against education entries.
    """

    def __init__(
        self,
        candidate: dict,
        required_skills: list[str] | None = None,
        job_description: str = "",
        min_experience_years: float = 0,
        required_degree: str = "",
    ) -> None:
        self.candidate = candidate
        self.job_description = job_description
        self.min_experience = min_experience_years
        self.required_degree = required_degree.lower()

        # Derive required skills from JD if not provided explicitly
        if required_skills:
            self.required_skills = [s.lower() for s in required_skills]
        else:
            self.required_skills = self._extract_skills_from_jd(job_description)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def match(self) -> dict:
        """Return full match result dict."""
        skill_result   = self._score_skills()
        exp_result     = self._score_experience()
        edu_result     = self._score_education()

        skill_score = skill_result["score"]
        exp_score   = exp_result["score"]
        edu_score   = edu_result["score"]

        overall = round(
            skill_score * WEIGHTS["skills"]
            + exp_score * WEIGHTS["experience"]
            + edu_score * WEIGHTS["education"],
            1,
        )

        return {
            "overall_score":      overall,
            "skill_score":        skill_score,
            "experience_score":   exp_score,
            "education_score":    edu_score,
            "matched_skills":     skill_result["matched"],
            "missing_skills":     skill_result["missing"],
            "verdict":            self._verdict(overall),
            "recommendation":     self._recommendation(overall),
            "weights_used":       WEIGHTS,
        }

    # ------------------------------------------------------------------
    # Skill scoring
    # ------------------------------------------------------------------
    def _score_skills(self) -> dict:
        candidate_skills = [s.lower() for s in self.candidate.get("skills", [])]

        if not self.required_skills:
            # No requirements → score based on breadth (max 80)
            return {
                "score":   min(80, len(candidate_skills) * 4),
                "matched": candidate_skills,
                "missing": [],
            }

        matched = [s for s in self.required_skills if self._skill_present(s, candidate_skills)]
        missing = [s for s in self.required_skills if not self._skill_present(s, candidate_skills)]

        score = round((len(matched) / len(self.required_skills)) * 100, 1)

        return {
            "score":   score,
            "matched": matched,
            "missing": missing,
        }

    @staticmethod
    def _skill_present(skill: str, candidate_skills: list[str]) -> bool:
        """Fuzzy check: skill is a substring of any candidate skill or vice-versa."""
        for cs in candidate_skills:
            if skill in cs or cs in skill:
                return True
        return False

    # ------------------------------------------------------------------
    # Experience scoring
    # ------------------------------------------------------------------
    def _score_experience(self) -> dict:
        actual = self.candidate.get("total_experience_years", 0) or 0

        if self.min_experience <= 0:
            # No requirement: map years → score linearly, cap at 100
            score = min(100, actual * 12)
        elif actual >= self.min_experience:
            # Bonus for exceeding requirement (capped at 100)
            bonus = min(20, (actual - self.min_experience) * 4)
            score = min(100, 80 + bonus)
        else:
            # Proportional score up to 79
            score = round((actual / self.min_experience) * 79, 1)

        return {"score": round(score, 1)}

    # ------------------------------------------------------------------
    # Education scoring
    # ------------------------------------------------------------------
    def _score_education(self) -> dict:
        edu_entries = self.candidate.get("education", [])
        if not edu_entries:
            return {"score": 40}   # unknown education → neutral penalty

        # Find highest tier
        highest = 0
        for entry in edu_entries:
            degree_text = entry.get("degree", "").lower()
            for key, tier_val in DEGREE_TIERS.items():
                if key in degree_text:
                    highest = max(highest, tier_val)

        if highest == 0:
            highest = 50   # fallback for unrecognised degrees

        # If a specific degree is required, penalise if not met
        if self.required_degree:
            required_tier = next(
                (v for k, v in DEGREE_TIERS.items() if k in self.required_degree),
                60,
            )
            if highest < required_tier:
                highest = max(30, highest - 15)

        return {"score": min(100, highest)}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_skills_from_jd(jd: str) -> list[str]:
        """Very light skill extraction from free-text JD."""
        from src.resume_parser import SKILL_KEYWORDS
        if not jd:
            return []
        jd_lower = jd.lower()
        found = []
        for skill in SKILL_KEYWORDS:
            pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
            if re.search(pattern, jd_lower):
                found.append(skill)
        return found

    @staticmethod
    def _verdict(score: float) -> str:
        for threshold, label in VERDICT_THRESHOLDS:
            if score >= threshold:
                return label
        return "Poor Match"

    @staticmethod
    def _recommendation(score: float) -> str:
        if score >= 76:
            return "Strongly recommend for interview."
        if score >= 60:
            return "Recommend for interview with minor reservations."
        if score >= 40:
            return "Consider only if the candidate pool is limited."
        return "Does not meet minimum requirements; do not proceed."
