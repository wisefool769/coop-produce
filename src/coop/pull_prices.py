from __future__ import annotations

import datetime
import re
import time
from argparse import ArgumentParser
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag
from IPython import embed
from requests.exceptions import RequestException

from coop.config import (
    LOCAL_INDICATORS,
    MAX_RETRIES,
    OUTPUT_FILE,
    PRODUCE_URL,
    REQUEST_TIMEOUT,
    RETRY_BACKOFF,
    TEMPLATE_FILE,
)


def clean_price(price_str: str) -> float | None:
    match = re.search(r"\d+\.?\d*", price_str)
    return float(match.group()) if match else None


def is_local(origin: str) -> bool:
    return any(indicator in origin for indicator in LOCAL_INDICATORS)


def to_snake_case(name: str) -> str:
    name = str(name)  # Ensure we're working with a string
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()
    return re.sub(r"\W+", "_", name).strip("_")


def extract_item(raw_name: str) -> str:
    # Extract the item name (everything before the first hyphen or dollar sign)
    item = re.split(r"[-$]", raw_name)[0].strip()
    # Remove any trailing words like "organic", "label", etc.
    item = re.sub(
        r"\s+(organic|label|ipm|conventional|bunch|loose)\s*$",
        "",
        item,
        flags=re.IGNORECASE,
    )
    return item.strip()


def fetch_produce_page() -> str:
    """Fetch the produce page with retries and error handling."""
    session = requests.Session()
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(PRODUCE_URL, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except RequestException as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:  # Don't sleep on the last attempt
                time.sleep(RETRY_BACKOFF * (attempt + 1))

    raise RuntimeError(f"Failed to fetch produce page after {MAX_RETRIES} attempts") from last_error


def scrape_produce_prices() -> list[dict[str, Any]]:
    try:
        html_content = fetch_produce_page()
    except Exception as e:
        raise RuntimeError("Failed to fetch produce prices") from e

    soup = BeautifulSoup(html_content, "lxml")
    table = soup.find("table")

    if not table or not isinstance(table, Tag):
        raise ValueError("No tables found on the page. The website structure might have changed.")

    # Extract headers
    headers = []
    for th in table.find_all("th"):
        header = to_snake_case(th.text.strip())
        headers.append(header)

    # Extract rows
    rows = []
    for tr in table.find_all("tr")[1:]:  # Skip header row
        if isinstance(tr, Tag):
            row = []
            for td in tr.find_all("td"):
                row.append(td.text.strip())
            if len(row) == len(headers):
                # Create a dictionary for each row
                row_dict = dict(zip(headers, row, strict=True))
                # Clean up the data
                row_dict["price"] = clean_price(row_dict.get("price", ""))
                if row_dict["price"] is not None:  # Only include rows with valid prices
                    row_dict["is_organic"] = row_dict.get("organic", "").strip()
                    row_dict["raw"] = row_dict.pop("name", "").strip()
                    row_dict["is_local"] = is_local(row_dict.get("origin", ""))
                    row_dict["item"] = extract_item(row_dict["raw"])
                    rows.append(row_dict)

    if not rows:
        raise ValueError("No valid produce items found. The page format might have changed.")

    # Sort by price
    return sorted(rows, key=lambda x: x["price"])


def create_html_table(data: list[dict[str, Any]]) -> str:
    if not data:
        return "<p>No items found.</p>"

    html = ['<table class="data-table">']
    # Add headers
    html.append("<tr>")
    for header in ["raw", "price", "origin"]:
        html.append(f"<th>{header}</th>")
    html.append("</tr>")

    # Add rows
    for row in data:
        html.append("<tr>")
        for key in ["raw", "price", "origin"]:
            html.append(f"<td>{row[key]}</td>")
        html.append("</tr>")

    html.append("</table>")
    return "\n".join(html)


def generate_html(data: list[dict[str, Any]]) -> str:
    # Split the data into local and non-local
    local_data = [item for item in data if item["is_local"]]
    non_local_data = [item for item in data if not item["is_local"]]

    try:
        with open(TEMPLATE_FILE) as f:
            template = f.read()
    except OSError as e:
        raise RuntimeError(f"Failed to read template file: {e}") from e

    # Format the template with our data
    return template.format(
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        local_table=create_html_table(local_data),
        non_local_table=create_html_table(non_local_data),
    )


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()

    try:
        data = scrape_produce_prices()
        if args.debug:
            embed()
        html_content = generate_html(data)

        # Write the HTML content to a file
        try:
            with open(OUTPUT_FILE, "w") as f:
                f.write(html_content)
        except OSError as e:
            raise RuntimeError(f"Failed to write output file {OUTPUT_FILE}: {e}") from e

        print(f"HTML file '{OUTPUT_FILE}' has been generated.")
    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            raise
        exit(1)


if __name__ == "__main__":
    main()
