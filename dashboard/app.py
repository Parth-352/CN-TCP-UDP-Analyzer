"""
NetPulse Streamlit Dashboard.

Displays TCP vs UDP performance metrics:
1. Per-packet size side-by-side metric comparison table
2. 5 Matplotlib visualization charts (Transmission Time, Throughput, RTT, Loss, Summary Grid)
3. Smart Protocol Recommender engine tab
4. Wireshark PCAP Packet Capture Inspector tab
5. Interactive sidebar to trigger background experiment runs
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
from analyzer.pcap_parser import parse_pcap_data, pcap_to_metrics, load_config

CSV_PATH = os.path.join(ROOT, "data", "results.csv")
RUNNER_PATH = os.path.join(ROOT, "run_experiments.py")

# Page Configuration
st.set_page_config(
    page_title="NetPulse — TCP vs UDP Analyzer",
    layout="wide",
)

st.title("NetPulse — TCP vs UDP Performance Analyzer")
st.caption("Real-Time Application-Layer Transport Protocol Metrics, Packet Capture & Recommendation Engine")


def load_data(uploaded_file=None):
    """Load the uploaded results CSV, or fall back to the saved dataset."""
    try:
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
        elif os.path.exists(CSV_PATH):
            df = pd.read_csv(CSV_PATH)
        else:
            return None

        if df.empty:
            return None

        required_columns = {
            "Protocol",
            "PacketSize",
            "TransmissionTime",
            "AvgRTT",
            "Throughput",
            "PacketLoss",
            "Jitter",
        }
        missing_columns = sorted(required_columns - set(df.columns))
        if missing_columns:
            st.error(
                "The results CSV is missing required columns: "
                + ", ".join(missing_columns)
            )
            return None

        for column in required_columns - {"Protocol"}:
            df[column] = pd.to_numeric(df[column], errors="coerce")
        df["Protocol"] = df["Protocol"].astype(str).str.upper().str.strip()
        df = df[df["Protocol"].isin(["TCP", "UDP"])].dropna(
            subset=[
                "PacketSize",
                "TransmissionTime",
                "AvgRTT",
                "Throughput",
                "PacketLoss",
                "Jitter",
            ]
        )
        if df.empty:
            st.error("The results CSV has no valid TCP or UDP metric rows.")
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


def clear_dataset():
    """Completely wipe data/results.csv file entries."""
    try:
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        headers = "Protocol,PacketSize,Packets,TransmissionTime,AvgRTT,Throughput,PacketLoss,Jitter,Timestamp\n"
        with open(CSV_PATH, "w", newline="") as f:
            f.write(headers)
        return True
    except Exception as e:
        return False


# ---------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------
st.sidebar.header("Benchmark Controls")

if st.sidebar.button(
    "Start Fresh Benchmark",
    use_container_width=True,
    help="Wipe dataset and run a new benchmark suite.",
):
    with st.spinner("Running fresh benchmark..."):
        success, output = run_experiment_subprocess(fresh=True)
        if success:
            st.sidebar.success("Fresh benchmark complete!")
            st.rerun()
        else:
            st.sidebar.error("Fresh benchmark failed.")
            st.sidebar.text_area("Error Log", output, height=150)

if st.sidebar.button(
    "Run Additional Benchmark",
    use_container_width=True,
    help="Keep existing data and append new runs.",
):
    with st.spinner("Running additional benchmark..."):
        success, output = run_experiment_subprocess(fresh=False)
        if success:
            st.sidebar.success("Additional benchmark complete!")
            st.rerun()
        else:
            st.sidebar.error("Additional benchmark failed.")
            st.sidebar.text_area("Error Log", output, height=150)

if st.sidebar.button(
    "Clear Dataset",
    use_container_width=True,
    help="Wipe all stored dataset entries.",
):
    if clear_dataset():
        st.sidebar.success("Dataset wiped!")
        st.rerun()
    else:
        st.sidebar.error("Failed to wipe dataset.")

# ---------------------------------------------------------
# Data Loading & Main Content
# ---------------------------------------------------------
pcap_metrics_df = st.session_state.get("pcap_metrics_df")
pcap_source_name = st.session_state.get("pcap_source_name")
df = pcap_metrics_df if pcap_metrics_df is not None and not pcap_metrics_df.empty else None

tab1, tab2, tab3, tab4 = st.tabs([
    "Metric Tables & Comparison",
    "Performance Graphs",
    "Smart Protocol Recommender",
    "Wireshark PCAP Inspector",
])

# ---------------------------------------------------------
# TAB 1: Comparison Table View
# ---------------------------------------------------------
with tab1:
    st.caption(
        f"Data source: Tab 4 PCAP ({pcap_source_name})."
        if pcap_source_name
        else "Upload a PCAP in Tab 4 to populate this tab."
    )
    if df is None:
        st.warning("No PCAP-derived data is available yet.")
        st.info("Upload a Wireshark `.pcap` or `.pcapng` file in Tab 4.")
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
    st.caption("Graphs use metrics derived from the PCAP uploaded in Tab 4.")
    if df is None:
        st.warning("No PCAP-derived data is available for graphing.")
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
    st.caption("Recommendations use metrics derived from the PCAP uploaded in Tab 4.")
    st.subheader("Rule-Based Protocol Recommendation Engine")
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
            f"Recommended Protocol: **UDP** (Confidence: **{rec['confidence_pct']}%**)"
        )
    else:
        st.info(
            f"Recommended Protocol: **TCP** (Confidence: **{rec['confidence_pct']}%**)"
        )

    score_col1, score_col2 = st.columns(2)
    score_col1.metric("TCP Score", f"{rec['tcp_score']} / 100")
    score_col2.metric("UDP Score", f"{rec['udp_score']} / 100")

    st.markdown("#### Key Decision Factors:")
    for reason in rec["reasons"]:
        st.markdown(f"- {reason}")

# ---------------------------------------------------------
# TAB 4: Wireshark PCAP Inspector
# ---------------------------------------------------------
with tab4:
    st.subheader("Wireshark PCAP Packet Capture Inspector")
    st.caption("Offline Scapy-based Packet Capture Parsing & TCP 3-Way Handshake Detection")

    cfg = load_config()
    default_port = cfg.get("server_port", 5001)

    # Controls Layout: Upload & Port Filter
    ctrl_col1, ctrl_col2 = st.columns([3, 1])

    with ctrl_col1:
        uploaded_pcap = st.file_uploader(
            "Upload Custom PCAP File (.pcap, .pcapng)",
            type=["pcap", "pcapng"],
            help="Upload any Wireshark capture file to analyze packets and TCP handshakes.",
        )

    with ctrl_col2:
        target_port = st.number_input(
            "Port Filter (0 = All):",
            min_value=0,
            max_value=65535,
            value=default_port,
            help="Filter packets by target port (set to 0 to inspect all ports)",
        )

    # Determine PCAP source file
    UPLOADED_PCAP_PATH = os.path.join(ROOT, "data", "uploaded_capture.pcap")
    pcap_target = None

    if uploaded_pcap is not None:
        os.makedirs(os.path.dirname(UPLOADED_PCAP_PATH), exist_ok=True)
        with open(UPLOADED_PCAP_PATH, "wb") as f:
            f.write(uploaded_pcap.getbuffer())
        pcap_target = UPLOADED_PCAP_PATH
        st.success(f"Analyzing uploaded PCAP: **{uploaded_pcap.name}** ({uploaded_pcap.size} bytes)")
    elif os.path.exists(os.path.join(ROOT, "data", "capture.pcap")):
        pcap_target = os.path.join(ROOT, "data", "capture.pcap")
    elif os.path.exists(os.path.join(ROOT, "data", "capture.pcapng")):
        pcap_target = os.path.join(ROOT, "data", "capture.pcapng")

    if not pcap_target or not os.path.exists(pcap_target):
        st.info("No .pcap capture file detected yet.")
        st.markdown("Upload a Wireshark `.pcap` or `.pcapng` file using the uploader above, or save your Wireshark capture into `data/capture.pcap`.")
    else:
        pcap_df, summary = parse_pcap_data(pcap_target, target_port)
        source_name = uploaded_pcap.name if uploaded_pcap is not None else os.path.basename(pcap_target)
        source_key = f"{source_name}:{target_port}:{len(pcap_df)}"

        if st.session_state.get("pcap_source_key") != source_key:
            st.session_state["pcap_metrics_df"] = pcap_to_metrics(pcap_df)
            st.session_state["pcap_source_name"] = source_name
            st.session_state["pcap_source_key"] = source_key
            st.rerun()

        if pcap_df.empty:
            port_msg = f"matching port {target_port}" if target_port > 0 else ""
            st.warning(f"No relevant TCP/UDP traffic found {port_msg} in `{os.path.basename(pcap_target)}`.")
        else:
            # Summary Metrics Cards
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Packets Captured", summary["total_packets"])
            m2.metric("TCP Packets", summary["tcp_count"])
            m3.metric("UDP Datagrams", summary["udp_count"])
            m4.metric("Complete Handshakes", summary["handshake_pairs"])

            st.markdown("### Parsed Packet Stream Table")
            display_cols = ["No.", "Protocol", "Source", "Destination", "Length (B)", "Flags", "Info"]
            st.dataframe(pcap_df[display_cols], use_container_width=True)

            # Protocol Breakdown Chart
            st.markdown("### Packet Capture Protocol Distribution")
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                fig_pcap, ax_pcap = plt.subplots(figsize=(5, 4))
                protocols = ["TCP", "UDP"]
                counts = [summary["tcp_count"], summary["udp_count"]]
                colors = ["#1f77b4", "#ff7f0e"]

                if sum(counts) > 0:
                    ax_pcap.pie(counts, labels=protocols, autopct="%1.1f%%", colors=colors, startangle=140, explode=(0.05, 0))
                    ax_pcap.set_title("TCP vs UDP Packet Volume", fontsize=11, fontweight="bold")
                    st.pyplot(fig_pcap)
                else:
                    st.info("No TCP/UDP packet distribution available.")

            with chart_col2:
                st.markdown("#### Handshake & Protocol Insights:")
                st.info(
                    f"- **Detected 3-Way Handshakes:** **{summary['handshake_pairs']}** complete (`SYN` ➔ `SYN/ACK` ➔ `ACK`) sequence(s).\n"
                    f"- **Average TCP Packet Size:** `{summary['avg_tcp_size']} bytes`.\n"
                    f"- **Average UDP Packet Size:** `{summary['avg_udp_size']} bytes`."
                )
                st.markdown("**Tip for Faculty Demo:** You can open .pcap files directly in Wireshark desktop GUI as well!")
