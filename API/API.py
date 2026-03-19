from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import tempfile
import os

from Utils import Utils
from WordCloud import WordCloud

app = FastAPI(title="WordCloud API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""
Process uploaded CSV files and return ticket rows for frontend word-cloud analysis.

Args:
    assets_csv (UploadFile): Uploaded assets CSV file.
    tickets_csv (UploadFile): Uploaded tickets CSV file.
    space_csv (UploadFile): Uploaded space CSV file.
    group_col (str | None, optional): Column name to filter/group by. Defaults to None.
    group_values (str | None, optional): Comma-separated list of allowed values for
        group_col. Defaults to None.

Returns:
    dict: JSON-serializable dictionary containing:
        - "ticket_rows": list[dict] with WORK_TASK_ID, BUILDING, and DESCRIPTION
"""
@app.post("/wordcloud")
async def generate_wordcloud(
    assets_csv: UploadFile = File(...),
    tickets_csv: UploadFile = File(...),
    space_csv: UploadFile = File(...),
    group_col: str | None = Form(None),
    group_values: str | None = Form(None),
):
    tmp_paths = []
    try:
        for up in [assets_csv, tickets_csv, space_csv]:
            suffix = os.path.splitext(up.filename or "")[1] or ".csv"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(await up.read())
            tmp.close()
            tmp_paths.append(tmp.name)

        assets_path, tickets_path, space_path = tmp_paths[0], tmp_paths[1], tmp_paths[2]

        df = Utils.process_data(tickets_path, assets_path, space_path)
        selected_values = parse_group_values(group_values)
        ticket_df = df.copy()
        if group_col != None and group_values != None:
            ticket_df = ticket_df[ticket_df[group_col].isin(selected_values)]
        
        ticket_df = (
            ticket_df[["WORK_TASK_ID", "BUILDING", "DESCRIPTION"]]
            .fillna("")
            .replace({float("inf"): "", float("-inf"): ""})
        )

        # Return records for JS to consume
        return {"ticket_rows":ticket_df[["WORK_TASK_ID", "BUILDING", "DESCRIPTION"]].to_dict(orient="records")}

    finally:
        for p in tmp_paths:
            try:
                os.remove(p)
            except Exception:
                pass

"""
Parse a comma-separated group-values string into a cleaned list of values.

Args:
    group_values (str | None): Comma-separated string of group values.

Returns:
    list[str]: Cleaned list of non-empty group values.
"""
def parse_group_values(group_values: str | None) -> list[str]:
    if not group_values:
        return []
    return [x.strip() for x in group_values.split(",") if x.strip()]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)