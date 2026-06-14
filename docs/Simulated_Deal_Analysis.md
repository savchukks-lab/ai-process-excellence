# Simulated Deal Analysis: 10 Pharmaceutical Commercial Requests

## Scope

This report manually simulates ten realistic Module 1 commercial deal requests and applies the available demo datasets for plan variance, price-volume benchmarking, inventory coverage, expiry/aging review, tender history, competitor intelligence, approval routing, and final recommendation.

Source datasets used: `Customer_Master.xlsx`, `Product_Master.xlsx`, `Commercial_Plan.xlsx`, `Price_Volume_History.xlsx`, `Inventory_Coverage.xlsx`, `Expiry_Aging.xlsx`, `Tender_History.xlsx`, `Competitor_Intelligence.xlsx`, `Approval_Matrix.xlsx`, and `Approver_Roster.xlsx`.

## Portfolio Summary

| Deal | Customer | Proposed Value | Discount | Margin | Route | Recommendation |
| --- | --- | ---: | ---: | ---: | --- | --- |
| SIM-001 Northstar Oncology Infusion Expansion | Northstar Health Systems | $449,700 | 17.5% | 35.1% | Sales Manager, Pricing Analyst, Finance Approver, Operations Reviewer, Legal Reviewer | Escalate / approve with conditions |
| SIM-002 Meridian Biosimilar Conversion | Meridian Specialty Pharmacy | $532,525 | 19.5% | 36.0% | Sales Manager, Pricing Analyst, Operations Reviewer | Approve with conditions |
| SIM-003 Apex National Formulary Access | Apex National GPO | $4,470,000 | 29.0% | 64.8% | Sales Manager, Pricing Analyst, Market Access Director, Finance Approver, Operations Reviewer, Legal Reviewer, Commercial Executive | Escalate / approve with conditions |
| SIM-004 HelioRx Rare Disease EU Launch | HelioRx Distribution | $622,880 | 21.0% | 23.8% | Sales Manager, Pricing Analyst, Finance Approver, Operations Reviewer | Approve with conditions |
| SIM-005 Summit Oncology Biosimilar Pilot | Summit Oncology Clinics | $245,100 | 15.0% | 41.1% | Sales Manager, Pricing Analyst, Operations Reviewer | Approve |
| SIM-006 Cityline Cardiology Rebate Renewal | Cityline Payer Alliance | $5,690,000 | 38.4% | 59.4% | Sales Manager, Pricing Analyst, Market Access Director, Finance Approver, Operations Reviewer, Legal Reviewer, Commercial Executive | Escalate / approve with conditions |
| SIM-007 Orion Hospital Trust Oncology Recovery Deal | Orion Hospital Trust | $230,180 | 27.1% | 26.4% | Sales Manager, Pricing Analyst, Finance Approver, Operations Reviewer, Legal Reviewer | Request revision before approval |
| SIM-008 Beacon Clinical Research Trial Supply Package | Beacon Clinical Research | $128,800 | 23.3% | 41.8% | Sales Manager, Pricing Analyst, Finance Approver, Operations Reviewer | Approve with conditions |
| SIM-009 Northstar Rare Disease Expansion | Northstar Health Systems | $800,000 | 22.8% | 19.9% | Sales Manager, Pricing Analyst, Finance Approver, Operations Reviewer, Legal Reviewer | Escalate / approve with conditions |
| SIM-010 Apex Oncology Tender Defense | Apex National GPO | $1,186,000 | 24.6% | 29.1% | Sales Manager, Pricing Analyst, Market Access Director, Finance Approver, Operations Reviewer, Legal Reviewer | Escalate / approve with conditions |

## SIM-001: Northstar Oncology Infusion Expansion

Customer: Northstar Health Systems (Integrated Delivery Network, North America, Enterprise)
Deal type: Competitive replacement; payment terms: Net 60; contract: 36 months
Strategic rationale: Strategic IDN expansion with competitor incumbent pressure and oncology infusion standardization.

| Line | Qty | List | Proposed | Discount | Margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| RX-ONC-100 - Oncavax IV 100mg Vial | 120 | $1,850 | $1,517 | 18.0% | 36.1% |
| RX-ONC-500 - Oncavax IV 500mg Vial | 40 | $7,200 | $5,904 | 18.0% | 33.1% |
| SVC-START - Patient Start Program | 1 | $35,000 | $31,500 | 10.0% | 44.4% |

Deal totals: list $545,000; proposed $449,700; discount 17.5%; estimated margin 35.1% versus weighted target 37.1%.

