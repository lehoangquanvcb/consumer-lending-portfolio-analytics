import pandas as pd
import numpy as np

def safe_div(a,b): return 0.0 if not b or pd.isna(b) else a/b

def policy_simulator(loans,min_score=620,max_amount=220000000,max_tenor=36,exclude_risk=None):
    x=loans.copy()
    e=x[(x.risk_score>=min_score)&(x.original_amount_vnd<=max_amount)&(x.tenor_months<=max_tenor)].copy()
    if exclude_risk: e=e[~e.risk_band.isin(exclude_risk)]
    pdm={"A":.012,"B":.022,"C":.04,"D":.075,"E":.14}; lgd={"A":.30,"B":.35,"C":.42,"D":.50,"E":.60}
    e["pd_proxy"]=e.risk_band.map(pdm); e["lgd_proxy"]=e.risk_band.map(lgd)
    e["expected_loss"]=e.original_amount_vnd*e.pd_proxy*e.lgd_proxy
    e["expected_profit"]=e.original_amount_vnd*(e.annual_interest_rate-.085)-e.expected_loss-850000
    return {"eligible":e,"approval_rate":safe_div(len(e),len(x)),"approved_volume":e.original_amount_vnd.sum(),
            "expected_loss":e.expected_loss.sum(),"expected_profit":e.expected_profit.sum(),
            "avg_pd":e.pd_proxy.mean() if len(e) else 0}

def champion_challenger(loans):
    specs=[("Champion",580,300000000,48,[]),("Tighter Cut-off",650,250000000,36,["E"]),
           ("Risk-Controlled Growth",620,220000000,36,["E"]),("Prime Growth",700,300000000,48,["D","E"])]
    rows=[]
    for n,s,a,t,e in specs:
        r=policy_simulator(loans,s,a,t,e); rows.append([n,s,r["approval_rate"],r["approved_volume"],r["avg_pd"],r["expected_loss"],r["expected_profit"]])
    return pd.DataFrame(rows,columns=["Strategy","Min Score","Approval Rate","Approved Volume","Expected PD","Expected Loss","Expected Profit"])

def risk_appetite(df,metrics):
    latest=df[df.snapshot_date==df.snapshot_date.max()]; bal=latest.outstanding_balance_vnd.sum()
    cor=df.expected_loss_vnd.sum()/max(df.groupby("snapshot_date").outstanding_balance_vnd.sum().mean(),1)
    rows=[["30+ DPD",metrics["30+ DPD"],.035],["90+ DPD",metrics["90+ DPD"],.018],["Cost of Risk",cor,.03],
          ["Digital Concentration",latest.loc[latest.channel=="Digital","outstanding_balance_vnd"].sum()/max(bal,1),.45],
          ["D/E Risk Band Share",latest.loc[latest.risk_band.isin(["D","E"]),"outstanding_balance_vnd"].sum()/max(bal,1),.18]]
    o=pd.DataFrame(rows,columns=["Indicator","Actual","Limit"]); o["Utilization"]=o.Actual/o.Limit
    o["Status"]=np.select([o.Utilization>1,o.Utilization>=.85],["Breach","Watch"],default="Within"); return o

def flow_analysis(df):
    x=df[["loan_id","snapshot_date","dpd_bucket","outstanding_balance_vnd","write_off_amount_vnd","recovery_amount_vnd"]].sort_values(["loan_id","snapshot_date"]).copy()
    x["prior"]=x.groupby("loan_id").dpd_bucket.shift()
    x["New NPL"]=np.where((x.dpd_bucket=="90+")&(x.prior!="90+"),x.outstanding_balance_vnd,0)
    x["Cure"]=np.where((x.dpd_bucket=="Current")&(x.prior.isin(["1-30","31-60","61-90","90+"])),x.outstanding_balance_vnd,0)
    return x.groupby("snapshot_date",as_index=False).agg(New_NPL=("New NPL","sum"),Cure=("Cure","sum"),Write_off=("write_off_amount_vnd","sum"),Recovery=("recovery_amount_vnd","sum"))

def vintage_diagnostic(df):
    latest=df[df.snapshot_date==df.snapshot_date.max()]; rows=[]
    for dim in ["product","channel","region","risk_band","loan_purpose"]:
        g=latest.groupby(dim).apply(lambda x: pd.Series({"Balance":x.outstanding_balance_vnd.sum(),
        "DPD30":x.loc[x.dpd>=30,"outstanding_balance_vnd"].sum()/max(x.outstanding_balance_vnd.sum(),1),
        "DPD90":x.loc[x.dpd>=90,"outstanding_balance_vnd"].sum()/max(x.outstanding_balance_vnd.sum(),1)}),include_groups=False).reset_index()
        g["Dimension"]=dim; g=g.rename(columns={dim:"Segment"}); rows.append(g)
    o=pd.concat(rows); bench=latest.loc[latest.dpd>=30,"outstanding_balance_vnd"].sum()/max(latest.outstanding_balance_vnd.sum(),1)
    o["Variance_vs_Portfolio"]=o.DPD30-bench; o["Flag"]=np.select([o.Variance_vs_Portfolio>.015,o.Variance_vs_Portfolio>.005],["Deteriorating","Watch"],default="Normal")
    return o.sort_values("Variance_vs_Portfolio",ascending=False)

def collection_funnel(df):
    l=df[df.snapshot_date==df.snapshot_date.max()]; n=len(l[l.dpd>0]); vals=[n,int(n*.78),int(n*.56),int(n*.31),int(n*.21),int(n*.10)]
    return pd.DataFrame({"Stage":["Assigned","Contacted","Right-Party Contact","Promise to Pay","Payment Received","Cured"],"Accounts":vals})

def stress_test(df):
    l=df[df.snapshot_date==df.snapshot_date.max()]; bal=l.outstanding_balance_vnd.sum()
    d30=l.loc[l.dpd>=30,"outstanding_balance_vnd"].sum()/max(bal,1); d90=l.loc[l.dpd>=90,"outstanding_balance_vnd"].sum()/max(bal,1)
    loss=df.expected_loss_vnd.sum()/max(df.snapshot_date.nunique(),1); base=(df.interest_income_vnd.sum()+df.fee_income_vnd.sum()-df.funding_cost_vnd.sum()-df.operating_cost_vnd.sum())/max(df.snapshot_date.nunique(),1)
    return pd.DataFrame([["Base",d30,d90,loss,base-loss],["Moderate Stress",d30*1.25,d90*1.38,loss*1.35,base-loss*1.35-bal*.015/12],
    ["Severe Stress",d30*1.60,d90*1.90,loss*1.90,base-loss*1.90-bal*.035/12]],columns=["Scenario","30+ DPD","90+ DPD","Expected Loss","Monthly Net Profit"])

def data_quality(loans,snaps):
    rows=[["Duplicate loan IDs",loans.loan_id.duplicated().sum()],["Missing loan IDs",loans.loan_id.isna().sum()+snaps.loan_id.isna().sum()],
    ["Negative balances",(snaps.outstanding_balance_vnd<0).sum()],["Invalid DPD",(snaps.dpd<0).sum()],["Orphan snapshots",(~snaps.loan_id.isin(loans.loan_id)).sum()]]
    o=pd.DataFrame(rows,columns=["Check","Exceptions"]); return o,max(0,100-o.Exceptions.sum()/max(len(snaps),1)*100)
