import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

st.set_page_config(page_title="Nassau Candy | Product Profitability", page_icon="🍬", layout="wide")
st.title("🍬 Product Line Profitability & Margin Performance Analysis")
st.caption("Nassau Candy Distributor | Unified Mentor analytics project")

DATA_PATH = Path(__file__).parent / "Nassau_Candy_Distributor.csv"

@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    for c in ["Sales", "Cost", "Gross Profit", "Units"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce", dayfirst=True)
    df["Gross Margin (%)"] = np.where(df["Sales"] > 0, df["Gross Profit"] / df["Sales"] * 100, np.nan)
    df["Profit per Unit"] = np.where(df["Units"] > 0, df["Gross Profit"] / df["Units"], np.nan)
    df["Revenue Contribution (%)"] = np.nan
    df["Profit Contribution (%)"] = np.nan
    df["Valid Profitability Record"] = (
        df["Sales"].notna() & (df["Sales"] > 0) &
        df["Gross Profit"].notna() & df["Units"].notna() & (df["Units"] > 0) &
        df["Cost"].notna()
    )
    return df

df = load_data(str(DATA_PATH))
valid_all = df[df["Valid Profitability Record"]].copy()
if valid_all.empty:
    st.error("No valid profitability records were found. Check the source dataset.")
    st.stop()

min_date = valid_all["Order Date"].min()
max_date = valid_all["Order Date"].max()
with st.sidebar:
    st.header("Filters")
    if pd.notna(min_date) and pd.notna(max_date):
        date_range = st.date_input("Order date range", value=(min_date.date(), max_date.date()),
                                   min_value=min_date.date(), max_value=max_date.date())
    else:
        date_range = None
    divisions = sorted(valid_all["Division"].dropna().astype(str).unique())
    selected_divisions = st.multiselect("Division", divisions, default=divisions)
    threshold = st.slider("Minimum gross margin threshold (%)", min_value=0, max_value=100, value=40, step=5)
    search = st.text_input("Search product name", "")

f = valid_all.copy()
if date_range and isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    f = f[f["Order Date"].between(start, end)]
if selected_divisions:
    f = f[f["Division"].isin(selected_divisions)]
if search.strip():
    f = f[f["Product Name"].astype(str).str.contains(search.strip(), case=False, na=False)]

if f.empty:
    st.warning("No records match the current filters.")
    st.stop()

sales_total = f["Sales"].sum()
profit_total = f["Gross Profit"].sum()
cost_total = f["Cost"].sum()
margin_total = profit_total / sales_total * 100 if sales_total else np.nan
unique_orders = f["Order ID"].nunique()

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Revenue", f"${sales_total:,.2f}")
c2.metric("Gross profit", f"${profit_total:,.2f}")
c3.metric("Manufacturing cost", f"${cost_total:,.2f}")
c4.metric("Weighted gross margin", f"{margin_total:.1f}%")
c5.metric("Unique orders", f"{unique_orders:,}")
st.caption("Gross margin is calculated as total gross profit divided by total sales. Product rows are line items; unique orders are counted separately.")

product = f.groupby(["Product ID","Product Name","Division"], dropna=False).agg(
    Sales=("Sales","sum"), Gross_Profit=("Gross Profit","sum"), Cost=("Cost","sum"),
    Units=("Units","sum"), Line_Items=("Order ID","size"), Unique_Orders=("Order ID","nunique")
).reset_index()
product["Gross_Margin_Pct"] = product["Gross_Profit"] / product["Sales"] * 100
product["Profit_Per_Unit"] = product["Gross_Profit"] / product["Units"]
product["Revenue_Contribution_Pct"] = product["Sales"] / product["Sales"].sum() * 100
product["Profit_Contribution_Pct"] = product["Gross_Profit"] / product["Gross_Profit"].sum() * 100
product["Margin_Risk"] = np.select(
    [product["Gross_Margin_Pct"] < threshold, (product["Sales"] >= product["Sales"].median()) & (product["Gross_Margin_Pct"] < threshold)],
    ["Below margin threshold", "High revenue / low margin"], default="Within threshold"
)
division = f.groupby("Division", dropna=False).agg(
    Sales=("Sales","sum"), Gross_Profit=("Gross Profit","sum"), Cost=("Cost","sum"),
    Units=("Units","sum"), Line_Items=("Order ID","size"), Unique_Orders=("Order ID","nunique")
).reset_index()
division["Gross_Margin_Pct"] = division["Gross_Profit"] / division["Sales"] * 100
division["Revenue_Contribution_Pct"] = division["Sales"] / division["Sales"].sum() * 100
division["Profit_Contribution_Pct"] = division["Gross_Profit"] / division["Gross_Profit"].sum() * 100

tabs = st.tabs(["Product Profitability Overview","Division Performance","Cost vs Margin Diagnostics","Profit Concentration","Data Quality"])
with tabs[0]:
    st.subheader("Product margin leaderboard")
    left,right=st.columns(2)
    with left:
        st.markdown("**Top products by gross profit**")
        st.dataframe(product.sort_values("Gross_Profit",ascending=False).head(10), use_container_width=True, hide_index=True)
    with right:
        st.markdown("**Top products by gross margin**")
        st.dataframe(product.sort_values("Gross_Margin_Pct",ascending=False).head(10), use_container_width=True, hide_index=True)
    fig,ax=plt.subplots()
    plot=product.sort_values("Gross_Profit",ascending=True)
    ax.barh(plot["Product Name"],plot["Gross_Profit"])
    ax.set_xlabel("Gross profit ($)")
    ax.set_title("Gross profit contribution by product")
    fig.tight_layout()
    st.pyplot(fig)
    st.download_button("Download product profitability CSV", product.to_csv(index=False).encode("utf-8"), "product_profitability.csv", "text/csv")
with tabs[1]:
    st.subheader("Revenue vs profit by division")
    st.dataframe(division.sort_values("Sales",ascending=False),use_container_width=True,hide_index=True)
    fig,ax=plt.subplots()
    x=np.arange(len(division))
    width=0.36
    ax.bar(x-width/2,division["Sales"],width,label="Sales")
    ax.bar(x+width/2,division["Gross_Profit"],width,label="Gross profit")
    ax.set_xticks(x); ax.set_xticklabels(division["Division"],rotation=0)
    ax.set_ylabel("Amount ($)"); ax.legend(); ax.set_title("Division revenue and gross profit")
    fig.tight_layout(); st.pyplot(fig)
    fig,ax=plt.subplots()
    ax.bar(division["Division"],division["Gross_Margin_Pct"])
    ax.set_ylabel("Gross margin (%)"); ax.set_title("Weighted gross margin by division")
    fig.tight_layout(); st.pyplot(fig)
with tabs[2]:
    st.subheader("Cost versus sales")
    fig,ax=plt.subplots()
    for div, group in f.groupby("Division"):
        ax.scatter(group["Sales"],group["Cost"],label=str(div),alpha=.65)
    ax.set_xlabel("Sales ($)"); ax.set_ylabel("Manufacturing cost ($)"); ax.legend()
    ax.set_title("Line-item cost versus sales")
    fig.tight_layout(); st.pyplot(fig)
    st.markdown("**Products below the selected margin threshold**")
    risks=product[product["Gross_Margin_Pct"] < threshold].sort_values("Sales",ascending=False)
    if risks.empty: st.success("No products fall below the selected margin threshold.")
    else: st.dataframe(risks,use_container_width=True,hide_index=True)
    st.caption("Margin flags are screening indicators, not automatic recommendations to discontinue a product. Validate pricing, cost allocation, demand, and strategic role first.")
with tabs[3]:
    st.subheader("Product concentration (Pareto analysis)")
    rev=product.sort_values("Sales",ascending=False).copy()
    rev["Cumulative revenue (%)"]=rev["Sales"].cumsum()/rev["Sales"].sum()*100
    prof=product.sort_values("Gross_Profit",ascending=False).copy()
    prof["Cumulative profit (%)"]=prof["Gross_Profit"].cumsum()/prof["Gross_Profit"].sum()*100
    rev80=int((rev["Cumulative revenue (%)"]<80).sum()+1)
    prof80=int((prof["Cumulative profit (%)"]<80).sum()+1)
    a,b=st.columns(2)
    a.metric("Products to reach 80% of revenue",f"{rev80} / {len(rev)}",f"{rev80/len(rev)*100:.1f}% of products")
    b.metric("Products to reach 80% of gross profit",f"{prof80} / {len(prof)}",f"{prof80/len(prof)*100:.1f}% of products")
    fig,ax=plt.subplots()
    ax.bar(rev["Product Name"],rev["Sales"])
    ax.set_ylabel("Revenue ($)"); ax.set_title("Revenue by product"); ax.tick_params(axis="x",rotation=70)
    fig.tight_layout(); st.pyplot(fig)
    st.dataframe(rev[["Product Name","Division","Sales","Revenue_Contribution_Pct","Cumulative revenue (%)"]],use_container_width=True,hide_index=True)
    st.markdown("**Profit concentration**")
    st.dataframe(prof[["Product Name","Division","Gross_Profit","Profit_Contribution_Pct","Cumulative profit (%)"]],use_container_width=True,hide_index=True)
with tabs[4]:
    st.subheader("Data quality checks")
    raw=pd.read_csv(DATA_PATH)
    quality=pd.DataFrame([
        {"Check":"Source rows","Result":len(raw)},
        {"Check":"Missing cells","Result":int(raw.isna().sum().sum())},
        {"Check":"Exact duplicate rows","Result":int(raw.duplicated().sum())},
        {"Check":"Missing / invalid order dates","Result":int(df["Order Date"].isna().sum())},
        {"Check":"Missing sales values","Result":int(df["Sales"].isna().sum())},
        {"Check":"Zero or negative sales","Result":int((df["Sales"]<=0).sum())},
        {"Check":"Missing / nonpositive units","Result":int((df["Units"].isna() | (df["Units"]<=0)).sum())},
        {"Check":"Missing cost or gross profit","Result":int((df["Cost"].isna() | df["Gross Profit"].isna()).sum())},
        {"Check":"Records included in profitability analysis","Result":len(valid_all)}
    ])
    st.dataframe(quality,use_container_width=True,hide_index=True)
    st.info("Gross profit is taken from the supplied dataset. The provided definition says Gross Profit = Sales − Cost; verify that relationship and any cost allocation rules with the data owner before making pricing or discontinuation decisions.")
    st.download_button("Download filtered line items CSV", f.to_csv(index=False).encode("utf-8"), "filtered_product_line_items.csv", "text/csv")

st.divider()
st.caption("Exploratory analytics only. Sales, cost and gross profit are not customer acquisition, logistics, or full operating-profit measures unless those costs are included in the supplied fields.")
