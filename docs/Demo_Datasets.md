# Demo Datasets

## Overview

The MVP should include realistic demo datasets that support end-to-end stakeholder walkthroughs. Demo data should show standard approvals, pricing exceptions, inventory constraints, competitive pressure, and executive dashboard trends.

The datasets should be synthetic and should not contain real customer confidential information.

## Dataset Goals

- Enable complete deal submission and approval demos.
- Support pricing, inventory, and competitive analysis.
- Populate executive dashboards with meaningful patterns.
- Demonstrate approval routing across roles.
- Show audit trail behavior across realistic deal lifecycles.

## Recommended Dataset Files

Potential seed files:

- `users.csv`
- `roles.csv`
- `customers.csv`
- `opportunities.csv`
- `products.csv`
- `price_books.csv`
- `price_book_entries.csv`
- `inventory_positions.csv`
- `historical_deals.csv`
- `historical_deal_line_items.csv`
- `competitive_intelligence.csv`
- `approval_policies.csv`
- `demo_deals.csv`
- `demo_approval_events.csv`

These files do not need to exist yet. This document defines their intended content.

## Users

Purpose:

Create realistic personas for deal submission, review, approval, and dashboard viewing.

Suggested records:

| Name | Email | Department | Region | Role |
| --- | --- | --- | --- | --- |
| Maya Chen | maya.chen@example.com | Sales | North America | Sales Representative |
| Jordan Blake | jordan.blake@example.com | Sales | North America | Sales Manager |
| Priya Nair | priya.nair@example.com | Pricing | Global | Pricing Analyst |
| Daniel Ortiz | daniel.ortiz@example.com | Finance | Global | Finance Approver |
| Elena Rossi | elena.rossi@example.com | Operations | EMEA | Operations Reviewer |
| Sarah Morgan | sarah.morgan@example.com | Executive | Global | Executive |
| Aisha Khan | aisha.khan@example.com | Legal | Global | Legal Reviewer |

## Customers

Purpose:

Represent accounts across segments, regions, industries, and strategic importance.

Suggested records:

| Customer | Segment | Industry | Region | Strategic Account | Credit Status |
| --- | --- | --- | --- | --- | --- |
| Northstar Health Systems | Enterprise | Healthcare | North America | Yes | Good |
| Meridian Manufacturing | Mid-Market | Industrial | North America | No | Good |
| Apex Retail Group | Enterprise | Retail | EMEA | Yes | Watch |
| HelioTech Energy | Enterprise | Energy | EMEA | Yes | Good |
| Summit BioLabs | Mid-Market | Life Sciences | North America | No | Good |
| Cityline Logistics | SMB | Logistics | North America | No | Good |

## Products

Purpose:

Support different margin profiles, inventory constraints, and approval scenarios.

Suggested records:

| SKU | Product Name | Product Line | Category | List Price | Standard Cost | Margin Target | Lead Time |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HW-100 | Core Hardware Unit | Hardware | Device | 12000 | 7200 | 35% | 21 days |
| HW-200 | Advanced Hardware Unit | Hardware | Device | 22000 | 14500 | 32% | 35 days |
| SW-ENT | Enterprise Software License | Software | Subscription | 18000 | 2500 | 75% | 0 days |
| SVC-IMP | Implementation Services | Services | Professional Services | 15000 | 9000 | 30% | 14 days |
| SVC-PREM | Premium Support | Services | Support | 8000 | 2500 | 60% | 0 days |
| CONS-01 | Consumable Kit | Consumables | Supply | 900 | 540 | 35% | 10 days |

## Price Books

Purpose:

Provide list prices and floor prices by segment or region.

Suggested price books:

- North America Enterprise
- North America Mid-Market
- EMEA Enterprise
- EMEA Mid-Market
- Global Standard

Price book entry fields:

- Price book
- SKU
- List price
- Floor price
- Target margin percent
- Currency
- Effective dates

## Inventory Positions

Purpose:

Support fulfillment risk scenarios.

Suggested records:

| SKU | Region | On Hand | Reserved | Available | Forecast Supply | Forecast Date | Allocation Restricted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HW-100 | North America | 120 | 40 | 80 | 100 | 2026-07-15 | No |
| HW-200 | North America | 20 | 15 | 5 | 30 | 2026-08-01 | Yes |
| HW-100 | EMEA | 75 | 55 | 20 | 80 | 2026-07-20 | No |
| HW-200 | EMEA | 8 | 6 | 2 | 20 | 2026-08-10 | Yes |
| CONS-01 | North America | 1000 | 250 | 750 | 500 | 2026-07-01 | No |
| CONS-01 | EMEA | 300 | 200 | 100 | 450 | 2026-07-18 | No |

## Historical Deals

Purpose:

Support pricing benchmarks, comparable deal analysis, recommendation context, and executive dashboards.

