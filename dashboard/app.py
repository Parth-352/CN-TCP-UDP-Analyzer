"""
NetPulse Streamlit Dashboard.

Displays TCP vs UDP performance metrics:
1. Per-packet size side-by-side metric comparison table
2. 5 Matplotlib visualization charts (Transmission Time, Throughput, RTT, Loss, Summary Grid)
3. Smart Protocol Recommender engine tab
4. Interactive sidebar to trigger background experiment runs
"""

import os
import subprocess
import sys
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Project root path setup
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from recommender.profiles import PROFILES
from recommender.engine import recommend

CSV_PATH = os.path.join(ROOT, "data", "results.csv")
RUNNER_PATH = os.path.join(ROOT, "run_experiments.py")

# Page Configuration
st.set_page_config(
    page_title="NetPulse — TCP vs UDP Analyzer",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ NetPulse — TCP vs UDP Performance Analyzer")
st.caption("Real-Time Application-Layer Transport Protocol Metrics & Smart Recommendation Engine")


def load_data():
    """Load results.csv into a pandas DataFrame."""
    if not os.path.exists(CSV_PATH):
        return None
    try:
        df = pd.read_csv(CSV_PATH)
        if df.empty:
            return None
        return df
    except Exception as e:
        st.error(f"Failed to read dataset: {e}")
        return None


def run_experiment_subprocess(fresh: bool = False):
    """Trigger run_experiments.py in a subprocess."""
    cmd = [sys.executable, RUNNER_PATH]
    if fresh:
        cmd.append("--fresh")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, proc.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


# ---------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------
st.sidebar.header("🛠 Experiment Controls")

if st.sidebar.button("🚀 Run Experiments (Append)", use_container_width=True):
    with st.spinner("Running TCP and UDP experiments..."):
        success, output = run_experiment_subprocess(fresh=False)
        if success:
            st.sidebar.success("Experiments complete!")
            st.rerun()
        else:
            st.sidebar.error("Experiment run failed.")
            st.sidebar.text_area("Error Log", output, height=200)

if st.sidebar.button("🔄 Run Fresh (Wipe & Re-run)", use_container_width=True):
    with st.spinner("Wiping results and re-running experiments..."):
        success, output = run_experiment_subprocess(fresh=True)
        if success:
            st.sidebar.success("Fresh run complete!")
            st.rerun()
        else:
            st.sidebar.error("Fresh run failed.")
            st.sidebar.text_area("Error Log", output, height=200)

st.sidebar.markdown("---")
st.sidebar.markdown("### About NetPulse")
st.sidebar.info(
    "NetPulse measures real-world transport protocol metrics "
    "(RTT, Throughput, Loss, Jitter) across varied packet sizes "
    "using custom socket clients & servers."
)

# ---------------------------------------------------------
# Data Loading & Main Content
# ---------------------------------------------------------
df = load_data()

tab1, tab2, tab3 = st.tabs([
    "📊 Metric Tables & Comparison",
    "📈 Performance Graphs",
    "🎯 Smart Protocol Recommender",
])

# ---------------------------------------------------------
# TAB 1: Comparison Table View
# ---------------------------------------------------------
with tab1:
    if df is None:
        st.warning("⚠️ No experiment data found (`data/results.csv` missing or empty).")
        st.info("Click **'🚀 Run Experiments'** in the sidebar to execute the benchmark suite.")
    else:
        st.subheader("Protocol Metric Comparison")
        latest_df = df.groupby(["Protocol", "PacketSize"], as_index=False).last()

        packet_sizes = sorted(latest_df["PacketSize"].unique())
        selected_size = st.selectbox(
            "Select Packet Size (bytes):",
            packet_sizes,
            index=0 if len(packet_sizes) > 0 else None,
        )

        if selected_size:
            size_df = latest_df[latest_df["PacketSize"] == selected_size]

            tcp_row = size_df[size_df["Protocol"] == "TCP"]
            udp_row = size_df[size_df["Protocol"] == "UDP"]

            metrics_names = [
                ("Transmission Time (sec)", "TransmissionTime", "{:.6f}"),
                ("Average RTT (ms)", "AvgRTT", "{:.4f}"),
                ("Throughput (Mbps)", "Throughput", "{:.4f}"),
                ("Packet Loss (%)", "PacketLoss", "{:.2f}%"),
                ("Jitter (ms)", "Jitter", "{:.4f}"),
            ]

            comp_rows = []
            for label, col, fmt in metrics_names:
                tcp_val = tcp_row[col].values[0] if not tcp_row.empty else float("nan")
                udp_val = udp_row[col].values[0] if not udp_row.empty else float("nan")

                if "%" in fmt:
                    tcp_str = f"{tcp_val:.2f}%" if pd.notnull(tcp_val) else "N/A"
                    udp_str = f"{udp_val:.2f}%" if pd.notnull(udp_val) else "N/A"
                else:
                    tcp_str = fmt.format(tcp_val) if pd.notnull(tcp_val) else "N/A"
                    udp_str = fmt.format(udp_val) if pd.notnull(udp_val) else "N/A"

                comp_rows.append({
                    "Metric": label,
                    "TCP": tcp_str,
                    "UDP": udp_str,
                })

            comp_df = pd.DataFrame(comp_rows)
            st.table(comp_df.set_index("Metric"))

        st.markdown("### Raw Results Dataset")
        st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------
# TAB 2: Graphs View (Matplotlib)
# ---------------------------------------------------------
with tab2:
    if df is None:
        st.warning("⚠️ No experiment data available for graphing.")
    else:
        st.subheader("Transport Protocol Visual Benchmarks")
        latest_df = df.groupby(["Protocol", "PacketSize"], as_index=False).last()

        tcp_df = latest_df[latest_df["Protocol"] == "TCP"].sort_values("PacketSize")
        udp_df = latest_df[latest_df["Protocol"] == "UDP"].sort_values("PacketSize")

        plt.style.use("seaborn-v0_8-whitegrid")

        # Graph 1: Transmission Time vs Packet Size
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        ax1.plot(tcp_df["PacketSize"], tcp_df["TransmissionTime"], "o-", label="TCP", color="#1f77b4", linewidth=2)
        ax1.plot(udp_df["PacketSize"], udp_df["TransmissionTime"], "s--", label="UDP", color="#ff7f0e", linewidth=2)
        ax1.set_title("Packet Size vs Transmission Time (seconds)", fontsize=12, fontweight="bold")
        ax1.set_xlabel("Packet Size (bytes)")
        ax1.set_ylabel("Transmission Time (sec)")
        ax1.legend()
        ax1.grid(True, linestyle="--", alpha=0.6)
        st.pyplot(fig1)

        col_left, col_right = st.columns(2)

        # Graph 2: Throughput vs Packet Size
        with col_left:
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            ax2.plot(tcp_df["PacketSize"], tcp_df["Throughput"], "o-", label="TCP", color="#2ca02c", linewidth=2)
            ax2.plot(udp_df["PacketSize"], udp_df["Throughput"], "s--", label="UDP", color="#d62728", linewidth=2)
            ax2.set_title("Packet Size vs Throughput (Mbps)", fontsize=11, fontweight="bold")
            ax2.set_xlabel("Packet Size (bytes)")
            ax2.set_ylabel("Throughput (Mbps)")
            ax2.legend()
            ax2.grid(True, linestyle="--", alpha=0.6)
            st.pyplot(fig2)

        # Graph 3: RTT vs Packet Size
        with col_right:
            fig3, ax3 = plt.subplots(figsize=(6, 4))
            ax3.plot(tcp_df["PacketSize"], tcp_df["AvgRTT"], "o-", label="TCP", color="#9467bd", linewidth=2)
            ax3.plot(udp_df["PacketSize"], udp_df["AvgRTT"], "s--", label="UDP", color="#8c564b", linewidth=2)
            ax3.set_title("Packet Size vs Average RTT (ms)", fontsize=11, fontweight="bold")
            ax3.set_xlabel("Packet Size (bytes)")
            ax3.set_ylabel("Avg RTT (ms)")
            ax3.legend()
            ax3.grid(True, linestyle="--", alpha=0.6)
            st.pyplot(fig3)

        # Graph 4: Packet Loss vs Packet Size
        fig4, ax4 = plt.subplots(figsize=(8, 4))
        ax4.bar(
            [p - 15 for p in tcp_df["PacketSize"]],
            tcp_df["PacketLoss"],
            width=30,
            label="TCP Loss (%)",
            color="#1f77b4",
            alpha=0.8,
        )
        ax4.bar(
            [p + 15 for p in udp_df["PacketSize"]],
            udp_df["PacketLoss"],
            width=30,
            label="UDP Loss (%)",
            color="#e377c2",
            alpha=0.8,
        )
        ax4.set_title("Packet Loss (%) vs Packet Size", fontsize=11, fontweight="bold")
        ax4.set_xlabel("Packet Size (bytes)")
        ax4.set_ylabel("Loss (%)")
        ax4.set_xticks(sorted(latest_df["PacketSize"].unique()))
        ax4.legend()
        ax4.grid(True, linestyle="--", alpha=0.6)
        st.pyplot(fig4)

        # Graph 5: Combined 2x2 Multi-Panel Grid Summary
        st.markdown("### Combined Performance Dashboard Grid")
        fig5, axes = plt.subplots(2, 2, figsize=(10, 8))

        # Panel 1: Throughput
        axes[0, 0].plot(tcp_df["PacketSize"], tcp_df["Throughput"], "o-", label="TCP", color="#1f77b4")
        axes[0, 0].plot(udp_df["PacketSize"], udp_df["Throughput"], "s--", label="UDP", color="#ff7f0e")
        axes[0, 0].set_title("Throughput (Mbps)")
        axes[0, 0].set_xlabel("Packet Size")
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.5)

        # Panel 2: Latency (RTT)
        axes[0, 1].plot(tcp_df["PacketSize"], tcp_df["AvgRTT"], "o-", label="TCP", color="#1f77b4")
        axes[0, 1].plot(udp_df["PacketSize"], udp_df["AvgRTT"], "s--", label="UDP", color="#ff7f0e")
        axes[0, 1].set_title("Average RTT (ms)")
        axes[0, 1].set_xlabel("Packet Size")
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.5)

        # Panel 3: Jitter
        axes[1, 0].plot(tcp_df["PacketSize"], tcp_df["Jitter"], "o-", label="TCP", color="#1f77b4")
        axes[1, 0].plot(udp_df["PacketSize"], udp_df["Jitter"], "s--", label="UDP", color="#ff7f0e")
        axes[1, 0].set_title("Jitter (ms)")
        axes[1, 0].set_xlabel("Packet Size")
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.5)

        # Panel 4: Transmission Time
        axes[1, 1].plot(tcp_df["PacketSize"], tcp_df["TransmissionTime"], "o-", label="TCP", color="#1f77b4")
        axes[1, 1].plot(udp_df["PacketSize"], udp_df["TransmissionTime"], "s--", label="UDP", color="#ff7f0e")
        axes[1, 1].set_title("Transmission Time (s)")
        axes[1, 1].set_xlabel("Packet Size")
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.5)

        plt.tight_layout()
        st.pyplot(fig5)

