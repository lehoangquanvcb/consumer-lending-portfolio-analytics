
import pandas as pd
import numpy as np
from modules.strategy_engine import policy_simulator, champion_challenger, vintage_diagnostic, risk_appetite, stress_test

def portfolio_health(metrics, appetite):
    breaches=(appetite["Status"]=="Breach").sum()
    watches=(appetite["Status"]=="Watch").sum()
    if breaches>=2 or metrics["90+ DPD"]>0.025: return "RED"
    if breaches>=1 or watches>=2: return "AMBER"
    return "GREEN"

def decision_cockpit(df, loans, metrics):
    appetite=risk_appetite(df,metrics)
    diag=vintage_diagnostic(df)
    top=diag.iloc[0]
    cc=champion_challenger(loans)
    best=cc.sort_values("Expected Profit",ascending=False).iloc[0]
    health=portfolio_health(metrics,appetite)
    issues=[]
    for _,r in appetite[appetite["Status"].isin(["Breach","Watch"])].head(3).iterrows():
        issues.append(f"{r['Indicator']}: {r['Status']} ({r['Actual']:.2%} vs limit {r['Limit']:.2%})")
    if len(issues)<3:
        issues.append(f"Highest deterioration: {top['Dimension']} / {top['Segment']} ({top['DPD30']:.2%} 30+ DPD)")
    return {
        "health":health,
        "issues":issues[:3],
        "top_driver":f"{top['Dimension']} / {top['Segment']}",
        "best_strategy":best["Strategy"],
        "best_profit":best["Expected Profit"],
        "appetite":appetite
    }

def management_insights(df, loans, metrics):
    diag=vintage_diagnostic(df)
    appetite=risk_appetite(df,metrics)
    top=diag.iloc[0]
    breaches=appetite[appetite.Status=="Breach"]
    rows=[]
    rows.append({
        "Priority":"High" if len(breaches) else "Medium",
        "Observation":f"30+ DPD is {metrics['30+ DPD']:.2%}; 90+ DPD is {metrics['90+ DPD']:.2%}.",
        "Diagnosis":f"The highest relative deterioration is {top['Dimension']} / {top['Segment']}, with 30+ DPD of {top['DPD30']:.2%}.",
        "Business Impact":f"{len(breaches)} risk-appetite indicator(s) are currently breached.",
        "Recommendation":f"Test tighter underwriting and early-intervention rules for {top['Segment']} before broad portfolio deployment.",
        "Decision Required":"Approve controlled champion–challenger test."
    })
    return pd.DataFrame(rows)

def strategy_optimizer(loans, objective="Maximize Expected Profit", min_approval=0.45, max_pd=0.06):
    scores=range(560,721,20)
    amounts=[150_000_000,200_000_000,250_000_000,300_000_000]
    tenors=[24,36,48]
    exclusions=[[],["E"],["D","E"]]
    rows=[]
    for score in scores:
        for amount in amounts:
            for tenor in tenors:
                for ex in exclusions:
                    r=policy_simulator(loans,score,amount,tenor,ex)
                    rows.append([score,amount,tenor,"+".join(ex) if ex else "None",
                                 r["approval_rate"],r["avg_pd"],r["expected_loss"],r["expected_profit"]])
    o=pd.DataFrame(rows,columns=["Min Score","Max Amount","Max Tenor","Excluded Bands","Approval Rate","Expected PD","Expected Loss","Expected Profit"])
    feasible=o[(o["Approval Rate"]>=min_approval)&(o["Expected PD"]<=max_pd)].copy()
    if feasible.empty: feasible=o.copy()
    if objective=="Minimize Expected Loss":
        feasible=feasible.sort_values(["Expected Loss","Expected Profit"],ascending=[True,False])
    elif objective=="Maximize Approval Rate":
        feasible=feasible.sort_values(["Approval Rate","Expected Profit"],ascending=[False,False])
    else:
        feasible=feasible.sort_values("Expected Profit",ascending=False)
    return feasible.reset_index(drop=True)

