import sys, os
from uab_model import fetch_season, get_pca_table

def main():
    if len(sys.argv) < 2:
        print("Usage: python precompute.py <season> [<season2> ...]")
        sys.exit(1)

    os.makedirs("data", exist_ok=True)

    for arg in sys.argv[1:]:
        try:
            season = int(arg)
        except ValueError:
            print(f"⚠️ Invalid season '{arg}', skipping.")
            continue

        print(f"\n🔄 Processing {season}...")
        data = fetch_season(season)
        table = get_pca_table(season, min_pa=200, data=data)

        outfile = f"data/pca{season}.csv"
        table.to_csv(outfile, index=False)
        print(f"✅ Saved PCA+ table with batter IDs to {outfile}")

if __name__ == "__main__":
    main()