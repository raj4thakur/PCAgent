import streamlit as st
import pandas as pd
import requests

# ---- Load sample data ----
@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

# ---- Sidebar ----
st.sidebar.title("Controls")
task = st.sidebar.selectbox("Choose task", ["Chat with Bot (via n8n)", "Analyze Data"])

# ---- Main UI ----
st.title("💬 Data Analysis Assistant (Streamlit + n8n + Ollama)")

if task == "Analyze Data":
    st.subheader("📊 Sales Data")
    st.dataframe(df)

    st.write("### Total Sales:")
    st.metric("💵 Amount", f"${df['amount'].sum():,.2f}")

    top_customer = df.groupby("customer")["amount"].sum().idxmax()
    st.write(f"**Top Customer:** {top_customer}")

elif task == "Chat with Bot (via n8n)":
    st.subheader("🤖 Ask Questions")
    user_input = st.text_area("Your question:", placeholder="e.g. Who spent the most?")

    if st.button("Ask Bot") and user_input:
        # Send request to n8n webhook
        payload = {
            "question": user_input,
            "data": df.to_dict(orient="records")
        }

        try:
            response = requests.post(
                "http://localhost:5678/webhook/chatbot",
                json=payload,
                timeout=60
            )
            if response.ok:
                answer = response.json().get("answer", response.text)
                st.success(answer)
            else:
                st.error(f"n8n Error: {response.status_code}")
        except Exception as e:
            st.error(f"Connection failed: {e}")