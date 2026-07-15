
from pathlib import Path
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

@pd.cache_data(show_spinner=False) if hasattr(pd, "cache_data") else (lambda f:f)
def load_data():
    loans = pd.read_csv(DATA_DIR / "loan_master.csv", parse_dates=["origination_date"])
    snaps = pd.read_csv(DATA_DIR / "monthly_snapshots.csv", parse_dates=["snapshot_date"])
    snaps["snapshot_month"] = snaps["snapshot_date"].dt.to_period("M").astype(str)
    loans["vintage_month"] = loans["origination_date"].dt.to_period("M").astype(str)
    snaps = snaps.merge(loans[["loan_id","vintage_month","original_amount_vnd","annual_interest_rate","loan_purpose"]],
                        on="loan_id", how="left")
    return loans, snaps

def filter_data(snaps, as_of, products, channels, regions, risk_bands):
    df = snaps[snaps["snapshot_date"] <= pd.Timestamp(as_of)].copy()
    if products: df=df[df["product"].isin(products)]
    if channels: df=df[df["channel"].isin(channels)]
    if regions: df=df[df["region"].isin(regions)]
    if risk_bands: df=df[df["risk_band"].isin(risk_bands)]
    return df

def latest_snapshot(df):
    if df.empty: return df
    return df[df["snapshot_date"]==df["snapshot_date"].max()].copy()

def safe_div(a,b):
    return 0 if b in (0,None) or pd.isna(b) else a/b

def kpis(df):
    latest=latest_snapshot(df)
    bal=latest["outstanding_balance_vnd"].sum()
    accounts=latest["loan_id"].nunique()
    dpd30=latest.loc[latest["dpd"]>=30,"outstanding_balance_vnd"].sum()
    dpd90=latest.loc[latest["dpd"]>=90,"outstanding_balance_vnd"].sum()
    woff=df["write_off_amount_vnd"].sum()
    avg_bal=df.groupby("snapshot_date")["outstanding_balance_vnd"].sum().mean()
    income=df["interest_income_vnd"].sum()+df["fee_income_vnd"].sum()
    months=max(df["snapshot_date"].nunique(),1)
    return {
        "Total Balance":bal, "Accounts":accounts, "30+ DPD":safe_div(dpd30,bal),
        "90+ DPD":safe_div(dpd90,bal), "Net Write-off Rate":safe_div(woff,avg_bal),
        "Portfolio Yield":safe_div(income,avg_bal)*12/months
    }

def balance_trend(df):
    return df.groupby("snapshot_date",as_index=False)["outstanding_balance_vnd"].sum()

def dpd_mix(df):
    out=df.groupby(["snapshot_date","dpd_bucket"],as_index=False)["outstanding_balance_vnd"].sum()
    out["share"]=out["outstanding_balance_vnd"]/out.groupby("snapshot_date")["outstanding_balance_vnd"].transform("sum")
    return out

def vintage_analysis(df, threshold=30):
    tmp=df[df["dpd"]>=threshold].groupby(["vintage_month","mob"],as_index=False)["outstanding_balance_vnd"].sum()
    den=df.groupby(["vintage_month","mob"],as_index=False)["original_amount_vnd"].sum()
    out=den.merge(tmp,on=["vintage_month","mob"],how="left").fillna(0)
    out["rate"]=out["outstanding_balance_vnd"]/out["original_amount_vnd"].replace(0,np.nan)
    return out

def migration_matrix(df):
    cols=["Current","1-30","31-60","61-90","90+"]
    x=df[["loan_id","snapshot_date","dpd_bucket","outstanding_balance_vnd"]].sort_values(["loan_id","snapshot_date"])
    x["next_bucket"]=x.groupby("loan_id")["dpd_bucket"].shift(-1)
    x=x.dropna(subset=["next_bucket"])
    m=x.pivot_table(index="dpd_bucket",columns="next_bucket",values="outstanding_balance_vnd",aggfunc="sum",fill_value=0)
    m=m.reindex(index=cols,columns=cols,fill_value=0)
    return m.div(m.sum(axis=1).replace(0,np.nan),axis=0).fillna(0)

