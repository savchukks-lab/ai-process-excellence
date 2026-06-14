# Streamlit MVP v1

This MVP implements Module 1: Commercial Deal Intake using the Excel files in `demo-data`.

## What It Includes

- Deal request list
- New deal intake form
- Editable line items
- Validation and warning checks
- Deal totals, discounts, and estimated margin
- Executive summary, decision score, score breakdown, and plan inclusion logic
- Planned price-volume variance, incremental opportunity analysis, gross profit impact, inventory, aging, tender, and competitor context
- Approval route preview
- Simulated approval queue
- Session audit log
- Reference data browser

## Run

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the app:

```powershell
streamlit run streamlit_app.py
```

The app reads source data from the local `demo-data` folder and stores newly created demo deals in Streamlit session state.
