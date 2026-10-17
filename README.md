# Nassau Candy Distributor — Product Line Profitability & Margin Performance Analysis

## Project objective
Analyse product- and division-level revenue, gross profit, gross margin, profit per unit, contribution, and product concentration using the supplied Nassau Candy Distributor dataset.

## Files
- `app.py`: interactive Streamlit dashboard
- `eda.py`: reproducible EDA and summary export
- `Nassau_Candy_Distributor.csv`: source dataset copy
- `product_profitability_summary.csv`: product-level aggregation
- `division_profitability_summary.csv`: division-level aggregation
- `eda_summary.json`: key metrics and data quality summary
- `Nassau_Candy_Product_Profitability_Research_Paper.docx`: research paper
- `Nassau_Candy_Product_Profitability_Executive_Summary.docx`: executive summary

## Run locally
```bash
pip install -r requirements.txt
python eda.py
streamlit run app.py
```

## Metrics
- Gross margin (%) = Gross profit / Sales × 100
- Profit per unit = Gross profit / Units
- Revenue contribution (%) = Product sales / total sales × 100
- Profit contribution (%) = Product gross profit / total gross profit × 100
- Division gross margin is weighted: total division gross profit / total division sales.

## Important interpretation notes
The dashboard filters invalid profitability rows (nonpositive sales, nonpositive or missing units, missing cost/profit). It uses the supplied Gross Profit field. Check whether Gross Profit equals Sales minus Cost for every row, as described in the project brief. The supplied order/shipment dates were known to have unusual relationships in the related logistics project, but profitability calculations do not rely on Ship Date. Margin flags are screening aids, not automatic discontinue decisions. This dataset does not contain full operating expenses, freight charges, promotional costs, or customer acquisition costs, so gross profit is not net profit.
