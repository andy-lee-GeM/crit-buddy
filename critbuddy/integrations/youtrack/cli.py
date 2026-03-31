#!/usr/bin/env python3
"""
Canonical CLI for YouTrack operations.

Usage:
    python -m critbuddy.integrations.youtrack.cli fetch-ready
    python -m critbuddy.integrations.youtrack.cli fetch CB-10
"""

import argparse
import json
import sys
from pathlib import Path

from .client import YouTrackClient


def cmd_fetch_ready(args):
    """Fetch all tickets in the configured ready status."""
    client = YouTrackClient()
    tickets = client.get_ready_tickets()

    if args.json:
        print(json.dumps(tickets, indent=2))
    else:
        if not tickets:
            print(f"No tickets in {client.status_field}='{client.ready_status}'")
            return

        print(
            f"Found {len(tickets)} ticket(s) in "
            f"{client.status_field}='{client.ready_status}':\n"
        )
        for t in tickets:
            ticket_id = t.get("idReadable", t.get("id"))
            summary = t.get("summary", "No summary")
            print(f"  {ticket_id}: {summary}")


def cmd_fetch(args):
    """Fetch single ticket by ID."""
    client = YouTrackClient()
    ticket = client.get_ticket(args.ticket_id)

    if args.json:
        print(json.dumps(ticket, indent=2))
    else:
        ticket_id = ticket.get("idReadable", ticket.get("id"))
        summary = ticket.get("summary", "No summary")
        description = ticket.get("description", "No description")

        print(f"Ticket: {ticket_id}")
        print(f"Summary: {summary}")
        print(f"\nDescription:\n{description}")


def cmd_push_results(args):
    """Push results to a ticket."""
    client = YouTrackClient()
    client.push_results(
        args.ticket_id,
        Path(args.results_dir),
        report_filename=args.report or "REPORT.md",
        csv_filename=args.csv or "all_results.csv",
    )
    print(f"\nResults pushed to {args.ticket_id}")


def cmd_create_form(args):
    """Create a template issue from a form."""
    client = YouTrackClient()
    result = client.create_template_issue(args.form_name)
    issue_id = result.get("idReadable", result.get("id"))
    print(f"Created: {issue_id}")
    print(f"URL: {client.url}/issue/{issue_id}")


def cmd_sync_form(args):
    """Sync a local form onto an existing template issue."""
    client = YouTrackClient()
    result = client.sync_form_to_issue(args.ticket_id, args.form_name)
    issue_id = result.get("idReadable", args.ticket_id)
    print(f"Synced: {issue_id}")
    print(f"URL: {client.url}/issue/{issue_id}")


def cmd_list_forms(args):
    """List available form templates."""
    client = YouTrackClient()
    forms = client.get_available_forms()
    if forms:
        print("Available forms:")
        for form in forms:
            print(f"  - {form}")
    else:
        print("No form templates found")


def cmd_update_status(args):
    """Update ticket status."""
    client = YouTrackClient()
    client.update_status(args.ticket_id, args.status)
    print(f"{args.ticket_id} -> {args.status}")


def cmd_mark_complete(args):
    """Mark ticket as complete."""
    client = YouTrackClient()
    client.mark_complete(args.ticket_id)
    print(f"{args.ticket_id} -> Complete")


def cmd_mark_failed(args):
    """Mark ticket as failed with error message."""
    client = YouTrackClient()
    client.mark_failed(args.ticket_id, args.error_message)
    print(f"{args.ticket_id} -> Failed")


def cmd_comment(args):
    """Add comment to ticket."""
    client = YouTrackClient()
    client.add_comment(args.ticket_id, args.text)
    print(f"Comment added to {args.ticket_id}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="youtrack_cli",
        description="Unified CLI for YouTrack operations",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p = subparsers.add_parser(
        "fetch-ready", help="Fetch all tickets in configured ready status"
    )
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_fetch_ready)

    p = subparsers.add_parser("fetch", help="Fetch single ticket by ID")
    p.add_argument("ticket_id", help="Ticket ID (e.g., CB-10)")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.set_defaults(func=cmd_fetch)

    p = subparsers.add_parser("push-results", help="Push results to ticket")
    p.add_argument("ticket_id", help="Ticket ID (e.g., CB-10)")
    p.add_argument("results_dir", help="Path to results directory")
    p.add_argument("--report", help="Report filename (default: REPORT.md)")
    p.add_argument("--csv", help="CSV filename (default: all_results.csv)")
    p.set_defaults(func=cmd_push_results)

    p = subparsers.add_parser(
        "create-form", help="Create template issue from a local form"
    )
    p.add_argument("form_name", help="Form name (e.g., pipe, cylinder)")
    p.set_defaults(func=cmd_create_form)

    p = subparsers.add_parser(
        "sync-form", help="Sync a local form to an existing issue"
    )
    p.add_argument("ticket_id", help="Ticket ID (e.g., CB-10)")
    p.add_argument(
        "form_name",
        help="Form name (e.g., centrifuge-unit-cell, pipe-cross-model)",
    )
    p.set_defaults(func=cmd_sync_form)

    p = subparsers.add_parser("list-forms", help="List available form templates")
    p.set_defaults(func=cmd_list_forms)

    p = subparsers.add_parser("update-status", help="Update ticket status")
    p.add_argument("ticket_id", help="Ticket ID (e.g., CB-10)")
    p.add_argument("status", help="New status (e.g., 'In Progress')")
    p.set_defaults(func=cmd_update_status)

    p = subparsers.add_parser("mark-complete", help="Mark ticket as complete")
    p.add_argument("ticket_id", help="Ticket ID (e.g., CB-10)")
    p.set_defaults(func=cmd_mark_complete)

    p = subparsers.add_parser("mark-failed", help="Mark ticket as failed")
    p.add_argument("ticket_id", help="Ticket ID (e.g., CB-10)")
    p.add_argument("error_message", help="Error message to post")
    p.set_defaults(func=cmd_mark_failed)

    p = subparsers.add_parser("comment", help="Add comment to ticket")
    p.add_argument("ticket_id", help="Ticket ID (e.g., CB-10)")
    p.add_argument("text", help="Comment text")
    p.set_defaults(func=cmd_comment)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
