import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="⚾ CAB+ Dashboard", layout="wide")
st.title("⚾ CAB+ (Competitive At-Bat Ratio) Dashboard")

# -----------------------------
# Detect available precomputed season CSVs
# -----------------------------
if not os.path.exists("data"):
    st.error("❌ No data directory found. Please run precompute.py first.")
    st.stop()

season_files = [f for f in os.listdir("data") if f.startswith("pca") and f.endswith(".csv")]
if not season_files:
    st.error("❌ No CAB+ CSV files found in data/. Run precompute.py <season> to generate them.")
    st.stop()

# Extract seasons (e.g. "pca2022.csv" -> 2022)
seasons = sorted([int(f[3:7]) for f in season_files])

# Sidebar controls
season = st.sidebar.selectbox("Select Season", seasons)
min_pa = st.sidebar.slider("Minimum Plate Appearances (PA)", 50, 600, 200)

# -----------------------------
# Load precomputed table
# -----------------------------
@st.cache_data
def load_table(season):
    return pd.read_csv(f"data/pca{season}.csv")

df = load_table(season)

# Add Baseball Savant URLs using batter IDs
df["savant_url"] = (
    "https://baseballsavant.mlb.com/savant-player/"
    + df["player_name"].str.lower().str.replace(" ", "-", regex=True)
    + "-"
    + df["batter"].astype(str)
)

# Apply PA filter
df = df[df["total_pa"] >= min_pa].reset_index(drop=True)

# -----------------------------
# Function to render leaderboard with clickable names and styled headers
# -----------------------------
def render_leaderboard(df_slice, title):
    st.subheader(title)

    df_disp = df_slice.copy().reset_index(drop=True)

    # Add leaderboard Rank column
    df_disp.index = df_disp.index + 1
    df_disp.reset_index(inplace=True)
    df_disp.rename(columns={"index": "Rank"}, inplace=True)

    # Make player_name clickable
    df_disp["Player"] = df_disp.apply(
        lambda r: f'<a href="{r["savant_url"]}" target="_blank">{r["player_name"].title()}</a>', axis=1,
    )

    # Select and rename columns for display
    df_disp = df_disp[["Rank", "Player", "total_pa", "uab", "cab", "uab_rate","cab_rate", "PCA+"]].rename(
        columns={
            "total_pa": "PA",
            "uab": "Uncompetitive ABs",
            "cab": "Competitive ABs",
            "PCA+": "CAB+",
            "uab_rate":"UAB Rate",
            "cab_rate":"CAB Rate",
        }
    )

    # CSS for leaderboard styling only
    st.markdown(
        """
        <style>
        table {
            width: 100% !important;
            table-layout: fixed;
            border-collapse: collapse;
        }
        th {
            background-color: #262730; 
            color: white !important;
            font-weight: bold;
            text-align: center !important;
            padding: 8px;
        }
        td {
            text-align: center !important;
            padding: 6px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        a {
            color: #1f77b4;
            text-decoration: none;
            font-weight: 600;
        }
        a:hover {
            text-decoration: underline;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(df_disp.to_html(escape=False, index=False), unsafe_allow_html=True)


# -----------------------------
# Leaderboards
# -----------------------------
render_leaderboard(df.head(20), f"🏆 Top 20 CAB+ Batters – {season}")
render_leaderboard(df.tail(20), f"💤 Bottom 20 CAB+ Batters – {season}")

# -----------------------------
# Player Search (simpler table display, no leaderboard CSS)
# -----------------------------
st.subheader("🔍 Player Search")
query = st.text_input("Enter player name (partial match ok)").strip()
if query:
    results = df[df["player_name"].str.contains(query, case=False)]
    if results.empty:
        st.warning("No matching player found.")
    else:
        # Clickable names still, but simpler formatting
        results_disp = results.copy()
        results_disp["Player"] = results_disp.apply(
            lambda r: f'<a href="{r["savant_url"]}" target="_blank">{r["player_name"].title()}</a>', axis=1
        )
        results_disp = results_disp[["Player", "total_pa", "uab", "cab", "uab_rate","cab_rate","PCA+"]].rename(
            columns={
                "total_pa": "PA",
                "uab": "Uncompetitive ABs",
                "cab": "Competitive ABs",
                "uab_rate": "UAB Rate",
                "cab_rate": "CAB Rate",
                "PCA+": "CAB+",
            }
        )

        st.markdown(
            results_disp.to_html(escape=False, index=False),
            unsafe_allow_html=True
        )

# -----------------------------
# Download Option
# -----------------------------
st.subheader("⬇️ Download Data")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label=f"Download {season} CAB+ data as CSV",
    data=csv,
    file_name=f"pca{season}_min{min_pa}.csv",
    mime="text/csv",
)