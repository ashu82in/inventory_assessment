import streamlit as st
import pandas as pd
import numpy as np

st.title("Inventory Policy Simulator")

# Sidebar inputs
opening_balance = st.sidebar.number_input("Opening Balance", value=500)
avg_demand = st.sidebar.number_input("Average Demand", value=25)
cov = st.sidebar.number_input("Coefficient of Variation", value=0.8)
lead_time = st.sidebar.number_input("Lead Time", value=3)
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

inventory = opening_balance
pipeline_orders = []

data = []

for day in range(num_days):

    # Receive shipments
    shipment_received = 0
    for order in pipeline_orders.copy():
        if order[0] == day:
            shipment_received += order[1]
            pipeline_orders.remove(order)

    opening = inventory

    inventory += shipment_received

    demand_today = demand[day]

    inventory -= demand_today
    inventory = max(inventory, 0)

    # Pipeline quantity
    pipeline_qty = sum(qty for arrival, qty in pipeline_orders)

    # Inventory position
    total_order_pipeline = opening - demand_today + shipment_received + pipeline_qty

    new_order = 0

    # Reorder rule (your logic)
    if total_order_pipeline < reorder_point:
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
        total_order_pipeline,
        new_order,
        closing,
        closing_with_pipeline
    ])

df = pd.DataFrame(data, columns=[
    "Date",
    "Opening Balance",
    "Demand",
    "Shipment Received",
    "Pipeline Order",
    "Total Order Including pipeline Order",
    "New Order",
    "Closing Balance",
    "Closing Balance Including pipeline Orders"
])

st.dataframe(df)
