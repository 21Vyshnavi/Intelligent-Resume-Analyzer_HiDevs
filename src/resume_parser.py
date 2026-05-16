"""
resume_parser.py
----------------
Extracts structured information from raw resume text.
Handles: name, email, phone, skills, experience, education.
"""

import re
import json
from typing import Optional


# ---------------------------------------------------------------------------
# Skill keyword bank – extend freely
# ---------------------------------------------------------------------------
SKILL_KEYWORDS: list[str] = [
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "bash", "shell",
    # Web
    "html", "css", "react", "angular", "vue", "next.js", "node.js", "django",
    "flask", "fastapi", "spring boot", "express", "graphql", "rest api",
    "tailwind", "bootstrap",
    # Data / ML
    "machine learning", "deep learning", "nlp", "computer vision", "tensorflow",
    "pytorch", "keras", "scikit-learn", "pandas", "numpy", "matplotlib",
    "seaborn", "opencv", "hugging face", "langchain",
    # Databases
    "sql", "mysql", "postgresql", "mongodb", "redis", "sqlite", "dynamodb",
    "cassandra", "elasticsearch", "firebase",
    # Cloud / DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "github actions", "gitlab ci", "ci/cd", "linux", "nginx",
    "prometheus", "grafana",
    # Tools
    "git", "github", "jira", "confluence", "figma", "postman", "swagger",
    "tableau", "power bi", "excel", "spark", "hadoop", "airflow", "kafka",
]

EDUCATION_DEGREES = [
    "b.tech", "b.e", "b.sc", "b.s", "b.com", "bca", "bba",
    "m.tech", "m.e", "m.sc", "m.s", "mca", "mba", "m.com",
    "ph.d", "phd", "doctorate",
    "bachelor", "master", "diploma", "associate",
]

SECTION_HEADERS = [
    "experience", "work experience", "employment", "professional experience",
    "education", "academic", "skills", "technical skills", "projects",
    "certifications", "achievements", "summary", "objective", "profile",
]


# ---------------------------------------------------------------------------
# ResumeParser
# ---------------------------------------------------------------------------
class ResumeParser:
    """Parse plain-text resume into a structured Python dict."""

    def __init__(self, text: str) -> None:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Resume text must be a non-empty string.")
        self.text = text
        self.lines = [ln.strip() for ln in text.splitlines()]
        self.lower = text.lower()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def parse(self) -> dict:
        """Return the full structured candidate profile."""
        result = {
            "name":       self._extract_name(),
            "email":      self._extract_email(),
            "phone":      self._extract_phone(),
            "summary":    self._extract_summary(),
            "skills":     self._extract_skills(),
            "experience": self._extract_experience(),
            "education":  self._extract_education(),
            "total_experience_years": self._calculate_experience_years(),
        }
        return result

    # ------------------------------------------------------------------
    # Extractors
    # ------------------------------------------------------------------
    def _extract_name(self) -> Optional[str]:
        """
        Heuristic: first non-empty line that has no '@', no digits,
        and looks like a proper name (2-4 words, title-cased).
        Falls back to regex for 'Name: …' patterns.
        """
        # Pattern: explicit label
        pattern = re.search(r"(?:name|full name)\s*[:\-]\s*(.+)", self.text, re.IGNORECASE)
        if pattern:
            return pattern.group(1).strip()

        # Heuristic: first non-blank line that resembles a name
        for line in self.lines[:6]:
            if not line:
                continue
            if "@" in line or re.search(r"\d{5,}", line):
                continue
            words = line.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                return line
        return None

    def _extract_email(self) -> Optional[str]:
        match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", self.text)
        return match.group(0) if match else None

    def _extract_phone(self) -> Optional[str]:
        match = re.search(
            r"(\+?\d[\d\s\-().]{8,14}\d)", self.text
        )
        return match.group(0).strip() if match else None

    def _extract_summary(self) -> Optional[str]:
        """Return the paragraph under Summary / Objective / Profile."""
        keywords = ["summary", "objective", "profile", "about"]
        for i, line in enumerate(self.lines):
            if any(kw in line.lower() for kw in keywords):
                # Grab up to 4 subsequent non-empty lines
                chunk = []
                for ln in self.lines[i + 1: i + 6]:
                    if ln and not any(h in ln.lower() for h in SECTION_HEADERS):
                        chunk.append(ln)
                    elif chunk:
                        break
                if chunk:
                    return " ".join(chunk)
        return None

    def _extract_skills(self) -> list[str]:
        """Match skill keywords found anywhere in the resume text."""
        found = []
        for skill in SKILL_KEYWORDS:
            # Whole-word match, case-insensitive
            pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
            if re.search(pattern, self.lower):
                # Keep original capitalisation from keyword list
                found.append(skill.title() if skill == skill.lower() else skill)
        return sorted(set(found))

    def _extract_experience(self) -> list[dict]:
        """
        Extract job blocks heuristically by looking for date ranges.
        Returns a list of {title, company, duration} dicts.
        """
        entries = []
        date_pattern = re.compile(
            r"(\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)?\.?\s*\d{4})"
            r"\s*[-–to]+\s*"
            r"(\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)?\.?\s*\d{4}|present|current)",
            re.IGNORECASE,
        )

        for i, line in enumerate(self.lines):
            m = date_pattern.search(line)
            if m:
                duration = f"{m.group(1).strip()} – {m.group(2).strip()}"
                # Try to find title/company on surrounding lines
                title_line = self.lines[i - 1] if i > 0 else line
                # Strip the date part from the current line to get company / title
                remainder = date_pattern.sub("", line).strip(" :-–|")
                entries.append({
                    "title":    title_line if title_line != line else remainder,
                    "company":  remainder or "",
                    "duration": duration,
                })
        return entries

    def _extract_education(self) -> list[dict]:
        """Detect education entries by degree keywords."""
        edu = []
        degree_pattern = re.compile(
            r"(" + "|".join(re.escape(d) for d in EDUCATION_DEGREES) + r")",
            re.IGNORECASE,
        )
        for i, line in enumerate(self.lines):
            if degree_pattern.search(line):
                year_match = re.search(r"\b(19|20)\d{2}\b", line)
                edu.append({
                    "degree":      line,
                    "institution": self.lines[i + 1] if i + 1 < len(self.lines) else "",
                    "year":        year_match.group(0) if year_match else "",
                })
        return edu

    def _calculate_experience_years(self) -> float:
        """
        Sum up years from date ranges found in the resume.
        Returns total rounded to 1 decimal.
        """
        date_re = re.compile(
            r"(\d{4})\s*[-–to]+\s*(\d{4}|present|current)",
            re.IGNORECASE,
        )
        current_year = 2025
        total = 0.0
        for m in date_re.finditer(self.lower):
            start = int(m.group(1))
            end_raw = m.group(2)
            end = current_year if end_raw.lower() in ("present", "current") else int(end_raw)
            diff = end - start
            if 0 < diff < 50:          # sanity check
                total += diff
        return round(total, 1)
