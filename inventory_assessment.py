import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("Inventory Policy Simulator")

# ---------------------------
# Sidebar Inputs
# ---------------------------

st.sidebar.header("Inventory Inputs")

opening_balance = st.sidebar.number_input("Opening Balance", value=500)

avg_demand = st.sidebar.number_input("Average Demand", value=25)

cov = st.sidebar.number_input("Coefficient of Variation", value=0.8)

lead_time = st.sidebar.number_input("Lead Time (Days)", value=3)

reorder_point = st.sidebar.number_input("Reorder Point", value=200)

order_qty = st.sidebar.number_input("Order Quantity", value=300)

unit_value = st.sidebar.number_input("Value Per Unit", value=100)

holding_cost_percent = st.sidebar.number_input(
    "Holding Cost (% of Inventory Value)",
    value=20.0
)

ordering_cost = st.sidebar.number_input(
    "Ordering Cost Per Order",
    value=500
)

num_days = st.sidebar.slider("Simulation Days", 100, 2000, 365)

holding_cost_rate = holding_cost_percent / 100

# ---------------------------
# Demand Simulation
# ---------------------------

std_demand = avg_demand * cov

demand = np.maximum(
    0,
    np.random.normal(avg_demand, std_demand, num_days)
).round()

dates = pd.date_range(start="2024-01-01", periods=num_days)

inventory = opening_balance

pipeline_orders = []

data = []

# ---------------------------
# Simulation Loop
# ---------------------------

for day in range(num_days):

    shipment_received = 0

    for order in pipeline_orders.copy():
        if order[0] == day:
            shipment_received += order[1]
            pipeline_orders.remove(order)

    opening = inventory

    inventory += shipment_received

    demand_today = demand[day]

    inventory -= demand_today

    if inventory < 0:
        inventory = 0

    pipeline_qty = sum(qty for arrival, qty in pipeline_orders)

    inventory_position = opening - demand_today + shipment_received + pipeline_qty

    new_order = 0

    if inventory_position < reorder_point:
        new_order = order_qty
        pipeline_orders.append((day + lead_time, order_qty))

    closing = inventory

    closing_with_pipeline = closing + sum(qty for arrival, qty in pipeline_orders)

    data.append([
        dates[day],
        opening,
        demand_today,
        shipment_received,
        pipeline_qty,
        inventory_position,
        new_order,
        closing,
        closing_with_pipeline
    ])

# ---------------------------
# DataFrame
# ---------------------------

df = pd.DataFrame(data, columns=[
    "Date",
    "Opening Balance",
    "Demand",
    "Shipment Received",
    "Pipeline Order",
    "Inventory Position",
    "New Order",
    "Closing Balance",
    "Closing Balance Including Pipeline"
])

# ---------------------------
# KPI Calculations
# ---------------------------

stockout_days = (df["Closing Balance"] == 0).sum()

average_inventory = df["Closing Balance Including Pipeline"].mean()

average_age_inventory = average_inventory / df["Demand"].mean()

df["Blocked Working Capital"] = df["Inventory Position"] * unit_value

average_working_capital = df["Blocked Working Capital"].mean()

# Cost calculations
df["Inventory Value"] = df["Closing Balance Including Pipeline"] * unit_value

df["Holding Cost"] = df["Inventory Value"] * holding_cost_rate / 365

total_holding_cost = df["Holding Cost"].sum()

number_of_orders = (df["New Order"] > 0).sum()

total_ordering_cost = number_of_orders * ordering_cost

total_inventory_cost = total_holding_cost + total_ordering_cost

# ---------------------------
# EOQ Calculation
# ---------------------------

annual_demand = avg_demand * 365

holding_cost_per_unit = unit_value * holding_cost_rate

eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)

# ---------------------------
# KPI Display
# ---------------------------

st.subheader("Key Inventory KPIs")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Stockout Days", stockout_days)

