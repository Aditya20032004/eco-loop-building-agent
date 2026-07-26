import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import OUTPUT_DIR_base, OUTPUT_DIR_AI, OUTPUT_DIR

# Adds a clean, clickable GitHub badge to your sidebar or main page
st.sidebar.markdown(
    "### 🔗 Project Links\n"
    "[![View on GitHub](https://img.shields.io/badge/GitHub-View_Source_Code-black?logo=GitHub)](https://github.com/aditya20032004/eco-loop-building-agent)"
)
# ============================================================
# PAGE CONFIG + VISUAL IDENTITY
# ------------------------------------------------------------
st.set_page_config(
    page_title="Eco-Loop AI Orchestrator",
    page_icon="🌿",
    layout="wide",
)

ZONE_COLORS = ["#4ADE80", "#38BDF8", "#FB923C", "#F472B6", "#A78BFA", "#FACC15", "#2DD4BF"]

CUSTOM_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {
    --bg-hi: #0A100D;
    --bg-lo: #060A08;
    --panel: rgba(22, 33, 28, 0.46);
    --panel-solid: #131C17;
    --border: rgba(255, 255, 255, 0.08);
    --border-strong: rgba(255, 255, 255, 0.14);
    --text: #E7EDE9;
    --muted: #7E9186;
    --good: #4ADE80;
    --warn: #F5A524;
    --bad: #F04438;
    --violet: #A78BFA;
}

html, body, [class*="css"]  { font-family: 'Space Grotesk', sans-serif; }

.stApp {
    color: var(--text);
    background-color: var(--bg-hi);
    background-image:
        radial-gradient(ellipse 80% 60% at 50% -10%, rgba(74, 222, 128, 0.05), transparent),
        repeating-linear-gradient(0deg, rgba(255,255,255,0.035) 0px, rgba(255,255,255,0.035) 1px, transparent 1px, transparent 48px),
        repeating-linear-gradient(90deg, rgba(255,255,255,0.035) 0px, rgba(255,255,255,0.035) 1px, transparent 1px, transparent 48px),
        linear-gradient(180deg, var(--bg-hi) 0%, var(--bg-lo) 100%);
}
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    opacity: 0.05;
    mix-blend-mode: overlay;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}

section[data-testid="stSidebar"] {
    background-color: rgba(6, 10, 8, 0.85);
    border-right: 1px solid var(--border);
    backdrop-filter: blur(10px);
}

h1, h2, h3 { font-weight: 600 !important; letter-spacing: -0.01em; }

.status-strip { display: flex; gap: 8px; flex-wrap: wrap; margin: 4px 0 18px 0; }
.status-chip {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.03em;
    color: var(--muted);
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 4px 12px;
    backdrop-filter: blur(6px);
}
.status-chip.live { color: var(--good); border-color: rgba(74,222,128,0.3); }
.status-chip.live::before { content: "● "; }

div[data-testid="stMetric"] {
    background: var(--panel);
    backdrop-filter: blur(18px) saturate(140%);
    -webkit-backdrop-filter: blur(18px) saturate(140%);
    border: 1px solid var(--border);
    border-top: 1px solid var(--border-strong);
    border-radius: 14px;
    padding: 16px 18px 12px 18px;
    box-shadow: 0 8px 28px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04);
    transition: transform 160ms ease, border-color 160ms ease;
}
div[data-testid="stMetric"]:hover { transform: translateY(-2px); border-color: var(--border-strong); }
div[data-testid="stMetric"] label { color: var(--muted) !important; letter-spacing: .03em; font-size: 0.78rem !important; text-transform: uppercase; }
div[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace !important; font-weight: 500 !important; }

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--panel) !important;
    backdrop-filter: blur(18px) saturate(140%);
    -webkit-backdrop-filter: blur(18px) saturate(140%);
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    box-shadow: 0 10px 34px rgba(0,0,0,0.32), inset 0 1px 0 rgba(255,255,255,0.03);
    padding: 4px 6px;
}

hr { border-color: var(--border) !important; }

div[data-baseweb="select"] > div {
    background: var(--panel-solid) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}
