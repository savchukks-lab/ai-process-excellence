# End-to-End Deal Simulation

## Scope

This document simulates ten complete pharmaceutical commercial deal requests using the updated financial-plan logic.

Each deal now uses `Included_In_Latest_Financial_Plan` to determine whether it receives plan variance analysis or incremental opportunity analysis.

## Financial Plan Logic

If `Included_In_Latest_Financial_Plan = Yes`, the simulation evaluates the deal as a plan variance:

- Planned Revenue = Planned Price x Planned Quantity
- Proposed Revenue = New Price x New Quantity
- Price Variance = (New Price - Planned Price) x New Quantity
- Volume Variance = (New Quantity - Planned Quantity) x New Price
- Net Revenue Variance = Proposed Revenue - Planned Revenue
- Gross Profit Variance = Proposed Gross Profit - Planned Gross Profit

If `Included_In_Latest_Financial_Plan = No`, the simulation classifies the deal as an incremental opportunity:

- Incremental Revenue = New Price x New Quantity
- Average Historical Price = historical approved or realized average net price
- Price vs Historical Price % = (New Price - Average Historical Price) / Average Historical Price
- Historical Average Margin % = historical gross margin percent benchmark
- Proposed Margin % = (New Price - Standard Cost) / New Price
- Margin Difference = Proposed Margin % - Historical Average Margin %

## Decision Scoring Logic

Each simulated deal receives five component scores from 0 to 20. The total decision score is the sum of all five components, producing a 0 to 100 score.

- Margin Score: measures gross margin quality, price variance, price versus history, and gross profit impact.
- Strategic Score: measures account importance, access value, contract duration, channel priority, and commercial rationale.
- Inventory Score: measures excess inventory, shortage risk, demand forecast coverage, allocation risk, and cannibalization risk against existing demand.
- Competitive Score: measures historical tender results, incumbent competitor posture, aggressive competitor pricing, supply issues, and nearby market behavior.
- Risk Score: measures payment terms, approval complexity, legal exposure, execution risk, and policy exception risk. A higher score means lower risk.

Decision rules:

- Approve: total score is 85 or higher with no material supply, pricing, or escalation override.
- Approve with Conditions: total score is 70 to 84 and risks can be controlled through standard approval conditions.
- Approve only if Aging Stock Allocated: near-expiry or aging inventory can materially improve the deal economics or reduce obsolescence exposure without creating service risk.
- Request Price Revision: margin, price versus history, or tender benchmark position is below acceptable thresholds.
- Request Supply Review: inventory shortage, allocation risk, demand forecast conflict, or supply continuity is the primary blocker.
- Reject: total score is below 50 or the deal has unacceptable margin, supply, compliance, or execution risk.
- Escalate to GM: deal has material enterprise, payer, GPO, public tender, or multi-year strategic exposure that requires executive judgment even if the economics are positive.

## Portfolio Summary

| Deal | Included In Plan | Margin | Strategic | Inventory | Competitive | Risk | Total Decision Score | Final Recommendation |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| DEAL-4001 Northstar Oncology Infusion Expansion | Yes | 8 | 16 | 5 | 14 | 9 | 52 | Request Supply Review |
| DEAL-4002 Meridian Biosimilar Conversion | Yes | 17 | 16 | 16 | 18 | 19 | 86 | Approve |
| DEAL-4003 Apex National Formulary Access | Yes | 15 | 20 | 15 | 16 | 12 | 78 | Escalate to GM |
| DEAL-4004 HelioRx Rare Disease EU Launch | No | 13 | 17 | 6 | 13 | 10 | 59 | Approve only if Aging Stock Allocated |
| DEAL-4005 Summit Oncology Biosimilar Pilot | Yes | 18 | 16 | 16 | 18 | 20 | 88 | Approve |
| DEAL-4006 Cityline Cardiology Rebate Renewal | Yes | 14 | 20 | 15 | 12 | 11 | 72 | Escalate to GM |
| DEAL-4007 Crescent Public Oncology Tender | Yes | 13 | 18 | 7 | 15 | 11 | 64 | Approve only if Aging Stock Allocated |
| DEAL-4008 Atlas Hospital Diagnostic Framework | No | 10 | 14 | 12 | 12 | 12 | 60 | Request Price Revision |
| DEAL-4009 BluePeak Immunology Access | Yes | 13 | 18 | 12 | 14 | 13 | 70 | Approve with Conditions |
| DEAL-4010 Metro Infusion Rare Disease Expansion | No | 15 | 16 | 6 | 13 | 12 | 62 | Request Supply Review |