def forward_forecast(df, horizon=6):
    monthly=df.groupby("snapshot_date").agg(
        Balance=("outstanding_balance_vnd","sum"),
        DPD30Bal=("outstanding_balance_vnd",lambda s: 0), # overwritten below
        ExpectedLoss=("expected_loss_vnd","sum")
    ).reset_index()
    quality=df.groupby("snapshot_date").apply(lambda x: pd.Series({
        "DPD30":x.loc[x.dpd>=30,"outstanding_balance_vnd"].sum()/max(x.outstanding_balance_vnd.sum(),1),
        "DPD90":x.loc[x.dpd>=90,"outstanding_balance_vnd"].sum()/max(x.outstanding_balance_vnd.sum(),1)
    }),include_groups=False).reset_index()
    monthly=monthly.merge(quality,on="snapshot_date")
    last=monthly.iloc[-1]
    def trend(col):
        y=monthly[col].tail(min(6,len(monthly))).values.astype(float)
        if len(y)<2: return 0
        return np.polyfit(np.arange(len(y)),y,1)[0]
    future=[]
    last_date=pd.Timestamp(last["snapshot_date"])
    for h in range(1,horizon+1):
        future.append([
            last_date+pd.offsets.MonthEnd(h),
            max(0,last["Balance"]+trend("Balance")*h),
            max(0,min(1,last["DPD30"]+trend("DPD30")*h)),
            max(0,min(1,last["DPD90"]+trend("DPD90")*h)),
            max(0,last["ExpectedLoss"]+trend("ExpectedLoss")*h),
            "Forecast"
        ])
    hist=monthly[["snapshot_date","Balance","DPD30","DPD90","ExpectedLoss"]].copy()
    hist["Type"]="Actual"
    fut=pd.DataFrame(future,columns=hist.columns)
    return pd.concat([hist,fut],ignore_index=True)

def pricing_simulator(loans, risk_band, apr, funding_cost=0.085, operating_cost=850000, collection_cost_rate=0.01):
    x=loans[loans.risk_band==risk_band].copy()
    pdm={"A":.012,"B":.022,"C":.04,"D":.075,"E":.14}
    lgd={"A":.30,"B":.35,"C":.42,"D":.50,"E":.60}
    volume=x.original_amount_vnd.sum()
    expected_loss=volume*pdm[risk_band]*lgd[risk_band]
    revenue=volume*apr
    funding=volume*funding_cost
    opex=len(x)*operating_cost
    collection=volume*collection_cost_rate*pdm[risk_band]
    profit=revenue-funding-opex-collection-expected_loss
    min_apr=(funding+opex+collection+expected_loss)/max(volume,1)
    return {"Volume":volume,"Expected Loss":expected_loss,"Expected Profit":profit,"Break-even APR":min_apr,"Margin":profit/max(volume,1)}

def collection_strategy_simulator(df):
    latest=df[df.snapshot_date==df.snapshot_date.max()]
    delinquent=latest.loc[latest.dpd>0,"outstanding_balance_vnd"].sum()
    specs=[
        ("Standard",.31,.15,.010),
        ("Early Intervention",.38,.18,.012),
        ("Intensive",.44,.24,.022),
    ]
    rows=[]
    for name,cure,recovery,cost in specs:
        gross=delinquent*recovery
        c=delinquent*cost
        rows.append([name,cure,gross,c,gross-c])
    return pd.DataFrame(rows,columns=["Strategy","Cure Rate","Gross Recovery","Collection Cost","Net Recovery"])

def partner_benchmark(df, metrics):
    # Demonstration benchmark; explicitly synthetic.
    rows=[
        ["30+ DPD",metrics["30+ DPD"],.035,.027],
        ["90+ DPD",metrics["90+ DPD"],.018,.012],
        ["Portfolio Yield",metrics["Portfolio Yield"],.24,.28],
        ["Net Write-off Rate",metrics["Net Write-off Rate"],.035,.025],
    ]
    return pd.DataFrame(rows,columns=["KPI","Current Portfolio","Synthetic Peer Median","Synthetic Best Quartile"])

def management_pack_tables(df, loans, metrics):
    cockpit=decision_cockpit(df,loans,metrics)
    insights=management_insights(df,loans,metrics)
    forecast=forward_forecast(df,6).tail(6)
    optimizer=strategy_optimizer(loans).head(5)
    return cockpit,insights,forecast,optimizer
