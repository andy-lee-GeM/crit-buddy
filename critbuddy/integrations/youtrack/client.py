"""
Unified YouTrack client for crit-buddy.

Consolidates all YouTrack API operations: fetching tickets, updating status,
posting comments, attaching files, and creating template issues.

Usage:
    from critbuddy.integrations.youtrack import YouTrackClient

    client = YouTrackClient()

    # Fetch tickets
    tickets = client.get_ready_tickets()
    ticket = client.get_ticket("CB-10")

    # Update ticket
    client.mark_in_progress("CB-10")
    client.add_comment("CB-10", "Analysis started")
    client.attach_file("CB-10", Path("results/REPORT.md"))
    client.mark_complete("CB-10")
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

import requests
import yaml


class YouTrackClient:
    """Unified YouTrack API client for crit-buddy."""

    # Single source of truth for YouTrack form templates.
    FORM_TEMPLATES = {
        "centrifuge-unit-cell": {
            "file": "centrifuge-unit-cell-form.md",
            "summary": "[TEMPLATE] Criticality Analysis Request: Centrifuge Unit Cell",
            "assets": ["centrifuge-unit-cell-geometry.png"],
        },
        "pipe-cross-model": {
            "file": "pipe-cross-model-form.md",
            "summary": "[TEMPLATE] Criticality Analysis Request: Pipe Cross Model",
        },
        "cylinder-array": {
            "file": "cylinder-array-form.md",
            "summary": "[TEMPLATE] Criticality Analysis Request: Cylinder Array",
        },
    }
    FORM_ALIASES = {
        "centrifuge": "centrifuge-unit-cell",
        "pipe-cross": "pipe-cross-model",
        "cylinder": "cylinder-array",
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize client with config from config.yaml and YOUTRACK_TOKEN env var.

        Args:
            config_path: Path to config.yaml (default: project root/config.yaml)
        """
        # Find project root
        self.root = Path(__file__).parent.parent.parent.parent

        # Load .env file if exists
        self._load_env()

        # Load config
        if config_path is None:
            config_path = self.root / "config.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path) as f:
            config = yaml.safe_load(f)

        youtrack_config = config.get("youtrack", {})
        self.url = youtrack_config.get("url")
        self.project_id = youtrack_config.get("project_id")
        self.project_internal_id = youtrack_config.get("project_internal_id")
        self.status_field = youtrack_config.get("status_field", "Stage")
        self.ready_status = youtrack_config.get("ready_status", "Ready for run")

        if not self.url:
            raise ValueError("youtrack.url not configured in config.yaml")

        # Get token from environment
        self.token = os.getenv("YOUTRACK_TOKEN")
        if not self.token:
            raise ValueError("YOUTRACK_TOKEN environment variable not set")

        # Standard headers for JSON requests
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Forms directory for templates
        self.forms_dir = self.root / "docs" / "doc-templates" / "youtrack-forms"
        self.form_assets_dir = self.forms_dir / "assets"

    def _load_env(self) -> None:
        """Load .env file manually (no external dependencies)."""
        env_path = self.root / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value

    def _get(self, endpoint: str) -> dict:
        """Make GET request to YouTrack API."""
        response = requests.get(f"{self.url}{endpoint}", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint: str, payload: dict) -> dict:
        """Make POST request to YouTrack API."""
        response = requests.post(
            f"{self.url}{endpoint}", json=payload, headers=self.headers
        )
        response.raise_for_status()
        return response.json() if response.content else {}

    def _post_multipart(self, endpoint: str, files: dict) -> dict:
        """Make multipart POST request for file uploads."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }
        response = requests.post(f"{self.url}{endpoint}", files=files, headers=headers)
        response.raise_for_status()
        return response.json() if response.content else {}

    # =========================================================================
    # READ OPERATIONS
    # =========================================================================

    def get_ready_tickets(self) -> List[dict]:
        """
        Fetch all tickets in configured ready status.

        Returns:
            List of ticket dicts with id, summary, and description
        """
        query = f"project:{self.project_id} {self.status_field}:{{{self.ready_status}}}"
        encoded_query = quote(query)
        return self._get(
            f"/api/issues?query={encoded_query}&fields=idReadable,summary,description"
        )

    def get_tickets_by_status(self, status: str) -> List[dict]:
        """
        Fetch all tickets with given status.

        Args:
            status: Status value (e.g., "Ready", "In Progress", "Complete")

        Returns:
            List of ticket dicts
        """
        query = f"project:{self.project_id} {self.status_field}:{{{status}}}"
        encoded_query = quote(query)
        return self._get(
            f"/api/issues?query={encoded_query}&fields=idReadable,summary,description"
        )

    def get_ticket(self, ticket_id: str) -> dict:
        """
        Fetch single ticket by ID.

        Args:
            ticket_id: Ticket ID (e.g., "CB-10")

        Returns:
            Ticket dict with full details including description and custom fields
        """
        return self._get(
            f"/api/issues/{ticket_id}?fields=idReadable,summary,description,customFields(name,value(name))"
        )

    def get_ticket_attachments(self, ticket_id: str) -> List[dict]:
        """Get list of attachments on a ticket."""
        return self._get(f"/api/issues/{ticket_id}/attachments?fields=name")

    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================

    def update_status(self, ticket_id: str, new_status: str) -> dict:
        """
        Change ticket status.

        Args:
            ticket_id: Ticket ID (e.g., "CB-10")
            new_status: New status value (e.g., "In Progress")

        Returns:
            API response
        """
        # Use /api/commands endpoint with issues array (YouTrack 2020.1+)
        return self._post(
            "/api/commands",
            {
                "query": f"{self.status_field} {{{new_status}}}",
                "issues": [{"idReadable": ticket_id}],
            },
        )

    def add_comment(self, ticket_id: str, text: str) -> dict:
        """
        Post markdown comment to ticket.

        Args:
            ticket_id: Ticket ID
            text: Comment text (markdown supported)

        Returns:
            API response with comment details
        """
        return self._post(f"/api/issues/{ticket_id}/comments", {"text": text})

    def attach_file(self, ticket_id: str, file_path: Path) -> dict:
        """
        Upload file attachment to ticket.

        Args:
            ticket_id: Ticket ID
            file_path: Path to file to attach

        Returns:
            API response with attachment details
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f)}
            return self._post_multipart(
                f"/api/issues/{ticket_id}/attachments", files
            )

    def create_issue(self, summary: str, description: str) -> dict:
        """
        Create a new issue in the project.

        Args:
            summary: Issue title
            description: Issue description (markdown)

        Returns:
            API response with new issue details
        """
        return self._post(
            "/api/issues",
            {
                "project": {"id": self.project_internal_id},
                "summary": summary,
                "description": description,
            },
        )

    def update_issue(
        self,
        ticket_id: str,
        *,
        summary: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        """
        Update summary and/or description for an existing issue.

        Args:
            ticket_id: Ticket ID (e.g., "CB-10")
            summary: New issue title
            description: New issue description

        Returns:
            API response with updated issue details
        """
        payload = {}
        if summary is not None:
            payload["summary"] = summary
        if description is not None:
            payload["description"] = description
        if not payload:
            raise ValueError("update_issue requires summary and/or description")
        return self._post(f"/api/issues/{ticket_id}", payload)

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    def mark_in_progress(self, ticket_id: str) -> dict:
        """Move ticket to 'In Progress' state."""
        return self.update_status(ticket_id, "In Progress")

    def mark_complete(self, ticket_id: str) -> dict:
        """Move ticket to 'Complete' state."""
        return self.update_status(ticket_id, "Complete")

    def mark_failed(self, ticket_id: str, error_message: str) -> dict:
        """
        Move ticket to 'Failed' state with error comment.

        Args:
            ticket_id: Ticket ID
            error_message: Error description to post as comment

        Returns:
            API response
        """
        self.add_comment(ticket_id, f"## Analysis Failed\n\n{error_message}")
        return self.update_status(ticket_id, "Failed")

    # =========================================================================
    # RESULTS PUBLISHING
    # =========================================================================

    def push_results(
        self,
        ticket_id: str,
        results_dir: Path,
        report_filename: str = "REPORT.md",
        csv_filename: str = "all_results.csv",
    ) -> None:
        """
        Push analysis results to a YouTrack ticket.

        Attaches CSV, plots, and posts report as comment.

        Args:
            ticket_id: Ticket ID (e.g., "CB-10")
            results_dir: Path to results directory
            report_filename: Name of report file (default: REPORT.md)
            csv_filename: Name of CSV file (default: all_results.csv)
        """
        results_dir = Path(results_dir)
        if not results_dir.exists():
            raise FileNotFoundError(f"Results directory not found: {results_dir}")

        report_path = results_dir / report_filename
        csv_path = results_dir / csv_filename
        plots_dir = results_dir / "plots"

        if not report_path.exists():
            raise FileNotFoundError(f"{report_filename} not found in {results_dir}")

        print(f"Pushing results to {ticket_id}...")
        print(f"  YouTrack URL: {self.url}")

        # 1. Attach files first
        attached_files = []

        if csv_path.exists():
            print(f"  Attaching {csv_path.name}...")
            try:
                self.attach_file(ticket_id, csv_path)
                attached_files.append(csv_path.name)
            except requests.HTTPError as e:
                print(f"  Error attaching CSV: {e}")

        if plots_dir.exists():
            for plot_path in sorted(plots_dir.glob("*.png")):
                print(f"  Attaching {plot_path.name}...")
                try:
                    self.attach_file(ticket_id, plot_path)
                    attached_files.append(plot_path.name)
                except requests.HTTPError as e:
                    print(f"  Error attaching {plot_path.name}: {e}")

        # 2. Post report as comment (fix image paths to reference attachments)
        report_content = report_path.read_text()
        # Convert plots/foo.png -> foo.png for attachment references
        report_content = re.sub(
            r"!\[([^\]]*)\]\(plots/([^)]+)\)", r"![\1](\2)", report_content
        )

        comment_text = f"""## Analysis Complete

Results have been attached to this ticket.

{report_content}

---
*Uploaded by Crit-Buddy*
"""

        print("  Adding comment...")
        try:
            self.add_comment(ticket_id, comment_text)
            print("  Comment added successfully")
        except requests.HTTPError as e:
            print(f"  Error adding comment: {e}")
            raise

        print(f"\nDone! View at: {self.url}/issue/{ticket_id}")

    # =========================================================================
    # FORM TEMPLATES
    # =========================================================================

    def _resolve_form(self, form_name: str) -> tuple[str, dict]:
        """Resolve a form name through aliases and return canonical metadata."""
        resolved = self.FORM_ALIASES.get(form_name, form_name)
        if resolved not in self.FORM_TEMPLATES:
            available = ", ".join(sorted(self.FORM_TEMPLATES.keys()))
            raise ValueError(f"Unknown form: {form_name}. Available: {available}")
        return resolved, self.FORM_TEMPLATES[resolved]

    def _load_form(self, form_name: str) -> tuple[str, str]:
        """Load a local form template and return its summary and description."""
        _, form_info = self._resolve_form(form_name)
        form_path = self.forms_dir / form_info["file"]

        if not form_path.exists():
            available = ", ".join(self.get_available_forms())
            raise FileNotFoundError(
                f"Form template not found for '{form_name}': {form_path}. "
                f"Available forms: {available or 'none'}"
            )

        return form_info["summary"], form_path.read_text()

    def _load_form_assets(self, form_name: str) -> List[Path]:
        """Load any local asset files associated with a form."""
        _, form_info = self._resolve_form(form_name)
        asset_names = form_info.get("assets", [])
        assets: List[Path] = []

        for asset_name in asset_names:
            asset_path = self.form_assets_dir / asset_name
            if not asset_path.exists():
                raise FileNotFoundError(
                    f"Form asset not found for '{form_name}': {asset_path}"
                )
            assets.append(asset_path)

        return assets

    def _prepare_form_description(self, description: str, assets: List[Path]) -> str:
        """Rewrite repo-local asset paths to YouTrack attachment references."""
        prepared = description
        for asset in assets:
            prepared = prepared.replace(
                f"(assets/{asset.name})", f"({asset.name})"
            ).replace(f"(./assets/{asset.name})", f"({asset.name})")
        return prepared

    def _attach_missing_files(self, ticket_id: str, files: List[Path]) -> None:
        """Attach local files that are not already present on the ticket."""
        if not files:
            return

        existing_names = {
            attachment.get("name")
            for attachment in self.get_ticket_attachments(ticket_id)
            if attachment.get("name")
        }

        for file_path in files:
            if file_path.name not in existing_names:
                self.attach_file(ticket_id, file_path)

    def get_available_forms(self) -> List[str]:
        """Get list of available form template names."""
        if not self.forms_dir.exists():
            return []
        available = []
        for form_name, meta in self.FORM_TEMPLATES.items():
            if (self.forms_dir / meta["file"]).exists():
                available.append(form_name)
        return sorted(available)

    def create_template_issue(self, form_name: str) -> dict:
        """
        Create a template issue from a form file.

        Args:
            form_name: Form name (e.g., "pipe", "cylinder", "shipping-cylinder")

        Returns:
            API response with new issue details
        """
        summary, description = self._load_form(form_name)
        assets = self._load_form_assets(form_name)
        prepared_description = self._prepare_form_description(description, assets)
        result = self.create_issue(summary, prepared_description)
        issue_id = result.get("idReadable", result.get("id"))
        if issue_id:
            self._attach_missing_files(issue_id, assets)
        return result

    def sync_form_to_issue(self, ticket_id: str, form_name: str) -> dict:
        """
        Overwrite an existing issue summary/description from a local form file.

        Args:
            ticket_id: Ticket ID to update
            form_name: Form name (e.g., "centrifuge-unit-cell")

        Returns:
            API response with updated issue details
        """
        summary, description = self._load_form(form_name)
        assets = self._load_form_assets(form_name)
        prepared_description = self._prepare_form_description(description, assets)
        self._attach_missing_files(ticket_id, assets)
        return self.update_issue(
            ticket_id,
            summary=summary,
            description=prepared_description,
        )