### Plan vs Actual Analysis
- RX-ONC-100: proposed net $1,517 vs planned net $1,628 (-6.8% variance); requested units 120 vs plan units 138 (-13.0% variance).
- RX-ONC-500: proposed net $5,904 vs planned net $6,336 (-6.8% variance); requested units 40 vs plan units 166 (-75.9% variance).
- SVC-START: no plan row available; plan variance cannot be calculated.

### Price Analysis
- RX-ONC-100: requested discount 18.0%; historical approved discount avg 19.0% across 1 comparable rows; proposed price variance to historical approved net 1.2%.
- RX-ONC-500: requested discount 18.0%; historical approved discount avg 15.5% across 2 comparable rows; proposed price variance to historical approved net -3.0%.
- SVC-START: no historical price-volume benchmark found.

### Inventory Analysis
- RX-ONC-100: requested 120; available 78 at Memphis DC (North America); coverage 15 days vs lead time 21 days; status Below Lead Time and quantity is short / constrained.
- RX-ONC-500: requested 40; available 471 at Frankfurt DC (North America); coverage 41 days vs lead time 28 days; status Tight and quantity is sufficient.
- SVC-START: no inventory coverage record found.

### Aging Analysis
- RX-ONC-100: nearest aging lot LOT-RX-ONC-100-001 has -55 days to expiry, bucket 0-90 days, quantity 475, quality status Released; recommendation: Prioritize tender or redistribution.
- RX-ONC-500: nearest aging lot LOT-RX-ONC-500-004 has 279 days to expiry, bucket 181-365 days, quantity 852, quality status Released; recommendation: Normal FEFO rotation.
- SVC-START: no expiry/aging record found.

### Tender History Analysis
- RX-ONC-100: relevant tender TDR-00013 for Union National Payer in United States had outcome Split Award, winning net $1,397, discount 24.5%, primary competitor Praxis Health, driver Supply assurance.
- RX-ONC-500: relevant tender TDR-00014 for Atlas Hospital Network in France had outcome Won, winning net $5,616, discount 22.0%, primary competitor Orionis Pharma, driver Clinical evidence.
- SVC-START: no tender history found.

### Competitor Intelligence Summary
- RX-ONC-100: Asteria Pharma signal: Rebate offer (Low confidence, 30 days old). Summary: Asteria Pharma reportedly constrained on supply for next quarter. Recommended response: Escalate to market access.
- RX-ONC-500: Asteria Pharma signal: Rebate offer (Low confidence, 30 days old). Summary: Asteria Pharma reportedly constrained on supply for next quarter. Recommended response: Escalate to market access.
- SVC-START: Asteria Pharma signal: Rebate offer (Low confidence, 30 days old). Summary: Asteria Pharma reportedly constrained on supply for next quarter. Recommended response: Escalate to market access.

### Recommended Approval Route
- Sales Manager: Every submitted deal requires baseline commercial review.
- Pricing Analyst: Discount exceeds product policy threshold.
- Finance Approver: Deal value exceeds $1M or margin is below target.
- Operations Reviewer: Supply risk, cold-chain, or coverage constraint exists.
- Legal Reviewer: Non-standard terms, long duration, or extended payment terms.

### Final Recommendation
Escalate / approve with conditions. Commercial case may be viable, but conditions are required: requested quantity exceeds tightest available inventory match; expired inventory appears in aging pool and must be excluded; margin below weighted product target.

## SIM-002: Meridian Biosimilar Conversion

Customer: Meridian Specialty Pharmacy (Specialty Pharmacy, North America, Mid-Market)
Deal type: Expansion; payment terms: Net 45; contract: 24 months
Strategic rationale: Biosimilar conversion program with moderate price pressure and volume commitment.

| Line | Qty | List | Proposed | Discount | Margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| BIO-RA-200 - Rheumera Biosimilar Pen | 500 | $1,180 | $944 | 20.0% | 34.3% |
| DX-COMP-01 - Companion Diagnostic Panel | 75 | $950 | $807 | 15.1% | 49.2% |

Deal totals: list $661,250; proposed $532,525; discount 19.5%; estimated margin 36.0% versus weighted target 35.3%.

### Plan vs Actual Analysis
- BIO-RA-200: proposed net $944 vs planned net $1,038 (-9.1% variance); requested units 500 vs plan units 180 (177.8% variance).
- DX-COMP-01: proposed net $807 vs planned net $779 (3.6% variance); requested units 75 vs plan units 334 (-77.5% variance).

### Price Analysis
- BIO-RA-200: requested discount 20.0%; historical approved discount avg 16.0% across 2 comparable rows; proposed price variance to historical approved net -4.8%.
- DX-COMP-01: requested discount 15.1%; historical approved discount avg 8.5% across 1 comparable rows; proposed price variance to historical approved net -7.1%.

