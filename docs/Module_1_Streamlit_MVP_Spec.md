# Module 1 Streamlit MVP Specification

## Purpose

This document specifies a Streamlit MVP for Module 1: Commercial Deal Intake. The MVP should demonstrate a working pharmaceutical commercial deal intake workflow using the repository demo datasets, without requiring production integrations, authentication infrastructure, or a full database.

The Streamlit MVP is intended for stakeholder demos, workflow validation, and rapid iteration before production application development.

## MVP Goal

Build a Streamlit app that lets a user:

- View existing sample deal requests.
- Create a new commercial deal draft.
- Select customer, opportunity, and pharmaceutical products from demo datasets.
- Enter commercial terms, proposed prices, delivery dates, and strategic rationale.
- Calculate line and deal totals.
- Validate required fields.
- Preview warnings and estimated approval route.
- Submit a deal into a simulated submitted state.
- View a read-only submitted deal summary and audit trail.

## Out of Scope

- Production authentication.
- Live CRM, CPQ, ERP, inventory, or pricing integrations.
- Persistent multi-user database.
- Real approval execution.
- AI-generated recommendations.
- Email or workflow notifications.
- Mobile-native app behavior beyond responsive Streamlit layout.
- Production-grade access control.

## Source Files

The Streamlit MVP should read from these local files:

- `demo-data/Customer_Master.xlsx`
- `demo-data/Product_Master.xlsx`
- `demo-data/Approval_Matrix.xlsx`
- `demo-data/Sample_Deal_Requests.xlsx`
- `demo-data/Deal_Request_Form.xlsx`

The MVP should use these files as seeded reference data and sample transaction data.

## Recommended App Structure

```text
streamlit_app.py
data/
  optional runtime copies or generated draft exports
docs/
  Module_1_Streamlit_MVP_Spec.md
demo-data/
  Customer_Master.xlsx
  Product_Master.xlsx
  Approval_Matrix.xlsx
  Sample_Deal_Requests.xlsx
  Deal_Request_Form.xlsx
```

For the MVP, a single Streamlit app file is acceptable. If the app grows, split helpers into:

- `data_loader.py`
- `calculations.py`
- `validation.py`
- `routing.py`
- `audit.py`

No code should be written as part of this specification step.

## Streamlit Pages

Use Streamlit multipage navigation or a sidebar radio control with these pages:

1. Deal Request List
2. New Deal Intake
3. Deal Detail
4. Approval Queue Preview
5. Reference Data
6. Audit Log

## Page 1: Deal Request List

### Purpose

Show existing sample deals and any new deals created during the session.

### Data Source

Primary:

- `Sample_Deal_Requests.xlsx`

Runtime:

- Streamlit session state for newly created or edited deals.

### Layout

Top section:

- Page title: `Commercial Deal Desk Copilot`
- Subheader: `Module 1: Deal Intake`
- KPI metrics:
  - Total deals
  - Draft deals
  - Submitted deals
  - Changes requested
  - High-risk deals

Filters:

- Status
- Region
- Segment
- Sales owner
- Intake risk
- Target close date range

Main table:

- Deal ID
- Deal title
- Customer
- Deal type
- Region
- Status
- Target close date
- Payment terms
- Intake risk
- Expected route

Actions:

- `Create New Deal`
- `Open Selected Deal`

### Streamlit Components

Suggested components:

- `st.metric`
- `st.selectbox`
- `st.multiselect`
- `st.date_input`
- `st.dataframe`
- `st.button`

### Acceptance Criteria

- User can view seeded sample deals.
- User can filter by status, region, segment, owner, and risk.
- User can select a deal to view details.
- User can start a new deal request.

## Page 2: New Deal Intake

### Purpose

Capture a complete commercial deal request through a Streamlit form-based workflow.

### Layout

Use tabs or expanders:

1. Customer and Opportunity
2. Deal Terms
3. Line Items
4. Strategic Rationale
5. Review and Submit

