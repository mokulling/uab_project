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

# Extract season years from file names like pca2022.csv
seasons = sorted([int(f[3:7]) for f in season_files])

# Sidebar controls
season = st.sidebar.selectbox("Select Season", seasons)
min_pa = st.sidebar.slider("Minimum Plate Appearances (PA)", 50, 600, 200)

# -----------------------------
# Load precomputed data
# -----------------------------
@st.cache_data
def load_table(season):
    return pd.read_csv(f"data/pca{season}.csv")

df = load_table(season)

# Apply PA filter
df = df[df["total_pa"] >= min_pa].reset_index(drop=True)

# -----------------------------
# Leaderboards
# -----------------------------
st.subheader(f"🏆 Top 20 CAB+ Batters – {season}")
st.dataframe(df.head(20))

st.subheader(f"💤 Bottom 20 CAB+ Batters – {season}")
st.dataframe(df.tail(20))

# -----------------------------
# Player Search
# -----------------------------
st.subheader("🔍 Player Search")
query = st.text_input("Enter player name (partial ok)").strip()
if query:
    results = df[df["player_name"].str.contains(query, case=False)]
    if results.empty:
        st.warning("No matching player in current dataset.")
    else:
        st.success(f"Found {len(results)} matching player(s).")
        st.dataframe(results)

# -----------------------------
# Download Option
# -----------------------------
st.subheader("⬇️ Download Data")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label=f"Download {season} CAB+ data as CSV",
    data=csv,
    file_name=f"CAB{season}_min{min_pa}.csv",
    mime="text/csv",
)