### Inventory Analysis
- BIO-RA-200: requested 500; available 459 at Amsterdam 3PL (North America); coverage 41 days vs lead time 18 days; status Tight and quantity is short / constrained.
- DX-COMP-01: requested 75; available 1,426 at Memphis DC (North America); coverage 47 days vs lead time 10 days; status Adequate and quantity is sufficient.

### Aging Analysis
- BIO-RA-200: nearest aging lot LOT-BIO-RA-200-003 has 251 days to expiry, bucket 181-365 days, quantity 839, quality status Released; recommendation: Normal FEFO rotation.
- DX-COMP-01: nearest aging lot LOT-DX-COMP-01-004 has 524 days to expiry, bucket >365 days, quantity 1,268, quality status Released; recommendation: Normal FEFO rotation.

### Tender History Analysis
- BIO-RA-200: relevant tender TDR-00015 for Europa Health Purchasing in Colombia had outcome Lost, winning net $950, discount 19.5%, primary competitor Novum Therapeutics, driver Local packaging.
- DX-COMP-01: relevant tender TDR-00030 for Atlas Hospital Network in Netherlands had outcome Lost, winning net $694, discount 26.9%, primary competitor Asteria Pharma, driver Local packaging.

### Competitor Intelligence Summary
- BIO-RA-200: Vantage Biosimilar signal: Formulary exclusion risk (High confidence, 60 days old). Summary: Vantage Biosimilar offered rebate corridor tied to volume commitment. Recommended response: Check supply commitment.
- DX-COMP-01: Novum Therapeutics signal: Supply shortage (Low confidence, 30 days old). Summary: Novum Therapeutics emphasized clinical switching data in tender discussion. Recommended response: Prepare battlecard.

### Recommended Approval Route
- Sales Manager: Every submitted deal requires baseline commercial review.
- Pricing Analyst: Discount exceeds product policy threshold.
- Operations Reviewer: Supply risk, cold-chain, or coverage constraint exists.

### Final Recommendation
Approve with conditions. Proceed if required reviewers accept conditions: requested quantity exceeds tightest available inventory match.

## SIM-003: Apex National Formulary Access

Customer: Apex National GPO (Group Purchasing Organization, North America, Enterprise)
Deal type: Strategic exception; payment terms: Net 90; contract: 48 months
Strategic rationale: National GPO preferred formulary position requiring rebate concession and executive visibility.

| Line | Qty | List | Proposed | Discount | Margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| RX-CARD-50 - Cardiovex 50mg Tablet Pack | 15,000 | $420 | $328 | 21.9% | 68.0% |
| REB-FORM - Formulary Access Rebate | 1 | $0 | $-450,000 | 0.0% | n/a |

Deal totals: list $6,300,000; proposed $4,470,000; discount 29.0%; estimated margin 64.8% versus weighted target 63.8%.

### Plan vs Actual Analysis
- RX-CARD-50: proposed net $328 vs planned net $344 (-4.7% variance); requested units 15,000 vs plan units 320 (4587.5% variance).
- REB-FORM: rebate adjustment line; compare at deal level rather than unit plan.

### Price Analysis
- RX-CARD-50: requested discount 21.9%; historical approved discount avg 16.5% across 2 comparable rows; proposed price variance to historical approved net -6.4%.
- REB-FORM: $-450,000 rebate concession reduces net deal value and triggers market access and finance review.

### Inventory Analysis
- RX-CARD-50: requested 15,000; available 421 at Chicago DC (North America); coverage 41 days vs lead time 7 days; status Tight and quantity is short / constrained.

### Aging Analysis
- RX-CARD-50: nearest aging lot LOT-RX-CARD-50-002 has 220 days to expiry, bucket 181-365 days, quantity 800, quality status Released; recommendation: Normal FEFO rotation.

### Tender History Analysis
- RX-CARD-50: relevant tender TDR-00028 for Crescent Public Tender Authority in Singapore had outcome Split Award, winning net $286, discount 31.9%, primary competitor Orionis Pharma, driver Supply assurance.

### Competitor Intelligence Summary
- RX-CARD-50: Praxis Health signal: Price pressure (Low confidence, Needs refresh). Summary: Praxis Health emphasized clinical switching data in tender discussion. Recommended response: Prepare battlecard.

### Recommended Approval Route
- Sales Manager: Every submitted deal requires baseline commercial review.
- Pricing Analyst: Discount exceeds product policy threshold.
- Market Access Director: Payer/GPO or formulary rebate concession is present.
- Finance Approver: Deal value exceeds $1M or margin is below target.
- Operations Reviewer: Supply risk, cold-chain, or coverage constraint exists.
- Legal Reviewer: Non-standard terms, long duration, or extended payment terms.
- Commercial Executive: Strategic account and deal value exceeds executive threshold.

