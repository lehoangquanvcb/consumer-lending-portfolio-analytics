
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from modules.data_engine import *
from modules.strategy_engine import *

st.set_page_config(
    page_title="Consumer Lending Portfolio Analytics Workbench - Author: Le Hoang Quan",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@media (max-width: 1400px) {
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
}
[data-testid="stPlotlyChart"] { overflow: hidden; }
[data-testid="stPlotlyChart"] > div { width: 100% !important; }
</style>
""", unsafe_allow_html=True)

# ---------- Theme and layout ----------
st.markdown("""
<style>
:root {
    --bg:#07182a;
    --panel:#10243a;
    --panel2:#0d2034;
    --border:#294158;
    --text:#f4f7fb;
    --muted:#9fb1c5;
    --blue:#2f6fed;
    --green:#61c46e;
    --red:#ff6b57;
    --amber:#f2b632;
}
html, body, [class*="css"] {font-family: Inter, "Segoe UI", Arial, sans-serif;}
.stApp {background:linear-gradient(135deg,#07182a 0%,#091d31 100%);color:var(--text);}
.block-container {padding:1.0rem 1.15rem 1.5rem 1.15rem;max-width:100%;}
[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#061629 0%,#081c30 100%);
    border-right:1px solid #20384f;
    min-width:245px; max-width:245px;
}
[data-testid="stSidebar"] .block-container {padding:1.0rem .8rem;}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 {color:white;}
h1 {font-size:1.65rem!important;margin-bottom:.05rem!important;}
h2 {font-size:1.18rem!important;}
h3 {font-size:1.02rem!important;}
p, label, .stMarkdown {color:var(--text);}
.subtle {color:var(--muted);font-size:.90rem;margin-top:-.20rem;margin-bottom:.8rem;}
.section-label {color:#879bb0;font-size:.70rem;letter-spacing:.09em;text-transform:uppercase;margin:.85rem 0 .25rem;}
.panel {
    background:linear-gradient(145deg,#11263d,#0d2136);
    border:1px solid var(--border);
    border-radius:10px;
    padding:.65rem .75rem .35rem .75rem;
    box-shadow:0 7px 18px rgba(0,0,0,.13);
    margin-bottom:.55rem;
}
.panel-title {font-size:.96rem;font-weight:700;margin-bottom:.15rem;color:#f8fbff;}
.kpi-card {
    background:linear-gradient(145deg,#122b44,#10243a);
    border:1px solid #2b455e;
    border-radius:10px;
    padding:.75rem .80rem;
    min-height:112px;
    position:relative;
    box-shadow:0 6px 14px rgba(0,0,0,.16);
}
.kpi-label {font-size:.76rem;color:#d0dceb;font-weight:600;line-height:1.2;}
.kpi-value {font-size:1.35rem;color:white;font-weight:750;margin:.28rem 0 .12rem;}
.kpi-delta-up {font-size:.72rem;color:#67d277;}
.kpi-delta-down {font-size:.72rem;color:#62c876;}
.kpi-delta-bad {font-size:.72rem;color:#ff7868;}
.icon-circle {
    width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;
    background:#1c4f91;font-size:1rem;margin-bottom:.42rem;
}
.report-card {
    background:#10243a;border:1px solid #294158;border-radius:10px;padding:.8rem;margin-bottom:.6rem;
}
.small-note {font-size:.72rem;color:#91a5ba;}
div[data-testid="stMetric"] {background:#10253b;border:1px solid #294158;padding:12px;border-radius:10px;}
div[data-testid="stDataFrame"] {border:1px solid #294158;border-radius:8px;overflow:hidden;}
[data-testid="stVerticalBlockBorderWrapper"] {border-color:#294158!important;}
.stButton>button,.stDownloadButton>button {
    background:#173858;color:white;border:1px solid #355574;border-radius:7px;
}
.stButton>button:hover,.stDownloadButton>button:hover {background:#235b99;border-color:#4b7bb0;}
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
    background:#0e2238!important;border-color:#2b455e!important;color:white!important;
}
[data-testid="stDateInput"] input {color:white!important;}
div[role="radiogroup"] label {
    background:transparent;border-radius:7px;padding:.32rem .42rem;margin-bottom:.05rem;
}
div[role="radiogroup"] label:has(input:checked) {background:#2464d8;}
hr {border-color:#294158!important;}
#MainMenu, footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#dfe9f5", size=11),
    margin=dict(l=22,r=18,t=58,b=28),
    legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="left", x=0),
    hoverlabel=dict(bgcolor="#10243a",font_color="white"),
)
GRID = "#294158"
BLUE = "#3c82f6"
GREEN = "#58bd68"
AMBER = "#e9aa29"
ORANGE = "#e87935"
RED = "#ed5b4a"
LIGHTBLUE = "#55a7df"

def chart_style(fig, height=300, legend=True):
    fig.update_layout(**PLOT_LAYOUT)
    fig.update_layout(height=height, showlegend=legend)
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    return fig

def panel_chart(title, fig):
    st.markdown(f'<div class="panel-title">{title}</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

def fmt_vnd(v):
    if abs(v) >= 1e12: return f"{v/1e12:,.2f}T"
    if abs(v) >= 1e9: return f"{v/1e9:,.1f}B"
    if abs(v) >= 1e6: return f"{v/1e6:,.1f}M"
    return f"{v:,.0f}"

def kpi_card(icon, label, value, delta, good=True, icon_bg="#174d8f"):
    cls = "kpi-delta-up" if good else "kpi-delta-bad"
    arrow = "▲" if delta.startswith("+") else "▼"
    return f"""
    <div class="kpi-card">
      <div class="icon-circle" style="background:{icon_bg}">{icon}</div>
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="{cls}">{arrow} {delta} <span style="color:#8da2b8">vs prior month</span></div>
    </div>"""

@st.cache_data(show_spinner=False)
def get_data():
    return load_data()

loans, snaps = get_data()

# ---------- Sidebar navigation ----------
st.sidebar.markdown("<div style='font-size:2rem;text-align:center'>🏦</div>", unsafe_allow_html=True)
st.sidebar.markdown("<div style='text-align:center;font-weight:750;font-size:.96rem'>PORTFOLIO WORKBENCH</div>", unsafe_allow_html=True)
st.sidebar.markdown("<div style='text-align:center;color:#8197ad;font-size:.70rem;margin-bottom:.7rem'>Consumer Lending Analytics</div>", unsafe_allow_html=True)

nav_items = [
    "🏠  Executive Overview",
    "▦  Portfolio Overview",
    "▥  Vintage Analysis",
    "▥  Roll Rate Analysis",
    "◴  DPD Migration",
    "⌁  Delinquency Analysis",
    "◌  Collection Analytics",
    "◉  Portfolio Profitability",
    "⌂  Early Warning Monitor",
    "◈  Risk Indicators",
    "▦  MIS Dashboard",
    "▱  Report Pack",
    "◫  Credit Policy Simulator",
    "◇  Champion–Challenger",
    "▧  Vintage Diagnostic",
    "↔  Stock–Flow Analysis",
    "⌁  Advanced Collection",
    "◎  Risk Appetite",
    "◬  Stress Testing",
    "✓  Action Tracker",
    "◧  Data Quality",
    "▤  Data Dictionary",
    "⚙  Assumptions",
]
st.sidebar.markdown('<div class="section-label">Navigation</div>', unsafe_allow_html=True)
selected = st.sidebar.radio("Navigation", nav_items, label_visibility="collapsed")
page = selected.split("  ",1)[-1]

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div class="report-card">
<div style="color:#5ba0ff;font-weight:700;font-size:.77rem">About This Workbench</div>
<div class="small-note" style="margin-top:.4rem">
End-to-end visibility across consumer lending portfolio performance, risk quality, collections and profitability.
</div>
<hr>
<div class="small-note">Built with: Python, Streamlit, Plotly, Pandas, SQL-ready data model</div>
<div class="small-note" style="margin-top:.4rem">Author: Le Hoang Quan</div>
</div>
""", unsafe_allow_html=True)

# ---------- Header ----------
h1,h2 = st.columns([5.2,1.8], vertical_alignment="center")
with h1:
    st.title("Consumer Lending Portfolio Analytics Workbench - Author: Le Hoang Quan")
    st.markdown('<div class="subtle">End-to-End Portfolio Monitoring, Risk Analytics & Management Reporting</div>', unsafe_allow_html=True)
with h2:
    max_date = snaps["snapshot_date"].max().date()
    st.markdown(f"<div style='text-align:right;color:#a9bbcd;font-size:.75rem'>Data as of: <b style='color:white'>{max_date.strftime('%d %b %Y')}</b></div>", unsafe_allow_html=True)

# ---------- Top filter bar ----------
filter_box = st.container(border=True)
with filter_box:
    f1,f2,f3,f4,f5,f6,f7 = st.columns([1.15,1.65,1.15,1.15,1.15,1.15,.72])
    with f1:
        as_of = st.date_input("As of Date", max_date, min_value=snaps["snapshot_date"].min().date(), max_value=max_date)
    with f2:
        min_orig,max_orig=loans["origination_date"].min().date(),loans["origination_date"].max().date()
        orig_range = st.date_input("Origination Date", (min_orig,max_orig), min_value=min_orig, max_value=max_orig)
    with f3:
        product = st.selectbox("Product",["All"]+sorted(snaps["product"].unique().tolist()))
    with f4:
        channel = st.selectbox("Channel",["All"]+sorted(snaps["channel"].unique().tolist()))
    with f5:
        purpose = st.selectbox("Loan Purpose",["All"]+sorted(loans["loan_purpose"].unique().tolist()))
    with f6:
        region = st.selectbox("Geography",["All"]+sorted(snaps["region"].unique().tolist()))
    with f7:
        st.markdown("<div style='height:1.72rem'></div>",unsafe_allow_html=True)
        reset = st.button("↻ Clear",use_container_width=True)

products_sel=[] if product=="All" else [product]
channels_sel=[] if channel=="All" else [channel]
regions_sel=[] if region=="All" else [region]
df=filter_data(snaps,as_of,products_sel,channels_sel,regions_sel,[])
if isinstance(orig_range,(tuple,list)) and len(orig_range)==2:
    allowed=loans[(loans["origination_date"].dt.date>=orig_range[0])&(loans["origination_date"].dt.date<=orig_range[1])]["loan_id"]
    df=df[df["loan_id"].isin(allowed)]
if purpose!="All":
    df=df[df["loan_purpose"]==purpose]
latest=latest_snapshot(df)
metrics=kpis(df)

# Prior month metrics/deltas
all_dates=sorted(df["snapshot_date"].drop_duplicates())
prior_df=df[df["snapshot_date"]<=all_dates[-2]] if len(all_dates)>1 else df
prior=kpis(prior_df)
def pct_change(cur,prev):
    if not prev: return 0
    return (cur-prev)/abs(prev)
d_balance=pct_change(metrics["Total Balance"],prior["Total Balance"])
d_accounts=pct_change(metrics["Accounts"],prior["Accounts"])
d30=metrics["30+ DPD"]-prior["30+ DPD"]
d90=metrics["90+ DPD"]-prior["90+ DPD"]
dw=metrics["Net Write-off Rate"]-prior["Net Write-off Rate"]
dy=metrics["Portfolio Yield"]-prior["Portfolio Yield"]

# ---------- Executive Overview ----------
if page=="Executive Overview":
    c=st.columns(6)
    cards=[
        ("💲","Total Loan Balance (VND)",fmt_vnd(metrics["Total Balance"]),f"{d_balance:+.1%}",d_balance>=0,"#17539a"),
        ("👥","Total Outstanding Accounts",f"{metrics['Accounts']:,.0f}",f"{d_accounts:+.1%}",d_accounts>=0,"#3c348a"),
        ("❗","30+ DPD (% of Balance)",f"{metrics['30+ DPD']:.2%}",f"{d30:+.2%}",d30<=0,"#7f3737"),
        ("❗","90+ DPD (% of Balance)",f"{metrics['90+ DPD']:.2%}",f"{d90:+.2%}",d90<=0,"#7f3737"),
        ("🗑","Net Write-off Rate (LTM)",f"{metrics['Net Write-off Rate']:.2%}",f"{dw:+.2%}",dw<=0,"#6a551d"),
        ("📈","Portfolio Yield (LTM)",f"{metrics['Portfolio Yield']:.1%}",f"{dy:+.2%}",dy>=0,"#245b34"),
    ]
    for col,card in zip(c,cards):
        col.markdown(kpi_card(*card),unsafe_allow_html=True)

    st.write("")
    r1c1,r1c2,r1c3=st.columns([1.12,1.28,1.15])
    trend=balance_trend(df)
    mix=dpd_mix(df)
    with r1c1:
        st.markdown('<div class="panel">',unsafe_allow_html=True)
        fig=go.Figure(go.Scatter(
            x=trend["snapshot_date"],y=trend["outstanding_balance_vnd"]/1e9,
            mode="lines+markers+text",text=[f"{x:,.0f}" for x in trend["outstanding_balance_vnd"]/1e9],
            textposition="top center",line=dict(color=BLUE,width=3),marker=dict(size=7)
        ))
        fig.update_layout(title="Portfolio Balance Trend (VND Billion)")
        chart_style(fig,300,False)
        panel_chart("",fig)
        st.markdown("</div>",unsafe_allow_html=True)
    with r1c2:
        st.markdown('<div class="panel">',unsafe_allow_html=True)
        order=["Current","1-30","31-60","61-90","90+"]
        colors={"Current":GREEN,"1-30":AMBER,"31-60":ORANGE,"61-90":"#f16a43","90+":RED}
        fig=px.bar(mix,x="snapshot_date",y="share",color="dpd_bucket",
                   category_orders={"dpd_bucket":order},color_discrete_map=colors,
                   text=mix["share"].map(lambda x:f"{x:.1%}"))
        fig.update_traces(textfont_size=10)
        fig.update_yaxes(tickformat=".0%")
        fig.update_layout(title="Portfolio Quality – DPD Buckets (% of Balance)",barmode="stack")
        chart_style(fig,300,True)
        panel_chart("",fig)
        st.markdown("</div>",unsafe_allow_html=True)
    with r1c3:
        st.markdown('<div class="panel">',unsafe_allow_html=True)
        rr=roll_rates(df)
        ct=collection_trend(df)
        key=pd.DataFrame({
            "Metric":["30+ DPD","90+ DPD","Roll Rate to 30+ DPD","Roll Rate to 90+ DPD","Collection Rate","Net Write-off Rate","Cost of Risk"],
            "Value":[metrics["30+ DPD"],metrics["90+ DPD"],rr["Rate"].iloc[1],rr["Rate"].iloc[3],ct["collection_rate"].iloc[-1],metrics["Net Write-off Rate"],
                     df["expected_loss_vnd"].sum()/max(df.groupby("snapshot_date")["outstanding_balance_vnd"].sum().mean(),1)]
        })
        key["Value"]=key["Value"].map(lambda x:f"{x:.2%}")
        st.markdown('<div class="panel-title">Key Risk Indicators</div>',unsafe_allow_html=True)
        st.dataframe(key,hide_index=True,use_container_width=True,height=250)
        st.markdown("</div>",unsafe_allow_html=True)

    # Executive analytics row: use a wider two-column first row and full-width
    # collection chart below. This prevents title/legend collisions on laptop screens.
    r2c1,r2c2=st.columns([1.05,1.0])
    with r2c1:
        st.markdown('<div class="panel">',unsafe_allow_html=True)
        v=vintage_analysis(df)
        recent=v["vintage_month"].drop_duplicates().sort_values().tail(6)
        vv=v[v["vintage_month"].isin(recent)].copy()
        vv["vintage_label"]=pd.to_datetime(vv["vintage_month"]).dt.strftime("%Y-%m")
        fig=px.line(vv,x="mob",y="rate",color="vintage_label",markers=True)
        fig.update_yaxes(tickformat=".0%")
        fig.update_layout(
            title=dict(text="Vintage Analysis – 30+ DPD (% of Original Balance)",x=0.01,xanchor="left"),
            legend=dict(
                title_text="Vintage",
                orientation="h",
                yanchor="top",
                y=-0.16,
                xanchor="left",
                x=0,
                font=dict(size=10)
            ),
            margin=dict(l=30,r=20,t=70,b=90)
        )
        chart_style(fig,390,True)
        # Re-apply chart-specific spacing after the shared style helper.
        fig.update_layout(
            title=dict(text="Vintage Analysis – 30+ DPD (% of Original Balance)",x=0.01,xanchor="left"),
            legend=dict(title_text="Vintage",orientation="h",yanchor="top",y=-0.16,xanchor="left",x=0,font=dict(size=10)),
            margin=dict(l=30,r=20,t=70,b=90)
        )
        panel_chart("",fig)
        st.markdown("</div>",unsafe_allow_html=True)

    with r2c2:
        st.markdown('<div class="panel">',unsafe_allow_html=True)
        m=migration_matrix(df)
        fig=px.imshow(
            m,text_auto=".1%",aspect="auto",
            color_continuous_scale=[[0,"#183a53"],[.55,"#477c4e"],[1,"#9b463b"]],
            labels={"x":"To (Next Month DPD)","y":"From (Current DPD)","color":"Rate"}
        )
        chart_style(fig,390,False)
        fig.update_layout(
            title=dict(text="DPD Migration Matrix (% of Balance)",x=0.01,xanchor="left"),
            margin=dict(l=60,r=25,t=70,b=55)
        )
        panel_chart("",fig)
        st.markdown("</div>",unsafe_allow_html=True)

    st.markdown('<div class="panel">',unsafe_allow_html=True)
    ct=collection_trend(df)
    fig=go.Figure()
    fig.add_bar(
        x=ct["snapshot_date"],y=ct["actual_payment_vnd"]/1e9,
        name="Collected Amount",marker_color="#3476d7",
        text=(ct["actual_payment_vnd"]/1e9).round(0),textposition="inside"
    )
    fig.add_scatter(
        x=ct["snapshot_date"],y=ct["collection_rate"],
        name="Collection Rate",yaxis="y2",
        line=dict(color=GREEN,width=3),mode="lines+markers+text",
        text=ct["collection_rate"].map(lambda x:f"{x:.1%}"),
        textposition="top center"
    )
    chart_style(fig,360,True)
    fig.update_layout(
        title=dict(text="Collection Performance (3M Rolling)",x=0.01,xanchor="left"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10)
        ),
        margin=dict(l=45,r=65,t=85,b=40),
        yaxis=dict(title="Collected Amount (VND Bn)"),
        yaxis2=dict(
            title="Collection Rate",
            overlaying="y",side="right",
            tickformat=".0%",
            gridcolor="rgba(0,0,0,0)"
        )
    )
    panel_chart("",fig)
    st.markdown("</div>",unsafe_allow_html=True)

    r3c1,r3c2,r3c3=st.columns([1.12,1.28,1.15])
    with r3c1:
        st.markdown('<div class="panel">',unsafe_allow_html=True)
        prod=latest.groupby("product",as_index=False)["outstanding_balance_vnd"].sum()
        fig=px.pie(prod,names="product",values="outstanding_balance_vnd",hole=.58,
                   color_discrete_sequence=[BLUE,GREEN,AMBER,"#9b4aa0",LIGHTBLUE])
        fig.update_traces(textinfo="percent+label",textposition="outside")
        fig.update_layout(title="Portfolio by Product",annotations=[dict(text=f"{metrics['Total Balance']/1e9:,.0f}B<br>VND",x=.5,y=.5,font_size=15,showarrow=False)])
        chart_style(fig,290,False)
        panel_chart("",fig)
        st.markdown("</div>",unsafe_allow_html=True)
    with r3c2:
        st.markdown('<div class="panel">',unsafe_allow_html=True)
        p=profitability(df)
        inc=p["interest_income_vnd"].sum()
        fee=p["fee_income_vnd"].sum()
        op=p["operating_cost_vnd"].sum()+p["funding_cost_vnd"].sum()+p["expected_loss_vnd"].sum()
        net=p["net_profit_vnd"].sum()
        st.markdown('<div class="panel-title">Portfolio Profitability (LTM)</div>',unsafe_allow_html=True)
        a,b,c,d=st.columns(4)
        for col,label,val,color in [(a,"Interest Income",inc,"white"),(b,"Fee & Other Income",fee,"white"),(c,"Total Cost",op,"#ff705c"),(d,"Net Income",net,"white")]:
            col.markdown(f"<div style='border:1px solid #294158;border-radius:7px;padding:.55rem;text-align:center'><div class='small-note'>{label}</div><b style='font-size:1.0rem;color:{color}'>{fmt_vnd(val)}</b></div>",unsafe_allow_html=True)
        st.write("")
        a,b,c,d=st.columns(4)
        ratios=[
            ("Yield on Loans",metrics["Portfolio Yield"]),
            ("Cost to Income",op/max(inc+fee,1)),
            ("Cost of Risk",p["expected_loss_vnd"].sum()/max(p["balance"].mean(),1)),
            ("ROA (LTM)",net/max(p["balance"].mean(),1))
        ]
        for col,(label,val) in zip([a,b,c,d],ratios):
            col.markdown(f"<div style='border:1px solid #294158;border-radius:7px;padding:.55rem;text-align:center'><div class='small-note'>{label}</div><b style='font-size:1.0rem;color:#67d277'>{val:.2%}</b></div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)
    with r3c3:
        st.markdown('<div class="panel">',unsafe_allow_html=True)
        conc=latest.groupby("customer_id",as_index=False)["outstanding_balance_vnd"].sum().sort_values("outstanding_balance_vnd",ascending=False)
        total=conc["outstanding_balance_vnd"].sum()
        vals=[]
        for n in [10,50,100,500]:
            vals.append([f"Top {n} Customers",conc.head(n)["outstanding_balance_vnd"].sum()/max(total,1)])
        con=pd.DataFrame(vals,columns=["Group","Share"])
        fig=px.bar(con,x="Share",y="Group",orientation="h",text=con["Share"].map(lambda x:f"{x:.2%}"),
                   color_discrete_sequence=[BLUE])
        fig.update_xaxes(tickformat=".0%")
        fig.update_layout(title="Concentration Analysis (% of Total Balance)")
        chart_style(fig,290,False)
        panel_chart("",fig)
        st.markdown("</div>",unsafe_allow_html=True)

    st.markdown("<div class='small-note'>Note: All metrics are calculated on loan balance unless otherwise specified. DPD = Days Past Due. LTM = Last Twelve Months. Synthetic demonstration data.</div>",unsafe_allow_html=True)

# ---------- Detail pages ----------
elif page=="Portfolio Overview":
    st.subheader("Portfolio Overview")

    # Responsive 2x2 layout to avoid overlap on laptop screens.
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    chart_specs = [
        (row1_col1, "product", "Balance by Product"),
        (row1_col2, "channel", "Balance by Channel"),
        (row2_col1, "region", "Balance by Region"),
        (row2_col2, "risk_band", "Balance by Risk Band"),
    ]

    for container, dim, title in chart_specs:
        g = latest.groupby(dim, as_index=False)["outstanding_balance_vnd"].sum()
        fig = px.pie(
            g,
            names=dim,
            values="outstanding_balance_vnd",
            hole=.52,
            title=title
        )
        chart_style(fig, 340, True)
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0
            ),
            margin=dict(l=10, r=10, t=70, b=20)
        )
        container.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False}
        )

    view = latest.groupby(["product", "risk_band"], as_index=False).agg(
        Balance=("outstanding_balance_vnd", "sum"),
        Accounts=("loan_id", "nunique"),
        Average_DPD=("dpd", "mean")
    )
    st.dataframe(view, use_container_width=True, hide_index=True)

elif page=="Vintage Analysis":
    st.subheader("Vintage Analysis")
    threshold=st.segmented_control("Delinquency Threshold",[30,60,90],default=30)
    v=vintage_analysis(df,threshold)
    fig=px.line(v,x="mob",y="rate",color="vintage_month",markers=True,title=f"{threshold}+ DPD by Vintage and Months on Book")
    fig.update_yaxes(tickformat=".1%"); chart_style(fig,480,True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    pivot=v.pivot_table(index="vintage_month",columns="mob",values="rate",aggfunc="max")
    st.dataframe(pivot.style.format("{:.2%}"),use_container_width=True)

elif page=="Roll Rate Analysis":
    st.subheader("Roll Rate Analysis")
    rr=roll_rates(df)
    fig=px.bar(rr,x="Metric",y="Rate",text_auto=".2%",title="Transition Rates Between Delinquency States")
    fig.update_yaxes(tickformat=".0%");chart_style(fig,430,False)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.dataframe(rr.style.format({"Rate":"{:.2%}"}),hide_index=True,use_container_width=True)
    st.info("Use roll rates to forecast future delinquency, prioritize collection resources and detect underwriting deterioration.")

elif page=="DPD Migration":
    st.subheader("DPD Migration")
    m=migration_matrix(df)
    fig=px.imshow(m,text_auto=".1%",aspect="auto",color_continuous_scale="RdYlGn_r",
                  labels={"x":"To Bucket","y":"From Bucket","color":"Transition Rate"})
    chart_style(fig,500,False)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.dataframe(m.style.format("{:.2%}"),use_container_width=True)

elif page=="Delinquency Analysis":
    st.subheader("Delinquency Analysis")
    d=dpd_mix(df)
    fig=px.area(d,x="snapshot_date",y="share",color="dpd_bucket",
                category_orders={"dpd_bucket":["Current","1-30","31-60","61-90","90+"]},
                title="DPD Bucket Mix Trend")
    fig.update_yaxes(tickformat=".0%");chart_style(fig,430,True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    seg=latest.groupby(["product","dpd_bucket"],as_index=False)["outstanding_balance_vnd"].sum()
    seg["share"]=seg["outstanding_balance_vnd"]/seg.groupby("product")["outstanding_balance_vnd"].transform("sum")
    st.dataframe(seg.pivot(index="product",columns="dpd_bucket",values="share").fillna(0).style.format("{:.2%}"),use_container_width=True)

elif page=="Collection Analytics":
    st.subheader("Collection Analytics")
    ct=collection_trend(df)
    a,b=st.columns(2)
    fig=go.Figure()
    fig.add_bar(x=ct["snapshot_date"],y=ct["actual_payment_vnd"]/1e9,name="Actual Payment")
    fig.add_bar(x=ct["snapshot_date"],y=ct["recovery_amount_vnd"]/1e9,name="Recovery")
    fig.update_layout(title="Collection Amount (VND Bn)",barmode="group");chart_style(fig,400,True)
    a.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    fig=px.line(ct,x="snapshot_date",y="collection_rate",markers=True,title="Collection Rate")
    fig.update_yaxes(tickformat=".0%");chart_style(fig,400,False)
    b.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    stage=latest.groupby("collection_stage",as_index=False).agg(Balance=("outstanding_balance_vnd","sum"),Accounts=("loan_id","nunique"))
    st.dataframe(stage,use_container_width=True,hide_index=True)

elif page=="Portfolio Profitability":
    st.subheader("Portfolio Profitability")
    p=profitability(df)
    fig=px.bar(p,x="snapshot_date",y="net_profit_vnd",title="Monthly Risk-adjusted Net Profit")
    chart_style(fig,400,False)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    dim=st.selectbox("Segmentation",["product","channel","region","risk_band"])
    sp=segment_profitability(df,dim)
    a,b=st.columns(2)
    fig=px.bar(sp,x=dim,y="net_profit",title=f"Net Profit by {dim.title()}");chart_style(fig,400,False)
    a.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    fig=px.scatter(sp,x="balance",y="profit_margin",size="balance",color=dim,title="Risk–Return Positioning")
    fig.update_yaxes(tickformat=".0%");chart_style(fig,400,True)
    b.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.dataframe(sp,use_container_width=True,hide_index=True)

elif page=="Early Warning Monitor":
    st.subheader("Early Warning Monitor")
    ew=early_warning(df)
    level=st.multiselect("Risk Level",["High","Medium","Low"],default=["High","Medium"])
    view=ew[ew["risk_level"].isin(level)]
    fig=px.scatter(ew,x="dpd30",y="dpd90",size="balance",color="risk_level",hover_name="segment",
                   title="Early Warning Segment Map",color_discrete_map={"High":RED,"Medium":AMBER,"Low":GREEN})
    fig.update_xaxes(tickformat=".0%");fig.update_yaxes(tickformat=".0%");chart_style(fig,430,True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.dataframe(view.style.format({"balance":"{:,.0f}","dpd30":"{:.2%}","dpd90":"{:.2%}"}),use_container_width=True,hide_index=True)

elif page=="Risk Indicators":
    st.subheader("Risk Indicators")
    monthly=df.groupby("snapshot_date").apply(lambda x: pd.Series({
        "Balance":x["outstanding_balance_vnd"].sum(),
        "30+ DPD":x.loc[x["dpd"]>=30,"outstanding_balance_vnd"].sum()/max(x["outstanding_balance_vnd"].sum(),1),
        "90+ DPD":x.loc[x["dpd"]>=90,"outstanding_balance_vnd"].sum()/max(x["outstanding_balance_vnd"].sum(),1),
        "Write-off":x["write_off_amount_vnd"].sum()/max(x["outstanding_balance_vnd"].sum(),1)
    }),include_groups=False).reset_index()
    fig=px.line(monthly,x="snapshot_date",y=["30+ DPD","90+ DPD","Write-off"],markers=True,title="Risk Indicator Trend")
    fig.update_yaxes(tickformat=".0%");chart_style(fig,440,True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.dataframe(monthly.style.format({"Balance":"{:,.0f}","30+ DPD":"{:.2%}","90+ DPD":"{:.2%}","Write-off":"{:.2%}"}),use_container_width=True,hide_index=True)

elif page=="MIS Dashboard":
    st.subheader("Management Information System Dashboard")
    by_prod=latest.groupby("product").apply(lambda x: pd.Series({
        "Balance":x["outstanding_balance_vnd"].sum(),
        "Accounts":x["loan_id"].nunique(),
        "30+ DPD":x.loc[x["dpd"]>=30,"outstanding_balance_vnd"].sum()/max(x["outstanding_balance_vnd"].sum(),1),
        "90+ DPD":x.loc[x["dpd"]>=90,"outstanding_balance_vnd"].sum()/max(x["outstanding_balance_vnd"].sum(),1)
    }),include_groups=False).reset_index()
    st.dataframe(by_prod.style.format({"Balance":"{:,.0f}","30+ DPD":"{:.2%}","90+ DPD":"{:.2%}"}),use_container_width=True,hide_index=True)
    st.download_button("Download MIS CSV",by_prod.to_csv(index=False).encode(),"management_mis.csv","text/csv")

elif page=="Report Pack":
    st.subheader("Management Report Pack")
    actions=management_actions(df)
    a,b,c,d=st.columns(4)
    a.metric("Portfolio Balance",fmt_vnd(metrics["Total Balance"]))
    b.metric("30+ DPD",f"{metrics['30+ DPD']:.2%}")
    c.metric("90+ DPD",f"{metrics['90+ DPD']:.2%}")
    d.metric("Portfolio Yield",f"{metrics['Portfolio Yield']:.2%}")
    st.markdown("### Executive Insights and Recommended Actions")
    st.dataframe(actions,hide_index=True,use_container_width=True)
    report=f"""CONSUMER LENDING PORTFOLIO MANAGEMENT REPORT
As of: {as_of}
Total balance: {metrics['Total Balance']:,.0f} VND
Accounts: {metrics['Accounts']:,.0f}
30+ DPD: {metrics['30+ DPD']:.2%}
90+ DPD: {metrics['90+ DPD']:.2%}
Net write-off rate: {metrics['Net Write-off Rate']:.2%}
Portfolio yield: {metrics['Portfolio Yield']:.2%}

ACTIONS
{actions.to_string(index=False)}
"""
    st.download_button("Download Management Report",report.encode(),"portfolio_management_report.txt","text/plain")


elif page=="Credit Policy Simulator":
    st.subheader("Credit Policy Simulator")
    c1,c2,c3,c4=st.columns(4)
    score=c1.slider("Minimum Credit Score",450,800,620,10)
    amount=c2.slider("Maximum Loan Amount (VND mn)",20,300,220,10)*1_000_000
    c3,c4=st.columns(2)
    tenor=c3.slider("Maximum Tenor (months)",6,48,36,6)
    exclude=c4.multiselect("Exclude Risk Bands",["A","B","C","D","E"],default=["E"])
    r=policy_simulator(loans,score,amount,tenor,exclude)
    cols=st.columns(5)
    vals=[("Approval Rate",f"{r['approval_rate']:.1%}"),("Approved Volume",fmt_vnd(r["approved_volume"])),("Expected PD",f"{r['avg_pd']:.2%}"),("Expected Loss",fmt_vnd(r["expected_loss"])),("Expected Profit",fmt_vnd(r["expected_profit"]))]
    for c,(n,v) in zip(cols,vals): c.metric(n,v)
    if len(r["eligible"]):
        g=r["eligible"].groupby("risk_band",as_index=False).original_amount_vnd.sum()
        fig=px.bar(g,x="risk_band",y="original_amount_vnd",title="Approved Volume by Risk Band")
        chart_style(fig,400,False); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

elif page=="Champion–Challenger":
    st.subheader("Champion–Challenger Strategy")
    cc=champion_challenger(loans)
    st.dataframe(cc.style.format({"Approval Rate":"{:.1%}","Approved Volume":"{:,.0f}","Expected PD":"{:.2%}","Expected Loss":"{:,.0f}","Expected Profit":"{:,.0f}"}),use_container_width=True,hide_index=True)
    fig=px.scatter(cc,x="Approval Rate",y="Expected Profit",size="Approved Volume",color="Strategy",hover_data=["Expected PD"],title="Growth vs Profitability")
    fig.update_xaxes(tickformat=".0%"); chart_style(fig,460,True); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

elif page=="Vintage Diagnostic":
    st.subheader("Vintage & Segment Diagnostic")
    d=vintage_diagnostic(df)
    st.dataframe(d.style.format({"Balance":"{:,.0f}","DPD30":"{:.2%}","DPD90":"{:.2%}","Variance_vs_Portfolio":"{:+.2%}"}),use_container_width=True,hide_index=True)
    top=d.head(15); fig=px.bar(top,x="Variance_vs_Portfolio",y="Segment",color="Flag",orientation="h",title="Largest 30+ DPD Variances vs Portfolio")
    fig.update_xaxes(tickformat="+.1%"); chart_style(fig,500,True); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

elif page=="Stock–Flow Analysis":
    st.subheader("NPL Stock–Flow Analysis")
    f=flow_analysis(df); long=f.melt(id_vars="snapshot_date",var_name="Flow",value_name="Amount")
    fig=px.bar(long,x="snapshot_date",y="Amount",color="Flow",barmode="group",title="New NPL, Cure, Write-off and Recovery")
    chart_style(fig,460,True); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False}); st.dataframe(f,use_container_width=True,hide_index=True)

elif page=="Advanced Collection":
    st.subheader("Advanced Collection Analytics")
    f=collection_funnel(df); fig=go.Figure(go.Funnel(y=f.Stage,x=f.Accounts,textinfo="value+percent initial"))
    fig.update_layout(title="Collection Funnel"); chart_style(fig,500,False); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.dataframe(f,use_container_width=True,hide_index=True)

elif page=="Risk Appetite":
    st.subheader("Risk Appetite Dashboard")
    r=risk_appetite(df,metrics)
    st.dataframe(r.style.format({"Actual":"{:.2%}","Limit":"{:.2%}","Utilization":"{:.0%}"}),use_container_width=True,hide_index=True)
    fig=px.bar(r,x="Indicator",y="Utilization",color="Status",text=r.Utilization.map(lambda x:f"{x:.0%}"),title="Risk Appetite Utilization")
    fig.add_hline(y=1,line_dash="dash"); chart_style(fig,430,True); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

elif page=="Stress Testing":
    st.subheader("Portfolio Stress Testing")
    s=stress_test(df)
    st.dataframe(s.style.format({"30+ DPD":"{:.2%}","90+ DPD":"{:.2%}","Expected Loss":"{:,.0f}","Monthly Net Profit":"{:,.0f}"}),use_container_width=True,hide_index=True)
    fig=px.bar(s,x="Scenario",y=["30+ DPD","90+ DPD"],barmode="group",title="Credit Quality Under Stress")
    fig.update_yaxes(tickformat=".0%"); chart_style(fig,430,True); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

elif page=="Action Tracker":
    st.subheader("Management Action Tracker")
    t=pd.DataFrame([["Raise score cut-off for deteriorating segment","Credit Policy","31 Jul 2026","In Progress","30+ DPD -0.4 pp"],
    ["Reallocate 31–60 DPD cases","Collection","15 Jul 2026","Completed","Cure rate +3 pp"],
    ["Review digital channel pricing","Portfolio Strategy","15 Aug 2026","Planned","Margin +0.8 pp"]],
    columns=["Action","Owner","Deadline","Status","Expected Impact"])
    edited=st.data_editor(t,use_container_width=True,hide_index=True,num_rows="dynamic")
    st.download_button("Download Action Tracker",edited.to_csv(index=False).encode(),"action_tracker.csv","text/csv")

elif page=="Data Quality":
    st.subheader("Data Quality & Reconciliation")
    checks,score=data_quality(loans,snaps)
    st.metric("Data Quality Score",f"{score:.2f}%"); st.dataframe(checks,use_container_width=True,hide_index=True)
    fig=px.bar(checks,x="Check",y="Exceptions",title="Data Quality Exceptions")
    chart_style(fig,400,False); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})


elif page=="Data Dictionary":
    st.subheader("Data Dictionary")
    dictionary=pd.DataFrame([
        ["loan_master.csv","loan_id","Unique loan/account identifier"],
        ["loan_master.csv","origination_date","Booking/origination date"],
        ["loan_master.csv","loan_purpose","Stated lending purpose"],
        ["monthly_snapshots.csv","mob","Months on book"],
        ["monthly_snapshots.csv","dpd","Days past due"],
        ["monthly_snapshots.csv","dpd_bucket","Current, 1-30, 31-60, 61-90, 90+"],
        ["monthly_snapshots.csv","actual_payment_vnd","Amount actually collected"],
        ["monthly_snapshots.csv","write_off_amount_vnd","Written-off balance"],
        ["monthly_snapshots.csv","expected_loss_vnd","Synthetic expected-loss estimate"],
    ],columns=["Dataset","Field","Definition"])
    st.dataframe(dictionary,use_container_width=True,hide_index=True)
    st.warning("All data are synthetic. Replace the files in /data using the same field names for production use.")

elif page=="Assumptions":
    st.subheader("Assumptions and Risk Appetite")
    assumptions=pd.read_csv(DATA_DIR/"assumptions.csv")
    st.dataframe(assumptions,use_container_width=True,hide_index=True)
    st.info("The assumptions sheet is also available in the accompanying Excel workbook.")