.stButton > button, .stDownloadButton > button {
    background: var(--panel-solid);
    color: var(--text);
    border: 1px solid var(--border-strong);
    border-radius: 10px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 500;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
    transition: border-color 140ms ease, background 140ms ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: var(--good); color: var(--good); background: rgba(74, 222, 128, 0.06);
}

.eco-banner-warn {
    background: rgba(245, 165, 36, 0.08); border: 1px solid rgba(245, 165, 36, 0.30);
    backdrop-filter: blur(12px); color: #F5A524; border-radius: 10px;
    padding: 12px 16px; font-size: 0.92rem; margin-bottom: 0.75rem;
}
.eco-banner-good {
    background: rgba(74, 222, 128, 0.07); border: 1px solid rgba(74, 222, 128, 0.28);
    backdrop-filter: blur(12px); color: #4ADE80; border-radius: 10px;
    padding: 12px 16px; font-size: 0.92rem; margin-bottom: 0.75rem;
}

[data-testid="stDataFrame"], .stJson, .stCodeBlock, textarea { font-family: 'JetBrains Mono', monospace !important; }

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--bg-lo); }
::-webkit-scrollbar-thumb { background: #23302A; border-radius: 6px; border: 2px solid var(--bg-lo); }
::-webkit-scrollbar-thumb:hover { background: #2C3B33; }
</style>
"""
# Strip any accidental existing tags and force the style wrapper[cite: 3]
clean_css = CUSTOM_CSS.replace("<style>", "").replace("</style>", "")
st.markdown(f"<style>{clean_css}</style>", unsafe_allow_html=True)

st.title("🌿 Eco-Loop AI — Smart Building HVAC & Carbon Orchestrator")
st.markdown(
    "<span style='color:#7E9186'>Autonomous multi-zone thermal control — closed-loop "
    "EnergyPlus + LLM agent, custom tool-calling, real-time grid carbon signals.</span>",
    unsafe_allow_html=True,
)

# ============================================================
# DATA LOADING
# ============================================================
BASELINE_PATH = os.path.join(OUTPUT_DIR_base, "eplusout.csv")
AI_PATH = os.path.join(OUTPUT_DIR_AI, "eplusout.csv")
LOGS_PATH = os.path.join(OUTPUT_DIR, "agent_logs.json")
LEGACY_PATH = os.path.join(OUTPUT_DIR, "eplusout.csv")


@st.cache_data(show_spinner=False)
def load_csv(path):
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_logs(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


ai_df = load_csv(AI_PATH)
baseline_df = load_csv(BASELINE_PATH)
using_legacy = False

if ai_df is None:
    ai_df = load_csv(LEGACY_PATH)
    using_legacy = True

if ai_df is None:
    st.error(
        f"❌ No simulation output found. Expected `{AI_PATH}` "
        f"(or legacy `{LEGACY_PATH}`). Run your orchestrator first: "
        f"`python -m src.orchestrator`."
    )
    st.stop()

agent_logs = load_logs(LOGS_PATH)
REAL_COMPARISON = baseline_df is not None

st.markdown(
    f"""
<div class="status-strip">
    <span class="status-chip live">SIMULATION LOADED</span>
    <span class="status-chip">ENERGYPLUS 22.1.0</span>
    <span class="status-chip">MODEL: MEDIUM OFFICE · CZ 2A</span>
    <span class="status-chip">AGENT: QWEN2.5:14B</span>
    <span class="status-chip">{'BASELINE: LINKED' if REAL_COMPARISON else 'BASELINE: MISSING'}</span>
</div>
""",
    unsafe_allow_html=True,
)

if not REAL_COMPARISON:
    st.markdown(
        "<div class='eco-banner-warn'>⚠️ <b>No baseline run found</b> — savings figures below "
        "are not yet a real comparison. Run a rule-based baseline simulation and save it to "
        f"<code>{BASELINE_PATH}</code> before treating any % savings number as a result you can "
        "report. This dashboard will not fabricate a baseline for you.</div>",
        unsafe_allow_html=True,
    )

# ============================================================
# METRICS & UNIT NORMALIZATION
# ============================================================
def get_kwh_series(df):
    if df is None or "Electricity:Facility" not in df.columns:
        return None
    series = df["Electricity:Facility"]
    # EnergyPlus natively outputs Joules. 1 kWh = 3,600,000 Joules.
    # If the numbers are massive (millions), convert to kWh.
    if series.max() > 50000:
        return series / 3600000.0
    return series

ai_energy_series = get_kwh_series(ai_df)
base_energy_series = get_kwh_series(baseline_df) if REAL_COMPARISON else None

ai_total = ai_energy_series.sum() if ai_energy_series is not None else 0.0
baseline_total = base_energy_series.sum() if base_energy_series is not None else None

if ai_energy_series is None:
    st.warning("Column `Electricity:Facility` not found in the AI run's output CSV.")

if REAL_COMPARISON and baseline_total:
    energy_saved_kwh = baseline_total - ai_total
    savings_pct = (energy_saved_kwh / baseline_total) * 100
else:
    energy_saved_kwh = None
    savings_pct = None

avg_carbon = ai_df["Carbon_Intensity"].mean() if "Carbon_Intensity" in ai_df.columns else None

COMFORT_MIN, COMFORT_MAX = 20.0, 26.0
temp_cols_all = [c for c in ai_df.columns if ":Zone Mean Air Temperature" in c]

if temp_cols_all:
    # EnergyPlus index represents hours. Mask to only evaluate occupied daytime hours (8 AM to 6 PM)
    is_occupied_hour = (ai_df.index % 24 >= 8) & (ai_df.index % 24 <= 18)
    
    occupied_temps = ai_df.loc[is_occupied_hour, temp_cols_all]
    
    if not occupied_temps.empty:
        violation_mask = (occupied_temps < COMFORT_MIN) | (occupied_temps > COMFORT_MAX)
        comfort_violation_pct = 100.0 * violation_mask.any(axis=1).mean()
    else:
        comfort_violation_pct = 0.0
else:
    comfort_violation_pct = None

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.header("🎛️ Control Panel")
view_mode = st.sidebar.radio(
    "Dashboard View",
    ["Overview & Savings", "Zone Thermal Analysis", "Grid & Carbon Metrics", "🤖 Agent Behavior & Logs"],
)
st.sidebar.markdown("---")
st.sidebar.markdown("AI run source: `output/ai/eplusout.csv`")
st.sidebar.caption(f"Baseline run: {'✅ loaded' if REAL_COMPARISON else '❌ not found'}")

# ============================================================
# KPI ROW
# ============================================================
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("AI Run — Total Energy", f"{ai_total:,.1f} kWh")
with col2:
    if savings_pct is not None:
        st.metric("Energy Saved vs Baseline", f"{energy_saved_kwh:,.1f} kWh", delta=f"{savings_pct:+.1f}%")
    else:
        st.metric("Energy Saved vs Baseline", "—", delta="no baseline loaded")
with col3:
    st.metric("Avg Grid Carbon Intensity", f"{avg_carbon:.1f} gCO2/kWh" if avg_carbon is not None else "—")
with col4:
    if comfort_violation_pct is not None:
        st.metric(
            "Comfort Violations", f"{comfort_violation_pct:.1f}% of time",
            delta="within bounds" if comfort_violation_pct < 5 else "check zones",
            delta_color="normal" if comfort_violation_pct < 5 else "inverse",
        )
    else:
        st.metric("Comfort Violations", "—")

st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

TRANSPARENT = "rgba(0,0,0,0)"
BASE_FONT = dict(family="Space Grotesk, sans-serif", color="#E7EDE9")
GRID_COLOR = "rgba(255,255,255,0.06)"


def style_fig(fig, height=None):
    fig.update_layout(
        paper_bgcolor=TRANSPARENT, plot_bgcolor=TRANSPARENT,
        font=BASE_FONT, margin=dict(t=50, b=36, l=48, r=24),
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, zeroline=False)
    fig.update_yaxes(gridcolor=GRID_COLOR, zeroline=False)
    if height:
        fig.update_layout(height=height)
    return fig


# ============================================================
# VIEWS
# ============================================================
if view_mode == "Overview & Savings":
    with st.container(border=True):
        st.subheader("📈 Cumulative Energy Performance")
        if ai_energy_series is not None:
            ai_cum = ai_energy_series.cumsum()
            fig_energy = go.Figure()
            
            if REAL_COMPARISON and base_energy_series is not None:
                baseline_cum = base_energy_series.cumsum()
                fig_energy.add_trace(go.Scatter(
                    y=baseline_cum, name="Baseline (rule-based)",
                    line=dict(color="#5B6B63", dash="dash", width=2),
                ))
                
            fig_energy.add_trace(go.Scatter(
                y=ai_cum,
                name=f"Eco-Loop AI{f' ({savings_pct:+.1f}% savings)' if savings_pct is not None else ''}",
                line=dict(color="#4ADE80", width=3),
            ))
            
            fig_energy.update_layout(
                title="Energy Consumption — Baseline vs AI-Driven (Cumulative)",
                xaxis_title="Simulation Timestep (hours)", yaxis_title="Cumulative kWh",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            st.plotly_chart(style_fig(fig_energy), use_container_width=True)
        else:
            st.warning("`Electricity:Facility` column not found in AI run output.")

elif view_mode == "Zone Thermal Analysis":
    with st.container(border=True):
        st.subheader("🌡️ Multi-Zone Thermal Comfort Tracking")
        if temp_cols_all:
            chart_mode = st.radio(
                "View", ["Small Multiples (recommended)", "Overlay (all zones, one chart)"],
                horizontal=True, label_visibility="collapsed",
            )
            zone_names = [c.split(":")[0] for c in temp_cols_all]

            if chart_mode.startswith("Small"):
                n = len(temp_cols_all)
                n_cols = 2 if n <= 4 else 3
                fig = make_subplots(
                    rows=-(-n // n_cols), cols=n_cols,
                    subplot_titles=zone_names, shared_yaxes=True,
                    vertical_spacing=0.12, horizontal_spacing=0.06,
                )
                for i, col in enumerate(temp_cols_all):
                    r, c = divmod(i, n_cols)
                    color = ZONE_COLORS[i % len(ZONE_COLORS)]
                    
                    # 1. Add green comfort band
                    fig.add_hrect(y0=COMFORT_MIN, y1=COMFORT_MAX, fillcolor="#4ADE80",
                                  opacity=0.07, line_width=0, row=r + 1, col=c + 1)
                    
                    # 2. Add Baseline Trace (Dotted grey line) - Plotted first so it sits behind the AI line
                    if REAL_COMPARISON and col in baseline_df.columns:
                        fig.add_trace(
                            go.Scatter(y=baseline_df[col], line=dict(color="#5B6B63", width=1.5, dash="dot"), showlegend=False),
                            row=r + 1, col=c + 1,
                        )

                    # 3. Add AI Trace (Solid colored line)
                    fig.add_trace(
                        go.Scatter(y=ai_df[col], line=dict(color=color, width=1.8), showlegend=False),
                        row=r + 1, col=c + 1,
                    )
                    
                fig.update_layout(height=170 * (-(-n // n_cols)))
                st.plotly_chart(style_fig(fig), use_container_width=True)
                st.caption(f"Green band = comfort range ({COMFORT_MIN}–{COMFORT_MAX}°C). Dotted grey line = Baseline. Each panel is one zone.")
            else:
                fig_temp = go.Figure()
                fig_temp.add_hrect(y0=COMFORT_MIN, y1=COMFORT_MAX, fillcolor="#4ADE80", opacity=0.06, line_width=0)
                for i, col in enumerate(temp_cols_all):
                    fig_temp.add_trace(go.Scatter(
                        y=ai_df[col], name=zone_names[i],
                        line=dict(color=ZONE_COLORS[i % len(ZONE_COLORS)], width=1.8),
                    ))
                fig_temp.add_hline(y=COMFORT_MAX, line_dash="dot", line_color="#F04438")
                fig_temp.add_hline(y=COMFORT_MIN, line_dash="dot", line_color="#38BDF8")
                fig_temp.update_layout(
                    title="All Zones — Overlay",
                    yaxis_title="Temperature (°C)", xaxis_title="Simulation Hour",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
                )
                st.plotly_chart(style_fig(fig_temp, height=460), use_container_width=True)

            if comfort_violation_pct is not None:
                if comfort_violation_pct < 5:
                    st.markdown(
                        f"<div class='eco-banner-good'>✅ Comfort maintained {100 - comfort_violation_pct:.1f}% "
                        "of the simulated period.</div>", unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div class='eco-banner-warn'>⚠️ Zones fell outside {COMFORT_MIN}–{COMFORT_MAX}°C "
                        f"{comfort_violation_pct:.1f}% of the time — check the Agent Behavior tab.</div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.warning("No `:Zone Mean Air Temperature` columns found.")

elif view_mode == "Grid & Carbon Metrics":
    with st.container(border=True):
        st.markdown("### 🌍 Total Carbon Emissions")
        
        if "Carbon_Intensity" in ai_df.columns and ai_energy_series is not None:
            # We use the properly normalized kWh series * Carbon_Intensity (g) / 1000 = kg
            ai_df['AI Emissions (kg)'] = ai_energy_series * ai_df['Carbon_Intensity'] / 1000.0
            
            if REAL_COMPARISON and base_energy_series is not None:
                baseline_df['Baseline Emissions (kg)'] = base_energy_series * baseline_df['Carbon_Intensity'] / 1000.0
                
                chart_data = pd.DataFrame({
                    'Hour': baseline_df.index,
                    'Baseline Emissions': baseline_df['Baseline Emissions (kg)'],
                    'AI Emissions': ai_df['AI Emissions (kg)']
                }).set_index('Hour')
                
                st.line_chart(chart_data, color=["#808080", "#4ADE80"])
            else:
                # Ensures proper formatting when comparing standalone AI runs
                standalone_chart = pd.DataFrame({
                    'Hour': ai_df.index,
                    'AI Emissions': ai_df['AI Emissions (kg)']
                }).set_index('Hour')
                st.line_chart(standalone_chart, color=["#4ADE80"])
        else:
            st.info("No `Carbon_Intensity` column in this run's output.")

elif view_mode == "🤖 Agent Behavior & Logs":
    with st.container(border=True):
        st.subheader("🧠 Cognitive LLM Agent — Reasoning & Tool-Call Logs")
        st.caption("Telemetry sent to the model, the prompt, the raw response, and the parsed actions executed.")
        if not agent_logs:
            st.warning(f"No agent logs found at `{LOGS_PATH}`.")
        else:
            log_options = [f"Day {log['day']} — Hour {log['hour']:02d}:00" for log in agent_logs]
            selected_idx = st.selectbox("Simulation Timestep", range(len(log_options)), format_func=lambda x: log_options[x])
            current_log = agent_logs[selected_idx]
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**📥 Telemetry Input**")
                st.json(current_log.get("telemetry", {}))
                st.markdown("**🛠️ Executed Actions**")
                st.json(current_log.get("parsed_actions", {}))
            with col_b:
                st.markdown("**💬 Prompt Sent to LLM**")
                st.text_area("prompt", current_log.get("prompt_sent", ""), height=180, label_visibility="collapsed")
                st.markdown("**🤖 Raw LLM Response**")
                st.code(current_log.get("raw_llm_response", ""), language="json")

# ============================================================
# RAW DATA + EXPORT
# ============================================================
with st.container(border=True):
    with st.expander("🔍 View Raw AI Run CSV"):
        st.dataframe(ai_df, use_container_width=True)
    if REAL_COMPARISON:
        with st.expander("🔍 View Raw Baseline Run CSV"):
            st.dataframe(baseline_df, use_container_width=True)

summary_rows = {
    "ai_total_kwh": ai_total, "baseline_total_kwh": baseline_total,
    "energy_saved_kwh": energy_saved_kwh, "savings_pct": savings_pct,
    "avg_carbon_intensity": avg_carbon, "comfort_violation_pct": comfort_violation_pct,
}
st.download_button("⬇️ Download summary metrics (JSON)", data=json.dumps(summary_rows, indent=2),
                    file_name="eco_loop_summary.json", mime="application/json")