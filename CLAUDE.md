# COOP Produce Price Tracker - Development Guide

## Commands

- **Run price scraper (CSV output)**: `python download_prices.py`
- **Run price scraper (HTML output)**: `python pull_prices.py`
- **Deploy to website**: Copy `produce_price_list.html` to `deploy/index.html`

## Code Style Guidelines

- **Naming**: Use snake_case for variables, functions, and file names
- **Imports**: Group imports by standard library → third-party → local modules
- **Functions**: Single responsibility, descriptive names, docstrings for complex functions
- **Error handling**: Use try/except for web requests and file operations
- **Types**: Use type hints for function parameters and return values
- **Formatting**: 4-space indentation, 100 character line limit
- **Libraries**: Use pandas for data processing, requests for web requests, BeautifulSoup/lxml for HTML parsing

## Project Structure

- **download_prices.py**: Scrapes prices, saves to CSV, opens interactive IPython shell
- **pull_prices.py**: Scrapes prices, generates HTML report
- **produce_price_list.csv**: Generated data file
- **deploy/index.html**: Web display of price data

This food co-op price tracker scrapes produce pricing from the food co-op website, processes the data, and generates reports in CSV or HTML format.