### Final Recommendation
Escalate / approve with conditions. Commercial case may be viable, but conditions are required: requested quantity exceeds tightest available inventory match.

## SIM-004: HelioRx Rare Disease EU Launch

Customer: HelioRx Distribution (Specialty Distributor, EMEA, Enterprise)
Deal type: New Sale; payment terms: Net 60; contract: 36 months
Strategic rationale: Rare disease launch in EU5 with cold-chain allocation and high strategic value.

| Line | Qty | List | Proposed | Discount | Margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| RX-RARE-10 - Lysomab Rare Disease Kit | 20 | $28,600 | $22,780 | 20.3% | 21.9% |
| RX-ONC-500 - Oncavax IV 500mg Vial | 30 | $7,200 | $5,576 | 22.6% | 29.2% |

Deal totals: list $788,000; proposed $622,880; discount 21.0%; estimated margin 23.8% versus weighted target 31.6%.

### Plan vs Actual Analysis
- RX-RARE-10: proposed net $22,780 vs planned net $24,739 (-7.9% variance); requested units 20 vs plan units 208 (-90.4% variance).
- RX-ONC-500: proposed net $5,576 vs planned net $6,228 (-10.5% variance); requested units 30 vs plan units 187 (-84.0% variance).

### Price Analysis
- RX-RARE-10: requested discount 20.3%; historical approved discount avg 8.0% across 1 comparable rows; proposed price variance to historical approved net -13.4%.
- RX-ONC-500: requested discount 22.6%; historical approved discount avg 8.5% across 2 comparable rows; proposed price variance to historical approved net -15.4%.

### Inventory Analysis
- RX-RARE-10: requested 20; available 264 at Singapore 3PL (EMEA); coverage 12 days vs lead time 45 days; status Below Lead Time and quantity is sufficient.
- RX-ONC-500: requested 30; available 243 at Chicago DC (EMEA); coverage 12 days vs lead time 28 days; status Below Lead Time and quantity is sufficient.

### Aging Analysis
- RX-RARE-10: nearest aging lot LOT-RX-RARE-10-002 has 279 days to expiry, bucket 181-365 days, quantity 878, quality status Quality Hold; recommendation: Normal FEFO rotation.
- RX-ONC-500: nearest aging lot LOT-RX-ONC-500-001 has 6 days to expiry, bucket 0-90 days, quantity 540, quality status Quality Hold; recommendation: Prioritize tender or redistribution.

### Tender History Analysis
- RX-RARE-10: relevant tender TDR-00029 for Union National Payer in United States had outcome Won, winning net $20,163, discount 29.5%, primary competitor Novum Therapeutics, driver Clinical evidence.
- RX-ONC-500: relevant tender TDR-00014 for Atlas Hospital Network in France had outcome Won, winning net $5,616, discount 22.0%, primary competitor Orionis Pharma, driver Clinical evidence.

### Competitor Intelligence Summary
- RX-RARE-10: Cobalt Generics signal: Tender pre-positioning (High confidence, Current). Summary: Cobalt Generics emphasized clinical switching data in tender discussion. Recommended response: Prepare battlecard.
- RX-ONC-500: Cobalt Generics signal: Tender pre-positioning (High confidence, Current). Summary: Cobalt Generics referenced as lower-price alternative during account negotiation. Recommended response: Monitor only.

### Recommended Approval Route
- Sales Manager: Every submitted deal requires baseline commercial review.
- Pricing Analyst: Discount exceeds product policy threshold.
- Finance Approver: Deal value exceeds $1M or margin is below target.
- Operations Reviewer: Supply risk, cold-chain, or coverage constraint exists.

### Final Recommendation
Approve with conditions. Proceed if required reviewers accept conditions: margin below weighted product target.

## SIM-005: Summit Oncology Biosimilar Pilot

Customer: Summit Oncology Clinics (Clinic Network, North America, Mid-Market)
Deal type: New Sale; payment terms: Net 30; contract: 12 months
Strategic rationale: Community oncology pilot to support biosimilar adoption and diagnostic panel attachment.

| Line | Qty | List | Proposed | Discount | Margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| BIO-RA-200 - Rheumera Biosimilar Pen | 180 | $1,180 | $1,003 | 15.0% | 38.2% |
| DX-COMP-01 - Companion Diagnostic Panel | 80 | $950 | $807 | 15.1% | 49.2% |

Deal totals: list $288,400; proposed $245,100; discount 15.0%; estimated margin 41.1% versus weighted target 36.9%.

### Plan vs Actual Analysis
- BIO-RA-200: proposed net $1,003 vs planned net $1,038 (-3.4% variance); requested units 180 vs plan units 180 (0.0% variance).
- DX-COMP-01: proposed net $807 vs planned net $850 (-5.1% variance); requested units 80 vs plan units 530 (-84.9% variance).

