#!/usr/bin/env python3
"""
merge_to_global.py

Concatenate yearly merged CSVs in data/interim -> save spotify_global_merged.csv
Also create a country-level aggregated CSV useful for the choropleth.

Usage:
  cd project/src/preprocessing
  python merge_to_global.py
  # or with custom paths:
  python merge_to_global.py --interim_dir ../../data/interim --out_dir ../../data/processed
"""

import os
import argparse
import glob
import pandas as pd

DEFAULT_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DEFAULT_INTERIM = os.path.join(DEFAULT_PROJECT_ROOT, "data", "interim")
DEFAULT_PROCESSED = os.path.join(DEFAULT_PROJECT_ROOT, "data", "processed")

def read_and_concat(interim_dir):
    pattern = os.path.join(interim_dir, "merged_data_*.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files found matching: {pattern}")

    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df["source_file"] = os.path.basename(f)
            dfs.append(df)
        except Exception as e:
            print(f"Warning: failed to read {f}: {e}")

    combined = pd.concat(dfs, ignore_index=True)
    return combined, files

def clean_dataframe(df):
    # Ensure expected columns exist and coerce types
    for col in ["streams", "peak_rank", "previous_rank", "weeks_on_chart"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # Normalize country code to upper-case if present
    if "country_code" in df.columns:
        df["country_code"] = df["country_code"].astype(str).str.upper()
    return df

def aggregate_by_country(df):
    # Require country_code column
    if "country_code" not in df.columns:
        raise KeyError("country_code column not found in data; cannot aggregate by country.")

    # Total streams per country
    total_streams = df.groupby("country_code")["streams"].sum(min_count=1).fillna(0)

    # Unique tracks per country
    unique_tracks = df.groupby("country_code")["uri"].nunique()

    # Unique artist counts
    if "artist_names" in df.columns:
        unique_artists = df.groupby("country_code")["artist_names"].nunique()
    else:
        unique_artists = pd.Series(0, index=total_streams.index)

    # Average peak_rank (lower is better), drop NaNs
    avg_peak = df.groupby("country_code")["peak_rank"].mean()

    # Country name (if present, take first non-null)
    if "country_name" in df.columns:
        country_names = df.groupby("country_code")["country_name"].first()
    else:
        country_names = pd.Series(index=total_streams.index, dtype=object)

    agg = pd.DataFrame({
        "country_code": total_streams.index,
        "country_name": country_names.reindex(total_streams.index).values,
        "total_streams": total_streams.values,
        "unique_tracks": unique_tracks.reindex(total_streams.index).values,
        "unique_artists": unique_artists.reindex(total_streams.index).values,
        "avg_peak_rank": avg_peak.reindex(total_streams.index).values
    })

    # Sort by total_streams desc
    agg = agg.sort_values("total_streams", ascending=False).reset_index(drop=True)
    return agg

def main(interim_dir, out_dir, write_aggregated=True, write_combined=True):
    os.makedirs(out_dir, exist_ok=True)

    combined, files = read_and_concat(interim_dir)
    print(f"Found {len(files)} interim files. Combined rows: {combined.shape[0]}")

    combined = clean_dataframe(combined)

    if write_combined:
        combined_path = os.path.join(out_dir, "spotify_global_merged.csv")
        combined.to_csv(combined_path, index=False)
        print(f"Wrote combined dataset to: {combined_path}")

    if write_aggregated:
        agg = aggregate_by_country(combined)
        agg_path = os.path.join(out_dir, "spotify_country_aggregated.csv")
        agg.to_csv(agg_path, index=False)
        print(f"Wrote country-aggregated dataset to: {agg_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge yearly interim CSVs into a single global CSV and produce aggregated country-level CSV.")
    parser.add_argument("--interim_dir", type=str, default=DEFAULT_INTERIM,
                        help="Directory containing merged_data_YYYY.csv files (default: data/interim)")
    parser.add_argument("--out_dir", type=str, default=DEFAULT_PROCESSED,
                        help="Directory to write spotify_global_merged.csv and aggregated outputs (default: data/processed)")
    parser.add_argument("--no_aggregate", action="store_true", help="Do not write the aggregated country CSV")
    parser.add_argument("--no_combined", action="store_true", help="Do not write the combined spotify_global_merged.csv (only useful if you want aggregation only)")

    args = parser.parse_args()
    main(interim_dir=args.interim_dir, out_dir=args.out_dir,
         write_aggregated=not args.no_aggregate,
         write_combined=not args.no_combined)