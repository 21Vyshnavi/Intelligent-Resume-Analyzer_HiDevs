# 📄 Intelligent Resume Analyzer

A Python application that automates resume screening by parsing resumes, matching candidates to job requirements, and generating detailed analysis reports.

## Features

- **Resume Parsing** — extracts name, email, phone, skills, work experience, education
- **Skill Matching** — compares candidate skills against required skills with fuzzy matching
- **Match Scoring** — calculates skill (50%), experience (30%), and education (20%) scores
- **Verdicts** — Strong Match / Good Match / Partial Match / Poor Match
- **Report Generation** — plain-text, Markdown, and JSON reports
- **JSON Persistence** — saves and loads all analyses to `data/output/`
- **Streamlit UI** — interactive web app with sample resumes, history, and candidate comparison
- **CLI** — run analyses directly from the terminal

## Project Structure

```
intelligent-resume-analyzer/
├── src/
│   ├── __init__.py
│   ├── resume_parser.py      # Extracts candidate info from raw text
│   ├── matcher.py            # Calculates match scores
│   ├── report_generator.py   # Generates text / Markdown reports
│   └── file_handler.py       # JSON save / load / list / delete
├── tests/
│   └── test_resume_analyzer.py   # 20+ unit tests (pytest)
├── data/
│   ├── sample_resumes/       # Sample .txt resumes to test with
│   └── output/               # Saved JSON analyses (auto-created)
├── app.py                    # Streamlit web app
├── main.py                   # CLI entry point
├── requirements.txt
└── README.md
```

## Installation

```bash
git clone https://github.com/<your-username>/Intelligent-Resume-Analyzer_HiDevs.git
cd Intelligent-Resume-Analyzer_HiDevs
pip install -r requirements.txt
```

## Usage

### Option 1 – Streamlit Web App (recommended)

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### Option 2 – Command Line

```bash
# Run the built-in demo
python main.py --demo

# Analyze a resume file
python main.py --resume data/sample_resumes/priya_sharma.txt \
               --skills python django docker react \
               --min-exp 3 \
               --job "Senior Python Developer" \
               --company "TechCorp"

# Save report in all formats
python main.py --resume data/sample_resumes/priya_sharma.txt \
               --format all \
               --output data/output/priya_report

# List all saved candidates
python main.py --list
```

### Option 3 – Python API

```python
from src.resume_parser import ResumeParser
from src.matcher import ResumeMatcher
from src.report_generator import ReportGenerator
from src.file_handler import save_candidate

# 1. Parse
text = open("data/sample_resumes/priya_sharma.txt").read()
parser = ResumeParser(text)
candidate = parser.parse()

# 2. Match
matcher = ResumeMatcher(
    candidate=candidate,
    required_skills=["python", "django", "react", "docker"],
    min_experience_years=2,
)
result = matcher.match()

print(f"Score: {result['overall_score']} | {result['verdict']}")

# 3. Report
reporter = ReportGenerator(candidate, result, job_title="Backend Developer")
print(reporter.generate_text())

# 4. Save
path = save_candidate(candidate, result)
print(f"Saved to {path}")
```

## Scoring Algorithm

| Component | Weight | How it's calculated |
|---|---|---|
| Skill Match | 50% | `matched_skills / required_skills × 100` |
| Experience | 30% | Linear scale vs minimum; bonus for exceeding |
| Education | 20% | Degree tier value (PhD=100, B.Tech=70, …) |

**Overall = Skill×0.5 + Experience×0.3 + Education×0.2**

| Score Range | Verdict |
|---|---|
| 76 – 100 | Strong Match |
| 60 – 75 | Good Match |
| 40 – 59 | Partial Match |
| 0 – 39 | Poor Match |

## Running Tests

```bash
pytest tests/ -v
```

Expected output: 20+ passing tests covering parser, matcher, report generator, and file handler.

## Tech Stack

- **Language:** Python 3.10+
- **UI:** Streamlit
- **Storage:** JSON files
- **Testing:** pytest
- **No external AI/ML APIs required** — fully rule-based, works offline

## Skills Extracted

The parser recognises 80+ skills across:
- **Languages:** Python, Java, JavaScript, TypeScript, Go, Rust, …
- **Web:** React, Angular, Vue, Django, Flask, FastAPI, Node.js, …
- **Data / ML:** TensorFlow, PyTorch, scikit-learn, Pandas, NLP, …
- **Databases:** PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, …
- **DevOps / Cloud:** AWS, Docker, Kubernetes, Terraform, Jenkins, …

## License

MIT License — free to use and modify.