### Price Analysis
- BIO-RA-200: requested discount 15.0%; historical approved discount avg 9.0% across 2 comparable rows; proposed price variance to historical approved net -6.6%.
- DX-COMP-01: requested discount 15.1%; historical approved discount avg 11.5% across 2 comparable rows; proposed price variance to historical approved net -4.0%.

### Inventory Analysis
- BIO-RA-200: requested 180; available 459 at Amsterdam 3PL (North America); coverage 41 days vs lead time 18 days; status Tight and quantity is sufficient.
- DX-COMP-01: requested 80; available 1,426 at Memphis DC (North America); coverage 47 days vs lead time 10 days; status Adequate and quantity is sufficient.

### Aging Analysis
- BIO-RA-200: nearest aging lot LOT-BIO-RA-200-003 has 251 days to expiry, bucket 181-365 days, quantity 839, quality status Released; recommendation: Normal FEFO rotation.
- DX-COMP-01: nearest aging lot LOT-DX-COMP-01-004 has 524 days to expiry, bucket >365 days, quantity 1,268, quality status Released; recommendation: Normal FEFO rotation.

### Tender History Analysis
- BIO-RA-200: relevant tender TDR-00015 for Europa Health Purchasing in Colombia had outcome Lost, winning net $950, discount 19.5%, primary competitor Novum Therapeutics, driver Local packaging.
- DX-COMP-01: relevant tender TDR-00030 for Atlas Hospital Network in Netherlands had outcome Lost, winning net $694, discount 26.9%, primary competitor Asteria Pharma, driver Local packaging.

### Competitor Intelligence Summary
- BIO-RA-200: Vantage Biosimilar signal: Formulary exclusion risk (Low confidence, 30 days old). Summary: Vantage Biosimilar has incumbent access and is defending formulary position. Recommended response: Use pricing guardrails.
- DX-COMP-01: Novum Therapeutics signal: Supply shortage (Low confidence, 30 days old). Summary: Novum Therapeutics emphasized clinical switching data in tender discussion. Recommended response: Prepare battlecard.

### Recommended Approval Route
- Sales Manager: Every submitted deal requires baseline commercial review.
- Pricing Analyst: Discount exceeds product policy threshold.
- Operations Reviewer: Supply risk, cold-chain, or coverage constraint exists.

### Final Recommendation
Approve. Pricing, margin, and supply indicators are within acceptable demo thresholds.

## SIM-006: Cityline Cardiology Rebate Renewal

Customer: Cityline Payer Alliance (Payer, North America, Enterprise)
Deal type: Renewal; payment terms: Net 90; contract: 48 months
Strategic rationale: Payer renewal with requested rebate for maintained preferred formulary tier.

| Line | Qty | List | Proposed | Discount | Margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| RX-CARD-50 - Cardiovex 50mg Tablet Pack | 22,000 | $420 | $295 | 29.8% | 64.4% |
| REB-FORM - Formulary Access Rebate | 1 | $0 | $-800,000 | 0.0% | n/a |

Deal totals: list $9,240,000; proposed $5,690,000; discount 38.4%; estimated margin 59.4% versus weighted target 66.2%.

### Plan vs Actual Analysis
- RX-CARD-50: proposed net $295 vs planned net $370 (-20.3% variance); requested units 22,000 vs plan units 180 (12122.2% variance).
- REB-FORM: rebate adjustment line; compare at deal level rather than unit plan.

### Price Analysis
- RX-CARD-50: requested discount 29.8%; historical approved discount avg 11.0% across 2 comparable rows; proposed price variance to historical approved net -21.0%.
- REB-FORM: $-800,000 rebate concession reduces net deal value and triggers market access and finance review.

### Inventory Analysis
- RX-CARD-50: requested 22,000; available 421 at Chicago DC (North America); coverage 41 days vs lead time 7 days; status Tight and quantity is short / constrained.

### Aging Analysis
- RX-CARD-50: nearest aging lot LOT-RX-CARD-50-002 has 220 days to expiry, bucket 181-365 days, quantity 800, quality status Released; recommendation: Normal FEFO rotation.

### Tender History Analysis
- RX-CARD-50: relevant tender TDR-00028 for Crescent Public Tender Authority in Singapore had outcome Split Award, winning net $286, discount 31.9%, primary competitor Orionis Pharma, driver Supply assurance.

### Competitor Intelligence Summary
- RX-CARD-50: Orionis Pharma signal: Incumbent vendor (High confidence, 60 days old). Summary: Orionis Pharma reportedly constrained on supply for next quarter. Recommended response: Escalate to market access.

