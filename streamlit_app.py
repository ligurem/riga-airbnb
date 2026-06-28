import streamlit as st
import altair as alt
import pandas as pd

st.set_page_config(page_title="Riga AirBnB Dashboard", layout="centered")
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

plot_df = df[
    df["neighbourhood_cleansed"].isin(top5_neighborhoods)
].copy()

# -------------------------
# Sidebar filters
# -------------------------

st.sidebar.header("Filters")

price_min = int(plot_df["price_$"].min())
price_max = int(plot_df["price_$"].quantile(0.99))

price_range = st.sidebar.slider(
    "Nightly Price",
    min_value=price_min,
    max_value=price_max,
    value=(price_min, price_max)
)

room_types = sorted(plot_df["room_type"].dropna().unique())

selected_rooms = st.sidebar.multiselect(
    "Room Type",
    room_types,
    default=room_types
)

show_percent = st.sidebar.toggle(
    "Normalize bars",
    value=False
)

plot_df = plot_df[
    plot_df["price_$"].between(*price_range)
]

plot_df = plot_df[
    plot_df["room_type"].isin(selected_rooms)
]

# -------------------------
# Constants
# -------------------------

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

plot_df["neighborhood_context"] = (
    plot_df["neighbourhood_cleansed"]
    .map(neigh_context)
)

if show_percent:
    y_encoding = alt.Y(
        "count():Q",
        stack="normalize",
        axis=alt.Axis(format="%"),
        title="Share of Listings"
    )
else:
    y_encoding = alt.Y(
        "count():Q",
        title="Number of Listings"
    )

# Shared selection

neighborhood_click = alt.selection_point(
    fields=["neighbourhood_cleansed"],
    empty=True
)

# -------------------------
# Chart 1
# -------------------------

chart1 = (
    alt.Chart(plot_df)
    .mark_bar()
    .encode(
        x=alt.X(
            "neighbourhood_cleansed:N",
            sort=neigh_order,
            title="Neighborhood (Top 5)"
        ),
        y=y_encoding,
        color=alt.Color(
            "host_size_group:O",
            title="Host Portfolio Size",
            scale=alt.Scale(
                domain=order,
                scheme="blues"
            )
        ),
        order=alt.Order(
            "host_size_order:Q",
            sort="descending"
        ),
        opacity=alt.condition(
            neighborhood_click,
            alt.value(1),
            alt.value(0.4)
        ),
        tooltip=[
            alt.Tooltip(
                "neighbourhood_cleansed:N",
                title="Neighborhood"
            ),
            alt.Tooltip(
                "neighborhood_context:N",
                title="About"
            ),
            alt.Tooltip(
                "host_size_group:N",
                title="Host Portfolio Size"
            ),
            alt.Tooltip(
                "count()",
                title="Listings"
            )
        ]
    )
    .properties(
        title="Listings by Neighborhood and Host Size",
        width=700,
        height=450
    )
    .add_params(neighborhood_click)
)

# -------------------------
# Chart 2
# -------------------------

df_super = plot_df[
    plot_df["host_is_superhost"].notna()
].copy()

df_super["host_is_superhost"] = (
    df_super["host_is_superhost"]
    .map({
        True: "Superhost",
        False: "Not Superhost"
    })
)

chart2 = (
    alt.Chart(df_super)
    .mark_bar()
    .transform_filter(neighborhood_click)
    .encode(
        y=alt.Y(
            "host_size_group:O",
            sort=order,
            title="Host Portfolio Size"
        ),
        x=alt.X(
            "count():Q",
            stack="normalize",
            title="Share of Listings"
        ),
        color=alt.Color(
            "host_is_superhost:N",
            title="",
            scale=alt.Scale(
                domain=[
                    "Superhost",
                    "Not Superhost"
                ],
                range=[
                    "#1f77b4",
                    "#ff7f0e"
                ]
            )
        ),
        tooltip=[
            alt.Tooltip(
                "host_size_group:N",
                title="Host Portfolio Size"
            ),
            alt.Tooltip(
                "host_is_superhost:N",
                title="Superhost Status"
            ),
            alt.Tooltip(
                "count()",
                title="Listings"
            )
        ]
    )
    .properties(
        title="Superhost Share by Host Portfolio",
        width=700,
        height=300
    )
)

# -------------------------
# Chart 3
# -------------------------

chart3 = (
    alt.Chart(plot_df)
    .mark_boxplot(size=45)
    .transform_filter(neighborhood_click)
    .encode(
        x=alt.X(
            "host_size_group:O",
            sort=order,
            title="Host Portfolio Size"
        ),
        y=alt.Y(
            "price_$:Q",
            title="Nightly Price ($)"
        ),
        color=alt.Color(
            "host_size_group:O",
            legend=None,
            scale=alt.Scale(
                domain=order,
                scheme="blues"
            )
        ),
        tooltip=[
            alt.Tooltip(
                "price_$:Q",
                title="Price"
            )
        ]
    )
    .properties(
        title="Nightly Price Distribution by Host Portfolio",
        width=700,
        height=350
    )
)

# -------------------------
# Dashboard
# -------------------------

dashboard = (
    alt.vconcat(
        chart1,
        chart2,
        chart3,
        spacing=25
    )
    .resolve_scale(
        color="independent"
    )
)

st.caption("Click a neighborhood in the first chart to update the charts below.")

st.altair_chart(
    dashboard,
    use_container_width=True
)