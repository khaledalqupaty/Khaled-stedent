import streamlit as st
from data.mock_data import load_data

load_data()

st.title("📊 لوحة التحكم")

c1, c2, c3 = st.columns(3)

c1.metric("👥 الطالبات", len(st.session_state.students_db))
c2.metric("🚐 السائقين", len(st.session_state.buses_db))
c3.metric(
    "💰 بانتظار الدفع",
    len(st.session_state.students_db[
        st.session_state.students_db["حالة الدفع"] != "تم الدفع"
    ])
)