## DEAL-4001: Northstar Oncology Infusion Expansion

Included_In_Latest_Financial_Plan: Yes
Customer: Northstar Health Systems (Integrated Delivery Network, North America, Enterprise)
Deal summary: Competitive replacement; channel IDN; payment terms Net 60; contract duration 36 months; proposed revenue $418,200.

### Plan vs Actual / Plan Impact
- Planned Revenue: $2,622,840
- Proposed Revenue: $418,200
- Price Variance: $-30,600
- Volume Variance: $-2,025,810
- Net Revenue Variance: $-2,204,640
- Gross Profit Variance: $-853,340
- RX-ONC-100: planned 210 units at $1,628; proposed 120 units at $1,517.
- RX-ONC-500: planned 360 units at $6,336; proposed 40 units at $5,904.

### Price-Volume Analysis
- RX-ONC-100: proposed price $1,517 versus historical average $1,582; proposed margin 36.1%.
- RX-ONC-500: proposed price $5,904 versus historical average $6,156; proposed margin 33.1%.

### Inventory Coverage
- RX-ONC-100: 24 days of simulated coverage; High supply risk; operations review recommended.
- RX-ONC-500: 24 days of simulated coverage; High supply risk; operations review recommended.
- Inventory finding: inventory shortage is likely against the requested volume, with high allocation risk and possible cannibalization of existing oncology demand forecast.

### Expiry Aging
- RX-ONC-100: nearest eligible lot has 145 days to expiry; use FEFO allocation and exclude expired lots.
- RX-ONC-500: nearest eligible lot has 145 days to expiry; use FEFO allocation and exclude expired lots.
- Expiry finding: near-expiry inventory exists but is not enough to offset the shortage signal; any allocation must prioritize aging lots without disrupting committed demand.

### Tender History
- RX-ONC-100: tender benchmark discount 28.0%; proposed discount 18.0%.
- RX-ONC-500: tender benchmark discount 28.0%; proposed discount 18.0%.

### Competitor Intelligence
- RX-ONC-100: competitor pressure is supply-assurance and clinical differentiation oriented; document pricing guardrails before approval.
- RX-ONC-500: competitor pressure is supply-assurance and clinical differentiation oriented; document pricing guardrails before approval.
- Competitive finding: the incumbent competitor is vulnerable on supply assurance, but nearby market behavior suggests customers will punish missed delivery more than modest price gaps.

### Approval Route
- Sales Manager
- Pricing Analyst
- Finance Approver
- Operations Reviewer

### Final Recommendation
Request Supply Review.

Decision scorecard:

- Margin Score: 8/20
- Strategic Score: 16/20
- Inventory Score: 5/20
- Competitive Score: 14/20
- Risk Score: 9/20
- Total Decision Score: 52/100

Why selected: the deal has strategic replacement value, but the total score is held down by severe negative plan impact, inventory shortage on both oncology products, high allocation risk, and only 24 days of simulated coverage. Competitor intelligence shows an incumbent that can be displaced through supply assurance, but the same finding makes delivery reliability the central decision factor. Approval should wait for operations confirmation of allocation, backorder exposure, demand forecast impact, and feasible delivery timing.

Confidence level: Medium.

## DEAL-4002: Meridian Biosimilar Conversion

Included_In_Latest_Financial_Plan: Yes
Customer: Meridian Specialty Pharmacy (Specialty Pharmacy, North America, Mid-Market)
Deal summary: Expansion; channel Specialty Pharmacy; payment terms Net 45; contract duration 24 months; proposed revenue $532,525.

### Plan vs Actual / Plan Impact
- Planned Revenue: $609,720
- Proposed Revenue: $532,525
- Price Variance: $-25,675
- Volume Variance: $-52,005
- Net Revenue Variance: $-77,195
- Gross Profit Variance: $-76,045
- BIO-RA-200: planned 320 units at $991; proposed 500 units at $944.
- DX-COMP-01: planned 350 units at $836; proposed 75 units at $807.

### Price-Volume Analysis
- BIO-RA-200: proposed price $944 versus historical average $979; proposed margin 34.3%.
- DX-COMP-01: proposed price $807 versus historical average $817; proposed margin 49.2%.

### Inventory Coverage
- BIO-RA-200: 42 days of simulated coverage; Medium supply risk; operations review recommended.
- DX-COMP-01: 42 days of simulated coverage; Medium supply risk; operations review recommended.
- Inventory finding: coverage is sufficient for the requested demand forecast, with moderate allocation risk and low cannibalization risk because the conversion supports planned specialty-pharmacy growth.

