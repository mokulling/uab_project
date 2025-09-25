import pandas as pd
import numpy as np
from pybaseball import statcast, playerid_reverse_lookup

# --- UAB Label ---
def label_uab(row):
    bad_outcomes = [
        "strikeout", "strikeout_double_play",
        "pop_out",
    ]
    if row["pitch_number"] <= 3 and row["events"] in bad_outcomes:
        return 1
    if row["events"] == "strikeout" and row["pitch_number"] <= 4:
        return 1
    if (
        pd.notnull(row.get("launch_speed")) 
        and pd.notnull(row.get("estimated_woba_using_speedangle"))
    ):
        if row["launch_speed"] < 80 and row["estimated_woba_using_speedangle"] < 0.200:
            return 1
    return 0

# --- Fetch chunked Statcast (slow, used in precompute) ---
def fetch_season(season):
    date_ranges = [
        (f"{season}-04-01", f"{season}-04-30"),
        (f"{season}-05-01", f"{season}-05-31"),
        (f"{season}-06-01", f"{season}-06-30"),
        (f"{season}-07-01", f"{season}-07-31"),
        (f"{season}-08-01", f"{season}-08-31"),
        (f"{season}-09-01", f"{season}-09-30"),
        (f"{season}-10-01", f"{season}-10-10"),
    ]
    dfs = []
    for start, end in date_ranges:
        print(f"Fetching {start} → {end}")
        df = statcast(start, end)
        print("  rows:", df.shape[0])
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

# --- Main analytics (build CAB+ table) ---
def get_pca_table(season, min_pa=200, data=None):
    if data is None:
        data = fetch_season(season)

    # Aggregate to plate appearances
    pa_data = (
        data.groupby(["game_pk", "at_bat_number", "batter"])
        .agg(
            pitch_number=("pitch_number", "max"),
            launch_speed=("launch_speed", "mean"),
            estimated_woba_using_speedangle=("estimated_woba_using_speedangle", "mean"),
            events=("events", "last"),
        ).reset_index()
    )

    pa_data["uab"] = pa_data.apply(label_uab, axis=1)
    pa_data["cab"] = 1 - pa_data["uab"]

    totals = (
        pa_data.groupby("batter")
        .agg(total_pa=("uab", "count"), uab=("uab", "sum"), cab=("cab", "sum"))
        .reset_index()
    )

    totals["raw_pca"] = totals["cab"].div(totals["uab"].replace(0, np.nan))
    totals["uab_rate"] = (totals["uab"]/totals["total_pa"]*100).round(2)
    totals["cab_rate"] = (totals["cab"]/totals["total_pa"]*100).round(2)

    # League avg normalization
    league_pca = totals["cab"].sum() / totals["uab"].sum()
    totals["CAB+"] = (totals["raw_pca"]/league_pca*100).round(1)

    totals = totals[totals["total_pa"] >= min_pa]

    # Batter ID → Name map
    ids = totals["batter"].tolist()
    id_map = playerid_reverse_lookup(ids, key_type="mlbam")[
        ["key_mlbam","name_first","name_last"]
    ].rename(columns={"key_mlbam":"batter"})
    totals = totals.merge(id_map, on="batter", how="left")
    totals["player_name"] = (totals["name_first"].fillna("")+" "+totals["name_last"].fillna(""))

    cols = ["player_name","total_pa","uab","cab","uab_rate","cab_rate","CAB+"]
    return totals[cols].sort_values("CAB+", ascending=False).reset_index(drop=True)