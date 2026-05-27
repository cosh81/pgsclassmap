import azure.functions as func
import json
import pandas as pd
from io import BytesIO

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

COLUMN_ALIASES = {
    "Primary School": ["Primary School", "School"],
    "Gender": ["Gender", "Sex"],
    "Pupil Name": ["Pupil Name", "Pupil", "Name"],
    "Sibling Island": ["Sibling Island", "Sibling island"],
    "Friend 1": ["Friend 1", "Friend1"],
    "Friend 2": ["Friend 2", "Friend2"]
}


def find_column(df_columns, possible_names):
    for name in possible_names:
        if name in df_columns:
            return name
    return None


def json_response(data, status_code):
    return func.HttpResponse(
        json.dumps(data, indent=2),
        mimetype="application/json",
        status_code=status_code
    )


@app.route(route="validate", methods=["POST"])
def validate(req: func.HttpRequest) -> func.HttpResponse:

    try:

        uploaded_file = req.files.get("file")

        if not uploaded_file:
            return json_response({
                "status": "error",
                "message": "No file uploaded."
            }, 400)

        file_bytes = uploaded_file.read()

        df = pd.read_excel(BytesIO(file_bytes))

        df = df.fillna("")

        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].astype(str).str.strip()

        columns = list(df.columns)

        mapped_columns = {}
        missing_columns = []

        for standard_name, aliases in COLUMN_ALIASES.items():

            matched_column = find_column(columns, aliases)

            if matched_column:
                mapped_columns[standard_name] = matched_column
            else:
                missing_columns.append(standard_name)

        if missing_columns:
            return json_response({
                "status": "error",
                "message": "Missing required columns.",
                "missingColumns": missing_columns,
                "foundColumns": columns
            }, 400)

        total_pupils = len(df)

        gender_counts = (
            df[mapped_columns["Gender"]]
            .astype(str)
            .str.strip()
            .value_counts()
            .to_dict()
        )

        sibling_count = (
            (df[mapped_columns["Sibling Island"]] != "")
            .sum()
        )

        friend_1_count = (
            (df[mapped_columns["Friend 1"]] != "")
            .sum()
        )

        friend_2_count = (
            (df[mapped_columns["Friend 2"]] != "")
            .sum()
        )

        pupils_with_any_friend = df[
            (df[mapped_columns["Friend 1"]] != "")
            |
            (df[mapped_columns["Friend 2"]] != "")
        ].shape[0]

        response = {
            "status": "success",
            "message": "File validated successfully.",
            "summary": {
                "totalPupils": int(total_pupils),
                "genderCounts": gender_counts,
                "siblingConstrainedPupils": int(sibling_count),
                "friend1Nominations": int(friend_1_count),
                "friend2Nominations": int(friend_2_count),
                "pupilsWithAnyFriend": int(pupils_with_any_friend)
            },
            "columns": columns,
            "mappedColumns": mapped_columns
        }

        return json_response(response, 200)

    except Exception as e:

        return json_response({
            "status": "error",
            "message": str(e)
        }, 500)