### Expiry Aging
- BIO-RA-200: nearest eligible lot has 260 days to expiry; use FEFO allocation and exclude expired lots.
- DX-COMP-01: nearest eligible lot has 260 days to expiry; use FEFO allocation and exclude expired lots.
- Expiry finding: no near-expiry blocker; standard FEFO is adequate and aging inventory is not the reason for approval.

### Tender History
- BIO-RA-200: tender benchmark discount 24.0%; proposed discount 20.0%.
- DX-COMP-01: tender benchmark discount 19.0%; proposed discount 15.1%.

### Competitor Intelligence
- BIO-RA-200: competitor pressure is price and access oriented; document pricing guardrails before approval.
- DX-COMP-01: competitor pressure is price and access oriented; document pricing guardrails before approval.
- Competitive finding: historical tender results show proposed discounts are less aggressive than benchmark, and nearby specialty pharmacy behavior supports biosimilar conversion when access terms are stable.

### Approval Route
- Sales Manager
- Pricing Analyst
- Operations Reviewer

### Final Recommendation
Approve.

Decision scorecard:

- Margin Score: 17/20
- Strategic Score: 16/20
- Inventory Score: 16/20
- Competitive Score: 18/20
- Risk Score: 19/20
- Total Decision Score: 86/100

Why selected: the proposed prices remain close to historical averages, tender discounts are better than historical tender benchmarks, and 42 days of inventory coverage supports the demand forecast with manageable allocation risk. Competitor pressure is price and access oriented, but there is no incumbent supply issue or nearby-market warning that would require a special condition. The negative plan variance is modest enough to approve.

Confidence level: High.

## DEAL-4003: Apex National Formulary Access

Included_In_Latest_Financial_Plan: Yes
Customer: Apex National GPO (Group Purchasing Organization, North America, Enterprise)
Deal summary: Strategic exception; channel GPO; payment terms Net 90; contract duration 48 months; proposed revenue $5,622,000.

### Plan vs Actual / Plan Impact
- Planned Revenue: $1,945,640
- Proposed Revenue: $5,622,000
- Price Variance: $-672,480
- Volume Variance: $3,794,480
- Net Revenue Variance: $3,676,360
- Gross Profit Variance: $2,815,660
- RX-CARD-50: planned 340 units at $370; proposed 15,000 units at $328.
- RX-ONC-ORAL: planned 220 units at $8,272; proposed 90 units at $7,800.

### Price-Volume Analysis
- RX-CARD-50: proposed price $328 versus historical average $359; proposed margin 68.0%.
- RX-ONC-ORAL: proposed price $7,800 versus historical average $8,037; proposed margin 33.1%.

### Inventory Coverage
- RX-CARD-50: 75 days of simulated coverage; Low supply risk; operations review not mandatory.
- RX-ONC-ORAL: 42 days of simulated coverage; Medium supply risk; operations review recommended.
- Inventory finding: RX-CARD-50 has excess coverage that can support the large access play, while RX-ONC-ORAL has moderate allocation risk and should be checked against oncology demand forecast before award.

### Expiry Aging
- RX-CARD-50: nearest eligible lot has 260 days to expiry; use FEFO allocation and exclude expired lots.
- RX-ONC-ORAL: nearest eligible lot has 260 days to expiry; use FEFO allocation and exclude expired lots.
- Expiry finding: no near-expiry constraint; aging inventory is not required to make the economics work.

### Tender History
- RX-CARD-50: tender benchmark discount 28.0%; proposed discount 21.9%.
- RX-ONC-ORAL: tender benchmark discount 28.0%; proposed discount 17.0%.

### Competitor Intelligence
- RX-CARD-50: competitor pressure is price and access oriented; document pricing guardrails before approval.
- RX-ONC-ORAL: competitor pressure is price and access oriented; document pricing guardrails before approval.
- Competitive finding: historical tender results support the requested discount level, but the national GPO context suggests aggressive competitor pricing and nearby market spillover risk if the price becomes a reference point.

### Approval Route
- Sales Manager
- Pricing Analyst
- Market Access Director
- Finance Approver
- Operations Reviewer
- Legal Reviewer
- Commercial Executive

### Final Recommendation
Escalate to GM.

Decision scorecard:

- Margin Score: 15/20
- Strategic Score: 20/20
- Inventory Score: 15/20
- Competitive Score: 16/20
- Risk Score: 12/20
- Total Decision Score: 78/100