# ---------------------------------------------------------
# TAB 3: Protocol Recommendation Engine
# ---------------------------------------------------------
with tab3:
    st.subheader("🎯 Rule-Based Protocol Recommendation Engine")
    st.write(
        "Select an application workload profile to analyze requirement sensitivity "
        "and get an automated transport protocol recommendation."
    )

    profile_options = {key: val["name"] for key, val in PROFILES.items()}
    selected_key = st.selectbox(
        "Choose Application Workload Profile:",
        options=list(profile_options.keys()),
        format_func=lambda k: f"{profile_options[k]} ({k})",
    )

    profile = PROFILES[selected_key]

    st.markdown(f"**Description:** {profile['description']}")

    # Display weights breakdown
    w = profile["weights"]
    w_col1, w_col2, w_col3, w_col4 = st.columns(4)
    w_col1.metric("Latency Sensitivity", f"{w['latency_sensitivity'] * 100:.0f}%")
    w_col2.metric("Jitter Sensitivity", f"{w['jitter_sensitivity'] * 100:.0f}%")
    w_col3.metric("Loss Tolerance", f"{w['loss_tolerance'] * 100:.0f}%")
    w_col4.metric("Reliability Need", f"{w['reliability_need'] * 100:.0f}%")

    st.markdown("---")

    # Extract metrics if available
    metrics = {}
    if df is not None:
        latest_df = df.groupby(["Protocol", "PacketSize"], as_index=False).last()
        tcp_df = latest_df[latest_df["Protocol"] == "TCP"]
        udp_df = latest_df[latest_df["Protocol"] == "UDP"]

        if not tcp_df.empty and not udp_df.empty:
            metrics["TCP"] = {
                "avg_rtt_ms": tcp_df["AvgRTT"].mean(),
                "packet_loss_pct": tcp_df["PacketLoss"].mean(),
                "jitter_ms": tcp_df["Jitter"].mean(),
            }
            metrics["UDP"] = {
                "avg_rtt_ms": udp_df["AvgRTT"].mean(),
                "packet_loss_pct": udp_df["PacketLoss"].mean(),
                "jitter_ms": udp_df["Jitter"].mean(),
            }

    rec = recommend(metrics, profile)

    # Recommendation Card Display
    st.markdown("### Recommendation Summary")

    if rec["protocol"] == "UDP":
        st.success(
            f"⚡ Recommended Protocol: **UDP** (Confidence: **{rec['confidence_pct']}%**)"
        )
    else:
        st.info(
            f"🔒 Recommended Protocol: **TCP** (Confidence: **{rec['confidence_pct']}%**)"
        )

    score_col1, score_col2 = st.columns(2)
    score_col1.metric("TCP Score", f"{rec['tcp_score']} / 100")
    score_col2.metric("UDP Score", f"{rec['udp_score']} / 100")

    st.markdown("#### Key Decision Factors:")
    for reason in rec["reasons"]:
        st.markdown(f"- {reason}")
