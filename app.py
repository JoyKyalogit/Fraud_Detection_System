import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Fraud Detection System",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    :root {
        --bg-primary: #1c1512;
        --bg-secondary: #2a1f1a;
        --surface-1: rgba(43, 32, 27, 0.82);
        --surface-2: rgba(43, 32, 27, 0.9);
        --surface-3: rgba(66, 49, 41, 0.65);
        --text-main: #f3e9dc;
        --text-muted: #c9b7a2;
        --border-soft: rgba(201, 183, 162, 0.24);
        --border-strong: rgba(201, 183, 162, 0.45);
        --accent: #b45309;
        --accent-hover: #92400e;
    }

    html, body, [class*="css"] {
        font-family: "Inter", "Segoe UI", Tahoma, sans-serif;
        color: var(--text-main);
        font-size: 17px;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }

    .stApp {
        background:
            radial-gradient(900px 400px at 0% 0%, rgba(180, 83, 9, 0.18), transparent 60%),
            radial-gradient(800px 350px at 100% 0%, rgba(153, 27, 27, 0.12), transparent 60%),
            linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
        color: var(--text-main);
    }

    #MainMenu, footer, header { visibility: hidden; }

    .main-header {
        padding: 0 4px 8px 4px;
        margin-bottom: 4px;
    }
    .main-header h1 {
        font-size: 2.45rem;
        font-weight: 650;
        color: #f3e9dc;
        margin: 0;
        letter-spacing: 0.01em;
    }
    .main-header p {
        color: var(--text-muted);
        margin: 4px 0 0 0;
        font-size: 1.05rem;
    }

    .section-card {
        margin-bottom: 14px;
    }
    .section-title {
        font-size: 0.95rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        color: var(--text-muted);
        margin-bottom: 10px;
    }

    .result-fraud, .result-legit {
        background: rgba(66, 49, 41, 0.52);
        border: 1px solid var(--border-soft);
        border-radius: 10px;
        padding: 10px 14px;
        text-align: left;
    }
    .result-verdict {
        font-size: 1.45rem;
        font-weight: 650;
        margin: 0;
    }
    .result-app-name {
        font-size: 0.92rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin: 0 0 8px 0;
    }
    .verdict-fraud, .verdict-legit { color: #f3e9dc; }

    .risk-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-top: 8px;
    }
    .risk-high { background: rgba(127, 29, 29, 0.5); color: #fecaca; border: 1px solid rgba(248, 113, 113, 0.36); }
    .risk-medium { background: rgba(120, 53, 15, 0.5); color: #fcd34d; border: 1px solid rgba(251, 191, 36, 0.4); }
    .risk-low { background: rgba(20, 83, 45, 0.45); color: #bbf7d0; border: 1px solid rgba(74, 222, 128, 0.36); }

    .metric-box {
        background: transparent;
        border: none;
        border-radius: 0;
        padding: 2px 0;
        text-align: left;
    }
    .metric-label {
        font-size: 0.92rem;
        color: var(--text-muted);
        text-transform: none;
        letter-spacing: 0.01em;
        margin-bottom: 2px;
    }
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.45rem;
        font-weight: 600;
        color: #e2e8f0;
    }

    .stSelectbox [data-baseweb="select"] > div,
    .stNumberInput input {
        background: var(--surface-2) !important;
        border: 1px solid var(--border-soft) !important;
        color: var(--text-main) !important;
        border-radius: 10px !important;
    }
    /* Ensure Streamlit field labels stay visible on light background */
    label[data-testid="stWidgetLabel"],
    .stNumberInput label,
    .stSelectbox label {
        color: #cbd5e1 !important;
        font-weight: 500 !important;
    }
    .stNumberInput input:focus,
    .stSelectbox [data-baseweb="select"] > div:focus-within {
        border-color: var(--border-strong) !important;
        box-shadow: 0 0 0 1px rgba(180, 83, 9, 0.45) !important;
    }

    .stButton > button {
        background: linear-gradient(180deg, var(--accent), var(--accent-hover)) !important;
        color: #f9fafb !important;
        border: 1px solid rgba(245, 158, 11, 0.45) !important;
        border-radius: 11px !important;
        font-weight: 600 !important;
        font-size: 1.04rem !important;
        padding: 12px 24px !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.01em !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 22px rgba(180, 83, 9, 0.32) !important;
        filter: brightness(1.03);
    }

    section[data-testid="stSidebar"] {
        background: rgba(28, 21, 18, 0.56) !important;
        border-right: 1px solid rgba(201, 183, 162, 0.24) !important;
    }
    .sidebar-stat {
        background: rgba(15, 23, 42, 0.72);
        border: 1px solid var(--border-soft);
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 9px;
    }
    .sidebar-stat-label {
        font-size: 0.68rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    .sidebar-stat-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.12rem;
        color: #f3e9dc;
        font-weight: 600;
    }
    .summary-side-card {
        background: rgba(43, 32, 27, 0.78);
        border: 1px solid var(--border-soft);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
        min-height: 430px;
    }
    .summary-side-title {
        color: var(--text-muted);
        font-size: 0.82rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .summary-mini {
        background: transparent;
        border: none;
        border-radius: 0;
        padding: 8px 2px;
        margin-bottom: 6px;
        border-bottom: 1px solid rgba(201, 183, 162, 0.2);
    }
    .summary-mini:last-child { border-bottom: none; }
    .summary-mini-label {
        color: var(--text-muted);
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .summary-mini-value {
        color: var(--text-main);
        font-size: 1.35rem;
        font-weight: 700;
        margin-top: 4px;
    }

    .rec-box {
        border-radius: 8px;
        padding: 8px 0 0 0;
        margin-top: 8px;
        font-weight: 500;
        font-size: 1.06rem;
        background: transparent;
        border: none;
        color: #e2e8f0;
    }
    .rec-block, .rec-approve { background: transparent; border: none; color: #e2e8f0; }
</style>
""",
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = []
if "latest_result" not in st.session_state:
    st.session_state.latest_result = None

with st.sidebar:
    st.markdown("### Fraud Detection System")

    total = len(st.session_state.history)
    fraud_count = sum(1 for r in st.session_state.history if r["is_fraud"])
    legit_count = total - fraud_count

    st.markdown("**Session Statistics**")
    st.markdown(
        f"""
    <div class='sidebar-stat'>
        <div class='sidebar-stat-label'>Total Analyzed</div>
        <div class='sidebar-stat-value'>{total}</div>
    </div>
    <div class='sidebar-stat'>
        <div class='sidebar-stat-label'>Fraud Detected</div>
        <div class='sidebar-stat-value' style='color:#b91c1c'>{fraud_count}</div>
    </div>
    <div class='sidebar-stat'>
        <div class='sidebar-stat-label'>Legitimate</div>
        <div class='sidebar-stat-value' style='color:#166534'>{legit_count}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if total > 0:
        rate = (fraud_count / total) * 100
        rate_color = "#b91c1c" if rate > 30 else "#b45309" if rate > 10 else "#166534"
        st.markdown(
            f"""
        <div class='sidebar-stat'>
            <div class='sidebar-stat-label'>Fraud Rate</div>
            <div class='sidebar-stat-value' style='color:{rate_color}'>{rate:.1f}%</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    if st.button("Clear History", type="secondary"):
        st.session_state.history = []
        st.rerun()

st.markdown(
    """
<div class='main-header'>
    <h1>Fraud Detection System</h1>
    <p>Transaction risk screening for secure payment decisions.</p>
</div>
""",
    unsafe_allow_html=True,
)

left_summary_col, main_content_col = st.columns([1.05, 2.15], gap="large")

with left_summary_col:
    st.markdown(
        f"""
<div class='summary-side-card'>
    <div class='summary-side-title'>Transaction Summary</div>
    <div class='summary-mini'>
        <div class='summary-mini-label'>Total Analyzed</div>
        <div class='summary-mini-value'>{total}</div>
    </div>
    <div class='summary-mini'>
        <div class='summary-mini-label'>Fraud Detected</div>
        <div class='summary-mini-value' style='color:#fca5a5'>{fraud_count}</div>
    </div>
    <div class='summary-mini'>
        <div class='summary-mini-label'>Legitimate</div>
        <div class='summary-mini-value' style='color:#bbf7d0'>{legit_count}</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )
    if st.button("Clear History"):
        st.session_state.history = []
        st.session_state.latest_result = None
        st.rerun()

with main_content_col:
    if st.session_state.latest_result:
        latest = st.session_state.latest_result
        prob = latest["fraud_probability"]
        is_fraud = latest["is_fraud"] == 1
        risk_level = latest.get("risk_level", "Low")
        amount_for_result = latest["amount"]

        st.markdown("#### Latest Analysis Result")
        res_col = st.container()

        with res_col:
            risk_class = {"High": "risk-high", "Medium": "risk-medium", "Low": "risk-low"}.get(risk_level, "risk-low")
            card_class = "result-fraud" if is_fraud else "result-legit"
            verdict_class = "verdict-fraud" if is_fraud else "verdict-legit"

            st.markdown(
                f"<p class='result-app-name'>Transaction Risk Assessment</p>",
                unsafe_allow_html=True,
            )

            m1, m2 = st.columns(2)
            with m1:
                metric_color = "#f59e0b" if prob > 0.5 else "#fbbf24" if prob > 0.3 else "#f3e9dc"
                st.markdown(
                    f"""
                <div class='metric-box' style='margin-top:12px'>
                    <div class='metric-label'>Fraud Probability</div>
                    <div class='metric-value' style='color:{metric_color}'>{prob*100:.2f}%</div>
                </div>""",
                    unsafe_allow_html=True,
                )
            with m2:
                st.markdown(
                    f"""
                <div class='metric-box' style='margin-top:12px'>
                    <div class='metric-label'>Amount</div>
                    <div class='metric-value'>KSH {amount_for_result:,.0f}</div>
                </div>""",
                    unsafe_allow_html=True,
                )

            st.markdown(f"<div class='rec-box'><strong>Verdict:</strong> {latest['recommendation']}</div>", unsafe_allow_html=True)

        st.markdown("")

    st.markdown("#### Transaction Input")
    col1, col2, col3 = st.columns(3)

    with col1:
        amount = st.number_input("Amount (KSH)", min_value=0.0, value=1000.0, step=100.0)
        txn_type = st.selectbox("Transaction Type", ["TRANSFER", "CASH_OUT", "PAYMENT", "CASH_IN", "DEBIT"])

    with col2:
        is_flagged = st.selectbox("System Flagged Fraud?", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
        new_sender = st.selectbox("New Sender?", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")

    with col3:
        odd_hour = st.selectbox("Odd Hour Transaction?", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
        freq_txn = st.selectbox("Frequent Transaction?", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")

    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        analyze = st.button("Analyze Transaction")

    large_txn_flag = 1 if amount > 200_000 else 0
    high_risk_type_flag = 1 if txn_type in ["TRANSFER", "CASH_OUT"] else 0

    with st.expander("Auto-computed Risk Flags"):
        fc1, fc2 = st.columns(2)
        fc1.info(f"Large Transaction Flag: {'Yes' if large_txn_flag else 'No'} (threshold: KSH 200,000)")
        fc2.info(f"High-Risk Type Flag: {'Yes' if high_risk_type_flag else 'No'} (TRANSFER / CASH_OUT)")

    st.markdown("")

payload = {
    "amount": amount,
    "isflaggedfraud": is_flagged,
    "large_txn_flag": large_txn_flag,
    "high_risk_type_flag": high_risk_type_flag,
    "new_sender_flag": new_sender,
    "odd_hour_flag": odd_hour,
    "frequent_txn_flag": freq_txn,
    "type_transfer": 1 if txn_type == "TRANSFER" else 0,
    "type_cash_out": 1 if txn_type == "CASH_OUT" else 0,
    "type_payment": 1 if txn_type == "PAYMENT" else 0,
    "type_cash_in": 1 if txn_type == "CASH_IN" else 0,
    "type_debit": 1 if txn_type == "DEBIT" else 0,
}

if analyze:
    with st.spinner("Analyzing transaction..."):
        try:
            response = requests.post("http://127.0.0.1:8000/predict", json=payload, timeout=5)
            result = response.json()

            prob = result["fraud_probability"]
            is_fraud = result["is_fraud"] == 1
            risk_level = result.get("risk_level", "Low")

            st.session_state.history.append(
                {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "amount": f"KSH {amount:,.2f}",
                    "type": txn_type,
                    "probability": f"{prob * 100:.1f}%",
                    "risk": risk_level,
                    "verdict": result["verdict"],
                    "is_fraud": is_fraud,
                }
            )
            result["amount"] = amount
            st.session_state.latest_result = result
            st.rerun()

        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API. Make sure `python -m uvicorn deploy:app --reload --port 8000` is running.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

if st.session_state.history:
    st.divider()
    st.markdown("<div class='section-title'>Session History</div>", unsafe_allow_html=True)

    df = pd.DataFrame(st.session_state.history[::-1])
    df_display = df[["time", "amount", "type", "probability", "risk", "verdict"]].copy()
    df_display.columns = ["Time", "Amount", "Type", "Fraud Prob.", "Risk", "Verdict"]

    st.dataframe(df_display, use_container_width=True, hide_index=True)