Why selected: the deal generates a large positive revenue and gross profit variance, with RX-CARD-50 excess inventory supporting the access play and RX-ONC-ORAL requiring a demand forecast check. Competitor findings show aggressive price and access pressure in a national GPO setting, with risk that nearby markets use the awarded price as a reference. The economics support pursuit, but inventory allocation and competitive spillover exposure are large enough to require GM judgment before approval.

Confidence level: Medium.

## DEAL-4004: HelioRx Rare Disease EU Launch

Included_In_Latest_Financial_Plan: No
Customer: HelioRx Distribution (Specialty Distributor, EMEA, Enterprise)
Deal summary: New Sale; channel Specialty Distributor; payment terms Net 60; contract duration 36 months; proposed revenue $740,600.

### Incremental Opportunity Analysis
- Classification: Incremental Opportunity
- Incremental Revenue: $740,600
- Average Historical Price: $25,147
- Price vs Historical Price %: -1.8%
- Historical Average Margin %: 23.9%
- Proposed Margin %: 22.5%
- Margin Difference: -1.4%

### Price-Volume Analysis
- RX-RARE-10: proposed price $22,780 versus historical average $23,452; proposed margin 21.9%.
- RX-RARE-INF: proposed price $28,500 versus historical average $28,536; proposed margin 23.5%.

### Inventory Coverage
- RX-RARE-10: 24 days of simulated coverage; High supply risk; operations review recommended.
- RX-RARE-INF: 24 days of simulated coverage; High supply risk; operations review recommended.
- Inventory finding: inventory shortage and allocation risk are high for both rare disease products, and the request may cannibalize committed patient-start demand if supply is not ring-fenced.

### Expiry Aging
- RX-RARE-10: nearest eligible lot has 145 days to expiry; use FEFO allocation and exclude expired lots.
- RX-RARE-INF: nearest eligible lot has 145 days to expiry; use FEFO allocation and exclude expired lots.
- Expiry finding: near-expiry and aging inventory can support the incremental opportunity only if the lots are clinically and logistically suitable for the launch markets.

### Tender History
- RX-RARE-10: tender benchmark discount 19.0%; proposed discount 20.3%.
- RX-RARE-INF: tender benchmark discount 19.0%; proposed discount 18.1%.

### Competitor Intelligence
- RX-RARE-10: competitor pressure is supply-assurance and clinical differentiation oriented; document pricing guardrails before approval.
- RX-RARE-INF: competitor pressure is supply-assurance and clinical differentiation oriented; document pricing guardrails before approval.
- Competitive finding: the incumbent competitor appears exposed on supply issues, but nearby EU market behavior favors reliable continuity over lowest price in rare disease categories.

### Approval Route
- Sales Manager
- Pricing Analyst
- Finance Approver
- Operations Reviewer

### Final Recommendation
Approve only if Aging Stock Allocated.

Decision scorecard:

- Margin Score: 13/20
- Strategic Score: 17/20
- Inventory Score: 6/20
- Competitive Score: 13/20
- Risk Score: 10/20
- Total Decision Score: 59/100

Why selected: this is an incremental rare disease launch opportunity with acceptable strategic value, but both products show inventory shortage, high allocation risk, 24 days of simulated coverage, and nearest eligible lots at 145 days to expiry. Competitor intelligence shows incumbent supply issues, so winning through reliability matters more than matching aggressive price behavior. Approval should be conditional on using appropriate aging stock under FEFO controls and protecting committed patient demand.

Confidence level: Medium.

## DEAL-4005: Summit Oncology Biosimilar Pilot

Included_In_Latest_Financial_Plan: Yes
Customer: Summit Oncology Clinics (Clinic Network, North America, Mid-Market)
Deal summary: New Sale; channel Clinic Network; payment terms Net 30; contract duration 12 months; proposed revenue $245,100.

### Plan vs Actual / Plan Impact
- Planned Revenue: $609,720
- Proposed Revenue: $245,100
- Price Variance: $-160
- Volume Variance: $-358,310
- Net Revenue Variance: $-364,620
- Gross Profit Variance: $-167,120
- BIO-RA-200: planned 320 units at $991; proposed 180 units at $1,003.
- DX-COMP-01: planned 350 units at $836; proposed 80 units at $807.

### Price-Volume Analysis
- BIO-RA-200: proposed price $1,003 versus historical average $979; proposed margin 38.2%.
- DX-COMP-01: proposed price $807 versus historical average $817; proposed margin 49.2%.