For Streamlit simplicity, a single page with expandable sections is preferred for the MVP.

### Section 1: Customer and Opportunity

Inputs:

- Customer selection
- Opportunity selection filtered by selected customer

Read-only context:

- Customer ID
- Account type
- Industry
- Region
- Segment
- Strategic account
- Credit status
- Account owner
- Annual revenue potential
- Commercial notes

Demo behavior:

- Selecting `Northstar Health Systems` should show IDN, Enterprise, Strategic Account, Credit Good.
- Selecting `Apex National GPO` should show a warning for Credit Watch.
- Selecting `Orion Hospital Trust` should show a stronger warning for Credit Hold.

Suggested Streamlit components:

- `st.selectbox`
- `st.columns`
- `st.info`
- `st.warning`
- `st.caption`

### Section 2: Deal Header and Commercial Terms

Inputs:

- Deal title
- Deal type
- Sales owner
- Sales manager
- Region
- Currency
- Target close date
- Requested effective date
- Payment terms
- Contract duration months
- Billing frequency
- Special terms requested
- Special terms description

Default values:

- Region defaults from customer.
- Currency defaults to USD for North America and EUR for EMEA.
- Sales owner defaults from customer account owner.
- Sales manager can default from owner mapping or demo default.

Warnings:

- Net 90 payment terms require Finance and Legal review.
- Contract duration above 36 months requires Legal review.
- Special terms requested requires description.

Suggested Streamlit components:

- `st.text_input`
- `st.selectbox`
- `st.date_input`
- `st.number_input`
- `st.checkbox`
- `st.text_area`

### Section 3: Deal Line Items

Inputs per line:

- SKU or product selection
- Quantity
- Proposed unit price
- Requested delivery date
- Line notes

Auto-populated fields:

- Product name
- Therapeutic area
- Product type
- Storage
- WAC/list price
- Standard cost where role permits
- Target margin
- Lead time days
- Inventory tracked
- Supply risk

Calculated fields:

- Extended list price
- Extended proposed price
- Discount amount
- Discount percent
- Estimated gross margin amount
- Estimated gross margin percent

MVP editing approach:

- Use `st.data_editor` for editable line items.
- Product metadata should be merged into the line-item table after SKU/product selection.
- Calculated columns should be displayed as read-only derived output below or beside the editable grid.

Suggested columns:

- SKU
- Product name
- Quantity
- Unit list price
- Proposed unit price
- Discount percent
- Extended proposed price
- Requested delivery date
- Storage
- Supply risk
- Notes

Warnings:

- Discount greater than threshold.
- Proposed unit price below floor price if available.
- Requested delivery date earlier than product lead time.
- Supply risk medium or high.
- Allocation restricted product.
- Rebate line requires commercial adjustment handling.

Suggested Streamlit components:

- `st.data_editor`
- `st.dataframe`
- `st.metric`
- `st.warning`
- `st.error`

### Section 4: Strategic Rationale

Inputs:

- Business justification
- Competitive situation
- Known competitor
- Customer decision deadline
- Executive sponsor
- Renewal or expansion impact

Conditional requirements:

- Business justification required for submission.
- Known competitor required when competitive situation is not `None known` or `Unknown`.
- Payer/GPO accounts should include formulary access rationale.

Suggested Streamlit components:

- `st.text_area`
- `st.selectbox`
- `st.text_input`
- `st.date_input`

### Section 5: Review and Submit

Display:

- Customer summary
- Commercial terms summary
- Line item count
- Total list price
- Total proposed price
- Total discount amount
- Total discount percent
- Estimated gross margin percent
- Blocking validation issues
- Warning validation issues
- Estimated approval route
- Audit event preview

Actions:

- `Save Draft`
- `Submit Deal`
- `Reset Form`

Submission behavior:

- `Save Draft` stores current deal in session state with status `Draft`.
- `Submit Deal` runs blocking validation.
- If validation passes, status becomes `Submitted`.
- Submitted deal appears in Deal Request List.
- Audit event is added to session audit log.
- App shows read-only submitted summary.

