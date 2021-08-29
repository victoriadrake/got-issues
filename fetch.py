import argparse
import json
import logging
import sys
from datetime import datetime
from typing import Dict, List
from urllib import request, error

import pytz
from dateutil import parser
from dateutil.relativedelta import relativedelta

logging.getLogger(__name__).addHandler(logging.NullHandler())


def last_date(bug_issues) -> datetime:
    """Check the date of the last issue we got"""
    try:
        last_item = bug_issues[-1]
    except (IndexError, TypeError):
        logging.error("I don't seem to have any data.")
        # No last item, thus no data; nothing else to do, so exit non-zero
        sys.exit(1)
    return parser.parse(last_item["created_at"])


def parse_item(item) -> Dict:
    """Parse relevant data from an issue item"""
    # TODO: Incorporate flags to control the output data
    issue = {
        # Build the shape of your output data here
        # You might set some defaults for missing values if you don't want nulls
        "url": item["html_url"],
        "title": item["title"],
        "body": item["body"],
        "author": item["user"]["login"],
        "created_at": item["created_at"],
        "closed_at": item["closed_at"],
        "updated_at": item["updated_at"],
    }
    issue["labels"] = []
    for label in item["labels"]:
        issue["labels"].append(label["name"])
    return issue


def fetch_page(p, parg) -> List:
    """Get data from bug issues"""
    args = parg.parse_args()
    if not args.repository or not args.months:
        logging.error("Missing arguments.")
        sys.exit(1)
    bugs = []
    # Get a page via API
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    # Tokens are only necessary for private repositories
    if args.token:
        headers["Authorization"] = f"token {args.token}"
    r = request.Request(
        url=f"https://api.github.com/repos/{args.repository}/issues?page={p}&state=all",
        headers=headers,
    )
    try:
        http_response = request.urlopen(r)
        data = http_response.read().decode(encoding="utf-8", errors="ignore")
        # Go through this page of data and parse the issues
        # Add any filtering criteria here
        for issue in json.loads(data):
            bugs.append(parse_item(issue))
    except error.HTTPError as e:
        logging.error(f"Could not fetch issues: {e.reason} ({e.code})")
    except Exception:
        logging.exception("Could not fetch issues.")
    return bugs


def main():
    """Fetch issues until the target date"""
    parg = argparse.ArgumentParser(
        description="Fetch data for issues from a GitHub repository for a number of past months.",
        epilog="Data will be JSON to stdout, so you may like to redirect this to a file.",
    )
    parg.add_argument(
        "repository",
        help="The GitHub repository to fetch issues from in the form: owner/repository-name",
    )
    parg.add_argument(
        "months",
        metavar="months",
        type=int,
        help="Number of past months to fetch issues for, e.g. 24 for the last two years.",
    )
    parg.add_argument(
        "--token", "-t", help="Personal Access Token string for private repositories."
    )
    args = parg.parse_args()
    months_past = args.months

    # Get the first page of issues
    page = 1
    bug_issues = fetch_page(page, parg)
    # Check if the last issue we got is sufficiently old
    fetch_until = datetime.now().replace(tzinfo=pytz.UTC) - relativedelta(
        months=months_past
    )
    while last_date(bug_issues) > fetch_until:
        # Get more issues if it's not old enough
        page += 1
        bug_issues += fetch_page(page, parg)

    # The last issue we got is older than the target date, we're finished
    return print(json.dumps(bug_issues))


if __name__ == "__main__":
    main()
