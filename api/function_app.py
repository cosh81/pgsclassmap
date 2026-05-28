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

CLASSES = ["Mull1", "Lewis1", "Lewis2", "Skye1", "Skye2", "Iona1", "Iona2"]


def find_column(df_columns, possible_names):
    for name in possible_names:
        if name in df_columns:
            return name
    return None


def json_response(data, status_code=200):
    return func.HttpResponse(
        json.dumps(data, indent=2),
        mimetype="application/json",
        status_code=status_code
    )


def read_and_map_excel(req):
    uploaded_file = req.files.get("file")

    if not uploaded_file:
        raise ValueError("No file uploaded.")

    df = pd.read_excel(BytesIO(uploaded_file.read()))
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
        raise ValueError(f"Missing required columns: {missing_columns}")

    return df, columns, mapped_columns


@app.route(route="validate", methods=["POST"])
def validate(req: func.HttpRequest) -> func.HttpResponse:
    try:
        df, columns, mapped_columns = read_and_map_excel(req)

        response = {
            "status": "success",
            "message": "File validated successfully.",
            "summary": {
                "totalPupils": int(len(df)),
                "genderCounts": df[mapped_columns["Gender"]].value_counts().to_dict(),
                "siblingConstrainedPupils": int((df[mapped_columns["Sibling Island"]] != "").sum()),
                "friend1Nominations": int((df[mapped_columns["Friend 1"]] != "").sum()),
                "friend2Nominations": int((df[mapped_columns["Friend 2"]] != "").sum()),
                "pupilsWithAnyFriend": int(
                    df[
                        (df[mapped_columns["Friend 1"]] != "")
                        |
                        (df[mapped_columns["Friend 2"]] != "")
                    ].shape[0]
                )
            },
            "columns": columns,
            "mappedColumns": mapped_columns
        }

        return json_response(response)

    except Exception as e:
        return json_response({
            "status": "error",
            "message": str(e)
        }, 500)


@app.route(route="generate", methods=["POST"])
def generate(req: func.HttpRequest) -> func.HttpResponse:
    try:
        df, columns, mapped_columns = read_and_map_excel(req)

        pupil_col = mapped_columns["Pupil Name"]
        gender_col = mapped_columns["Gender"]
        school_col = mapped_columns["Primary School"]
        sibling_col = mapped_columns["Sibling Island"]

        allocations = []
        class_summary = {class_name: {"total": 0, "male": 0, "female": 0, "schools": {}} for class_name in CLASSES}

        for index, row in df.iterrows():
            class_name = CLASSES[index % len(CLASSES)]

            gender = str(row[gender_col]).strip().upper()
            school = str(row[school_col]).strip()

            allocation = {
                "pupil": str(row[pupil_col]).strip(),
                "class": class_name,
                "gender": gender,
                "primarySchool": school,
                "siblingIsland": str(row[sibling_col]).strip()
            }

            allocations.append(allocation)

            class_summary[class_name]["total"] += 1

            if gender == "M":
                class_summary[class_name]["male"] += 1
            elif gender == "F":
                class_summary[class_name]["female"] += 1

            if school:
                class_summary[class_name]["schools"][school] = class_summary[class_name]["schools"].get(school, 0) + 1

        return json_response({
            "status": "success",
            "message": "Dummy class allocation generated successfully.",
            "note": "This is not the optimiser yet. It simply spreads pupils evenly across classes to prove the generate workflow.",
            "summary": class_summary,
            "allocations": allocations[:20]
        })

    except Exception as e:
        return json_response({
            "status": "error",
            "message": str(e)
        }, 500)
