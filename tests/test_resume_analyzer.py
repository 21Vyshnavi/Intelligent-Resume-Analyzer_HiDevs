"""
tests/test_resume_analyzer.py
------------------------------
Unit tests for all core modules.
Run with:  pytest tests/ -v
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.resume_parser import ResumeParser
from src.matcher import ResumeMatcher
from src.report_generator import ReportGenerator
from src.file_handler import save_candidate, load_candidate, list_candidates, delete_candidate


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
SAMPLE_RESUME = """\
Name: Anjali Mehta
Email: anjali.mehta@example.com
Phone: +91-9123456780

Summary:
Backend developer with 3 years of experience in Python and cloud technologies.

Experience:
- Python Developer at CloudBase Pvt Ltd (2022-2025)
  REST APIs, PostgreSQL, Docker deployment on AWS.
- Intern at WebStartup (2021-2022)
  Assisted in Django projects.

Skills: Python, Django, PostgreSQL, Docker, AWS, Git, REST API, Linux

Education:
B.Tech Computer Science, JNTU Hyderabad, 2021
"""

REQUIRED_SKILLS = ["python", "django", "docker", "kubernetes", "react"]


@pytest.fixture
def candidate():
    return ResumeParser(SAMPLE_RESUME).parse()


@pytest.fixture
def match_result(candidate):
    return ResumeMatcher(
        candidate=candidate,
        required_skills=REQUIRED_SKILLS,
        min_experience_years=2,
    ).match()


# ---------------------------------------------------------------------------
# ResumeParser tests
# ---------------------------------------------------------------------------
class TestResumeParser:
    def test_extract_name(self, candidate):
        assert candidate["name"] == "Anjali Mehta"

    def test_extract_email(self, candidate):
        assert candidate["email"] == "anjali.mehta@example.com"

    def test_extract_phone(self, candidate):
        assert candidate["phone"] is not None
        assert "9123456780" in candidate["phone"]

    def test_extract_skills_non_empty(self, candidate):
        assert isinstance(candidate["skills"], list)
        assert len(candidate["skills"]) > 0

    def test_python_skill_extracted(self, candidate):
        skills_lower = [s.lower() for s in candidate["skills"]]
        assert "python" in skills_lower

    def test_experience_years_positive(self, candidate):
        assert candidate["total_experience_years"] >= 0

    def test_education_extracted(self, candidate):
        assert isinstance(candidate["education"], list)

    def test_empty_resume_raises(self):
        with pytest.raises(ValueError):
            ResumeParser("").parse()

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            ResumeParser("   \n\t  ").parse()

    def test_summary_extracted(self, candidate):
        assert candidate["summary"] is not None


# ---------------------------------------------------------------------------
# ResumeMatcher tests
# ---------------------------------------------------------------------------
class TestResumeMatcher:
    def test_overall_score_range(self, match_result):
        assert 0 <= match_result["overall_score"] <= 100

    def test_skill_score_range(self, match_result):
        assert 0 <= match_result["skill_score"] <= 100

    def test_experience_score_range(self, match_result):
        assert 0 <= match_result["experience_score"] <= 100

    def test_education_score_range(self, match_result):
        assert 0 <= match_result["education_score"] <= 100

    def test_matched_skills_subset(self, match_result):
        for s in match_result["matched_skills"]:
            assert s in REQUIRED_SKILLS

    def test_missing_skills_includes_react(self, match_result):
        # react is required but not in the sample resume
        assert "react" in match_result["missing_skills"]

    def test_verdict_is_string(self, match_result):
        assert isinstance(match_result["verdict"], str)
        assert match_result["verdict"] in [
            "Strong Match", "Good Match", "Partial Match", "Poor Match"
        ]

    def test_recommendation_is_string(self, match_result):
        assert isinstance(match_result["recommendation"], str)

    def test_no_required_skills(self, candidate):
        result = ResumeMatcher(candidate=candidate).match()
        assert 0 <= result["overall_score"] <= 100

    def test_all_skills_matched(self, candidate):
        result = ResumeMatcher(
            candidate=candidate,
            required_skills=["python"],
        ).match()
        assert result["skill_score"] == 100.0

    def test_strong_match_threshold(self, candidate):
        result = ResumeMatcher(
            candidate=candidate,
            required_skills=["python", "django", "postgresql"],
        ).match()
        # Python, Django, PostgreSQL are all present → should be strong
        assert result["skill_score"] == 100.0


# ---------------------------------------------------------------------------
# ReportGenerator tests
# ---------------------------------------------------------------------------
class TestReportGenerator:
    def test_text_report_contains_name(self, candidate, match_result):
        reporter = ReportGenerator(candidate, match_result)
        report = reporter.generate_text()
        assert "Anjali Mehta" in report

    def test_text_report_contains_score(self, candidate, match_result):
        reporter = ReportGenerator(candidate, match_result)
        report = reporter.generate_text()
        score = str(int(match_result["overall_score"]))
        assert score in report

    def test_markdown_report_has_headings(self, candidate, match_result):
        reporter = ReportGenerator(candidate, match_result)
        md = reporter.generate_markdown()
        assert "## Match Scores" in md
        assert "## Candidate Profile" in md

    def test_report_save_text(self, candidate, match_result, tmp_path):
        reporter = ReportGenerator(candidate, match_result)
        path = reporter.save(tmp_path / "report", fmt="text")
        assert Path(path).exists()
        assert Path(path).read_text()

    def test_report_save_markdown(self, candidate, match_result, tmp_path):
        reporter = ReportGenerator(candidate, match_result)
        path = reporter.save(tmp_path / "report", fmt="markdown")
        assert Path(path).suffix == ".md"


# ---------------------------------------------------------------------------
# FileHandler tests
# ---------------------------------------------------------------------------
class TestFileHandler:
    def test_save_and_load(self, candidate, match_result, tmp_path):
        path = save_candidate(candidate, match_result, output_dir=tmp_path)
        assert Path(path).exists()
        loaded = load_candidate(path)
        assert loaded["candidate"]["name"] == "Anjali Mehta"

    def test_load_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            load_candidate("nonexistent_path/file.json")

    def test_list_candidates(self, candidate, match_result, tmp_path):
        save_candidate(candidate, match_result, output_dir=tmp_path)
        records = list_candidates(output_dir=tmp_path)
        assert len(records) >= 1
        assert records[0]["name"] == "Anjali Mehta"

    def test_delete_candidate(self, candidate, match_result, tmp_path):
        path = save_candidate(candidate, match_result, output_dir=tmp_path)
        deleted = delete_candidate(path)
        assert deleted is True
        assert not Path(path).exists()

    def test_delete_nonexistent_returns_false(self):
        result = delete_candidate("no_such_file.json")
        assert result is False

    def test_load_invalid_json_raises(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json {{{}}")
        with pytest.raises(ValueError):
            load_candidate(bad_file)
