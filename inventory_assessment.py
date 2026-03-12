import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Inventory Simulation", layout="wide")

st.title("Inventory Policy Simulator")

# Sidebar Inputs
st.sidebar.header("Inventory Parameters")

opening_balance = st.sidebar.number_input("Opening Balance", value=500)

avg_demand = st.sidebar.number_input("Average Daily Demand", value=25)

cov = st.sidebar.number_input("Coefficient of Variation", value=0.8)

lead_time = st.sidebar.number_input("Lead Time (days)", value=3)

reorder_point = st.sidebar.number_input("Reorder Point", value=200)

order_qty = st.sidebar.number_input("Order Quantity", value=300)

num_days = st.sidebar.slider("Simulation Days", 100, 2000, 365)

# Demand variability
std_demand = avg_demand * cov

# Generate demand
demand = np.maximum(
    0,
    np.random.normal(avg_demand, std_demand, num_days)
).round()

dates = pd.date_range(start="2024-01-01", periods=num_days)

opening = []
shipment = []
closing = []

inventory = opening_balance

# pipeline orders
pipeline = []

for day in range(num_days):

    received_today = 0

    # check arriving orders
    for order in pipeline.copy():
        if order[0] == day:
            received_today += order[1]
            pipeline.remove(order)

    inventory += received_today

    opening.append(inventory)
    shipment.append(received_today)

    inventory -= demand[day]
    inventory = max(inventory, 0)

    # reorder logic
    if inventory <= reorder_point:
        pipeline.append((day + lead_time, order_qty))

    closing.append(inventory)

df = pd.DataFrame({
    "Date": dates,
    "Opening Balance": opening,
    "Demand": demand,
    "Shipment Received": shipment,
    "Closing Balance": closing
})

# KPIs
st.subheader("Key Metrics")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Average Demand", round(df["Demand"].mean(),2))
col2.metric("Max Demand", df["Demand"].max())
col3.metric("Minimum Inventory", df["Closing Balance"].min())
col4.metric("Stockout Days", (df["Closing Balance"]==0).sum())

st.divider()

# Inventory Chart
st.subheader("Daily Closing Inventory")

fig_inventory = px.line(
    df,
    x="Date",
    y="Closing Balance",
    title="Inventory Level Over Time"
)

fig_inventory.update_yaxes(rangemode="tozero")

fig_inventory.add_hline(
    y=reorder_point,
    line_dash="dash",
    annotation_text="Reorder Point"
)

st.plotly_chart(fig_inventory, use_container_width=True)

# Demand Histogram
st.subheader("Demand Distribution")

fig_hist = px.histogram(
    df,
    x="Demand",
    nbins=20,
    title="Demand Histogram"
)

st.plotly_chart(fig_hist, use_container_width=True)

# Show Data
st.subheader("Simulation Data")

st.dataframe(df)