Recommended volume:

- 75 to 150 historical deals.
- At least 12 months of historical dates.
- Mix of approved, rejected, revised, and withdrawn deals.
- Mix of regions, customers, products, and risk levels.

Suggested fields:

- Historical deal ID
- Customer
- Region
- Segment
- Product line
- Total list price
- Total proposed price
- Discount percent
- Estimated margin percent
- Status
- Approval cycle time hours
- Competitor involved
- Inventory risk rating
- Pricing risk rating
- Created date
- Closed date

Data distribution:

- 60 percent approved.
- 15 percent rejected.
- 20 percent revised or changes requested.
- 5 percent withdrawn.
- 20 percent high-discount deals.
- 15 percent inventory-risk deals.
- 25 percent competitive-pressure deals.

## Competitive Intelligence

Purpose:

Support account and product-specific competitive context.

Suggested competitors:

- Competitor A
- Competitor B
- Competitor C
- Regional Specialist
- Low-Cost Entrant

Suggested records:

| Customer | Product Line | Competitor | Signal Type | Summary | Confidence |
| --- | --- | --- | --- | --- | --- |
| Northstar Health Systems | Hardware | Competitor A | Incumbent vendor | Competitor A is the current incumbent for device refresh. | High |
| Apex Retail Group | Software | Low-Cost Entrant | Price pressure | Procurement referenced a lower subscription quote. | Medium |
| HelioTech Energy | Hardware | Competitor B | Prior loss | Prior opportunity was lost on lead time and bundled support. | High |
| Summit BioLabs | Services | Competitor C | Feature comparison | Customer values faster implementation timeline. | Medium |

## Approval Policies

Purpose:

Drive deterministic approval routing for demo deals.

Suggested policies:

| Policy | Condition | Required Role | Sequence |
| --- | --- | --- | --- |
| Standard Sales Manager Approval | Any submitted deal | Sales Manager | 1 |
| Pricing Review | Discount greater than 15% | Pricing Analyst | 2 |
| Finance Review | Margin below target or deal value above 250000 | Finance Approver | 3 |
| Operations Review | Inventory risk is medium or high | Operations Reviewer | 3 |
| Executive Review | Deal value above 750000 or strategic exception | Executive | 4 |
| Legal Review | Payment terms exceed 90 days or contract duration exceeds 36 months | Legal Reviewer | 4 |

## Demo Deals

### Demo Deal 1: Clean Standard Approval

Customer:

Meridian Manufacturing

Scenario:

Moderate deal value, acceptable discount, available inventory, no major competitive pressure.

Expected recommendation:

Approve.

Expected route:

Sales Manager only.

### Demo Deal 2: Aggressive Discount

Customer:

Northstar Health Systems

Scenario:

Strategic account requests 28 percent discount on hardware and services. Margin falls below target but competitor pressure is high.

Expected recommendation:

Escalate or approve with conditions.

Expected route:

Sales Manager, Pricing Analyst, Finance Approver, Executive.

### Demo Deal 3: Inventory Constraint

Customer:

Apex Retail Group

Scenario:

Pricing is acceptable, but requested quantity of advanced hardware exceeds available EMEA inventory.

Expected recommendation:

Approve with conditions or request revised delivery schedule.

Expected route:

Sales Manager, Operations Reviewer.

### Demo Deal 4: Competitive Save

Customer:

HelioTech Energy

Scenario:

Competitor is threatening replacement. Discount is above normal range, but strategic rationale is strong and software margin remains high.

Expected recommendation:

Approve with conditions.

Expected route:

Sales Manager, Pricing Analyst, Finance Approver.

### Demo Deal 5: Reject or Revise

Customer:

Cityline Logistics

Scenario:

Small customer requests high discount, extended payment terms, low-margin hardware, and rush delivery with no strategic justification.

Expected recommendation:

Request revision or reject.

Expected route:

Sales Manager, Pricing Analyst, Finance Approver, Legal Reviewer.

## Dashboard Seed Metrics

The demo data should produce:

- At least 20 active deals.
- At least 8 pending approval deals.
- At least 5 high-risk deals.
- At least 3 inventory-risk deals.
- At least 4 deals above standard discount thresholds.
- At least 2 executive review deals.
- Approval cycle times ranging from less than 4 hours to more than 5 days.

## Data Realism Guidelines

- Use plausible commercial values.
- Avoid perfect distributions.
- Include missing or stale competitive intelligence for some deals.
- Include deals where AI confidence should be low.
- Include deals where policy rules and AI recommendation disagree.
- Include reviewer overrides with clear justification.

## Privacy Guidelines

- Use synthetic names, emails, customers, and competitors.
- Do not include real customer contracts, pricing, notes, or account details.
- Mark all datasets as demo-only.
- Avoid copying real company-specific approval thresholds unless approved for use.

