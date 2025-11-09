import os
import pandas as pd
import glob

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
INTERIM_DIR = os.path.join(PROJECT_ROOT, "data", "interim")

COUNTRY_MAP = {
    "US": "United States",
    "CA": "Canada",
    "MX": "Mexico",
    "BR": "Brazil",
    "AR": "Argentina",
    "CO": "Colombia",
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "SE": "Sweden",
    "ES": "Spain",
    "IT": "Italy",
    "JP": "Japan",
    "KR": "South Korea",
    "IN": "India",
    "SG": "Singapore",
    "ZA": "South Africa",
    "NG": "Nigeria",
    "AU": "Australia",
    "TR": "Turkey",
    "PL": "Poland"
}

QUARTER_MAP = {
    '01': 'Q1',
    '04': 'Q2',
    '07': 'Q3',
    '10': 'Q4'
}

def load_and_clean_spotify_charts(year_dir, year):
    all_data = []

    # loop over all CSVs in folder
    for filepath in glob.glob(os.path.join(year_dir, f"regional-*-weekly-{year}-*.csv")):
        filename = os.path.basename(filepath)

        # map country code to country name
        parts = filename.split('-')
        country_code = parts[1].upper()
        country_name = COUNTRY_MAP.get(country_code, country_code)

        # extract month to determine quarter
        date_str = filename.split(f"{year}-")[-1].replace('.csv', '')
        month = date_str.split('-')[0]
        quarter = QUARTER_MAP.get(month, None)

        # read CSV
        data = pd.read_csv(filepath)

        # keep only top 50 tracks
        data = data.head(50)

        # add metadata columns
        data['country_code'] = country_code
        data['country_name'] = country_name
        data['quarter'] = quarter
        data['year'] = year

        all_data.append(data)

    # merge all quarterly data
    merged_df = pd.concat(all_data, ignore_index=True)

    # save to CSV
    output_path = os.path.join(INTERIM_DIR, f"merged_data_{year}.csv")
    merged_df.to_csv(output_path, index=False)

    print(f"Cleaned data for {year} saved to: {output_path}")
    return merged_df

def process_multiple_years(base_dir, years):
    for year in years:
        year_dir = os.path.join(base_dir, f"spotify_charts_{year}")
        if os.path.exists(year_dir):
            load_and_clean_spotify_charts(year_dir, year)
        else:
            print(f"Directory not found for year {year}: {year_dir}")