def roll_rates(df):
    m=migration_matrix(df)
    return pd.DataFrame({
        "Metric":["Current → 1-30","1-30 → 31-60","31-60 → 61-90","61-90 → 90+","Delinquent → Current"],
        "Rate":[m.loc["Current","1-30"],m.loc["1-30","31-60"],m.loc["31-60","61-90"],m.loc["61-90","90+"],
                m.loc[["1-30","31-60","61-90","90+"],"Current"].mean()]
    })

def collection_trend(df):
    out=df.groupby("snapshot_date",as_index=False).agg(
        scheduled_payment_vnd=("scheduled_payment_vnd","sum"),
        actual_payment_vnd=("actual_payment_vnd","sum"),
        recovery_amount_vnd=("recovery_amount_vnd","sum"))
    out["collection_rate"]=out["actual_payment_vnd"]/out["scheduled_payment_vnd"].replace(0,np.nan)
    return out

def profitability(df):
    out=df.groupby("snapshot_date",as_index=False).agg(
        interest_income_vnd=("interest_income_vnd","sum"), fee_income_vnd=("fee_income_vnd","sum"),
        funding_cost_vnd=("funding_cost_vnd","sum"), operating_cost_vnd=("operating_cost_vnd","sum"),
        expected_loss_vnd=("expected_loss_vnd","sum"), balance=("outstanding_balance_vnd","sum"))
    out["net_profit_vnd"]=out["interest_income_vnd"]+out["fee_income_vnd"]-out["funding_cost_vnd"]-out["operating_cost_vnd"]-out["expected_loss_vnd"]
    out["roa_monthly"]=out["net_profit_vnd"]/out["balance"].replace(0,np.nan)
    return out

def segment_profitability(df, dimension="product"):
    out=df.groupby(dimension,as_index=False).agg(
        balance=("outstanding_balance_vnd","sum"), interest=("interest_income_vnd","sum"), fees=("fee_income_vnd","sum"),
        funding=("funding_cost_vnd","sum"), opex=("operating_cost_vnd","sum"), loss=("expected_loss_vnd","sum"))
    out["net_profit"]=out["interest"]+out["fees"]-out["funding"]-out["opex"]-out["loss"]
    out["profit_margin"]=out["net_profit"]/(out["interest"]+out["fees"]).replace(0,np.nan)
    return out

def early_warning(df):
    latest=latest_snapshot(df)
    rows=[]
    for dim in ["product","channel","region","risk_band"]:
        g=latest.groupby(dim).apply(lambda x: pd.Series({
            "balance":x["outstanding_balance_vnd"].sum(),
            "dpd30":x.loc[x["dpd"]>=30,"outstanding_balance_vnd"].sum()/max(x["outstanding_balance_vnd"].sum(),1),
            "dpd90":x.loc[x["dpd"]>=90,"outstanding_balance_vnd"].sum()/max(x["outstanding_balance_vnd"].sum(),1),
            "accounts":x["loan_id"].nunique()
        })).reset_index()
        g["dimension"]=dim
        g=g.rename(columns={dim:"segment"})
        rows.append(g)
    out=pd.concat(rows,ignore_index=True)
    out["risk_level"]=np.select([out["dpd90"]>=0.03,out["dpd30"]>=0.06],["High","Medium"],default="Low")
    return out

def management_actions(df):
    k=kpis(df)
    actions=[]
    if k["30+ DPD"]>0.035:
        actions.append(("Credit Quality","High","30+ DPD is above risk appetite","Tighten cut-offs for weak segments and review recent vintages."))
    if k["90+ DPD"]>0.018:
        actions.append(("NPL","High","90+ DPD is elevated","Prioritize late-stage collection and restructure viable borrowers."))
    c=collection_trend(df)
    if not c.empty and c["collection_rate"].iloc[-1]<0.33:
        actions.append(("Collection","Medium","Collection rate below target","Reallocate cases, refine contact strategy and monitor cure rates."))
    p=profitability(df)
    if not p.empty and p["net_profit_vnd"].iloc[-1]<0:
        actions.append(("Profitability","High","Portfolio is loss-making","Reprice, reduce high-cost channels and tighten risk appetite."))
    if not actions:
        actions.append(("Portfolio","Low","Metrics are within broad thresholds","Maintain monitoring and test targeted growth in profitable segments."))
    return pd.DataFrame(actions,columns=["Area","Priority","Insight","Recommended Action"])
