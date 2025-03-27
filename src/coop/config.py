"""Configuration for the Food Co-op price scraper."""

from pathlib import Path

# Base URLs and endpoints
PRODUCE_URL = "https://www.foodcoop.com/produce/"

# Request configuration
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 1  # seconds

# File paths
PACKAGE_ROOT = Path(__file__).parent
TEMPLATE_DIR = PACKAGE_ROOT / "templates"
TEMPLATE_FILE = TEMPLATE_DIR / "produce_list_template.html"
OUTPUT_FILE = "index.html"

# Local produce indicators
LOCAL_INDICATORS = [
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