## Page 3: Deal Detail

### Purpose

Show selected deal in read-only or draft-editable mode.

### Layout

Header:

- Deal ID
- Deal title
- Status
- Customer
- Owner
- Target close date

Tabs:

- Overview
- Intake
- Line Items
- Route Preview
- Audit

Overview:

- Total proposed value
- Discount percent
- Intake risk
- Expected route
- Payment terms
- Contract duration
- Strategic account flag

Intake:

- Header fields
- Customer context
- Commercial terms
- Strategic rationale

Line Items:

- Product-level details and calculated values

Route Preview:

- Approval policies triggered
- Required roles
- Sequence
- SLA hours
- Reason triggered

Audit:

- Deal created
- Deal updated
- Deal validation failed
- Deal submitted

### Acceptance Criteria

- Submitted deals are read-only.
- Draft deals can be reopened for editing.
- User can inspect line-level details.
- User can see why approval roles are expected.

## Page 4: Approval Queue Preview

### Purpose

Preview how submitted deals would appear to approvers. This is a simulated approval screen for Module 1 and should not execute full workflow logic.

### Layout

Filters:

- Role
- Region
- Risk
- SLA status

Queue table:

- Deal ID
- Customer
- Product focus
- Proposed value
- Discount percent
- Intake risk
- Required role
- Trigger reason
- SLA hours

Review panel:

- Selected deal summary
- Intake context
- Required checks
- Simulated actions:
  - Approve
  - Request changes
  - Escalate
  - Reject

MVP behavior:

- Action buttons may append audit events and update a simulated decision field.
- They do not need to implement full multi-step workflow.

### Role-Specific Emphasis

Pricing Analyst:

- WAC/list price
- Proposed price
- Discount percent
- Floor price

Finance Approver:

- Margin estimate
- Deal value
- Payment terms
- Credit status

Operations Reviewer:

- Supply risk
- Storage
- Requested delivery date
- Inventory tracked

Market Access Director:

- Payer/GPO account type
- Rebate line
- Formulary access rationale

Legal Reviewer:

- Special terms
- Contract duration
- Payment terms

Commercial Executive:

- Strategic account
- Large deal value
- Exception rationale

## Page 5: Reference Data

### Purpose

Let demo users inspect the source data powering the MVP.

### Tabs

- Customers
- Opportunities
- Products
- Price Book
- Inventory
- Approval Matrix
- Roles

### Data Sources

- `Customer_Master.xlsx`
- `Product_Master.xlsx`
- `Approval_Matrix.xlsx`

### Acceptance Criteria

- User can view reference datasets.
- User can filter or search reference tables.
- User can understand where default values come from.

## Page 6: Audit Log

### Purpose

Show the simulated audit trail for deal intake actions.

### Audit Event Fields

- Timestamp
- Deal ID
- Actor
- Role
- Action
- Entity
- Previous value
- New value
- Source
- Correlation ID

### MVP Audit Events

Required:

- App started demo session
- Deal draft created
- Deal draft saved
- Deal validation failed
- Deal submitted
- Deal viewed

Optional:

- Line item added
- Line item updated
- Approval route preview generated
- Simulated approval action captured

## Session State Model

The MVP can use Streamlit session state rather than a database.

Recommended session keys:

| Key | Purpose |
| --- | --- |
| `customers_df` | Customer master data. |
| `opportunities_df` | Opportunity reference data. |
| `products_df` | Product master data. |
| `price_book_df` | Price book data. |
| `inventory_df` | Inventory data. |
| `approval_matrix_df` | Approval policy data. |
| `sample_deals_df` | Seeded deal request records. |
| `sample_lines_df` | Seeded line item records. |
| `runtime_deals` | New or edited deals created in session. |
| `runtime_line_items` | New line items created in session. |
| `audit_events` | Simulated audit events. |
| `selected_deal_id` | Currently selected deal. |
| `current_user` | Demo user persona. |
| `current_role` | Demo role persona. |