### Recommended Approval Route
- Sales Manager: Every submitted deal requires baseline commercial review.
- Pricing Analyst: Discount exceeds product policy threshold.
- Market Access Director: Payer/GPO or formulary rebate concession is present.
- Finance Approver: Deal value exceeds $1M or margin is below target.
- Operations Reviewer: Supply risk, cold-chain, or coverage constraint exists.
- Legal Reviewer: Non-standard terms, long duration, or extended payment terms.
- Commercial Executive: Strategic account and deal value exceeds executive threshold.

### Final Recommendation
Escalate / approve with conditions. Commercial case may be viable, but conditions are required: requested quantity exceeds tightest available inventory match; margin below weighted product target.

## SIM-007: Orion Hospital Trust Oncology Recovery Deal

Customer: Orion Hospital Trust (Hospital Trust, EMEA, Mid-Market)
Deal type: Renewal; payment terms: Net 90; contract: 24 months
Strategic rationale: Credit-hold hospital renewal seeking oncology supply continuity while payment issues are resolved.

| Line | Qty | List | Proposed | Discount | Margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| RX-ONC-500 - Oncavax IV 500mg Vial | 22 | $7,200 | $5,100 | 29.2% | 22.5% |
| RX-ONC-100 - Oncavax IV 100mg Vial | 85 | $1,850 | $1,388 | 25.0% | 30.1% |

Deal totals: list $315,650; proposed $230,180; discount 27.1%; estimated margin 26.4% versus weighted target 37.0%.

### Plan vs Actual Analysis
- RX-ONC-500: proposed net $5,100 vs planned net $6,228 (-18.1% variance); requested units 22 vs plan units 187 (-88.2% variance).
- RX-ONC-100: proposed net $1,388 vs planned net $1,711 (-18.9% variance); requested units 85 vs plan units 96 (-11.5% variance).

### Price Analysis
- RX-ONC-500: requested discount 29.2%; historical approved discount avg 11.0% across 2 comparable rows; proposed price variance to historical approved net -20.4%.
- RX-ONC-100: requested discount 25.0%; historical approved discount avg 9.0% across 2 comparable rows; proposed price variance to historical approved net -17.6%.

### Inventory Analysis
- RX-ONC-500: requested 22; available 243 at Chicago DC (EMEA); coverage 12 days vs lead time 28 days; status Below Lead Time and quantity is sufficient.
- RX-ONC-100: requested 85; available 221 at Amsterdam 3PL (EMEA); coverage 12 days vs lead time 21 days; status Below Lead Time and quantity is sufficient.

### Aging Analysis
- RX-ONC-500: nearest aging lot LOT-RX-ONC-500-001 has 6 days to expiry, bucket 0-90 days, quantity 540, quality status Quality Hold; recommendation: Prioritize tender or redistribution.
- RX-ONC-100: nearest aging lot LOT-RX-ONC-100-002 has 36 days to expiry, bucket 0-90 days, quantity 566, quality status Quality Hold; recommendation: Prioritize tender or redistribution.

### Tender History Analysis
- RX-ONC-500: relevant tender TDR-00014 for Atlas Hospital Network in France had outcome Won, winning net $5,616, discount 22.0%, primary competitor Orionis Pharma, driver Clinical evidence.
- RX-ONC-100: relevant tender TDR-00013 for Union National Payer in United States had outcome Split Award, winning net $1,397, discount 24.5%, primary competitor Praxis Health, driver Supply assurance.

### Competitor Intelligence Summary
- RX-ONC-500: Novum Therapeutics signal: Supply shortage (Low confidence, Needs refresh). Summary: Novum Therapeutics offered rebate corridor tied to volume commitment. Recommended response: Check supply commitment.
- RX-ONC-100: Novum Therapeutics signal: Supply shortage (Low confidence, Needs refresh). Summary: Novum Therapeutics offered rebate corridor tied to volume commitment. Recommended response: Check supply commitment.

### Recommended Approval Route
- Sales Manager: Every submitted deal requires baseline commercial review.
- Pricing Analyst: Discount exceeds product policy threshold.
- Finance Approver: Deal value exceeds $1M or margin is below target.
- Operations Reviewer: Supply risk, cold-chain, or coverage constraint exists.
- Legal Reviewer: Non-standard terms, long duration, or extended payment terms.

### Final Recommendation
Request revision before approval. Resolve blocking issue(s): customer credit status is Hold.

## SIM-008: Beacon Clinical Research Trial Supply Package

Customer: Beacon Clinical Research (Research Network, North America, SMB)
Deal type: New Sale; payment terms: Net 45; contract: 18 months
Strategic rationale: Clinical research pilot requiring companion diagnostics and patient access program support.

