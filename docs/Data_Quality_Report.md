# Data Quality Report

## Scope

This report validates whether the Excel datasets in `demo-data` can support an end-to-end Commercial Deal Desk analysis for Module 1.

Target repository:

`C:\Users\User\Documents\ai-process-excellence`

Reviewed datasets:

- `Approval_Matrix.xlsx`
- `Approver_Roster.xlsx`
- `Commercial_Plan.xlsx`
- `Competitor_Intelligence.xlsx`
- `Customer_Master.xlsx`
- `Deal_Request_Form.xlsx`
- `Expiry_Aging.xlsx`
- `Inventory_Coverage.xlsx`
- `Price_Volume_History.xlsx`
- `Product_Master.xlsx`
- `Sample_Deal_Requests.xlsx`
- `Tender_History.xlsx`

Validation checks:

1. Relationships between files
2. Matching keys across datasets
3. Missing or inconsistent fields
4. Whether each deal request can be linked to customer, product, plan, inventory, aging, tender history, competitor intelligence, and approval matrix
5. Gaps preventing end-to-end simulation

## Executive Summary

The datasets can support a basic end-to-end deal intake and approval-routing simulation for the seeded sample deals. The strongest path is:

`Deal Request -> Customer -> Opportunity -> Deal Line Items -> Product Master -> Approval Matrix -> Approver Roster`

Most analytical paths also work for the seeded deals:

- Price request versus plan
- Price-volume benchmark
- Inventory coverage
- Expiry and aging
- Tender history
- Competitor intelligence
- Approval routing

The main gaps are:

- The larger analytical datasets contain six SKUs missing from `Product_Master.xlsx`.
- Several analytical datasets contain customers or tendering accounts missing from `Customer_Master.xlsx`.
- Some datasets use customer names instead of stable `Customer ID` keys.
- `DEAL-3001` includes `SVC-START`, which is missing from plan, inventory coverage, expiry aging, and tender history.
- `Deal_Request_Form.xlsx` is useful as a template, but it is not normalized as a relational data source.

Conclusion:

The current files are usable for a controlled MVP demo, but master data should be expanded before relying on the full analytical dataset network.

## Dataset Inventory

| File | Sheet | Rows | Columns | Role |
| --- | --- | ---: | ---: | --- |
| `Approval_Matrix.xlsx` | Approval Matrix | 8 | 12 | Approval policy rules |
| `Approval_Matrix.xlsx` | Roles | 8 | 6 | Role definitions |
| `Approver_Roster.xlsx` | Approver Roster | 70 | 11 | Approver assignment and scope |
| `Commercial_Plan.xlsx` | Commercial Plan | 144 | 19 | Plan baseline |
| `Competitor_Intelligence.xlsx` | Competitor Intelligence | 150 | 16 | Competitive signals |
| `Customer_Master.xlsx` | Customers | 8 | 11 | Customer master |
| `Customer_Master.xlsx` | Opportunities | 6 | 10 | Opportunity master |
| `Deal_Request_Form.xlsx` | Deal Request Form | 21 | 10 | Intake template |
| `Deal_Request_Form.xlsx` | Validation Lists | 4 | 6 | Form picklists |
| `Expiry_Aging.xlsx` | Expiry Aging | 156 | 15 | Lot-level aging and expiry |
| `Inventory_Coverage.xlsx` | Inventory Coverage | 168 | 17 | Demand-backed inventory coverage |
| `Price_Volume_History.xlsx` | Price Volume History | 180 | 19 | Historical price-volume outcomes |
| `Product_Master.xlsx` | Products | 8 | 13 | Product master |
| `Product_Master.xlsx` | Price Book | 9 | 11 | Price book entries |
| `Product_Master.xlsx` | Inventory | 7 | 10 | Basic inventory sample |
| `Sample_Deal_Requests.xlsx` | Deal Requests | 6 | 17 | Seeded deal headers |
| `Sample_Deal_Requests.xlsx` | Line Items | 11 | 16 | Seeded deal line items |
| `Sample_Deal_Requests.xlsx` | Deal Summary | 6 | 10 | Deal-level summary |
| `Tender_History.xlsx` | Tender History | 120 | 19 | Tender outcomes and competitive pricing |

## Relationship Validation

### Relationships Passing

The following relationships are valid:

- `Customer_Master.Opportunities.Customer ID` matches `Customer_Master.Customers.Customer ID`.
- `Sample_Deal_Requests.Deal Requests.Customer ID` matches `Customer_Master.Customers.Customer ID`.
- `Sample_Deal_Requests.Deal Requests.Opportunity ID` matches `Customer_Master.Opportunities.Opportunity ID`.
- `Sample_Deal_Requests.Line Items.Deal ID` matches `Sample_Deal_Requests.Deal Requests.Deal ID`.
- `Sample_Deal_Requests.Line Items.SKU` matches `Product_Master.Products.SKU`.
- `Product_Master.Price Book.SKU` matches `Product_Master.Products.SKU`.
- `Product_Master.Inventory.SKU` matches `Product_Master.Products.SKU`.
- `Approval_Matrix.Required Role` matches `Approver_Roster.Role`.

