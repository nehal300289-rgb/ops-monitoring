"""
Tagmatic — operations dashboard.

Reads config/thresholds.yaml and the two data files, and answers one question
for the person on call: is any commitment made in the Phase 1 operations plan
currently breached, and if so, which runbook do I open?

Run:  streamlit run src/dashboard.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

import metrics as m  # noqa: E402

st.set_page_config(
    page_title="Tagmatic · Operations",
    page_icon="◐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PAGE_BG = "#F5F7FA"
SURFACE = "#FFFFFF"
INK = "#111827"
MUTED = "#475569"
LINE = "#CBD5E1"
GRID = "#E2E8F0"
OK = "#047857"
WARN = "#A65300"
BREACH = "#B42318"
BREACH_BG = "#FFF1F0"
OK_BG = "#ECFDF3"
WARN_BG = "#FFF7E6"
BAR = "#5F86AD"
TABLE_HEAD = "#E8EEF5"

STATUS_COLOUR = {"ok": OK, "warn": WARN, "breach": BREACH}
STATUS_WORD = {"ok": "Within limit", "warn": "Approaching", "breach": "Breached"}

st.markdown(
    f"""
    <style>
      :root {{ color-scheme: light !important; }}

      /* Streamlit-native controls */
      div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
      div[data-testid="stSelectbox"] div[data-baseweb="select"] > div > div {{
        background: {SURFACE} !important;
        color: {INK} !important;
        border-color: {LINE} !important;
      }}
      div[data-testid="stSelectbox"] span,
      div[data-testid="stSelectbox"] input,
      div[data-testid="stSelectbox"] svg {{
        color: {INK} !important;
        fill: {INK} !important;
      }}
      div[data-testid="stSelectbox"] div[data-baseweb="select"] * {{
        -webkit-text-fill-color: {INK} !important;
      }}

      /* Altair/dataframe action toolbar */
      [data-testid="stElementToolbar"],
      [data-testid="stElementToolbar"] > div {{
        background: {SURFACE} !important;
        border-color: {LINE} !important;
        box-shadow: 0 1px 4px rgba(15, 23, 42, .14) !important;
      }}
      [data-testid="stElementToolbar"] button {{
        background: {SURFACE} !important;
        color: {INK} !important;
      }}
      [data-testid="stElementToolbar"] button svg {{
        color: {INK} !important;
        fill: {INK} !important;
        stroke: {INK} !important;
      }}

      /* Native dataframe shell */
      div[data-testid="stDataFrame"] {{
        background: {SURFACE} !important;
        color: {INK} !important;
        border-color: {LINE} !important;
      }}
      div[data-testid="stDataFrame"] iframe {{
        background: {SURFACE} !important;
      }}
      html, body, .stApp, [data-testid="stAppViewContainer"] {{
        background-color: {PAGE_BG} !important;
        color: {INK} !important;
      }}
      [data-testid="stHeader"] {{
        background-color: {PAGE_BG} !important;
      }}
      [data-testid="stMarkdownContainer"],
      [data-testid="stMarkdownContainer"] p,
      [data-testid="stMarkdownContainer"] li,
      [data-testid="stWidgetLabel"] p,
      label {{
        color: {INK};
      }}
      [data-baseweb="select"] > div {{
        background-color: {SURFACE} !important;
        border-color: {LINE} !important;
        color: {INK} !important;
      }}
      [data-baseweb="select"] span,
      [data-baseweb="select"] svg {{
        color: {INK} !important;
        fill: {INK} !important;
      }}
      [data-baseweb="popover"],
      [data-baseweb="menu"] {{
        background-color: {SURFACE} !important;
        color: {INK} !important;
      }}
      [role="option"] {{ color: {INK} !important; }}
      [role="option"]:hover {{ background-color: #E8EEF6 !important; }}
      [data-testid="stExpander"] {{
        background-color: {SURFACE};
        border: 1px solid {LINE};
        border-radius: .35rem;
      }}
      [data-testid="stExpander"] summary,
      [data-testid="stExpander"] summary p {{
        color: {INK} !important;
      }}
      [data-testid="stDataFrame"] {{
        background-color: {SURFACE};
        border: 1px solid {LINE};
      }}
      [data-testid="stMarkdownContainer"] code,
      .stMarkdown code {{
        color: #1E3A5F !important;
        background-color: #E6EDF5 !important;
        border: 1px solid #C8D4E3 !important;
        border-radius: .25rem !important;
        padding: .05rem .28rem !important;
      }}

      div[data-testid="stSelectbox"] [role="combobox"] {{
        background-color: {SURFACE} !important;
        color: {INK} !important;
        border-color: {LINE} !important;
      }}
      div[data-testid="stSelectbox"] [role="combobox"] * {{
        color: {INK} !important;
        -webkit-text-fill-color: {INK} !important;
      }}
      [role="listbox"],
      [role="option"],
      [data-baseweb="popover"] ul {{
        background-color: {SURFACE} !important;
        color: {INK} !important;
      }}

      .tg-table-wrap {{
        overflow-x: auto;
        border: 1px solid {LINE};
        border-radius: .5rem;
        background: {SURFACE};
      }}
      .tg-data-table {{
        width: 100%;
        border-collapse: collapse;
        background: {SURFACE};
        color: {INK};
        font-size: .83rem;
      }}
      .tg-data-table th {{
        background: {TABLE_HEAD};
        color: {INK};
        text-align: left;
        font-weight: 600;
        padding: .65rem .75rem;
        border-right: 1px solid {LINE};
        border-bottom: 1px solid {LINE};
        white-space: nowrap;
      }}
      .tg-data-table th:last-child {{ border-right: 0; }}
      .tg-data-table td {{
        background: {SURFACE};
        color: {INK};
        padding: .62rem .75rem;
        border-bottom: 1px solid #E7ECF2;
        white-space: nowrap;
      }}
      .tg-data-table tr:last-child td {{ border-bottom: 0; }}
      .tg-data-table tr.tg-row-breach td {{ background: {BREACH_BG}; }}
      .tg-data-table tr.tg-row-warn td {{ background: {WARN_BG}; }}

      .block-container {{ padding-top: 2.2rem; max-width: 1320px; }}
      .tg-mono {{ font-family: ui-monospace, "SF Mono", "JetBrains Mono", Menlo, monospace; }}

      .tg-masthead {{
        display: flex; align-items: baseline; justify-content: space-between;
        gap: 1rem; flex-wrap: wrap;
        border-bottom: 2px solid {INK}; padding-bottom: .7rem; margin-bottom: 1.4rem;
      }}
      .tg-wordmark {{ font-size: 1.45rem; font-weight: 700; letter-spacing: -.02em; color: {INK}; }}
      .tg-wordmark span {{ font-weight: 400; color: {MUTED}; }}
      .tg-chips {{
        font-family: ui-monospace, "SF Mono", Menlo, monospace;
        font-size: .72rem; color: {MUTED}; letter-spacing: .01em;
      }}
      .tg-chips b {{ color: {INK}; font-weight: 600; }}

      .tg-alert {{
        border-left: 4px solid {BREACH}; background: {BREACH_BG};
        padding: .85rem 1.1rem; margin-bottom: 1.3rem; border-radius: 2px;
      }}
      .tg-alert-clear {{
        border-left: 4px solid {OK}; background: {OK_BG};
        padding: .85rem 1.1rem; margin-bottom: 1.3rem; border-radius: 2px;
      }}
      .tg-alert-title {{
        font-size: .74rem; text-transform: uppercase; letter-spacing: .09em;
        font-weight: 700; margin-bottom: .3rem;
      }}
      .tg-alert-body {{ font-size: .9rem; color: {INK}; line-height: 1.5; }}

      .tg-card {{
        border: 1px solid {LINE}; border-left-width: 4px; border-radius: 3px;
        padding: .95rem 1.05rem 0.8rem; background: {SURFACE}; height: 100%;
      }}
      .tg-card-label {{
        font-size: .73rem; text-transform: uppercase; letter-spacing: .07em;
        color: {MUTED}; font-weight: 600; min-height: 2.1em; line-height: 1.35;
      }}
      .tg-value {{
        font-family: ui-monospace, "SF Mono", Menlo, monospace;
        font-size: 2.15rem; font-weight: 600; letter-spacing: -.03em;
        line-height: 1.15; margin: .35rem 0 .1rem;
      }}
      .tg-status {{
        display: inline-block; font-size: .68rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: .07em; margin-bottom: .55rem;
      }}
      .tg-threshold {{
        font-size: .76rem; color: {MUTED}; line-height: 1.45;
        padding-bottom: .55rem; border-bottom: 1px dotted {LINE};
      }}
      .tg-prov {{
        font-family: ui-monospace, "SF Mono", Menlo, monospace;
        font-size: .67rem; color: {MUTED}; line-height: 1.65; padding-top: .5rem;
      }}
      .tg-prov b {{ color: {INK}; font-weight: 600; }}

      .tg-section {{
        font-size: .76rem; text-transform: uppercase; letter-spacing: .09em;
        font-weight: 700; color: {INK}; margin: 1.9rem 0 .2rem;
        border-bottom: 1px solid {LINE}; padding-bottom: .35rem;
      }}
      .tg-note {{ font-size: .8rem; color: {MUTED}; line-height: 1.55; margin-top: .5rem; }}
      .tg-foot {{
        font-family: ui-monospace, "SF Mono", Menlo, monospace;
        font-size: .68rem; color: {MUTED}; line-height: 1.7;
        border-top: 1px solid {LINE}; margin-top: 2.2rem; padding-top: .8rem;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

cfg = m.load_config()
meta = cfg["meta"]
all_sprints = m.sprints()

st.markdown(
    f"""
    <div class="tg-masthead">
      <div class="tg-wordmark">Tagmatic <span>/ Operations</span></div>
      <div class="tg-chips">
        model <b>{meta['model_version']}</b> &nbsp;·&nbsp;
        taxonomy <b>v{meta['taxonomy_version']}</b> &nbsp;·&nbsp;
        thresholds <b>v{meta['config_version']}</b> &nbsp;·&nbsp;
        owner <b>{meta['owner']}</b>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1, 3])
with left:
    sprint = st.selectbox(
        "Reporting sprint",
        all_sprints,
        index=len(all_sprints) - 1,
        format_func=lambda s: f"Sprint {s}",
    )
with right:
    scored = m.load_holdout().query("sprint == @sprint")["scored_at"].max()
    volume = len(m.load_live().query("sprint == @sprint"))
    st.markdown(
        f"<div class='tg-note' style='padding-top:1.9rem'>"
        f"{volume} tickets classified · hold-out re-scored {scored:%d %b %Y}</div>",
        unsafe_allow_html=True,
    )

kpis = m.compute_kpis(sprint)
breaches = [k for k in kpis if k.status == "breach"]
warns = [k for k in kpis if k.status == "warn"]

if breaches:
    runbooks = sorted({k.runbook for k in breaches})
    items = "".join(
        f"<li><b>{k.label}</b> at {k.display} — {k.risk_ref}. Open <b>{k.runbook}</b>.</li>"
        for k in breaches
    )
    st.markdown(
        f"""
        <div class="tg-alert">
          <div class="tg-alert-title" style="color:{BREACH}">
            {len(breaches)} threshold breached · open {', '.join(runbooks)}
          </div>
          <div class="tg-alert-body"><ul style="margin:.3rem 0 0 1.1rem;padding:0">{items}</ul></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    extra = f" {len(warns)} metric(s) in the warning band." if warns else ""
    st.markdown(
        f"""
        <div class="tg-alert-clear">
          <div class="tg-alert-title" style="color:{OK}">All thresholds within limit</div>
          <div class="tg-alert-body">
            No Phase 1 operational commitment is breached this sprint.{extra}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def band_help(kpi: m.Kpi) -> str:
    """Short on-card copy distinguishing the Phase 2 warn band from the Phase 1 breach."""
    if kpi.key == "pii_escapes":
        return "No warn band — any escape is an immediate breach (P1)."
    if kpi.key == "primary_label_accuracy":
        return (
            f"Warn below {kpi.warn_at:.0%} · breach below {kpi.breach_at:.0%} "
            "(higher is better)."
        )
    if kpi.key == "per_label_f1_delta":
        return (
            f"Warn above {kpi.warn_at * 100:.0f} pp drop · "
            f"breach above {kpi.breach_at * 100:.0f} pp drop."
        )
    return (
        f"Warn above {kpi.warn_at:.0%} · breach above {kpi.breach_at:.0%}."
    )


cols = st.columns(4, gap="small")
for col, kpi in zip(cols, kpis):
    colour = STATUS_COLOUR[kpi.status]
    with col:
        st.markdown(
            f"""
            <div class="tg-card" style="border-left-color:{colour}">
              <div class="tg-card-label">{kpi.label}</div>
              <div class="tg-value" style="color:{colour}">{kpi.display}</div>
              <div class="tg-status" style="color:{colour}">{STATUS_WORD[kpi.status]}</div>
              <div class="tg-threshold">{kpi.threshold_text}</div>
              <div class="tg-threshold" style="border-bottom:0;padding-bottom:0;padding-top:.35rem">
                {band_help(kpi)}
              </div>
              <div class="tg-prov">
                <b>{kpi.source}</b><br>
                risk <b>{kpi.risk_ref.split(' — ')[0]}</b> ·
                runbook <b>{kpi.runbook}</b>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with st.expander("Why these four, and why these numbers"):
    for kpi in kpis:
        st.markdown(f"**{kpi.label}** — {kpi.source}")
        st.markdown(f"<div class='tg-note'>{kpi.rationale}</div>", unsafe_allow_html=True)
        st.write("")

st.markdown("<div class='tg-section'>Trend against thresholds</div>", unsafe_allow_html=True)
chart_l, chart_r = st.columns(2, gap="large")


def trend(frame: pd.DataFrame, field: str, title: str, warn_at: float, breach_at: float, fmt: str):
    base = alt.Chart(frame).encode(
        x=alt.X("sprint:O", title="Sprint", axis=alt.Axis(labelAngle=0, grid=False))
    )
    area = base.mark_area(opacity=0.10, color=INK).encode(alt.Y(f"{field}:Q", title=title))
    line = base.mark_line(color=INK, strokeWidth=2).encode(alt.Y(f"{field}:Q", axis=alt.Axis(format=fmt)))
    pts = base.mark_point(color=INK, filled=True, size=55).encode(
        alt.Y(f"{field}:Q"),
        tooltip=[alt.Tooltip("sprint:O", title="Sprint"), alt.Tooltip(f"{field}:Q", format=fmt)],
    )
    rules = alt.Chart(
        pd.DataFrame(
            [
                {"v": warn_at, "label": "warn", "colour": WARN},
                {"v": breach_at, "label": "breach", "colour": BREACH},
            ]
        )
    ).mark_rule(strokeDash=[5, 4], strokeWidth=1.5).encode(
        y="v:Q", color=alt.Color("colour:N", scale=None)
    )
    return (
        (area + line + pts + rules)
        .properties(height=250, background=SURFACE)
        .configure_view(fill=SURFACE, stroke=LINE)
        .configure_axis(
            labelColor=INK,
            titleColor=INK,
            gridColor=GRID,
            domainColor=LINE,
            tickColor=LINE,
        )
    )


flag_spec = cfg["kpis"]["review_flag_rate"]
acc_spec = cfg["kpis"]["primary_label_accuracy"]

with chart_l:
    st.markdown("**Human-review flag rate**")
    st.altair_chart(
        trend(
            m.flag_rate_by_sprint(), "flag_rate", "Flag rate",
            flag_spec["warn_at"], flag_spec["breach_at"], ".0%",
        ),
        width="stretch",
    )
    st.markdown(
        f"<div class='tg-note'>Dashed lines: warn at {flag_spec['warn_at']:.0%}, "
        f"breach at {flag_spec['breach_at']:.0%} (Phase 1 Objective 1).</div>",
        unsafe_allow_html=True,
    )

with chart_r:
    st.markdown("**Primary-label accuracy, hold-out set**")
    st.altair_chart(
        trend(
            m.accuracy_by_sprint(), "accuracy", "Accuracy",
            acc_spec["warn_at"], acc_spec["breach_at"], ".0%",
        ),
        width="stretch",
    )
    st.markdown(
        f"<div class='tg-note'>Dashed lines: warn at {acc_spec['warn_at']:.0%}, "
        f"floor at {acc_spec['breach_at']:.0%} (Phase 1 Objective 3).</div>",
        unsafe_allow_html=True,
    )

st.markdown("<div class='tg-section'>Per-label drift detail</div>", unsafe_allow_html=True)
table_l, table_r = st.columns([3, 2], gap="large")

with table_l:
    table = m.f1_table(sprint)
    display = table.rename(columns={"Status": "State"}).copy()
    display["Baseline F1"] = display["Baseline F1"].map("{:.3f}".format)
    display["Current F1"] = display["Current F1"].map("{:.3f}".format)
    display["State"] = display["State"].map(STATUS_WORD)

    def shade(row):
        colour = {
            "Breached": BREACH_BG,
            "Approaching": WARN_BG,
        }.get(row["State"], SURFACE)
        return [f"background-color: {colour}; color: {INK}" for _ in row]

    st.dataframe(
        display.style.apply(shade, axis=1),
        hide_index=True,
        width="stretch",
    )
    st.markdown(
        "<div class='tg-note'>Baselines frozen at end of Sprint 1 and versioned in "
        "<code>config/thresholds.yaml</code>. Re-baselining requires an approved retune.</div>",
        unsafe_allow_html=True,
    )

with table_r:
    lang = m.flag_rate_by_language(sprint)
    st.markdown("**Flag rate by ticket language**")
    bar = (
        alt.Chart(lang)
        .mark_bar(size=34)
        .encode(
            x=alt.X("flag_rate:Q", title="Flag rate", axis=alt.Axis(format=".0%")),
            y=alt.Y("language:N", title=None, sort="-x"),
            color=alt.value(BAR),
            tooltip=[
                alt.Tooltip("language:N", title="Language"),
                alt.Tooltip("tickets:Q", title="Tickets"),
                alt.Tooltip("flag_rate:Q", format=".1%", title="Flag rate"),
            ],
        )
        .properties(height=130, background=SURFACE)
        .configure_view(fill=SURFACE, stroke=LINE)
        .configure_axis(
            labelColor=INK,
            titleColor=INK,
            gridColor=GRID,
            domainColor=LINE,
            tickColor=LINE,
        )
    )
    st.altair_chart(bar, width="stretch")
    fr = lang.query("language == 'French'")
    n_fr = int(fr["tickets"].iloc[0]) if len(fr) else 0
    st.markdown(
        f"<div class='tg-note'>The classifier prompt, its few-shot examples and the "
        f"spaCy censor are English-validated, so French tickets carry both the drift "
        f"risk (R1) and the censor risk (R2). n={n_fr} this sprint — indicative, not "
        f"yet significant. Tracked in RB-01 and RB-02.</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    f"""
    <div class="tg-foot">
      Thresholds v{meta['config_version']} · baselines established {meta['baseline_established']} ·
      config owner {meta['owner']} · approver {meta['approver']}<br>
      Sources: <code>data/classification_log.csv</code> (synthetic simulated classifier traffic ),
      <code>data/holdout_eval.csv</code> (fixed labelled set, re-scored per sprint).
      Synthetic data — Actual ticket content is not committed to this repository.
    </div>
    """,
    unsafe_allow_html=True,
)