col2.metric(
    "Average Age of Inventory (Days)",
    round(average_age_inventory,1)
)

col3.metric(
    "Average Inventory",
    round(average_inventory,0)
)

col4.metric(
    "Avg Blocked Working Capital",
    round(average_working_capital,0)
)

st.divider()

# ---------------------------
# Cost KPIs
# ---------------------------

st.subheader("Inventory Cost Metrics")

c1, c2, c3 = st.columns(3)

c1.metric("Total Holding Cost", round(total_holding_cost,0))

c2.metric("Total Ordering Cost", round(total_ordering_cost,0))

c3.metric("Total Inventory Cost", round(total_inventory_cost,0))

# ---------------------------
# EOQ Recommendation
# ---------------------------

st.subheader("EOQ Recommendation")

e1, e2, e3 = st.columns(3)

e1.metric("Economic Order Quantity (EOQ)", round(eoq,0))

e2.metric("Selected Order Quantity", order_qty)

e3.metric("Difference from EOQ", round(order_qty - eoq,0))

st.divider()

# ---------------------------
# Inventory Behaviour Chart
# ---------------------------

st.subheader("Inventory Behaviour")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Closing Balance"],
    name="Closing Inventory"
))

fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Closing Balance Including Pipeline"],
    name="Inventory Position"
))

fig.add_hline(
    y=reorder_point,
    line_dash="dash",
    annotation_text="Reorder Point"
)

stockouts = df[df["Closing Balance"] == 0]

fig.add_trace(go.Scatter(
    x=stockouts["Date"],
    y=stockouts["Closing Balance"],
    mode="markers",
    name="Stockout",
    marker=dict(color="red", size=8)
))

reorders = df[df["New Order"] > 0]

fig.add_trace(go.Scatter(
    x=reorders["Date"],
    y=reorders["Closing Balance"],
    mode="markers",
    name="Reorder Trigger",
    marker=dict(color="green", size=9, symbol="triangle-up")
))

fig.update_yaxes(rangemode="tozero")

st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Pipeline Inventory Chart
# ---------------------------

st.subheader("Pipeline Inventory (Orders in Transit)")

fig_pipeline = px.line(
    df,
    x="Date",
    y="Pipeline Order"
)

st.plotly_chart(fig_pipeline, use_container_width=True)

# ---------------------------
# Orders Chart
# ---------------------------

st.subheader("Orders Placed")

orders = df[df["New Order"] > 0]

fig_orders = px.scatter(
    orders,
    x="Date",
    y="New Order"
)

st.plotly_chart(fig_orders, use_container_width=True)

# ---------------------------
# Demand Histogram
# ---------------------------

st.subheader("Demand Distribution")

fig_hist = px.histogram(
    df,
    x="Demand",
    nbins=20
)

st.plotly_chart(fig_hist, use_container_width=True)

# ---------------------------
# Working Capital Chart
# ---------------------------

st.subheader("Blocked Working Capital")

fig_wc = px.line(
    df,
    x="Date",
    y="Blocked Working Capital"
)

st.plotly_chart(fig_wc, use_container_width=True)

# ---------------------------
# Inventory Waterfall
# ---------------------------

st.subheader("Inventory Flow Waterfall")

selected_day = st.slider("Select Day", 0, len(df)-1, 0)

row = df.iloc[selected_day]

fig_waterfall = go.Figure(go.Waterfall(

    measure=["absolute","relative","relative","total"],

    x=[
        "Opening Balance",
        "Demand",
        "Shipment Received",
        "Closing Balance"
    ],

    y=[
        row["Opening Balance"],
        -row["Demand"],
        row["Shipment Received"],
        row["Closing Balance"]
    ]

))

fig_waterfall.update_layout(
    title=f"Inventory Flow on {row['Date'].date()}"
)

st.plotly_chart(fig_waterfall, use_container_width=True)

# ---------------------------
# Data Table
# ---------------------------

st.subheader("Simulation Data")

st.dataframe(df)
