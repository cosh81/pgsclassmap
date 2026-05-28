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

def clean_text(value):
    if value is None:
        return ""

    return " ".join(
        str(value)
        .replace("\n", " ")
        .replace("\t", " ")
        .strip()
        .split()
    ).lower()


def display_text(value):
    if value is None:
        return ""

    return " ".join(
        str(value)
        .replace("\n", " ")
        .replace("\t", " ")
        .strip()
        .split()
    )


def get_island(class_name):
    return ''.join([c for c in class_name if not c.isdigit()]).lower()


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


def calculate_friendship_results(allocations):
    pupil_to_class = {
        clean_text(a["pupil"]): a["class"]
        for a in allocations
    }

    results = {}

    for allocation in allocations:
        class_name = allocation["class"]

        if class_name not in results:
            results[class_name] = {
                "withFriends": 0,
                "friendsOk": 0,
                "friendsNo": 0,
                "noneListed": 0
            }

        pupil_class = allocation["class"]

        friends = [
            clean_text(allocation.get("friend1", "")),
            clean_text(allocation.get("friend2", ""))
        ]

        friends = [
            f for f in friends
            if f and f in pupil_to_class
        ]

        if not friends:
            results[class_name]["noneListed"] += 1
            continue

        results[class_name]["withFriends"] += 1

        friend_in_same_class = any(
            pupil_to_class[f] == pupil_class
            for f in friends
        )

        if friend_in_same_class:
            results[class_name]["friendsOk"] += 1
        else:
            results[class_name]["friendsNo"] += 1

    return results

@app.route(route="generate", methods=["POST"])
def generate(req: func.HttpRequest) -> func.HttpResponse:
    try:
        df, columns, mapped_columns = read_and_map_excel(req)

        pupil_col = mapped_columns["Pupil Name"]
        gender_col = mapped_columns["Gender"]
        school_col = mapped_columns["Primary School"]
        sibling_col = mapped_columns["Sibling Island"]
        friend1_col = mapped_columns["Friend 1"]
        friend2_col = mapped_columns["Friend 2"]

        pupils = []

        # -----------------------------
        # NORMALISE PUPIL DATA
        # -----------------------------

        for _, row in df.iterrows():

            display_name = display_text(row[pupil_col])

            pupil = {
                "display_name": display_name,
                "name": clean_text(display_name),

                "gender": clean_text(row[gender_col]),
                "school": clean_text(row[school_col]),
                "sibling_island": clean_text(row[sibling_col]),

                "friend1": clean_text(row[friend1_col]),
                "friend2": clean_text(row[friend2_col]),
            }

            pupils.append(pupil)

        # -----------------------------
        # CLASS MODEL
        # -----------------------------

        classes = {}

        for class_name in CLASSES:
            classes[class_name] = {
                "name": class_name,
                "island": get_island(class_name),
                "pupils": [],
                "male": 0,
                "female": 0,
                "schools": {}
            }

        max_class_size = max(1, round(len(pupils) / len(CLASSES)))

        # -----------------------------
        # SCORING FUNCTION
        # -----------------------------

        def calculate_score(pupil, class_data):

            score = 0

            # HARD LIMITS
            if len(class_data["pupils"]) >= max_class_size:
                score += 1000

            # SIBLING ISLAND MATCH
            if pupil["sibling_island"]:

                if pupil["sibling_island"] != class_data["island"]:
                    score += 1000

            # GENDER BALANCE
            if pupil["gender"] == "m":
                score += class_data["male"] * 10

            elif pupil["gender"] == "f":
                score += class_data["female"] * 10

            # SCHOOL CLUSTERING
            school_count = class_data["schools"].get(
                pupil["school"],
                0
            )

            score += school_count * 5

            # FRIEND BONUS
friends = [
    pupil["friend1"],
    pupil["friend2"]
]

friends = [
    f for f in friends
    if f
]

if friends:

    class_pupil_names = [
        p["name"]
        for p in class_data["pupils"]
    ]

    matching_friends = sum(
        1 for f in friends
        if f in class_pupil_names
    )

    # Reduce score if friends already in class
    score -= matching_friends * 40

            # CLASS SIZE BALANCE
            score += len(class_data["pupils"]) * 3

            return score

        # -----------------------------
        # SORT CONSTRAINED PUPILS FIRST
        # -----------------------------

        pupils.sort(
            key=lambda p: (
                0 if p["sibling_island"] else 1
            )
        )

        allocations = []

        # -----------------------------
        # ALLOCATE
        # -----------------------------

        for pupil in pupils:

            best_class = None
            best_score = None

            for class_name, class_data in classes.items():

                score = calculate_score(
                    pupil,
                    class_data
                )

                if best_score is None or score < best_score:
                    best_score = score
                    best_class = class_name

            class_data = classes[best_class]

            class_data["pupils"].append(pupil)

            if pupil["gender"] == "m":
                class_data["male"] += 1

            elif pupil["gender"] == "f":
                class_data["female"] += 1

            if pupil["school"]:

                class_data["schools"][pupil["school"]] = (
                    class_data["schools"].get(
                        pupil["school"],
                        0
                    ) + 1
                )

            allocations.append({
                "pupil": pupil["display_name"],
                "class": best_class,
                "gender": pupil["gender"].upper(),
                "primarySchool": pupil["school"].title(),
                "siblingIsland": pupil["sibling_island"].title(),
                "friend1": pupil["friend1"].title(),
                "friend2": pupil["friend2"].title()
            })

        friendship_summary = calculate_friendship_results(allocations)

        # -----------------------------
        # SUMMARY
        # -----------------------------

        class_summary = {}

        for class_name, class_data in classes.items():

            class_summary[class_name] = {
                "total": len(class_data["pupils"]),
                "male": class_data["male"],
                "female": class_data["female"],
                "schools": class_data["schools"]
            }

        return json_response({
    "status": "success",
    "message": "Allocation generated successfully.",
    "summary": class_summary,
    "friendshipSummary": friendship_summary,
    "allocations": allocations
})

    except Exception as e:
        return json_response({
            "status": "error",
            "message": str(e)
        }, 500)