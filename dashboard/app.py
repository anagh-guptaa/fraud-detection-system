import time
import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG — must be the very first Streamlit call
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FraudGuard — L3 Detection",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded",
)

API_BASE = "http://127.0.0.1:8000"

# ─────────────────────────────────────────────────────────────────────────────
# COLOR PALETTE — every color is defined here in one place.
# Reference by key (C["red"]) so changing one value updates the whole UI.
# ─────────────────────────────────────────────────────────────────────────────
C = {
    "bg_deep":      "#0B0E14",
    "bg_dark":      "#1A202C",
    "bg_card":      "#141920",
    "border":       "#2D3748",
    "border_light": "#3D4A5C",
    "text":         "#E2E8F0",
    "muted":        "#A0AEC0",
    "dim":          "#718096",
    "red":          "#E53E3E",
    "red_light":    "#F56565",
    "orange":       "#DD6B20",
    "orange_light": "#ED8936",
    "green":        "#38A169",
    "green_light":  "#48BB78",
    "blue":         "#3182CE",
    "blue_light":   "#63B3ED",
    "teal":         "#319795",
    "teal_light":   "#4FD1C5",
}


def rgb(hex_color: str) -> str:
    """Convert #RRGGBB → 'R,G,B' for use inside rgba()."""
    h = hex_color.lstrip("#")
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS INJECTION
# Streamlit's theming API is limited; we inject CSS to get fine-grained control.
# fmt: off
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
/* ── Google Fonts ──────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Global reset ──────────────────────────────────────────────────────── */
html, body, .stApp, [data-testid="stAppViewContainer"] {{
    background-color: {C["bg_deep"]} !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    color: {C["text"]} !important;
}}
[data-testid="stMain"] {{
    background-color: {C["bg_deep"]} !important;
}}

/* ── Hide Streamlit chrome ─────────────────────────────────────────────── */
#MainMenu, footer, header, [data-testid="stToolbar"] {{ visibility: hidden !important; }}

/* ── Sidebar ───────────────────────────────────────────────────────────── */
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
    background-color: #0C1018 !important;
    border-right: 1px solid {C["border"]} !important;
}}
[data-testid="stSidebar"] * {{ color: {C["text"]} !important; }}
[data-testid="stSidebar"] label {{ color: {C["muted"]} !important; font-size: 12px !important; }}

/* ── Inputs ────────────────────────────────────────────────────────────── */
input, [data-testid="stNumberInput"] input, [data-testid="stTextInput"] input {{
    background-color: {C["bg_dark"]} !important;
    color: {C["text"]} !important;
    border: 1px solid {C["border"]} !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
}}
input:focus {{ border-color: {C["blue"]} !important; outline: none !important; }}

