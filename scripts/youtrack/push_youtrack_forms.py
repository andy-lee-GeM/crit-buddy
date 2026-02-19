#!/usr/bin/env python3
"""
Push YouTrack form templates as issues.

Usage:
    python push_youtrack_forms.py                    # Push all forms
    python push_youtrack_forms.py maker-array        # Push specific form
"""

import os
import sys
import requests
import yaml
from pathlib import Path


# Project root (scripts/youtrack/ -> root)
ROOT = Path(__file__).parent.parent.parent


def load_env():
    """Load .env file manually."""
    env_path = ROOT / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value


load_env()

# Load config
config_path = ROOT / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

YOUTRACK_URL = config["youtrack"]["url"]
PROJECT_ID = config["youtrack"]["project_id"]
PROJECT_INTERNAL_ID = config["youtrack"]["project_internal_id"]
YOUTRACK_TOKEN = os.getenv("YOUTRACK_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {YOUTRACK_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def create_issue(summary: str, description: str) -> dict:
    """Create a YouTrack issue."""
    url = f"{YOUTRACK_URL}/api/issues"

    payload = {
        "project": {"id": PROJECT_INTERNAL_ID},
        "summary": summary,
        "description": description,
    }

    response = requests.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def main():
    forms_dir = ROOT / "docs/doc-templates/youtrack-forms"

    all_forms = {
        "parallel-pipes": {
            "file": "parallel-pipes-form.md",
            "summary": "[TEMPLATE] Criticality Analysis Request: Parallel Pipes",
        },
        "shipping-cylinder": {
            "file": "shipping-cylinder-form.md",
            "summary": "[TEMPLATE] Criticality Analysis Request: Shipping Cylinder",
        },
        "maker-array": {
            "file": "maker-array-form.md",
            "summary": "[TEMPLATE] Criticality Analysis Request: Maker Array",
        },
        "cylinder": {
            "file": "cylinder-form.md",
            "summary": "[TEMPLATE] Criticality Analysis Request: Cylinder",
        },
        "rectangular-box": {
            "file": "rectangular-box-form.md",
            "summary": "[TEMPLATE] Criticality Analysis Request: Rectangular Box",
        },
    }

    # Filter forms based on command line argument
    if len(sys.argv) > 1:
        form_name = sys.argv[1]
        if form_name not in all_forms:
            print(f"Unknown form: {form_name}")
            print(f"Available: {', '.join(all_forms.keys())}")
            sys.exit(1)
        forms = [all_forms[form_name]]
    else:
        forms = list(all_forms.values())

    for form in forms:
        form_path = forms_dir / form["file"]
        if not form_path.exists():
            print(f"Form not found: {form_path}")
            continue

        description = form_path.read_text()

        print(f"Creating: {form['summary']}")
        try:
            result = create_issue(form["summary"], description)
            issue_id = result.get("idReadable", result.get("id"))
            print(f"  Created: {issue_id}")
            print(f"  URL: {YOUTRACK_URL}/issue/{issue_id}")
        except requests.HTTPError as e:
            print(f"  Error: {e}")
            print(f"  Response: {e.response.text}")


if __name__ == "__main__":
    main()
