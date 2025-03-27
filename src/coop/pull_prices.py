from __future__ import annotations

import datetime
import re
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag
from IPython import embed


def clean_price(price_str: str) -> float | None:
    match = re.search(r"\d+\.?\d*", price_str)
    return float(match.group()) if match else None


def is_local(origin: str) -> bool:
    local_indicators: list[str] = [
        "500 miles",
        "NY",
        "New York",
        "VT",
        "Vermont",
        "MA",
        "Massachusetts",
        "PA",
        "Pennsylvania",
        "NJ",
        "New Jersey",
        "CT",
        "Connecticut",
        "Company",
        "NC",
        "North Carolina",
    ]
    return any(indicator in origin for indicator in local_indicators)


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


def scrape_produce_prices() -> list[dict[str, Any]]:
    url: str = "https://www.foodcoop.com/produce/"
    response: requests.Response = requests.get(url)

    soup = BeautifulSoup(response.text, "lxml")
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

    # Get the template path
    template_path = Path(__file__).parent / "templates" / "produce_list_template.html"
    with open(template_path) as f:
        template = f.read()

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
    data = scrape_produce_prices()
    if args.debug:
        embed()
    html_content = generate_html(data)
    # Write the HTML content to a file
    fname: str = "index.html"
    with open(fname, "w") as f:
        f.write(html_content)

    print(f"HTML file '{fname}' has been generated.")


if __name__ == "__main__":
    main()