### Inventory Coverage
- BIO-RA-200: 42 days of simulated coverage; Medium supply risk; operations review recommended.
- DX-COMP-01: 42 days of simulated coverage; Medium supply risk; operations review recommended.
- Inventory finding: coverage is adequate for a pilot and does not indicate excess inventory dependence; allocation risk is moderate and cannibalization risk is low because the deal volume is contained.

### Expiry Aging
- BIO-RA-200: nearest eligible lot has 260 days to expiry; use FEFO allocation and exclude expired lots.
- DX-COMP-01: nearest eligible lot has 260 days to expiry; use FEFO allocation and exclude expired lots.
- Expiry finding: no near-expiry or aging-stock constraint; standard FEFO controls are sufficient.

### Tender History
- BIO-RA-200: tender benchmark discount 24.0%; proposed discount 15.0%.
- DX-COMP-01: tender benchmark discount 19.0%; proposed discount 15.1%.

### Competitor Intelligence
- BIO-RA-200: competitor pressure is price and access oriented; document pricing guardrails before approval.
- DX-COMP-01: competitor pressure is price and access oriented; document pricing guardrails before approval.
- Competitive finding: historical tender results indicate the proposed discount is favorable versus benchmark, and nearby clinic behavior supports adoption when biosimilar savings are paired with diagnostic workflow support.

### Approval Route
- Sales Manager
- Pricing Analyst
- Operations Reviewer

### Final Recommendation
Approve.

Decision scorecard:

- Margin Score: 18/20
- Strategic Score: 16/20
- Inventory Score: 16/20
- Competitive Score: 18/20
- Risk Score: 20/20
- Total Decision Score: 88/100

Why selected: the pilot has strong margin quality, proposed pricing is at or above historical levels for the main biosimilar line, and 42 days of inventory coverage is adequate for the demand forecast. Competitor findings show price and access pressure, but historical tender results are favorable and there is no incumbent supply issue requiring a condition. The plan variance is negative mainly because requested quantity is below plan, not because of weak price quality.

Confidence level: High.

## DEAL-4006: Cityline Cardiology Rebate Renewal

Included_In_Latest_Financial_Plan: Yes
Customer: Cityline Payer Alliance (Payer, North America, Enterprise)
Deal summary: Renewal; channel Payer; payment terms Net 90; contract duration 48 months; proposed revenue $7,471,000.

### Plan vs Actual / Plan Impact
- Planned Revenue: $358,200
- Proposed Revenue: $7,471,000
- Price Variance: $-1,714,800
- Volume Variance: $7,152,700
- Net Revenue Variance: $7,112,800
- Gross Profit Variance: $4,411,500
- RX-CARD-50: planned 340 units at $370; proposed 22,000 units at $295.
- RX-HOSP-20: planned 200 units at $1,162; proposed 900 units at $1,090.

### Price-Volume Analysis
- RX-CARD-50: proposed price $295 versus historical average $359; proposed margin 64.4%.
- RX-HOSP-20: proposed price $1,090 versus historical average $1,129; proposed margin 44.0%.

### Inventory Coverage
- RX-CARD-50: 75 days of simulated coverage; Low supply risk; operations review not mandatory.
- RX-HOSP-20: 42 days of simulated coverage; Medium supply risk; operations review recommended.
- Inventory finding: RX-CARD-50 has excess inventory coverage against forecast, while RX-HOSP-20 has moderate allocation risk that should be checked before committing payer pull-through volumes.

### Expiry Aging
- RX-CARD-50: nearest eligible lot has 260 days to expiry; use FEFO allocation and exclude expired lots.
- RX-HOSP-20: nearest eligible lot has 260 days to expiry; use FEFO allocation and exclude expired lots.
- Expiry finding: no near-expiry blocker; aging inventory is not a primary driver, so the renewal should stand on access economics rather than inventory clearance.

### Tender History
- RX-CARD-50: tender benchmark discount 28.0%; proposed discount 29.8%.
- RX-HOSP-20: tender benchmark discount 19.0%; proposed discount 17.4%.

### Competitor Intelligence
- RX-CARD-50: competitor pressure is price and access oriented; document pricing guardrails before approval.
- RX-HOSP-20: competitor pressure is price and access oriented; document pricing guardrails before approval.
- Competitive finding: historical tender results show RX-CARD-50 is priced more aggressively than benchmark, likely reflecting incumbent competitor pressure and nearby payer-market reference behavior.

