from typing import Optional, List
import datetime
from io import StringIO
import requests
import pandas as pd
import re
from IPython import embed
from argparse import ArgumentParser

def clean_price(price_str: str) -> Optional[float]:
    match = re.search(r'\d+\.?\d*', price_str)
    return float(match.group()) if match else None

def is_local(origin: str) -> bool:
    local_indicators: List[str] = ['500 miles', 'NY', 'New York', 'VT', 'Vermont', 'MA', 'Massachusetts', 
                        'PA', 'Pennsylvania', 'NJ', 'New Jersey', 'CT', 'Connecticut',
                        'Company', 'NC', 'North Carolina']
    return any(indicator in origin for indicator in local_indicators)

def to_snake_case(name: str) -> str:
    name = str(name)  # Ensure we're working with a string
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    return re.sub(r'\W+', '_', name).strip('_')

def extract_item(raw_name: str) -> str:
    # Extract the item name (everything before the first hyphen or dollar sign)
    item = re.split(r'[-$]', raw_name)[0].strip()
    # Remove any trailing words like "organic", "label", etc.
    item = re.sub(r'\s+(organic|label|ipm|conventional|bunch|loose)\s*$', '', item, flags=re.IGNORECASE)
    return item.strip()

def scrape_produce_prices() -> pd.DataFrame:
    url: str = "https://www.foodcoop.com/produce/"
    response: requests.Response = requests.get(url)
    
    tables: List[pd.DataFrame] = pd.read_html(StringIO(response.text))
    
    if len(tables) > 0:
        df: pd.DataFrame = tables[0]
        
        # Remove unwanted column
        df = df.drop(columns=[col for col in df.columns if 'Unnamed:' in col], errors='ignore')
        
        # Rename columns and convert to snake_case
        df.columns = pd.Index([to_snake_case(col) for col in df.columns])
        df = df.rename(columns={'organic': 'is_organic', 'name': 'raw'})
        
        # Clean up the data
        if 'price' in df.columns:
            df['price'] = df['price'].apply(clean_price)
        df = df[~df["price"].isnull()]
        
        # Clean up other columns
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip()
        
        # Add is_local column
        df['is_local'] = df['origin'].apply(is_local)
        
        # Add item column
        df['item'] = df['raw'].apply(extract_item)
        
        # Sort values by price
        df = df.sort_values('price')
        return df
    else:
        raise ValueError("No tables found on the page. The website structure might have changed.")


def generate_html(df: pd.DataFrame) -> str:
    # Split the data into local and non-local
    local_df: pd.DataFrame = df[df['is_local'] == True].sort_values('price')
    non_local_df: pd.DataFrame = df[df['is_local'] == False].sort_values('price')
    
    # Function to create an HTML table from a DataFrame
    def df_to_html_table(df: pd.DataFrame) -> str:
        return df[['raw', 'price', 'origin']].to_html(index=False, classes='data-table')
    
    # Generate the HTML content
    html_content: str = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Produce Price List</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
            h1 {{ color: #333; }}
            .data-table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            .data-table th, .data-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            .data-table th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Produce Price List</h1>
        <p>Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>Local Produce</h2>
        {df_to_html_table(local_df)}
        
        <h2>Non-Local Produce</h2>
        {df_to_html_table(non_local_df)}
    </body>
    </html>
    """
    
    return html_content

def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()
    df = scrape_produce_prices()
    if args.debug:
        embed()
    html_content = generate_html(df)
    # Write the HTML content to a file
    fname: str = "index.html"
    with open(fname, 'w') as f:
        f.write(html_content)
    
    print(f"HTML file '{fname}' has been generated.")

if __name__ == "__main__":
    main()
