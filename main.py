"""
main.py  –  Command-line interface for Intelligent Resume Analyzer
Usage:
  python main.py --resume path/to/resume.txt [options]
  python main.py --demo
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.resume_parser import ResumeParser
from src.matcher import ResumeMatcher
from src.report_generator import ReportGenerator
from src.file_handler import save_candidate, list_candidates


# ---------------------------------------------------------------------------
# Demo resumes
# ---------------------------------------------------------------------------
DEMO_RESUME = """\
Name: Priya Sharma
Email: priya.sharma@email.com
Phone: +91-9876543210

Summary:
Full-stack developer with 4 years of experience building scalable
web applications and REST APIs in fast-paced startup environments.

Experience:
- Software Engineer at TechCorp (2021-2025)
  Built REST APIs in Python/Django, React dashboards, PostgreSQL databases.
  Led a team of 3 junior developers.
- Junior Developer at StartupXYZ (2020-2021)
  Developed features using Node.js and Vue.js.

Skills: Python, Django, React, JavaScript, PostgreSQL, Docker,
        Git, REST APIs, Redis, AWS, HTML, CSS

Education:
B.Tech Computer Science, IIT Hyderabad, 2020

Projects:
- Real-time analytics dashboard (Python, React, WebSockets)
- E-commerce platform with payment integration (Django, Stripe)
"""

DEMO_REQUIRED_SKILLS = ["python", "django", "react", "postgresql", "docker", "kubernetes"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Intelligent Resume Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --demo
  python main.py --resume resume.txt --skills python django docker --min-exp 3
  python main.py --resume resume.txt --jd job_description.txt --output report
  python main.py --list
        """,
    )
    p.add_argument("--resume",  help="Path to resume text file")
    p.add_argument("--jd",      help="Path to job description text file")
    p.add_argument("--skills",  nargs="+", help="Required skill list")
    p.add_argument("--min-exp", type=float, default=0, help="Min years experience")
    p.add_argument("--degree",  default="", help="Required degree (e.g. b.tech)")
    p.add_argument("--job",     default="the position", help="Job title")
    p.add_argument("--company", default="", help="Company name")
    p.add_argument("--output",  help="Output file path (without extension)")
    p.add_argument("--format",  choices=["text", "markdown", "json", "all"],
                   default="text", help="Report format")
    p.add_argument("--demo",    action="store_true", help="Run with built-in demo data")
    p.add_argument("--list",    action="store_true", help="List all saved candidates")
    return p


def run(args: argparse.Namespace) -> None:
    # --- List mode ---
    if args.list:
        records = list_candidates()
        if not records:
            print("No saved records found.")
            return
        print(f"\n{'Name':<25} {'Score':>6}  {'Verdict':<18}  Analyzed At")
        print("-" * 75)
        for r in records:
            print(f"{r['name']:<25} {r['overall_score']:>5.1f}  {r['verdict']:<18}  {r['analyzed_at'][:19]}")
        return

    # --- Load resume ---
    if args.demo:
        resume_text = DEMO_RESUME
        required_skills = DEMO_REQUIRED_SKILLS
        print("Running demo analysis…\n")
    else:
        if not args.resume:
            print("Error: provide --resume <path> or use --demo")
            sys.exit(1)
        path = Path(args.resume)
        if not path.exists():
            print(f"Error: file not found → {path}")
            sys.exit(1)
        resume_text = path.read_text(encoding="utf-8")
        required_skills = args.skills or []

    # --- Job description ---
    jd_text = ""
    if hasattr(args, "jd") and args.jd:
        jd_path = Path(args.jd)
        if jd_path.exists():
            jd_text = jd_path.read_text(encoding="utf-8")

    # --- Parse ---
    try:
        parser = ResumeParser(resume_text)
        candidate = parser.parse()
    except ValueError as e:
        print(f"Parsing error: {e}")
        sys.exit(1)

    # --- Match ---
    matcher = ResumeMatcher(
        candidate=candidate,
        required_skills=required_skills,
        job_description=jd_text,
        min_experience_years=args.min_exp,
        required_degree=args.degree,
    )
    match_result = matcher.match()

    # --- Report ---
    reporter = ReportGenerator(
        candidate=candidate,
        match=match_result,
        job_title=args.job,
        company=args.company,
    )

    fmt = args.format
    output_base = args.output or "data/output/report"

    if fmt in ("text", "all"):
        txt = reporter.generate_text()
        print(txt)
        if args.output:
            p = reporter.save(output_base, fmt="text")
            print(f"\nSaved → {p}")

    if fmt in ("markdown", "all"):
        md = reporter.generate_markdown()
        if args.output:
            p = reporter.save(output_base, fmt="markdown")
            print(f"Saved → {p}")
        elif fmt == "markdown":
            print(md)

    if fmt in ("json", "all"):
        payload = {"candidate": candidate, "match_result": match_result}
        json_str = json.dumps(payload, indent=2)
        if args.output:
            out_path = Path(output_base).with_suffix(".json")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json_str, encoding="utf-8")
            print(f"Saved → {out_path}")
        else:
            print(json_str)

    # Always save to the history store
    saved = save_candidate(candidate, match_result)
    print(f"\nRecord saved → {saved}")


def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