| Line | Qty | List | Proposed | Discount | Margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| DX-COMP-01 - Companion Diagnostic Panel | 140 | $950 | $720 | 24.2% | 43.1% |
| SVC-START - Patient Start Program | 1 | $35,000 | $28,000 | 20.0% | 37.5% |

Deal totals: list $168,000; proposed $128,800; discount 23.3%; estimated margin 41.8% versus weighted target 43.9%.

### Plan vs Actual Analysis
- DX-COMP-01: proposed net $720 vs planned net $779 (-7.6% variance); requested units 140 vs plan units 334 (-58.1% variance).
- SVC-START: no plan row available; plan variance cannot be calculated.

### Price Analysis
- DX-COMP-01: requested discount 24.2%; historical approved discount avg 13.5% across 2 comparable rows; proposed price variance to historical approved net -12.4%.
- SVC-START: no historical price-volume benchmark found.

### Inventory Analysis
- DX-COMP-01: requested 140; available 1,426 at Memphis DC (North America); coverage 47 days vs lead time 10 days; status Adequate and quantity is sufficient.
- SVC-START: no inventory coverage record found.

### Aging Analysis
- DX-COMP-01: nearest aging lot LOT-DX-COMP-01-004 has 524 days to expiry, bucket >365 days, quantity 1,268, quality status Released; recommendation: Normal FEFO rotation.
- SVC-START: no expiry/aging record found.

### Tender History Analysis
- DX-COMP-01: relevant tender TDR-00030 for Atlas Hospital Network in Netherlands had outcome Lost, winning net $694, discount 26.9%, primary competitor Asteria Pharma, driver Local packaging.
- SVC-START: no tender history found.

### Competitor Intelligence Summary
- DX-COMP-01: Novum Therapeutics signal: Supply shortage (Low confidence, 30 days old). Summary: Novum Therapeutics emphasized clinical switching data in tender discussion. Recommended response: Prepare battlecard.
- SVC-START: Cobalt Generics signal: Tender pre-positioning (High confidence, Current). Summary: Cobalt Generics emphasized clinical switching data in tender discussion. Recommended response: Prepare battlecard.

### Recommended Approval Route
- Sales Manager: Every submitted deal requires baseline commercial review.
- Pricing Analyst: Discount exceeds product policy threshold.
- Finance Approver: Deal value exceeds $1M or margin is below target.
- Operations Reviewer: Supply risk, cold-chain, or coverage constraint exists.

### Final Recommendation
Approve with conditions. Proceed if required reviewers accept conditions: requested quantity exceeds tightest available inventory match; margin below weighted product target.

## SIM-009: Northstar Rare Disease Expansion

Customer: Northstar Health Systems (Integrated Delivery Network, North America, Enterprise)
Deal type: Expansion; payment terms: Net 60; contract: 42 months
Strategic rationale: Strategic rare disease expansion with long contract term and cold-chain supply constraints.

| Line | Qty | List | Proposed | Discount | Margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| RX-RARE-10 - Lysomab Rare Disease Kit | 35 | $28,600 | $22,000 | 23.1% | 19.1% |
| SVC-START - Patient Start Program | 1 | $35,000 | $30,000 | 14.3% | 41.7% |

Deal totals: list $1,036,000; proposed $800,000; discount 22.8%; estimated margin 19.9% versus weighted target 30.4%.

### Plan vs Actual Analysis
- RX-RARE-10: proposed net $22,000 vs planned net $23,452 (-6.2% variance); requested units 35 vs plan units 334 (-89.5% variance).
- SVC-START: no plan row available; plan variance cannot be calculated.

### Price Analysis
- RX-RARE-10: requested discount 23.1%; historical approved discount avg 8.0% across 1 comparable rows; proposed price variance to historical approved net -16.4%.
- SVC-START: no historical price-volume benchmark found.

### Inventory Analysis
- RX-RARE-10: requested 35; available 360 at Memphis DC (North America); coverage 41 days vs lead time 45 days; status Below Lead Time and quantity is sufficient.
- SVC-START: no inventory coverage record found.

### Aging Analysis
- RX-RARE-10: nearest aging lot LOT-RX-RARE-10-001 has 189 days to expiry, bucket 181-365 days, quantity 735, quality status Released; recommendation: Normal FEFO rotation.
- SVC-START: no expiry/aging record found.

### Tender History Analysis
- RX-RARE-10: relevant tender TDR-00029 for Union National Payer in United States had outcome Won, winning net $20,163, discount 29.5%, primary competitor Novum Therapeutics, driver Clinical evidence.
- SVC-START: no tender history found.

