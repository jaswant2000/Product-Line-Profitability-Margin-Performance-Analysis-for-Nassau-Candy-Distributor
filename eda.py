import json
from pathlib import Path
import pandas as pd

BASE=Path(__file__).parent
df=pd.read_csv(BASE/"Nassau_Candy_Distributor.csv")
for c in ["Sales","Cost","Gross Profit","Units"]:
    df[c]=pd.to_numeric(df[c],errors="coerce")
df["Order Date"]=pd.to_datetime(df["Order Date"],errors="coerce",dayfirst=True)
valid=df[df["Sales"].gt(0)&df["Gross Profit"].notna()&df["Units"].gt(0)&df["Cost"].notna()].copy()
valid["Gross Margin (%)"]=valid["Gross Profit"]/valid["Sales"]*100
valid["Profit per Unit"]=valid["Gross Profit"]/valid["Units"]
products=valid.groupby(["Product ID","Product Name","Division"],dropna=False).agg(
    Sales=("Sales","sum"),Gross_Profit=("Gross Profit","sum"),Cost=("Cost","sum"),
    Units=("Units","sum"),Line_Items=("Order ID","size"),Unique_Orders=("Order ID","nunique")
).reset_index()
products["Gross_Margin_Pct"]=products["Gross_Profit"]/products["Sales"]*100
divisions=valid.groupby("Division").agg(Sales=("Sales","sum"),Gross_Profit=("Gross Profit","sum"),Cost=("Cost","sum"),Units=("Units","sum"),Unique_Orders=("Order ID","nunique")).reset_index()
divisions["Gross_Margin_Pct"]=divisions["Gross_Profit"]/divisions["Sales"]*100
summary={
 "rows":int(len(df)),"unique_orders":int(df["Order ID"].nunique()),
 "unique_products":int(df["Product ID"].nunique()),"missing_cells":int(df.isna().sum().sum()),
 "duplicate_rows":int(df.duplicated().sum()),"valid_profitability_rows":int(len(valid)),
 "sales_total":float(valid["Sales"].sum()),"gross_profit_total":float(valid["Gross Profit"].sum()),
 "cost_total":float(valid["Cost"].sum()),"weighted_gross_margin_pct":float(valid["Gross Profit"].sum()/valid["Sales"].sum()*100),
 "order_date_min":str(valid["Order Date"].min().date()),"order_date_max":str(valid["Order Date"].max().date()),
 "division_metrics":divisions.to_dict("records"),
 "top_5_products_by_profit":products.sort_values("Gross_Profit",ascending=False).head(5)[["Product Name","Division","Sales","Gross_Profit","Gross_Margin_Pct"]].to_dict("records")
}
rev=products.sort_values("Sales",ascending=False).copy(); rev["cum"]=rev["Sales"].cumsum()/rev["Sales"].sum()*100
prof=products.sort_values("Gross_Profit",ascending=False).copy(); prof["cum"]=prof["Gross_Profit"].cumsum()/prof["Gross_Profit"].sum()*100
summary["products_for_80pct_revenue"]=int((rev["cum"]<80).sum()+1)
summary["products_for_80pct_profit"]=int((prof["cum"]<80).sum()+1)
(BASE/"eda_summary.json").write_text(json.dumps(summary,indent=2,default=str),encoding="utf-8")
products.to_csv(BASE/"product_profitability_summary.csv",index=False)
divisions.to_csv(BASE/"division_profitability_summary.csv",index=False)
print(json.dumps(summary,indent=2,default=str))