### Approval Route
- Sales Manager
- Pricing Analyst
- Market Access Director
- Finance Approver
- Operations Reviewer
- Legal Reviewer
- Commercial Executive

### Final Recommendation
Escalate to GM.

Decision scorecard:

- Margin Score: 14/20
- Strategic Score: 20/20
- Inventory Score: 15/20
- Competitive Score: 12/20
- Risk Score: 11/20
- Total Decision Score: 72/100

Why selected: the renewal creates the largest proposed revenue and a strong positive gross profit variance, with RX-CARD-50 excess coverage supporting the forecast and RX-HOSP-20 needing an allocation check. Competitor findings show aggressive payer and tender pricing behavior, including a cardiology discount deeper than benchmark and nearby-market reference risk. The commercial upside is meaningful, but executive review is needed to confirm access value, rebate exposure, and inventory allocation.

Confidence level: Medium.

## DEAL-4007: Crescent Public Oncology Tender

Included_In_Latest_Financial_Plan: Yes
Customer: Crescent Public Tender Authority (Tender Authority, LATAM, Strategic Public)
Deal summary: Tender; channel Tender Authority; payment terms Net 75; contract duration 36 months; proposed revenue $2,121,000.

### Plan vs Actual / Plan Impact
- Planned Revenue: $574,280
- Proposed Revenue: $2,121,000
- Price Variance: $-250,200
- Volume Variance: $1,616,250
- Net Revenue Variance: $1,546,720
- Gross Profit Variance: $558,420
- RX-ONC-100: planned 210 units at $1,628; proposed 600 units at $1,375.
- RX-HOSP-20: planned 200 units at $1,162; proposed 1,200 units at $1,080.

### Price-Volume Analysis
- RX-ONC-100: proposed price $1,375 versus historical average $1,582; proposed margin 29.5%.
- RX-HOSP-20: proposed price $1,080 versus historical average $1,129; proposed margin 43.5%.

### Inventory Coverage
- RX-ONC-100: 24 days of simulated coverage; High supply risk; operations review recommended.
- RX-HOSP-20: 42 days of simulated coverage; Medium supply risk; operations review recommended.
- Inventory finding: RX-ONC-100 has shortage risk and high allocation risk, while RX-HOSP-20 can support demand with standard controls. The tender could cannibalize planned oncology demand if award timing is not phased.

### Expiry Aging
- RX-ONC-100: nearest eligible lot has 145 days to expiry; use FEFO allocation and exclude expired lots.
- RX-HOSP-20: nearest eligible lot has 260 days to expiry; use FEFO allocation and exclude expired lots.
- Expiry finding: RX-ONC-100 has near-expiry inventory that can improve obsolescence risk if allocated to the tender first; RX-HOSP-20 does not need aging-stock intervention.

### Tender History
- RX-ONC-100: tender benchmark discount 28.0%; proposed discount 25.7%.
- RX-HOSP-20: tender benchmark discount 19.0%; proposed discount 18.2%.

### Competitor Intelligence
- RX-ONC-100: competitor pressure is supply-assurance and clinical differentiation oriented; document pricing guardrails before approval.
- RX-HOSP-20: competitor pressure is price and access oriented; document pricing guardrails before approval.
- Competitive finding: historical public tender results support the requested discount, but the incumbent competitor is likely to challenge oncology supply assurance and nearby LATAM tenders may react to the awarded price.

### Approval Route
- Sales Manager
- Pricing Analyst
- Market Access Director
- Finance Approver
- Operations Reviewer
- Legal Reviewer

### Final Recommendation
Approve only if Aging Stock Allocated.

Decision scorecard:

- Margin Score: 13/20
- Strategic Score: 18/20
- Inventory Score: 7/20
- Competitive Score: 15/20
- Risk Score: 11/20
- Total Decision Score: 64/100

Why selected: the public tender has strategic access value and positive gross profit impact, but RX-ONC-100 has shortage risk, high allocation risk, only 24 days of coverage, and a 145-day eligible lot. Competitor findings show the incumbent may attack supply assurance and nearby LATAM tender behavior could make the awarded price visible beyond this account. The decision should be conditional on allocating suitable aging inventory first and confirming FEFO execution before award acceptance.

Confidence level: Medium.

## DEAL-4008: Atlas Hospital Diagnostic Framework

Included_In_Latest_Financial_Plan: No
Customer: Atlas Hospital Network (Hospital Network, EMEA, Enterprise)
Deal summary: New Sale; channel Hospital Trust; payment terms Net 60; contract duration 36 months; proposed revenue $803,500.

