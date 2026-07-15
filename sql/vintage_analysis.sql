SELECT DATE_TRUNC('month', l.origination_date) vintage_month, s.mob,
SUM(CASE WHEN s.dpd>=30 THEN s.outstanding_balance_vnd ELSE 0 END)/NULLIF(SUM(l.original_amount_vnd),0) vintage_30_plus
FROM monthly_snapshots s JOIN loan_master l ON s.loan_id=l.loan_id GROUP BY 1,2;