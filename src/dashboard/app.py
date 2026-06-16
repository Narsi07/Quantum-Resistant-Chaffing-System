"""
Post-Quantum Metadata Obfuscation — Streamlit Dashboard

Live visualization of:
  - Real vs Dummy packet traffic
  - Packet size distribution
  - Shannon entropy per packet
  - GAN discriminability score
  - Multipath routing distribution
  - ANFIS training status
"""
import streamlit as st
import pandas as pd
import numpy as np
import time
import threading
import queue
import sys
import os
import math

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.obfuscation.engine import ObfuscationEngine
from src.adversarial.discriminator import AdversarialEvaluator

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QR-Chaff Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .metric-card {
        background: linear-gradient(135deg, #1a1f2e, #252b3b);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .metric-value { font-size: 2rem; font-weight: bold; color: #7c3aed; }
    .metric-label { font-size: 0.85rem; color: #9ca3af; }
    .status-badge-running {
        background: #065f46; color: #34d399;
        padding: 4px 12px; border-radius: 20px;
        font-size: 0.8rem; font-weight: bold;
    }
    .status-badge-stopped {
        background: #7f1d1d; color: #f87171;
        padding: 4px 12px; border-radius: 20px;
        font-size: 0.8rem; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────
if "packet_queue" not in st.session_state:
    st.session_state.packet_queue = queue.Queue()
if "engine_running" not in st.session_state:
    st.session_state.engine_running = False
if "traffic_data" not in st.session_state:
    st.session_state.traffic_data = []
if "evaluator" not in st.session_state:
    st.session_state.evaluator = AdversarialEvaluator()
if "anfis_status" not in st.session_state:
    st.session_state.anfis_status = "Checking..."

MAX_POINTS = 200


def packet_callback(payload: bytes, meta: dict):
    """Called by engine for every packet sent."""
    st.session_state.evaluator.add_packet(
        size=meta["size"],
        iat_ms=meta["iat_ms"],
        is_dummy=meta["is_dummy"],
    )
    st.session_state.packet_queue.put({
        "timestamp": time.time(),
        "size": meta["size"],
        "type": "Dummy" if meta["is_dummy"] else "Real",
        "entropy": meta["entropy"],
        "iat_ms": meta["iat_ms"],
        "path_id": meta.get("path_id", 0),
        "pq_mode": meta.get("pq_mode", "simulation"),
    })


@st.cache_resource
def get_engine():
    """Singleton engine instance."""
    return ObfuscationEngine(output_callback=packet_callback)


@st.cache_resource
def check_anfis_status():
    """Check if ANFIS weights exist."""
    from pathlib import Path
    models_dir = Path(__file__).parent.parent / "neuro_fuzzy" / "models"
    size_ok = (models_dir / "anfis_size.pt").exists()
    iat_ok = (models_dir / "anfis_iat.pt").exists()
    if size_ok and iat_ok:
        return "✅ Pre-trained weights loaded"
    return "⚠️ No weights found — using random init (run train_anfis.py)"


engine = get_engine()
anfis_status = check_anfis_status()

# ── Header ─────────────────────────────────────────────────────────────────
st.title("🛡️ Quantum-Resistant Chaffing System")
st.markdown("**Post-Quantum Metadata Obfuscation Layer** · Neuro-Fuzzy Traffic Synthesis")

pq_mode = "real (liboqs)" if engine.kem.is_enabled() else "⚠️ simulation mode"
col_h1, col_h2, col_h3 = st.columns(3)
col_h1.info(f"🔐 **PQ Crypto:** {pq_mode}")
col_h2.info(f"🤖 **ANFIS:** {anfis_status}")
engine_badge = (
    '<span class="status-badge-running">● RUNNING</span>'
    if st.session_state.engine_running
    else '<span class="status-badge-stopped">■ STOPPED</span>'
)
col_h3.markdown(f"**Engine Status:** {engine_badge}", unsafe_allow_html=True)

st.divider()

# ── Sidebar controls ───────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Control Panel")

    if st.button("▶ Start Engine", use_container_width=True, type="primary"):
        if not st.session_state.engine_running:
            engine.start()
            st.session_state.engine_running = True
            st.success("Engine started!")

    if st.button("⏹ Stop Engine", use_container_width=True):
        if st.session_state.engine_running:
            engine.stop()
            st.session_state.engine_running = False
            st.warning("Engine stopped.")

    st.divider()
    st.subheader("📨 Send Data")
    user_msg = st.text_input("Message to send", placeholder="Enter secret message...")
    if st.button("Send Encrypted", use_container_width=True):
        if user_msg:
            engine.send_data(user_msg.encode())
            st.sidebar.success(f"Queued: {len(user_msg)} bytes (AES-256-GCM)")

    st.divider()
    st.subheader("ℹ️ Engine Stats")
    stats = engine.get_stats()
    st.metric("Total Packets", stats["total_packets"])
    st.metric("Total Bytes", f"{stats['total_bytes']:,}")
    st.metric("Dummy Ratio", f"{stats['dummy_ratio']*100:.1f}%")

# ── Drain the queue ────────────────────────────────────────────────────────
while not st.session_state.packet_queue.empty():
    st.session_state.traffic_data.append(st.session_state.packet_queue.get())

if len(st.session_state.traffic_data) > MAX_POINTS:
    st.session_state.traffic_data = st.session_state.traffic_data[-MAX_POINTS:]

# ── Live Metrics Row ───────────────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)

if st.session_state.traffic_data:
    df = pd.DataFrame(st.session_state.traffic_data)
    total = len(df)
    real_c = df[df["type"] == "Real"].shape[0]
    dummy_c = df[df["type"] == "Dummy"].shape[0]
    avg_entropy = df["entropy"].mean()
    disc_score = st.session_state.evaluator.get_discriminability()

    m1.metric("📦 Total Packets", total)
    m2.metric("🔵 Real", real_c)
    m3.metric("🔴 Dummy", dummy_c, f"{dummy_c/total*100:.0f}%")
    m4.metric("🌀 Avg Entropy", f"{avg_entropy:.3f} bits/B")
    m5.metric(
        "🎯 GAN Discriminability",
        f"{disc_score:.3f}",
        delta=None,
        help="0=perfect obfuscation, 1=easily detected",
    )
else:
    m1.metric("📦 Total Packets", 0)
    m2.metric("🔵 Real", 0)
    m3.metric("🔴 Dummy", 0)
    m4.metric("🌀 Avg Entropy", "—")
    m5.metric("🎯 Discriminability", "—")

st.divider()

# ── Charts ──────────────────────────────────────────────────────────────────
if st.session_state.traffic_data and len(st.session_state.traffic_data) >= 2:
    df = pd.DataFrame(st.session_state.traffic_data)
    df["time_rel"] = (df["timestamp"] - df["timestamp"].min()).round(2)

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📈 Traffic Flow", "📊 Entropy", "🔀 Multipath", "📋 Packet Log"]
    )

    with tab1:
        st.subheader("Packet Size over Time (Real vs Dummy)")
        st.scatter_chart(df, x="time_rel", y="size", color="type", height=300)

    with tab2:
        st.subheader("Shannon Entropy per Packet")
        st.markdown(
            "Entropy ≈ 8 bits/byte = truly random data (ideal for dummy packets). "
            "Real encrypted data should also show high entropy."
        )
        entropy_df = df[["time_rel", "entropy", "type"]].copy()
        st.line_chart(entropy_df.set_index("time_rel")["entropy"], height=300)

        col_e1, col_e2 = st.columns(2)
        col_e1.metric("Real Entropy", f"{df[df['type']=='Real']['entropy'].mean():.3f}" if real_c else "—")
        col_e2.metric("Dummy Entropy", f"{df[df['type']=='Dummy']['entropy'].mean():.3f}" if dummy_c else "—")

    with tab3:
        st.subheader("Multipath Routing Distribution")
        st.markdown("Traffic is randomly split across 3 network paths to resist correlation attacks.")
        path_counts = df["path_id"].value_counts().reset_index()
        path_counts.columns = ["Path", "Packets"]
        path_counts["Path"] = path_counts["Path"].apply(lambda x: f"Path {x}")
        st.bar_chart(path_counts.set_index("Path"), height=300)

    with tab4:
        st.subheader("Live Packet Log (Last 20)")
        log_df = df[["time_rel", "type", "size", "entropy", "iat_ms", "path_id"]].tail(20)
        log_df = log_df.sort_values("time_rel", ascending=False)
        log_df.columns = ["Time (s)", "Type", "Size (B)", "Entropy", "IAT (ms)", "Path"]
        st.dataframe(log_df, use_container_width=True)

else:
    st.info("▶ Start the engine to see live traffic visualization.")

# ── Auto-refresh ────────────────────────────────────────────────────────────
if st.session_state.engine_running:
    time.sleep(1)
    st.rerun()
