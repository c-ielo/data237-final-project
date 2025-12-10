import os
import pandas as pd
import glob
import argparse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
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


def load_and_clean_spotify_charts(year_dir, year, output_dir=INTERIM_DIR):
    all_data = []

    # loop over all CSVs in folder
    pattern = os.path.join(year_dir, f"regional-*-weekly-{year}-*.csv")
    csv_files = glob.glob(pattern)

    if not csv_files:
        print(f"No files found for year {year} in: {year_dir}")
        return None

    for filepath in csv_files:
        filename = os.path.basename(filepath)

        # map country code to country name
        parts = filename.split('-')
        country_code = parts[1].upper()
        country_name = COUNTRY_MAP.get(country_code, country_code)

        # extract month to determine quarter
        date_str = filename.split(f"{year}-")[-1].replace(".csv", "")
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

    merged_df = pd.concat(all_data, ignore_index=True)

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"merged_data_{year}.csv")
    merged_df.to_csv(output_path, index=False)

    print(f"✔ Cleaned data for {year} saved to: {output_path}")
    return merged_df


def process_multiple_years(base_dir, years, output_dir=INTERIM_DIR):
    for year in years:
        year_dir = os.path.join(base_dir, "spotify", f"{year}")
        if os.path.exists(year_dir):
            load_and_clean_spotify_charts(year_dir, year, output_dir)
        else:
            print(f"✘ Directory not found for year {year}: {year_dir}")


def main():
    parser = argparse.ArgumentParser(description="Merge Spotify weekly regional datasets into yearly merged datasets.")

    parser.add_argument(
        "--base_dir",
        type=str,
        default=RAW_DIR,
        help="Base directory containing the yearly Spotify folders."
    )

    parser.add_argument(
        "--out_dir",
        type=str,
        default=INTERIM_DIR,
        help="Output directory for merged CSVs."
    )

    parser.add_argument(
        "--years",
        nargs="*",
        type=int,
        default=[2019, 2020, 2021, 2022, 2023, 2024, 2025],
        help="Years to process."
    )

    args = parser.parse_args()

    print("=== Spotify Dataset Merger ===")
    print(f"Base directory: {args.base_dir}")
    print(f"Output directory: {args.out_dir}")
    print(f"Years: {args.years}\n")

    process_multiple_years(args.base_dir, args.years, args.out_dir)


if __name__ == "__main__":
    main()