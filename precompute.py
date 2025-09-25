import sys
import os
from uab_model import fetch_season, get_pca_table

def main():
    if len(sys.argv) < 2:
        print("Usage: python precompute.py <season> [<season2> <season3> ...]")
        sys.exit(1)

    # Create data/ directory if missing
    os.makedirs("data", exist_ok=True)

    # Loop through all seasons passed as arguments
    for arg in sys.argv[1:]:
        try:
            season = int(arg)
        except ValueError:
            print(f"⚠️ Invalid season '{arg}' — must be an integer like 2022.")
            continue

        print(f"\n🔄 Processing {season}...")
        data = fetch_season(season)  # slow Statcast download
        table = get_pca_table(season, min_pa=200, data=data)

        outfile = f"data/pca{season}.csv"
        table.to_csv(outfile, index=False)
        print(f"✅ Saved PCA+ table for {season} to {outfile}")

if __name__ == "__main__":
    main()