## Data Loading Requirements

At app startup:

1. Load `Customer_Master.xlsx`.
2. Load `Product_Master.xlsx`.
3. Load `Approval_Matrix.xlsx`.
4. Load `Sample_Deal_Requests.xlsx`.
5. Normalize sheet names and column names.
6. Store loaded dataframes in Streamlit session state or cached data functions.

Recommended caching:

- Use cached reads for static demo Excel files.
- Do not cache runtime session deal edits globally.

## Calculations

### Line-Level

- Extended list price = quantity multiplied by unit list price.
- Extended proposed price = quantity multiplied by proposed unit price.
- Discount amount = extended list price minus extended proposed price.
- Discount percent = discount amount divided by extended list price.
- Estimated gross margin amount = extended proposed price minus total standard cost.
- Estimated gross margin percent = estimated gross margin amount divided by extended proposed price.

### Deal-Level

- Total list price = sum of line extended list prices.
- Total proposed price = sum of line extended proposed prices.
- Total discount amount = total list price minus total proposed price.
- Total discount percent = total discount amount divided by total list price.
- Estimated gross margin percent = aggregate margin divided by total proposed value.
- Line item count = count of non-empty line items.

### Display Rules

- Currency values should be formatted as USD or EUR depending on deal currency.
- Percentages should display to one decimal place.
- Margin values should be hidden or shown as a risk indicator for sales-user demo personas.
- Pricing, finance, and executive demo personas may see full margin detail.

## Validation Rules

### Blocking Validation

The app must block submission when:

- Deal title is blank.
- Deal type is blank.
- Customer is blank.
- Region is blank.
- Currency is blank.
- Target close date is blank.
- Requested effective date is blank.
- Payment terms are blank.
- Contract duration months is missing or less than or equal to zero.
- No valid line items exist.
- Any valid line item has quantity less than or equal to zero.
- Any valid line item has missing proposed unit price.
- Any valid line item has negative proposed unit price unless it is the `Formulary Access Rebate` adjustment line.
- Business justification is blank.
- Known competitor is blank when competitive situation requires it.
- Special terms description is blank when special terms requested is true.

### Warning Validation

The app should warn but allow submission when:

- Discount exceeds configured threshold.
- Estimated margin is below target.
- Payment terms exceed Net 60.
- Contract duration exceeds 36 months.
- Requested delivery date is earlier than lead time.
- Customer credit status is Watch.
- Customer credit status is Hold.
- Strategic account has above-threshold discount.
- Competitive situation is Unknown for a deal above $1M.
- Supply risk is Medium or High.

## Approval Route Preview

The route preview should apply the seeded approval matrix as deterministic rules.

Minimum rule logic:

- Every submitted deal requires Sales Manager.
- Discount above threshold requires Pricing Analyst.
- Payer or GPO rebate/formulary concession requires Market Access Director.
- Margin below target or deal value above $1M requires Finance Approver.
- Medium or high supply risk requires Operations Reviewer.
- Contract duration above 36 months, Net 90 terms, or special terms requires Legal Reviewer.
- Strategic account deal above $2.5M requires Commercial Executive.
- Credit Hold requires Finance review and warning.

Output:

- Required role.
- Sequence.
- Trigger reason.
- SLA hours.

## Demo User Personas

The app should allow switching demo persona in the sidebar.

| Persona | Role | Suggested Use |
| --- | --- | --- |
| Maya Chen | Sales Representative | Create Northstar or Apex deals. |
| Jordan Blake | Sales Manager | Review submitted team deals. |
| Priya Nair | Pricing Analyst | Review discount exceptions. |
| Marcus Reed | Market Access Director | Review payer and GPO rebate deals. |
| Daniel Ortiz | Finance Approver | Review margin and credit risk. |
| Elena Rossi | Operations Reviewer | Review cold-chain and supply risk. |
| Aisha Khan | Legal Reviewer | Review special terms. |
| Sarah Morgan | Commercial Executive | Review strategic exceptions. |