### Competitor Intelligence Summary
- RX-RARE-10: Asteria Pharma signal: Rebate offer (Low confidence, 30 days old). Summary: Asteria Pharma reportedly constrained on supply for next quarter. Recommended response: Escalate to market access.
- SVC-START: Asteria Pharma signal: Rebate offer (Low confidence, 30 days old). Summary: Asteria Pharma reportedly constrained on supply for next quarter. Recommended response: Escalate to market access.

### Recommended Approval Route
- Sales Manager: Every submitted deal requires baseline commercial review.
- Pricing Analyst: Discount exceeds product policy threshold.
- Finance Approver: Deal value exceeds $1M or margin is below target.
- Operations Reviewer: Supply risk, cold-chain, or coverage constraint exists.
- Legal Reviewer: Non-standard terms, long duration, or extended payment terms.

### Final Recommendation
Escalate / approve with conditions. Commercial case may be viable, but conditions are required: requested quantity exceeds tightest available inventory match; margin below weighted product target.

## SIM-010: Apex Oncology Tender Defense

Customer: Apex National GPO (Group Purchasing Organization, North America, Enterprise)
Deal type: Competitive replacement; payment terms: Net 75; contract: 36 months
Strategic rationale: Tender defense against incumbent competitor for oncology vial access across GPO members.

| Line | Qty | List | Proposed | Discount | Margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| RX-ONC-100 - Oncavax IV 100mg Vial | 500 | $1,850 | $1,400 | 24.3% | 30.7% |
| RX-ONC-500 - Oncavax IV 500mg Vial | 90 | $7,200 | $5,400 | 25.0% | 26.9% |

Deal totals: list $1,573,000; proposed $1,186,000; discount 24.6%; estimated margin 29.1% versus weighted target 37.2%.

### Plan vs Actual Analysis
- RX-ONC-100: proposed net $1,400 vs planned net $1,517 (-7.7% variance); requested units 500 vs plan units 194 (157.7% variance).
- RX-ONC-500: proposed net $5,400 vs planned net $5,904 (-8.5% variance); requested units 90 vs plan units 250 (-64.0% variance).

### Price Analysis
- RX-ONC-100: requested discount 24.3%; historical approved discount avg 14.0% across 2 comparable rows; proposed price variance to historical approved net -12.0%.
- RX-ONC-500: requested discount 25.0%; historical approved discount avg 14.0% across 2 comparable rows; proposed price variance to historical approved net -12.8%.

### Inventory Analysis
- RX-ONC-100: requested 500; available 78 at Memphis DC (North America); coverage 15 days vs lead time 21 days; status Below Lead Time and quantity is short / constrained.
- RX-ONC-500: requested 90; available 471 at Frankfurt DC (North America); coverage 41 days vs lead time 28 days; status Tight and quantity is sufficient.

### Aging Analysis
- RX-ONC-100: nearest aging lot LOT-RX-ONC-100-001 has -55 days to expiry, bucket 0-90 days, quantity 475, quality status Released; recommendation: Prioritize tender or redistribution.
- RX-ONC-500: nearest aging lot LOT-RX-ONC-500-004 has 279 days to expiry, bucket 181-365 days, quantity 852, quality status Released; recommendation: Normal FEFO rotation.

### Tender History Analysis
- RX-ONC-100: relevant tender TDR-00073 for Apex National GPO in United States had outcome Split Award, winning net $1,258, discount 32.0%, primary competitor HelixBio, driver Supply assurance.
- RX-ONC-500: relevant tender TDR-00014 for Atlas Hospital Network in France had outcome Won, winning net $5,616, discount 22.0%, primary competitor Orionis Pharma, driver Clinical evidence.

### Competitor Intelligence Summary
- RX-ONC-100: Praxis Health signal: Price pressure (Low confidence, Needs refresh). Summary: Praxis Health emphasized clinical switching data in tender discussion. Recommended response: Prepare battlecard.
- RX-ONC-500: Praxis Health signal: Price pressure (Low confidence, Needs refresh). Summary: Praxis Health emphasized clinical switching data in tender discussion. Recommended response: Prepare battlecard.

### Recommended Approval Route
- Sales Manager: Every submitted deal requires baseline commercial review.
- Pricing Analyst: Discount exceeds product policy threshold.
- Market Access Director: Payer/GPO or formulary rebate concession is present.
- Finance Approver: Deal value exceeds $1M or margin is below target.
- Operations Reviewer: Supply risk, cold-chain, or coverage constraint exists.
- Legal Reviewer: Non-standard terms, long duration, or extended payment terms.

### Final Recommendation
Escalate / approve with conditions. Commercial case may be viable, but conditions are required: requested quantity exceeds tightest available inventory match; expired inventory appears in aging pool and must be excluded; margin below weighted product target.