/* ── Button ────────────────────────────────────────────────────────────── */
.stButton > button {{
    background: linear-gradient(135deg, {C["blue"]} 0%, #2B6CB0 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    width: 100% !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s ease !important;
}}
.stButton > button:hover {{
    background: linear-gradient(135deg, #4299E1 0%, {C["blue"]} 100%) !important;
    box-shadow: 0 4px 16px rgba({rgb(C["blue"])}, 0.4) !important;
    transform: translateY(-1px) !important;
}}

/* ── Divider ───────────────────────────────────────────────────────────── */
hr {{ border-color: {C["border"]} !important; margin: 20px 0 !important; }}

/* ── Dataframe ─────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] iframe {{ background-color: {C["bg_dark"]} !important; }}
.stDataFrame * {{ font-family: 'Inter', sans-serif !important; }}

/* ── Scrollbar ─────────────────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {C["bg_deep"]}; }}
::-webkit-scrollbar-thumb {{ background: {C["border"]}; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: {C["border_light"]}; }}

/* ── Spinner ───────────────────────────────────────────────────────────── */
.stSpinner > div {{ border-top-color: {C["blue"]} !important; }}

/* ── Keyframes ─────────────────────────────────────────────────────────── */
@keyframes pulse {{
    0%, 100% {{ opacity:1; box-shadow: 0 0 0 0 rgba({rgb(C["green_light"])}, 0.5); }}
    50%       {{ opacity:.8; box-shadow: 0 0 0 6px rgba({rgb(C["green_light"])}, 0); }}
}}
@keyframes pulse-red {{
    0%, 100% {{ opacity:1; box-shadow: 0 0 0 0 rgba({rgb(C["red"])}, 0.6); }}
    50%       {{ opacity:.8; box-shadow: 0 0 0 8px rgba({rgb(C["red"])}, 0); }}
}}
@keyframes fadeUp {{
    from {{ opacity:0; transform:translateY(6px); }}
    to   {{ opacity:1; transform:translateY(0);   }}
}}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def safe_get(path: str, params: dict = None):
    """GET from the API; returns None if the server is unreachable."""
    try:
        r = requests.get(f"{API_BASE}/{path}", params=params, timeout=3)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def metric_card(label: str, value: str, subtitle: str = "", color: str = None, accent: str = None) -> str:
    """
    Renders a dark metric card with a colored top accent bar.
    Returns raw HTML string — call via st.markdown(..., unsafe_allow_html=True).
    """
    color  = color  or C["text"]
    accent = accent or C["border"]
    return f"""
    <div style="
        background: linear-gradient(160deg, {C['bg_dark']} 0%, {C['bg_card']} 100%);
        border: 1px solid {C['border']};
        border-top: 3px solid {accent};
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4);
        animation: fadeUp 0.4s ease;
    ">
        <p style="color:{C['muted']}; font-size:10px; font-weight:700;
                  letter-spacing:0.12em; text-transform:uppercase; margin:0 0 10px;">
            {label}
        </p>
        <p style="color:{color}; font-size:32px; font-weight:700; margin:0;
                  font-family:'JetBrains Mono',monospace; line-height:1.1; letter-spacing:-0.02em;">
            {value}
        </p>
        {'<p style="color:'+C["dim"]+';\
            font-size:11px; margin:8px 0 0;">'+subtitle+'</p>' if subtitle else ''}
    </div>"""


def alert_card(alert: dict) -> str:
    """Renders a single fraud alert card with glowing red left border."""
    ts = ""
    if alert.get("timestamp"):
        try:
            ts = datetime.fromisoformat(alert["timestamp"]).strftime("%H:%M:%S")
        except Exception:
            ts = ""
    reason = (alert.get("reason") or "")[:90]
    amt    = float(alert.get("amount", 0))

    return f"""
    <div style="
        background: linear-gradient(135deg,
            rgba({rgb(C['red'])}, 0.08) 0%,
            rgba({rgb(C['red'])}, 0.03) 100%);
        border: 1px solid rgba({rgb(C['red'])}, 0.22);
        border-left: 4px solid {C['red']};
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 8px;
        animation: fadeUp 0.3s ease;
    ">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px;">
            <div style="flex:1; min-width:0;">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:5px; flex-wrap:wrap;">
                    <span style="color:{C['red_light']}; font-weight:700; font-size:12px;
                                 letter-spacing:0.06em;">🚨 FRAUD DETECTED</span>
                    <span style="color:{C['muted']}; font-size:11px;
                                 font-family:'JetBrains Mono',monospace;">
                        #{alert.get('transaction_id','?')}
                    </span>
                    <span style="color:{C['dim']}; font-size:11px;">{ts}</span>
                </div>
                <p style="color:{C['text']}; font-size:14px; font-weight:600; margin:0 0 3px;
                           white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                    {alert.get('merchant','?')} &nbsp;—&nbsp; ₹{amt:,.2f}
                </p>
                <p style="color:{C['muted']}; font-size:12px; margin:0 0 4px;">
                    User #{alert.get('user_id','?')} &nbsp;·&nbsp;
                    {alert.get('location','?')} &nbsp;·&nbsp;
                    {str(alert.get('device_id',''))[:22]}
                </p>
                <p style="color:{C['dim']}; font-size:11px; margin:0;
                           font-family:'JetBrains Mono',monospace;
                           white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                    {reason}
                </p>
            </div>
            <div style="text-align:center; flex-shrink:0;">
                <div style="
                    background: {C['red']};
                    color: white;
                    font-size:17px; font-weight:700;
                    font-family:'JetBrains Mono',monospace;
                    padding: 8px 10px; border-radius: 8px;
                    box-shadow: 0 0 14px rgba({rgb(C['red'])}, 0.45);
                    animation: pulse-red 2s infinite;
                    min-width: 56px; text-align:center;
                ">{alert.get('risk_score', 0) * 100:.0f}%</div>
                <div style="color:{C['dim']}; font-size:10px; margin-top:4px; letter-spacing:0.08em;">
                    RISK
                </div>
            </div>
        </div>
    </div>"""


def section_label(text: str) -> str:
    """Renders a small uppercase section heading."""
    return (f"<p style='color:{C['muted']}; font-size:10px; font-weight:700; "
            f"letter-spacing:0.12em; text-transform:uppercase; margin:0 0 12px;'>"
            f"{text}</p>")


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — Manual Transaction Test
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:4px 0 20px;">
        <p style="color:{C['teal']}; font-size:10px; font-weight:700;
                  letter-spacing:0.14em; text-transform:uppercase; margin:0;">
            FRAUDGUARD L3
        </p>
        <p style="color:{C['text']}; font-size:20px; font-weight:700; margin:4px 0 0;
                  letter-spacing:-0.01em;">
            Test Transaction
        </p>
        <p style="color:{C['dim']}; font-size:12px; margin:4px 0 0;">
            Manually fire a transaction through the ensemble model
        </p>
    </div>
    <hr>
    """, unsafe_allow_html=True)

    user_id   = st.number_input("User ID",        min_value=1,    value=1000, step=1)
    amount    = st.number_input("Amount (₹)",      min_value=1.0,  value=5000.0, step=500.0)
    merchant  = st.text_input( "Merchant",         value="Amazon")
    location  = st.text_input( "Location",         value="Mumbai")
    device_id = st.text_input( "Device ID",        value="android_245")

    if st.button("🔍 Run Detection"):
        payload = {
            "user_id":   int(user_id),
            "amount":    float(amount),
            "merchant":  merchant,
            "location":  location,
            "device_id": device_id,
        }
        with st.spinner("Running 3-model ensemble…"):
            try:
                resp = requests.post(f"{API_BASE}/predict", json=payload, timeout=10)
                if resp.status_code == 200:
                    st.session_state["test_result"]  = resp.json()
                    st.session_state["test_payload"] = payload
                else:
                    st.error(f"API returned {resp.status_code}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

    # ── Display last test result (persists across auto-refresh reruns) ──────
    if "test_result" in st.session_state:
        r    = st.session_state["test_result"]
        is_f = r.get("is_fraud", False)
        prob = r.get("fraud_probability", 0)

        banner_bg    = f"rgba({rgb(C['red'])}, 0.14)"    if is_f else f"rgba({rgb(C['teal'])}, 0.12)"
        banner_border= C["red"]                           if is_f else C["teal"]
        banner_color = C["red_light"]                     if is_f else C["green_light"]
        banner_icon  = "🚨 FRAUD"                         if is_f else "✅ NORMAL"

        st.markdown(f"""
        <div style="background:{banner_bg}; border:1px solid {banner_border};
                border-radius:10px; padding:14px; text-align:center; margin:14px 0;">
            <div style="color:{banner_color}; font-size:18px; font-weight:700;
                        letter-spacing:0.04em;">{banner_icon}</div>
            <div style="color:{banner_color}; font-size:30px; font-weight:700;
                        font-family:'JetBrains Mono',monospace; margin-top:4px;">
                {prob*100:.1f}%
            </div>
            <div style="color:{C['dim']}; font-size:11px; margin-top:4px;">
                fraud probability
            </div>
        </div>""", unsafe_allow_html=True)

        # Per-model scores
        scores = r.get("model_scores", {})
        st.markdown(f"""
        <div style="background:{C['bg_dark']}; border:1px solid {C['border']};
                border-radius:8px; padding:12px 14px; margin-bottom:12px;">
            <p style="color:{C['muted']}; font-size:10px; font-weight:700;
                      letter-spacing:0.12em; text-transform:uppercase; margin:0 0 10px;">
                MODEL BREAKDOWN
            </p>
            <div style="display:flex; flex-direction:column; gap:6px;
                        font-family:'JetBrains Mono',monospace; font-size:12px;">
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:{C['muted']};">IsolationForest</span>
                    <span style="color:{C['text']};">{scores.get('isolation_forest',0)*100:.1f}%</span>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:{C['muted']};">LocalOutlierFactor</span>
                    <span style="color:{C['text']};">{scores.get('local_outlier_factor',0)*100:.1f}%</span>
                </div>
                <div style="display:flex; justify-content:space-between; border-top:1px solid {C['border']}; padding-top:6px;">
                    <span style="color:{C['muted']};">LightGBM</span>
                    <span style="color:{C['text']};">{scores.get('lightgbm',0)*100:.1f}%</span>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        # SHAP top reasons
        reasons = r.get("top_reasons", [])
        if reasons:
            st.markdown(f"<p style='color:{C['muted']}; font-size:10px; font-weight:700; "
                        f"letter-spacing:0.12em; text-transform:uppercase; "
                        f"margin:0 0 8px;'>TOP SHAP DRIVERS</p>", unsafe_allow_html=True)
            for re in reasons:
                toward_fraud = re["direction"] == "toward_fraud"
                icon  = "▲" if toward_fraud else "▼"
                col   = C["red"] if toward_fraud else C["teal"]
                st.markdown(
                    f"<div style='font-family:\"JetBrains Mono\",monospace; font-size:11px; "
                    f"color:{col}; padding:3px 0;'>"
                    f"{icon} {re['feature']}: {abs(re['impact']):.4f}</div>",
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────────────────────────────────────

# ── Fetch all data ────────────────────────────────────────────────────────────
stats   = safe_get("stats")
api_ok  = stats is not None
trend   = safe_get("fraud-trend", {"limit": 80})
alerts  = safe_get("alerts",      {"limit": 8})
history = safe_get("history",     {"limit": 30})

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex; align-items:flex-start; justify-content:space-between;
            margin-bottom:28px; padding-bottom:18px; border-bottom:1px solid {C['border']};">
    <div>
        <h1 style="color:{C['text']}; font-size:24px; font-weight:700; margin:0;
                   letter-spacing:-0.02em;">
            🛡️ &nbsp;FraudGuard
        </h1>
        <p style="color:{C['muted']}; font-size:12px; margin:5px 0 0 0; line-height:1.5;">
            Ensemble Detection &nbsp;·&nbsp; IsolationForest + LOF + LightGBM
            &nbsp;·&nbsp; SHAP Explanations &nbsp;·&nbsp; 30-Feature Engineering
        </p>
    </div>
    <div style="display:flex; align-items:center; gap:12px; padding-top:4px;">
        <div style="text-align:right;">
            <p style="color:{C['dim']}; font-size:10px; margin:0; letter-spacing:0.06em;
                      text-transform:uppercase;">Last refresh</p>
            <p style="color:{C['muted']}; font-size:12px; margin:2px 0 0;
                      font-family:'JetBrains Mono',monospace;">
                {time.strftime('%H:%M:%S')}
            </p>
        </div>
        <div style="display:flex; align-items:center; gap:8px;
                    background:{C['bg_dark']}; border:1px solid {C['border']};
                    border-radius:20px; padding:7px 14px;">
            <div style="width:8px; height:8px; border-radius:50%;
                        background:{'#48BB78' if api_ok else C['red']};
                        {'animation:pulse 2.5s infinite;' if api_ok else 'animation:pulse-red 1s infinite;'}">
            </div>
            <span style="color:{'#48BB78' if api_ok else C['red_light']}; font-size:12px;
                         font-weight:600; letter-spacing:0.04em;">
                {'API LIVE' if api_ok else 'API OFFLINE'}
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── API offline banner ────────────────────────────────────────────────────────
if not api_ok:
    st.markdown(f"""
    <div style="background:rgba({rgb(C['red'])},0.09); border:1px solid {C['red']};
            border-radius:10px; padding:20px; text-align:center; margin-bottom:20px;">
        <p style="color:{C['red_light']}; font-size:16px; font-weight:700; margin:0;">
            ⚠️ &nbsp; API server is not reachable
        </p>
        <p style="color:{C['muted']}; font-size:13px; margin:8px 0 0;">
            Start it with:
            <code style="color:{C['teal_light']}; background:{C['bg_dark']};
                         padding:2px 8px; border-radius:4px; font-family:'JetBrains Mono',monospace;">
                uvicorn backend.main:app --reload
            </code>
        </p>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(4)
    st.rerun()

# ── Metric cards row ──────────────────────────────────────────────────────────
total  = stats.get("total_transactions",    0)
fraud  = stats.get("fraud_count",           0)
rate   = stats.get("fraud_rate_percent",    0.0)
high   = stats.get("high_risk_count",       0)
avg_r  = stats.get("avg_fraud_probability", 0.0)
avg_a  = stats.get("avg_transaction_amount",0.0)

# Fraud rate colour — red if above 8%, orange if 3–8%, green below 3%
rate_color = C["red"] if rate > 8 else (C["orange"] if rate > 3 else C["green"])

col1, col2, col3, col4, col5 = st.columns(5, gap="small")
with col1:
    st.markdown(metric_card(
        "Total Processed", f"{total:,}", "through ML pipeline",
        C["blue_light"], C["blue"]
    ), unsafe_allow_html=True)
with col2:
    st.markdown(metric_card(
        "Frauds Detected", f"{fraud:,}", f"out of {total:,} total",
        C["red_light"], C["red"]
    ), unsafe_allow_html=True)
with col3:
    st.markdown(metric_card(
        "Fraud Rate", f"{rate:.2f}%", "industry avg < 0.5%",
        rate_color, rate_color
    ), unsafe_allow_html=True)
with col4:
    st.markdown(metric_card(
        "High Risk (>75%)", f"{high:,}", "require immediate review",
        C["orange_light"], C["orange"]
    ), unsafe_allow_html=True)
with col5:
    st.markdown(metric_card(
        "Avg Risk Score", f"{avg_r:.3f}", f"Avg txn ₹{avg_a:,.0f}",
        C["teal_light"], C["teal"]
    ), unsafe_allow_html=True)

st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

# ── Charts row ────────────────────────────────────────────────────────────────
chart_col, donut_col = st.columns([3, 1], gap="medium")

# ── Fraud Probability Trend ───────────────────────────────────────────────────
with chart_col:
    st.markdown(section_label("Fraud probability trend — last 80 transactions"), unsafe_allow_html=True)

    if trend:
        tdf = pd.DataFrame(trend)

        # Map fraud_status to color for each data point
        point_colors = [
            C["red"] if s == "FRAUD" else C["teal"]
            for s in tdf["fraud_status"]
        ]
        point_sizes = [
            11 if s == "FRAUD" else 5.5
            for s in tdf["fraud_status"]
        ]

        fig = go.Figure()

        # Shaded threshold regions (drawn first so they appear behind data)
        fig.add_hrect(y0=0.75, y1=1.01,
                      fillcolor=C["red"],    opacity=0.05, line_width=0)
        fig.add_hrect(y0=0.45, y1=0.75,
                      fillcolor=C["orange"], opacity=0.04, line_width=0)
        fig.add_hrect(y0=0.0,  y1=0.45,
                      fillcolor=C["teal"],   opacity=0.03, line_width=0)

        # Dotted threshold lines
        for y, color, label in [
            (0.75, C["red"],    "HIGH"),
            (0.45, C["orange"], "MED"),
        ]:
            fig.add_hline(
                y=y, line_dash="dot",
                line_color=color, line_width=1, opacity=0.45,
                annotation_text=label,
                annotation_font=dict(color=color, size=10),
                annotation_position="right",
            )

        # Connecting line (neutral grey — data dots provide the color signal)
        fig.add_trace(go.Scatter(
            x=tdf["seq"], y=tdf["risk_score"],
            mode="lines",
            line=dict(color=C["border"], width=1.2),
            showlegend=False, hoverinfo="skip",
        ))

        # Scatter points — colored by fraud status, sized by severity
        fig.add_trace(go.Scatter(
            x=tdf["seq"],
            y=tdf["risk_score"],
            mode="markers",
            marker=dict(
                size=point_sizes,
                color=point_colors,
                line=dict(color=C["bg_deep"], width=1.5),
                opacity=0.92,
            ),
            hovertemplate=(
                "<b>Txn #%{customdata[0]}</b><br>"
                "Merchant : %{customdata[1]}<br>"
                "Amount   : ₹%{customdata[2]:,.2f}<br>"
                "Risk     : %{y:.3f}<br>"
                "<extra></extra>"
            ),
            customdata=list(
                zip(tdf["transaction_id"], tdf["merchant"], tdf["amount"])
            ),
            showlegend=False,
        ))

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor=C["bg_card"],
            font=dict(color=C["muted"], family="Inter", size=11),
            height=240,
            margin=dict(l=0, r=40, t=4, b=0),
            xaxis=dict(
                showgrid=False, zeroline=False,
                title=None,
                tickfont=dict(color=C["dim"], size=10),
            ),
            yaxis=dict(
                range=[-0.02, 1.05],
                showgrid=True, gridcolor=C["border"], gridwidth=0.5,
                zeroline=False,
                tickformat=".0%",
                tickfont=dict(color=C["dim"], size=10),
                title=None,
            ),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    else:
        st.markdown(f"""
        <div style="height:240px; background:{C['bg_card']}; border:1px solid {C['border']};
                border-radius:8px; display:flex; flex-direction:column;
                align-items:center; justify-content:center; gap:8px;">
            <span style="font-size:28px;">📡</span>
            <span style="color:{C['dim']}; font-size:13px;">
                Waiting for transactions — start the simulator
            </span>
        </div>""", unsafe_allow_html=True)

# ── Risk Distribution Donut ───────────────────────────────────────────────────
with donut_col:
    st.markdown(section_label("Risk distribution"), unsafe_allow_html=True)

    h_count = stats.get("high_risk_count",   0)
    m_count = stats.get("medium_risk_count", 0)
    l_count = stats.get("low_risk_count",    0)

    if h_count + m_count + l_count > 0:
        fig_pie = go.Figure(data=[go.Pie(
            labels=["High Risk", "Medium Risk", "Low Risk"],
            values=[h_count, m_count, l_count],
            hole=0.64,
            marker=dict(
                colors=[C["red"], C["orange"], C["teal"]],
                line=dict(color=C["bg_deep"], width=3),
            ),
            textfont=dict(color=C["text"], size=11),
            textposition="outside",
            hovertemplate="<b>%{label}</b><br>%{value} transactions<br>%{percent}<extra></extra>",
        )])
        fig_pie.add_annotation(
            text=f"<b>{total:,}</b><br><span style='font-size:10px'>TOTAL</span>",
            x=0.5, y=0.5,
            font=dict(color=C["text"], size=15, family="Inter"),
            showarrow=False,
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=C["muted"], family="Inter"),
            height=240,
            margin=dict(l=0, r=0, t=4, b=0),
            showlegend=True,
            legend=dict(
                font=dict(color=C["muted"], size=10),
                bgcolor="rgba(0,0,0,0)",
                x=0.5, xanchor="center", y=-0.08, orientation="h",
            ),
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown(f"""
        <div style="height:240px; background:{C['bg_card']}; border:1px solid {C['border']};
                border-radius:8px; display:flex; align-items:center; justify-content:center;">
            <span style="color:{C['dim']}; font-size:13px;">No risk data yet</span>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

# ── Alerts + History ──────────────────────────────────────────────────────────
alert_col, table_col = st.columns([1, 1], gap="medium")

# ── Active Fraud Alerts ───────────────────────────────────────────────────────
with alert_col:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:14px;">
        <div style="width:9px; height:9px; border-radius:50%; background:{C['red']};
                    animation: pulse-red 1.8s infinite;"></div>
        {section_label("Active Fraud Alerts").replace("<p style=", "<p style='display:inline;").replace("</p>", "")}
    </div>""", unsafe_allow_html=True)

    if alerts:
        for al in alerts:
            st.markdown(alert_card(al), unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:{C['bg_dark']}; border:1px solid {C['border']};
                border-radius:10px; padding:40px 20px; text-align:center;">
            <p style="font-size:28px; margin:0;">✅</p>
            <p style="color:{C['green_light']}; font-size:14px; font-weight:600; margin:10px 0 4px;">
                No Fraud Alerts
            </p>
            <p style="color:{C['dim']}; font-size:12px; margin:0;">
                System is monitoring all transactions
            </p>
        </div>""", unsafe_allow_html=True)

# ── Transaction History Table ─────────────────────────────────────────────────
with table_col:
    st.markdown(section_label("Recent Transactions (last 30)"), unsafe_allow_html=True)

    if history:
        hdf = pd.DataFrame(history)

        # Build display DataFrame with formatted columns
        display_df = pd.DataFrame({
            "Time":     pd.to_datetime(hdf["timestamp"]).dt.strftime("%H:%M:%S"),
            "Txn":      "#" + hdf["transaction_id"].astype(str),
            "User":     "U" + hdf["user_id"].astype(str),
            "Amount":   hdf["amount"].apply(lambda x: f"₹{x:,.0f}"),
            "Merchant": hdf["merchant"],
            "Location": hdf["location"],
            "Risk %":   hdf["risk_score"].apply(lambda x: f"{x*100:.1f}%"),
            "Status":   hdf["fraud_status"].apply(
                lambda x: "🔴 FRAUD" if x == "FRAUD" else "🟢 SAFE"
            ),
        })

        def style_status(val: str) -> str:
            if "FRAUD" in str(val):
                return f"color: {C['red_light']}; font-weight: 700;"
            return f"color: {C['green_light']};"

        def style_risk(val: str) -> str:
            try:
                v = float(str(val).replace("%", "")) / 100
                if v >= 0.75:
                    return f"color: {C['red_light']}; font-weight: 700;"
                if v >= 0.45:
                    return f"color: {C['orange_light']};"
                return f"color: {C['teal_light']};"
            except Exception:
                return ""

        # pandas 2.1+ uses .map() instead of deprecated .applymap()
        styled = (
            display_df.style
            .map(style_status, subset=["Status"])
            .map(style_risk,   subset=["Risk %"])
            .set_properties(**{
                "background-color": C["bg_dark"],
                "color":            C["text"],
                "font-size":        "12px",
                "border-color":     C["border"],
            })
            .set_table_styles([{
                "selector": "thead th",
                "props": [
                    ("background-color", C["bg_card"]),
                    ("color",            C["muted"]),
                    ("font-size",        "10px"),
                    ("font-weight",      "700"),
                    ("letter-spacing",   "0.1em"),
                    ("text-transform",   "uppercase"),
                    ("border-color",     C["border"]),
                ],
            }])
        )

        st.dataframe(styled, use_container_width=True, height=390, hide_index=True)

    else:
        st.markdown(f"""
        <div style="background:{C['bg_dark']}; border:1px solid {C['border']};
                border-radius:10px; height:390px; display:flex;
                flex-direction:column; align-items:center; justify-content:center; gap:10px;">
            <span style="font-size:36px;">📊</span>
            <p style="color:{C['muted']}; font-size:14px; font-weight:600; margin:0;">
                No transactions yet
            </p>
            <p style="color:{C['dim']}; font-size:12px; margin:0; text-align:center; max-width:220px;">
                Run the simulator to start seeing real-time detections
            </p>
            <code style="color:{C['teal_light']}; background:{C['bg_card']};
                         padding:4px 10px; border-radius:4px; font-size:11px;
                         font-family:'JetBrains Mono',monospace; margin-top:4px;">
                python -m simulation.transaction_simulator
            </code>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# AUTO-REFRESH every 3 seconds
# st.rerun() re-executes this entire script from the top.
# session_state preserves test_result and test_payload across reruns.
# ─────────────────────────────────────────────────────────────────────────────
time.sleep(3)
st.rerun()
