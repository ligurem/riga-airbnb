import streamlit as st
import altair as alt
import pandas as pd

st.title("🚨 IF YOU SEE THIS, THIS FILE IS RUNNING 🚨")
st.write("Path test version 1")

st.set_page_config(page_title="Riga AirBnb Dashboard", layout="centered")
st.title("Breakdown of Riga's AirBnB Listings")

@st.cache_data
def load_data():
    return pd.read_parquet("data/riga_airbnb_clean.parquet")

df = load_data()

top5_neighborhoods = (
    df["neighbourhood_cleansed"]
    .value_counts()
    .head(5)
    .index
    .tolist()
)

plot_df = df[df["neighbourhood_cleansed"].isin(top5_neighborhoods)].copy()

neigh_order = top5_neighborhoods

order = [
    "1-3 properties",
    "4-9 properties",
    "10-19 properties",
    "20+ properties"
]

neigh_context = {
    "Centrs": "Central business and residential district",
    "Vecpilsēta": "Old Town; historic center",
    "Maskavas forštate": "Moscow District; historic eastern quarter",
    "Avoti": "Inner-city residential neighborhood east of Centrs",
    "Grīziņkalns": "Older residential area; historically working-class, now transitioning"
}

plot_df["neighborhood_context"] = plot_df["neighbourhood_cleansed"].map(neigh_context)

view_mode = st.radio(
    "View mode",
    ["Count", "Percentage"],
    horizontal=True
)

y_encoding = (
    alt.Y("count():Q", title="Number of Listings")
    if view_mode == "Count"
    else alt.Y(
        "count():Q",
        stack="normalize",
        title="Share of Listings",
        axis=alt.Axis(format="%")
    )
)

st.write("**Listings by Neighborhood and Host Size**")

chart = (
    alt.Chart(plot_df)
    .mark_bar()
    .encode(
        x=alt.X(
            "neighbourhood_cleansed:N",
            title="Neighborhood (Top 5)",
            sort=neigh_order
        ),
        y=y_encoding,
        color=alt.Color(
            "host_size_group:O",
            scale=alt.Scale(
                domain=order,
                scheme="blues"
            ),
            title="Host Portfolio Size"
        ),
        order=alt.Order(
            "host_size_order:Q",
            sort="descending"
        ),
        tooltip=[
            alt.Tooltip("neighbourhood_cleansed:N", title="Neighborhood"),
            alt.Tooltip("neighborhood_context:N", title="About"),
            alt.Tooltip("host_size_group:N", title="Host Portfolio Size"),
            alt.Tooltip("count()", title="Listings")
        ]
    )
    .properties(
        width=700,
        height=500
    )
)

st.altair_chart(chart, use_container_width=True)