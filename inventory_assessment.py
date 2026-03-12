import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.title("Inventory Policy Simulator")

# Sidebar Inputs
st.sidebar.header("Inventory Parameters")

opening_balance = st.sidebar.number_input("Opening Balance", value=500)
avg_demand = st.sidebar.number_input("Average Demand", value=25)
cov = st.sidebar.number_input("Coefficient of Variation", value=0.8)
lead_time = st.sidebar.number_input("Lead Time (days)", value=3)
reorder_point = st.sidebar.number_input("Reorder Point", value=200)
order_qty = st.sidebar.number_input("Order Quantity", value=300)
num_days = st.sidebar.slider("Simulation Days", 100, 2000, 365)

std_demand = avg_demand * cov

# Generate demand
demand = np.maximum(
    0,
    np.random.normal(avg_demand, std_demand, num_days)
).round()

dates = pd.date_range(start="2024-01-01", periods=num_days)

opening = []
shipment = []
pipeline_today = []
total_pipeline = []
new_orders = []
closing = []
closing_with_pipeline = []

inventory = opening_balance
pipeline = []

for day in range(num_days):

    received_today = 0

    # Check arriving shipments
    for order in pipeline.copy():
        if order[0] == day:
            received_today += order[1]
            pipeline.remove(order)

    inventory += received_today

    opening.append(inventory)
    shipment.append(received_today)

    # Demand
    inventory -= demand[day]
    inventory = max(inventory, 0)

    # Pipeline calculation
    pipeline_qty = sum(qty for arrival, qty in pipeline)
    pipeline_today.append(pipeline_qty)

    new_order = 0

    # Reorder decision
    if inventory + pipeline_qty <= reorder_point:
        new_order = order_qty
        pipeline.append((day + lead_time, order_qty))

    new_orders.append(new_order)

    pipeline_qty = sum(qty for arrival, qty in pipeline)
    total_pipeline.append(pipeline_qty)

    closing.append(inventory)
    closing_with_pipeline.append(inventory + pipeline_qty)

# Dataframe
df = pd.DataFrame({
    "Date": dates,
    "Opening Balance": opening,
    "Demand": demand,
    "Shipment Received": shipment,
    "Pipeline Order": pipeline_today,
    "Total Order Including pipeline Order": total_pipeline,
    "New Order": new_orders,
    "Closing Balance": closing,
    "Closing Balance Including pipeline Orders": closing_with_pipeline
})

st.subheader("Simulation Data")

st.dataframe(df)

# Inventory Chart
fig = px.line(
    df,
    x="Date",
    y="Closing Balance",
    title="Daily Closing Inventory"
)

fig.update_yaxes(rangemode="tozero")

st.plotly_chart(fig, use_container_width=True)