These passing relationships are enough to support the core Module 1 workflow for the seeded sample deals.

### Broken Product References

The expanded analytical datasets reference six SKUs that are not present in `Product_Master.xlsx`.

Missing SKUs:

- `BIO-DERM-80`
- `DX-GENE-02`
- `RX-HOSP-20`
- `RX-ONC-ORAL`
- `RX-RARE-INF`
- `SVC-PAT-01`

Affected datasets:

- `Commercial_Plan.xlsx`
- `Price_Volume_History.xlsx`
- `Inventory_Coverage.xlsx`
- `Expiry_Aging.xlsx`
- `Tender_History.xlsx`
- `Competitor_Intelligence.xlsx`

Impact:

- These rows cannot be joined to product attributes such as therapeutic area, product type, list price, standard cost, lead time, storage, and inventory-tracked flag.
- Analysis will be incomplete for any deal using these SKUs unless the application carries duplicate product attributes from the analytical files.

Recommended fix:

Add the six missing SKUs to `Product_Master.xlsx`, including product type, therapeutic area, WAC/list price, standard cost, target margin, lead time, inventory-tracked flag, supply risk, and status.

### Broken Customer References

The expanded analytical datasets reference customer names not present in `Customer_Master.xlsx`.

Missing customers in `Price_Volume_History.xlsx` and `Competitor_Intelligence.xlsx`:

- Atlas Hospital Network
- BluePeak Payer Coalition
- Crescent Public Tender Authority
- Europa Health Purchasing
- Harbor Specialty Rx
- Metro Infusion Partners
- NovaCare Oncology
- Pioneer Medical Group
- Redwood Regional IDN
- Sterling Specialty Distribution
- Union National Payer
- Valence Integrated Care

Missing tendering accounts in `Tender_History.xlsx`:

- Atlas Hospital Network
- BluePeak Payer Coalition
- Crescent Public Tender Authority
- Europa Health Purchasing
- Union National Payer

Impact:

- Historical price-volume, tender, and competitor intelligence records cannot consistently join to customer segment, account type, strategic flag, credit status, region, or account owner.
- Account-level analysis will be partial for those rows.

Recommended fix:

Expand `Customer_Master.xlsx` to include all customers and tendering accounts used by the analysis datasets.

## Matching Keys Across Datasets

### Strong Keys

The following keys are usable and consistent:

- `Customer ID`
- `Opportunity ID`
- `Deal ID`
- `Line #` within deal
- `SKU`
- `Policy ID`
- `Approver ID`

### Weak or Missing Keys

The following datasets rely on names instead of stable IDs:

- `Price_Volume_History.xlsx` uses `Customer`, not `Customer ID`.
- `Tender_History.xlsx` uses `Tendering Account`, not `Customer ID`.
- `Competitor_Intelligence.xlsx` uses `Customer`, not `Customer ID`.

Recommended fix:

Add `Customer ID` to:

- `Price_Volume_History.xlsx`
- `Tender_History.xlsx`
- `Competitor_Intelligence.xlsx`

Also add optional `Opportunity ID` or `Deal ID` when a record is meant to support a specific active deal.

## Missing or Inconsistent Fields

### Deal Request Form

`Deal_Request_Form.xlsx` is formatted as a human-facing form. It is not a clean relational source.

Issues:

- Header row is not normalized for data ingestion.
- Some columns are unnamed.
- Data is arranged in form sections rather than a single entity table.

Recommendation:

Keep it as a form/template artifact. Do not use it as the authoritative deal source. Use `Sample_Deal_Requests.xlsx` for structured deal data.

### Price Book Coverage

`Product_Master.xlsx` has only 9 price book rows for 8 products.

Issues:

- Not every product has price book coverage for every region and segment.
- New analytical SKUs are not covered.

Recommendation:

Expand the price book to cover active SKUs by region, segment, and currency.

### Inventory Sources

There are two inventory-style sources:

- `Product_Master.xlsx` / `Inventory`
- `Inventory_Coverage.xlsx`

Issue:

The basic inventory sheet and the expanded inventory coverage sheet overlap conceptually.

Recommendation:

Use `Inventory_Coverage.xlsx` as the authoritative source for analysis. Keep `Product_Master.xlsx` / `Inventory` only as a small legacy/simple intake sample or remove it later.

### Competitor Master

Competitor names appear in:

- `Tender_History.xlsx`
- `Competitor_Intelligence.xlsx`

Issue:

There is no competitor master.

Recommendation:

Create `Competitor_Master.xlsx` in a future cleanup if competitor analytics become more important.

## Deal-Level Linkage Coverage

The table below checks whether each seeded deal can link to the main analytical sources.