### Incremental Opportunity Analysis
- Classification: Incremental Opportunity
- Incremental Revenue: $803,500
- Average Historical Price: $2,618
- Price vs Historical Price %: -4.1%
- Historical Average Margin %: 39.1%
- Proposed Margin %: 36.5%
- Margin Difference: -2.6%

### Price-Volume Analysis
- DX-GENE-02: proposed price $1,030 versus historical average $1,101; proposed margin 43.7%.
- RX-ONC-ORAL: proposed price $7,800 versus historical average $8,037; proposed margin 33.1%.

### Inventory Coverage
- DX-GENE-02: 42 days of simulated coverage; Medium supply risk; operations review recommended.
- RX-ONC-ORAL: 42 days of simulated coverage; Medium supply risk; operations review recommended.
- Inventory finding: inventory coverage is moderate for both products, with no excess inventory benefit and no acute shortage, but allocation should be checked against hospital launch demand forecast.

### Expiry Aging
- DX-GENE-02: nearest eligible lot has 260 days to expiry; use FEFO allocation and exclude expired lots.
- RX-ONC-ORAL: nearest eligible lot has 260 days to expiry; use FEFO allocation and exclude expired lots.
- Expiry finding: no near-expiry or aging-stock rationale; approval depends on price quality and competitive positioning rather than inventory cleanup.

### Tender History
- DX-GENE-02: tender benchmark discount 19.0%; proposed discount 19.5%.
- RX-ONC-ORAL: tender benchmark discount 28.0%; proposed discount 17.0%.

### Competitor Intelligence
- DX-GENE-02: competitor pressure is price and access oriented; document pricing guardrails before approval.
- RX-ONC-ORAL: competitor pressure is price and access oriented; document pricing guardrails before approval.
- Competitive finding: historical tender results show the diagnostic line is already slightly beyond benchmark discount, and nearby hospital behavior suggests competitors may use bundled diagnostic pricing to pressure oncology access.

### Approval Route
- Sales Manager
- Pricing Analyst
- Operations Reviewer

### Final Recommendation
Request Price Revision.

Decision scorecard:

- Margin Score: 10/20
- Strategic Score: 14/20
- Inventory Score: 12/20
- Competitive Score: 12/20
- Risk Score: 12/20
- Total Decision Score: 60/100

Why selected: the opportunity is incremental and inventory coverage is manageable at 42 days, but there is no excess or aging inventory benefit to justify weak economics. Competitor findings show price and access pressure, with the diagnostic line already slightly beyond historical tender benchmark and nearby hospital behavior favoring bundled discounts. The primary issue is price quality, so the request should return to sales for revised price, reduced discount, or stronger strategic justification.

Confidence level: Medium.

## DEAL-4009: BluePeak Immunology Access

Included_In_Latest_Financial_Plan: Yes
Customer: BluePeak Payer Coalition (Payer, North America, Enterprise)
Deal summary: Strategic exception; channel Payer; payment terms Net 75; contract duration 42 months; proposed revenue $1,314,250.

### Plan vs Actual / Plan Impact
- Planned Revenue: $629,860
- Proposed Revenue: $1,314,250
- Price Variance: $-79,000
- Volume Variance: $720,350
- Net Revenue Variance: $684,390
- Gross Profit Variance: $211,440
- BIO-DERM-80: planned 380 units at $823; proposed 850 units at $805.
- BIO-RA-200: planned 320 units at $991; proposed 700 units at $900.

### Price-Volume Analysis
- BIO-DERM-80: proposed price $805 versus historical average $813; proposed margin 37.3%.
- BIO-RA-200: proposed price $900 versus historical average $979; proposed margin 31.1%.

### Inventory Coverage
- BIO-DERM-80: 42 days of simulated coverage; Medium supply risk; operations review recommended.
- BIO-RA-200: 42 days of simulated coverage; Medium supply risk; operations review recommended.
- Inventory finding: coverage supports the forecast with moderate allocation risk, but the payer coalition volume may cannibalize other access commitments if pull-through accelerates faster than forecast.

### Expiry Aging
- BIO-DERM-80: nearest eligible lot has 260 days to expiry; use FEFO allocation and exclude expired lots.
- BIO-RA-200: nearest eligible lot has 260 days to expiry; use FEFO allocation and exclude expired lots.
- Expiry finding: no near-expiry issue; aging inventory does not drive the recommendation.

