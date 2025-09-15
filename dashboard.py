import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile, os

# -------------------------------
# Load and Extract Data
# -------------------------------
zip_files = [f for f in os.listdir(".") if f.endswith(".zip")]
if not zip_files:
    st.error("❌ Please upload archive.zip (Kaggle Air Quality Data) into this folder.")
    st.stop()

zip_path = zip_files[0]
extract_path = "air_quality_data"
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_path)

csv_map = {
    "station_hour": "station_hour.csv",
    "station_day": "station_day.csv",
    "city_hour": "city_hour.csv",
    "city_day": "city_day.csv"
}

# -------------------------------
# Sidebar Controls
# -------------------------------
st.set_page_config(page_title=" Air Quality Dashboard", layout="wide")
st.sidebar.title("⚙️ Controls")

dataset_choice = st.sidebar.selectbox("Dataset", list(csv_map.keys()))
csv_path = os.path.join(extract_path, csv_map[dataset_choice])
df = pd.read_csv(csv_path, parse_dates=["Datetime"])

# Fill missing values
for col in df.columns:
    if col not in ["City", "Station", "Datetime", "AQI_Bucket"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.fillna(method="ffill").fillna(method="bfill")

cities = df["City"].dropna().unique()
city = st.sidebar.selectbox("City", cities)

stations = df["Station"].dropna().unique() if "Station" in df.columns else []
station = st.sidebar.selectbox("Station", stations) if len(stations) else None

pollutants = [c for c in df.columns if c not in ["City", "Station", "Datetime", "AQI_Bucket"]]
pollutant = st.sidebar.selectbox("Pollutant", pollutants)

days = st.sidebar.slider("Time Range (days)", 1, 60, 7)

# -------------------------------
# Filter Data
# -------------------------------
if "Station" in df.columns:
    mask = (df["City"] == city) & (df["Station"] == station)
else:
    mask = (df["City"] == city)

mask &= df["Datetime"] >= (df["Datetime"].max() - pd.Timedelta(days=days))
df_filtered = df.loc[mask]

st.markdown("<h2 style='color:green'> Air Quality Dashboard</h2>", unsafe_allow_html=True)
st.caption(f"Dataset: {dataset_choice} | City: {city} | Pollutant: {pollutant}")

# -------------------------------
# Layout: 4 Panels
# -------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    fig_ts = px.line(df_filtered, x="Datetime", y=pollutant,
                     title=f"{pollutant} Time Series",
                     color_discrete_sequence=["green"])
    st.plotly_chart(fig_ts, use_container_width=True)

with col2:
    corr = df_filtered[pollutants].corr()
    fig_corr = px.imshow(corr, text_auto=True,
                         title="Pollutant Correlations",
                         color_continuous_scale="Greens")
    st.plotly_chart(fig_corr, use_container_width=True)

# Summary cards row
st.subheader(" Summary Statistics")
if not df_filtered.empty:
    summary = df_filtered[pollutant].describe()
    colA, colB, colC, colD, colE, colF = st.columns(6)
    colA.metric("Mean", f"{summary['mean']:.2f}")
    colB.metric("Median", f"{summary['50%']:.2f}")
    colC.metric("Std Dev", f"{summary['std']:.2f}")
    colD.metric("Min", f"{summary['min']:.2f}")
    colE.metric("Max", f"{summary['max']:.2f}")
    colF.metric("Count", int(summary['count']))

col3, col4 = st.columns(2)

with col3:
    fig_hist = px.histogram(df_filtered, x=pollutant, nbins=20,
                            title=f"{pollutant} Distribution",
                            color_discrete_sequence=["green"])
    st.plotly_chart(fig_hist, use_container_width=True)

with col4:
    st.write("Data Quality")
    if not df_filtered.empty:
        completeness = 100 * df_filtered.notna().mean().mean()
        validity = 100 * (df_filtered[pollutant].dropna() >= 0).mean()
        st.success(f"Completeness: {completeness:.1f}%")
        st.success(f"Validity: {validity:.1f}%")
    else:
        st.warning(" No data for this selection")