| Deal ID | Customer | SKUs | Customer | Opportunity | Product | Plan | Inventory | Aging | Tender | Competitor Intel | Approval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEAL-3001` | Northstar Health Systems | `RX-ONC-100`, `RX-ONC-500`, `SVC-START` | Pass | Pass | Pass | Partial | Partial | Partial | Partial | Pass | Pass |
| `DEAL-3002` | Meridian Specialty Pharmacy | `BIO-RA-200` | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |
| `DEAL-3003` | Apex National GPO | `REB-FORM`, `RX-CARD-50` | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |
| `DEAL-3004` | HelioRx Distribution | `RX-RARE-10` | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |
| `DEAL-3005` | Summit Oncology Clinics | `BIO-RA-200`, `DX-COMP-01` | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |
| `DEAL-3006` | Cityline Payer Alliance | `REB-FORM`, `RX-CARD-50` | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass | Pass |

### Deal-Level Notes

`DEAL-3001` is the only seeded deal with incomplete analytical linkage.

Reason:

- `SVC-START` exists in product master and deal lines, but does not appear in:
  - `Commercial_Plan.xlsx`
  - `Inventory_Coverage.xlsx`
  - `Expiry_Aging.xlsx`
  - `Tender_History.xlsx`

Interpretation:

This is acceptable if `SVC-START` is intentionally treated as a service line that should not require inventory, expiry, or tender coverage. It should still have plan coverage if services are included in plan-vs-actual reporting.

Recommended fix:

Add a service-plan row for `SVC-START` in `Commercial_Plan.xlsx`, or explicitly mark service lines as excluded from inventory, aging, and tender analysis.

## End-to-End Simulation Assessment

### Can the Dataset Support a Complete Deal Approval Workflow?

Yes, for a controlled MVP demo.

The following workflow can be simulated:

1. Select customer.
2. Link opportunity.
3. Add deal line items.
4. Resolve products by SKU.
5. Compare requested price to commercial plan where available.
6. Compare price and volume to historical approved outcomes.
7. Check inventory coverage.
8. Check expiry and aging exposure.
9. Review tender history.
10. Review competitor intelligence.
11. Evaluate approval matrix.
12. Assign approver roles from approver roster.
13. Produce final recommendation.

### Strongest Demo Deals

The cleanest end-to-end demo candidates are:

- `DEAL-3002`
- `DEAL-3003`
- `DEAL-3004`
- `DEAL-3005`
- `DEAL-3006`

These deals link to all required analysis sources.

### Weaker Demo Deal

`DEAL-3001` is still usable, but its service line requires special handling.

Recommended handling:

- Treat `SVC-START` as excluded from inventory, expiry, and tender analysis.
- Add `SVC-START` to commercial plan if service revenue should appear in plan-vs-actual analysis.

## Gaps Preventing Full End-to-End Simulation

### Gap 1: Product Master Does Not Cover All Analytical SKUs

Severity:

High

Effect:

Full analytical history cannot be joined to product master.

Fix:

Add six missing SKUs to `Product_Master.xlsx`.

### Gap 2: Customer Master Does Not Cover All Analytical Customers

Severity:

High

Effect:

Tender, competitor, and price-volume analysis cannot fully join to account context.

Fix:

Add missing customers to `Customer_Master.xlsx`.

### Gap 3: Analysis Datasets Need Stable Customer IDs

Severity:

Medium

Effect:

Name-based joins are fragile.

Fix:

Add `Customer ID` to price-volume, tender history, and competitor intelligence.

### Gap 4: Service Lines Need Explicit Analysis Rules

Severity:

Medium

Effect:

Service SKUs such as `SVC-START` create false gaps in inventory, aging, and tender analysis.

Fix:

Add `Analysis Exclusion Flag` or `Line Type` logic for service and rebate lines.

### Gap 5: Price Book Is Too Sparse

Severity:

Medium

Effect:

Some region/segment/product combinations cannot be priced from the master price book.

Fix:

Expand price book by active SKU, region, segment, and currency.

### Gap 6: No Competitor Master

Severity:

Low

Effect:

Competitor names cannot be governed or enriched.

Fix:

Add competitor master later if competitive analytics become deeper.

## Recommended Fixes

### Priority 1

1. Add missing analytical SKUs to `Product_Master.xlsx`.
2. Add missing analytical customers to `Customer_Master.xlsx`.
3. Add `Customer ID` to `Price_Volume_History.xlsx`, `Tender_History.xlsx`, and `Competitor_Intelligence.xlsx`.

### Priority 2

1. Add plan coverage for `SVC-START`, or explicitly exclude service lines from plan-vs-actual analysis.
2. Add `Line Type` to deal line items with values such as Product, Service, Rebate, Diagnostic, Support.
3. Expand the price book for every active SKU by region and segment.
4. Rationalize inventory sources and mark `Inventory_Coverage.xlsx` as authoritative.

### Priority 3

1. Add `Competitor_Master.xlsx`.
2. Add `Policy Trigger ID` output for approval-route explainability.
3. Add `Plan Period` to deal requests so plan comparisons can be time-aligned.
4. Add `Tender ID` to deal requests when the deal is tender-driven.

## Final Recommendation

The current data is ready for a Module 1 MVP demo if the demo is limited to the seeded deal requests and service/rebate lines are handled deliberately.

Before expanding into a broader analytics demo, normalize the product and customer masters and add stable customer keys to the analytical datasets. Those fixes will make the data model much more reliable for end-to-end Commercial Deal Desk analysis.