## Sidebar Requirements

Sidebar controls:

- Demo persona selector.
- Role selector or auto-derived role.
- Navigation control.
- Data refresh button.
- Reset demo session button.

Sidebar display:

- Current user.
- Current role.
- Session deal count.
- Last saved timestamp.

## Visual Design Requirements

Streamlit should be configured for a wide layout.

Recommended visual patterns:

- Use `st.set_page_config(layout="wide")`.
- Use columns for desktop summary panels.
- Use tabs or expanders for long forms.
- Use metrics for total value, discount, warning count, and route count.
- Use status badges through short labels or styled markdown.
- Use warning and error callouts for validation.
- Use clear table headers and restrained colors.

Avoid:

- Marketing-style hero pages.
- Oversized explanatory text.
- Decorative imagery.
- Dense nested expanders that hide critical validation errors.

## MVP Data Persistence

The MVP may use session-only persistence for fastest delivery.

Minimum:

- New deals persist while the Streamlit session remains active.
- Reset button clears session-created deals.

Preferred demo option:

- Allow exporting runtime deals and audit events to local CSV or Excel.
- Do not overwrite source demo-data workbooks unless explicitly requested.

## Error Handling

Expected errors:

- Missing demo-data file.
- Missing expected sheet.
- Missing expected column.
- Invalid date.
- Empty line-item table.
- Product SKU not found.
- Price book entry missing.

Required behavior:

- Show a clear error message in the app.
- Keep user-entered form state where possible.
- Do not crash the full app for one bad line item.
- Provide enough detail for demo operator to fix the data.

## Testing Checklist

### Data Load

- App loads all five demo-data workbooks.
- Expected sheets are available.
- Expected columns are available.

### Deal List

- Seeded sample deals display.
- Filters work.
- Selected deal opens detail view.

### New Deal

- Customer selection populates customer context.
- Opportunity list filters by customer.
- Product selection populates product context.
- Calculations update after line item changes.

### Validation

- Missing required fields block submission.
- Warning conditions show clearly.
- Warnings do not block submission.

### Submission

- Save draft stores a draft in session state.
- Submit changes status to Submitted.
- Submitted deal appears in list.
- Audit event is created.

### Route Preview

- Standard deal shows Sales Manager.
- High discount deal shows Pricing Analyst.
- GPO/payer rebate deal shows Market Access Director.
- High supply risk deal shows Operations Reviewer.
- Net 90 or long contract shows Legal Reviewer.
- Large strategic deal shows Commercial Executive.

## Recommended Demo Script

1. Open Deal Request List.
2. Show seeded deals and filters.
3. Start new deal.
4. Select `Northstar Health Systems`.
5. Select `Northstar Oncology Infusion Expansion`.
6. Add Oncavax line items.
7. Enter Net 60, 36-month contract, and competitive replacement rationale.
8. Show calculated totals and discount warning.
9. Show approval route preview.
10. Submit the deal.
11. Open submitted deal detail.
12. Show audit log.
13. Switch to Approval Queue Preview.
14. Show Pricing Analyst or Finance Approver view.

## File Deliverables for First Streamlit Build

When implementation begins, expected files may include:

- `streamlit_app.py`
- `requirements.txt`
- `README_Streamlit_MVP.md`
- Optional `app/` helper modules if the single-file app becomes too large.

No implementation files are created by this specification.

## Definition of Done

The Streamlit MVP is complete when:

- It loads repository demo datasets.
- It displays sample deal requests.
- It supports creating and saving a draft deal.
- It supports entering line items from the product master.
- It calculates totals and discounts.
- It validates blocking and warning rules.
- It previews approval routing.
- It submits a deal into session state.
- It shows a deal detail view.
- It records and displays audit events.
- It can be demonstrated without live integrations.

