import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Inventory Dashboard", layout="wide")

st.title("Inventory Analytics Dashboard")

# Upload File
uploaded_file = st.file_uploader("Upload Inventory Excel/CSV File", type=["xlsx","csv"])

if uploaded_file:

    # Read file
    if uploaded_file.name.endswith("csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    required_columns = [
        "Date",
        "Opening Balance",
        "Demand",
        "Shipment Received",
        "Closing Balance"
    ]

    if not all(col in df.columns for col in required_columns):
        st.error("File missing required columns")
        st.stop()

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    # Sidebar filters
    st.sidebar.header("Filters")

    start_date = st.sidebar.date_input(
        "Start Date", df["Date"].min()
    )

    end_date = st.sidebar.date_input(
        "End Date", df["Date"].max()
    )

    df = df[(df["Date"] >= pd.to_datetime(start_date)) &
            (df["Date"] <= pd.to_datetime(end_date))]

    # KPIs
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Average Demand", round(df["Demand"].mean(),2))
    col2.metric("Max Demand", df["Demand"].max())
    col3.metric("Min Inventory", df["Closing Balance"].min())
    col4.metric("Stockout Days", (df["Closing Balance"]==0).sum())

    st.divider()

    # Inventory chart
    st.subheader("Inventory Level Over Time")

    fig_inventory = px.line(
        df,
        x="Date",
        y="Closing Balance",
        title="Daily Closing Inventory"
    )

    st.plotly_chart(fig_inventory, use_container_width=True)

    # Demand histogram
    st.subheader("Demand Distribution")

    bins = st.slider("Number of Histogram Bins", 5, 50, 20)

    fig_hist = px.histogram(
        df,
        x="Demand",
        nbins=bins,
        title="Demand Histogram"
    )

    st.plotly_chart(fig_hist, use_container_width=True)

    # Data table
    st.subheader("Data Table")

    st.dataframe(df, use_container_width=True)
