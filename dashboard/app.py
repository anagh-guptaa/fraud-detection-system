import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="Fraud Detection Dashboard", layout="wide")
st.title("AI Fraud Detection Dashboard")
st.markdown("Real-Time Transaction Monitoring System")
st.sidebar.header("Transaction Input")

transaction_id=st.sidebar.number_input("Transaction ID", value=999999)
user_id=st.sidebar.number_input("User ID", value=1000)
amount=st.sidebar.number_input("Amount", value=5000)
merchant=st.sidebar.text_input("Merchant",value="Amazon")
location=st.sidebar.text_input("Location", value="Mumbai")
device_id=st.sidebar.text_input("Device ID", value="android_245")

if st.sidebar.button("Detect Fraud"):
    payload={
        "transaction_id": transaction_id,
        "user_id": user_id,
        "amount": amount,
        "merchant": merchant,
        "location": location,
        "device_id": device_id

    }

    response=requests.post("http://127.0.0.1:8000/predict", json=payload)

    result=response.json()

    st.subheader("Prediction Result")
    col1,col2,col3 = st.columns(3)
    with col1:
        fraud_status=("FRAUD" if result["is_fraud"] else "NORMAL")
        st.metric("Fraud Status",fraud_status)

    with col2:
        st.metric("Risk Level",result["risk_level"])

    with col3:
        st.metric("Anomaly Score",result["anomaly_score"])

    st.subheader("Behavioral Features")
    features_df=pd.DataFrame(result["features"].items(),columns=["Feature","Value"])
    st.dataframe(features_df,use_container_width=True)

    st.subheader("Feature Visualization")
    fig=px.bar(features_df,x="Feature",y="Value",title="Transaction Feature Analysis")
    st.plotly_chart(fig,use_container_width=True)

