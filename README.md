# TicketMastery Dashboard Frontend (CSV Prototype)

This is a standalone frontend prototype for your dashboard using local CSV data.

## Run

1. Open `/Users/beckedwards/Documents/Codex/TicketMastery/dashboard/index.html` in a browser.
2. Load `merged_tickets_assets.csv`.
3. Optionally load `merged_tickets_assets_surveys.csv` to enrich survey scores and baseline dates.

## Data mapping

- Ticket ID: `WORK_TASK_ID`
- Description: `DESCRIPTION`
- Ticket type: `TASK_TYPE`
- Asset ID: `ASSET_ID`
- Building: `ASSET_PRIMARY_LOCATION_BUILDING` (fallback `building`)
- Date: `BASELINE_START_LTZ` (fallback `CREATE_DATE_LTZ`)
- Survey score: `average_survey_score`

## Repetitive assets panel logic

Panel 1 uses the same approach as your pandas snippet:

- Group rows by `ASSET_ID`
- Sort by event date
- For each task, look ahead to subsequent tasks for the same asset
- Mark task repetitive if a subsequent task occurs within X days (default 90)

## Current panel behavior

1. Repetitive assets in X-day window using look-ahead repetition detection.
2. Corrective ticket heat map by building and day-of-week.
3. Comparison stats for assets with preventative maintenance vs without.
4. Keyword search + word cloud from descriptions.
5. Data sparsity view for `ASSET_ID` coverage overall and by building.
6. Placeholder for future isolation forest/regression (temporary heuristic ranking only).

## Notes

- Frontend-only and CSV-backed for now.
- Future Snowflake integration can swap CSV ingestion with API calls while keeping this UI structure.
