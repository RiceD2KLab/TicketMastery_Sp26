from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from pathlib import Path
import tempfile
import os

from utils.mapProcessing import build_map_html
from utils import wordCloudProcessing
from utils import repetitiveTicketProcessing as rtp

app = Flask(__name__)
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=False,
)


"""
Process uploaded CSV files and return ticket rows for frontend word-cloud analysis.

Args:
    assets_csv: Uploaded assets CSV file.
    tickets_csv: Uploaded tickets CSV file.
    space_csv: Uploaded space CSV file.
    group_col (str | None, optional): Column name to filter/group by. Defaults to None.
    group_values (str | None, optional): Comma-separated list of allowed values for
        group_col. Defaults to None.

Returns:
    dict: JSON-serializable dictionary containing:
        - "ticket_rows": list[dict] with WORK_TASK_ID, BUILDING, DESCRIPTION
"""
@app.route("/wordcloud", methods=["POST"])
def generate_wordcloud():
    tmp_paths = []
    try:
        assets_csv = request.files["assets_csv"]
        tickets_csv = request.files["tickets_csv"]
        space_csv = request.files["space_csv"]

        group_col = request.form.get("group_col")
        group_values = request.form.get("group_values")

        for up in [assets_csv, tickets_csv, space_csv]:
            suffix = os.path.splitext(up.filename or "")[1] or ".csv"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            up.save(tmp.name)
            tmp.close()
            tmp_paths.append(tmp.name)

        assets_path, tickets_path, space_path = tmp_paths[0], tmp_paths[1], tmp_paths[2]

        df = wordCloudProcessing.process_data(tickets_path, assets_path, space_path)

        allowed_group_cols = {
            "SERVICE_CLASS",
            "REQUEST_CLASS",
            "RESPONSIBLE_ORGANIZATION_NAME",
        }
        selected_values = parse_group_values(group_values)
        ticket_df = df.copy()

        if group_col:
            if group_col not in allowed_group_cols:
                return jsonify({"detail": "Invalid group_col"}), 400

            if group_col not in ticket_df.columns:
                return jsonify({"detail": f"{group_col} not found in data"}), 400

            if selected_values:
                ticket_df = ticket_df[ticket_df[group_col].isin(selected_values)]

            ticket_df["GROUP_VALUE"] = ticket_df[group_col].fillna("")
        else:
            ticket_df["GROUP_VALUE"] = ""

        ticket_df = (
            ticket_df[["WORK_TASK_ID", "BUILDING", "DESCRIPTION", "GROUP_VALUE"]]
            .fillna("")
            .replace({float("inf"): "", float("-inf"): ""})
        )

        return jsonify({
            "ticket_rows": ticket_df.to_dict(orient="records"),
            "group_col": group_col or ""
        })

    finally:
        for p in tmp_paths:
            try:
                os.remove(p)
            except Exception:
                pass


@app.route("/repetitive-objects", methods=["POST"])
def repetitive_objects_api():
    """Return ticket rows for repetitive-object frontend rendering.

    The endpoint returns both a ticket table payload and a small summary object.
    """
    tmp_paths = []

    try:
        tickets_csv = request.files["tickets_csv"]
        assets_csv = request.files["assets_csv"]
        space_csv = request.files["space_csv"]

        num_days = request.form.get("num_days", default=90, type=int)
        min_days = request.form.get("min_days", default=3, type=int)

        repetitive_only = request.form.get("repetitive_only", default="true").lower() == "true"
        drop_missing_space = request.form.get("drop_missing_space", default="true").lower() == "true"
        corrective_only = request.form.get("corrective_only", default="true").lower() == "true"

        for upload in [tickets_csv, assets_csv, space_csv]:
            suffix = os.path.splitext(upload.filename or "")[1] or ".csv"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            upload.save(tmp.name)
            tmp.close()
            tmp_paths.append(tmp.name)

        tickets_path, assets_path, space_path = tmp_paths
        labeled_df = rtp.build_repetitive_labels_from_csvs(
            tickets_csv_path=tickets_path,
            assets_csv_path=assets_path,
            space_csv_path=space_path,
            group_cols=["SERVICE_CLASS", "BUILDING", "FLOOR", "SPACE"],
            num_days=num_days,
            min_days=min_days,
            drop_missing_space=drop_missing_space,
            corrective_only=corrective_only,
        )

        ticket_rows_df = rtp.build_repetitive_ticket_rows(
            labeled_df=labeled_df,
            repetitive_only=repetitive_only,
        )

        repetitive_count = int((labeled_df["REPETITIVE"] == 1).sum()) if "REPETITIVE" in labeled_df.columns else 0
        total_count = int(len(labeled_df))
        filtered_count = int(len(ticket_rows_df))

        return jsonify({
            "ticket_rows": ticket_rows_df.to_dict(orient="records"),
            "summary": {
                "total_rows": total_count,
                "repetitive_rows": repetitive_count,
                "returned_rows": filtered_count,
                "num_days": num_days,
                "min_days": min_days,
                "repetitive_only": repetitive_only,
                "drop_missing_space": drop_missing_space,
                "corrective_only": corrective_only,
            },
        })

    except Exception as exc:
        return jsonify({"detail": str(exc)}), 500

    finally:
        for path in tmp_paths:
            try:
                os.remove(path)
            except OSError:
                pass


@app.route("/map-html", methods=["GET"])
def get_map_html():
    project_root = Path(__file__).resolve().parents[3]
    csv_path = project_root / "data" / "TICKETS_WITH_COORDS.csv"
    html = build_map_html(str(csv_path))
    return Response(html, mimetype="text/html")


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
    app.run(host="0.0.0.0", port=8000, debug=True)