### Tender History
- BIO-DERM-80: tender benchmark discount 24.0%; proposed discount 17.9%.
- BIO-RA-200: tender benchmark discount 24.0%; proposed discount 23.7%.

### Competitor Intelligence
- BIO-DERM-80: competitor pressure is price and access oriented; document pricing guardrails before approval.
- BIO-RA-200: competitor pressure is price and access oriented; document pricing guardrails before approval.
- Competitive finding: historical tender results support BIO-DERM-80 pricing, while BIO-RA-200 is close to benchmark and exposed to aggressive competitor pricing in nearby payer markets.

### Approval Route
- Sales Manager
- Pricing Analyst
- Market Access Director
- Finance Approver
- Operations Reviewer
- Legal Reviewer

### Final Recommendation
Approve with Conditions.

Decision scorecard:

- Margin Score: 13/20
- Strategic Score: 18/20
- Inventory Score: 12/20
- Competitive Score: 14/20
- Risk Score: 13/20
- Total Decision Score: 70/100

Why selected: the deal has positive revenue and gross profit variance, payer access value, and 42 days of inventory coverage, but allocation should be monitored against other access commitments. Competitor findings are mixed: BIO-DERM-80 is defensible versus historical tender results, while BIO-RA-200 faces aggressive nearby payer pricing and is meaningfully below historical average. Conditions are required for pricing guardrails, pull-through monitoring, and finance plus legal approval.

Confidence level: Medium.

## DEAL-4010: Metro Infusion Rare Disease Expansion

Included_In_Latest_Financial_Plan: No
Customer: Metro Infusion Partners (Clinic Network, North America, Mid-Market)
Deal summary: Expansion; channel Clinic Network; payment terms Net 45; contract duration 24 months; proposed revenue $680,600.

### Incremental Opportunity Analysis
- Classification: Incremental Opportunity
- Incremental Revenue: $680,600
- Average Historical Price: $26,190
- Price vs Historical Price %: -0.0%
- Historical Average Margin %: 23.8%
- Proposed Margin %: 23.8%
- Margin Difference: -0.0%

### Price-Volume Analysis
- RX-RARE-INF: proposed price $28,900 versus historical average $28,536; proposed margin 24.6%.
- RX-RARE-10: proposed price $23,000 versus historical average $23,452; proposed margin 22.6%.

### Inventory Coverage
- RX-RARE-INF: 24 days of simulated coverage; High supply risk; operations review recommended.
- RX-RARE-10: 24 days of simulated coverage; High supply risk; operations review recommended.
- Inventory finding: inventory shortage and high allocation risk are the controlling issues, with cannibalization risk against existing rare disease patient continuity if incremental demand is accepted without ring-fenced supply.

### Expiry Aging
- RX-RARE-INF: nearest eligible lot has 145 days to expiry; use FEFO allocation and exclude expired lots.
- RX-RARE-10: nearest eligible lot has 145 days to expiry; use FEFO allocation and exclude expired lots.
- Expiry finding: near-expiry inventory exists and could support controlled expansion, but only if aging stock can be matched to the right clinic timing and cold-chain pathway.

### Tender History
- RX-RARE-INF: tender benchmark discount 19.0%; proposed discount 17.0%.
- RX-RARE-10: tender benchmark discount 19.0%; proposed discount 19.6%.

### Competitor Intelligence
- RX-RARE-INF: competitor pressure is supply-assurance and clinical differentiation oriented; document pricing guardrails before approval.
- RX-RARE-10: competitor pressure is supply-assurance and clinical differentiation oriented; document pricing guardrails before approval.
- Competitive finding: incumbent supply issues create an opening, but nearby market behavior in rare disease favors continuity and patient-start reliability over aggressive discounting.

### Approval Route
- Sales Manager
- Pricing Analyst
- Finance Approver
- Operations Reviewer

### Final Recommendation
Request Supply Review.

Decision scorecard:

- Margin Score: 15/20
- Strategic Score: 16/20
- Inventory Score: 6/20
- Competitive Score: 13/20
- Risk Score: 12/20
- Total Decision Score: 62/100

Why selected: the incremental revenue and margin benchmark are acceptable, but both rare disease products show inventory shortage, high allocation risk, and only 24 days of simulated coverage. Competitor findings show an incumbent weakness around supply assurance, but nearby market behavior makes continuity more important than aggressive pricing. Operations should confirm allocation feasibility, patient continuity risk, demand forecast impact, and whether aging stock can be used before the deal moves forward.

Confidence level: Medium.
