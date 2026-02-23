"""
One-time project scaffold script.

Creates the directory structure and starter files for the
Movie NLP Success Analyzer project. Run once when bootstrapping
a fresh clone, then use the generated structure directly.

Usage:
    python project_setup.py
"""

from pathlib import Path

PROJECT_NAME = "movie-nlp-success-analyzer"

DIRECTORIES = [
    "data/raw/tmdb_metadata",
    "data/raw/subtitles",
    "data/raw/awards",
    "data/raw/oscars",
    "data/processed",
    "data/external",
    "notebooks",
    "src/data",
    "src/features",
    "src/models",
    "src/visualization",
    "models",
    "reports/figures",
]

STARTER_FILES = {
    ".env": (
        "# API keys — never commit this file\n"
        "TMDB_API_KEY=\n"
        "OPENSUBTITLES_API_KEY=\n"
        "OPENSUBTITLES_USER=\n"
        "OPENSUBTITLES_PASS=\n"
    ),
    "src/__init__.py": "",
}


def create_project_structure():
    base = Path.cwd() / PROJECT_NAME
    base.mkdir(exist_ok=True)
    print(f"Project root: {base}")

    for d in DIRECTORIES:
        path = base / d
        path.mkdir(parents=True, exist_ok=True)
        if "src" in str(d):
            (path / "__init__.py").touch()

    for filename, content in STARTER_FILES.items():
        filepath = base / filename
        if not filepath.exists():
            filepath.write_text(content, encoding="utf-8")

    print("Directory structure created.")
    print("Starter files written (.env, src/__init__.py).")
    print(f"\nNext steps:")
    print(f"  1. cd {PROJECT_NAME}")
    print(f"  2. python -m venv venv && source venv/bin/activate")
    print(f"  3. pip install -r requirements.txt")
    print(f"  4. Add your API keys to .env")


if __name__ == "__main__":
    create_project_structure()
