function addClassRow() {

  const tbody =
    document.querySelector(
      "#classTable tbody"
    );

  const row =
    document.createElement("tr");

  row.innerHTML = `
    <td>
      <input placeholder="e.g. Lewis1">
    </td>

    <td>
      <input placeholder="e.g. Lewis">
    </td>
  `;

  tbody.appendChild(row);
}

function getClassConfig() {

  const rows =
    document.querySelectorAll(
      "#classTable tbody tr"
    );

  const classes = [];

  rows.forEach(row => {

    const inputs =
      row.querySelectorAll("input");

    const className =
      inputs[0].value.trim();

    const island =
      inputs[1].value.trim();

    if (!className) {
      return;
    }

    classes.push({
      className,
      island
    });

  });

  return classes;
}

const pupilFile = document.getElementById("pupilFile");
const result = document.getElementById("result");

const pupilFileInput = document.getElementById("pupilFile");
const selectedFileName = document.getElementById("selectedFileName");
const uploadArea = document.querySelector(".upload-area");

if (pupilFileInput && selectedFileName && uploadArea) {
  pupilFileInput.addEventListener("change", () => {

    if (pupilFileInput.files.length > 0) {

      selectedFileName.textContent =
        `Uploaded: ${pupilFileInput.files[0].name}`;

      selectedFileName.classList.add("has-file");
      uploadArea.classList.add("has-file");

    } else {

      selectedFileName.textContent =
        "No file selected";

      selectedFileName.classList.remove("has-file");
      uploadArea.classList.remove("has-file");
    }
  });
}


async function generateClasses() {

  const fileInput =
    document.getElementById(
      "pupilFile"
    );

  const result =
    document.getElementById(
      "result"
    );

  if (!fileInput.files.length) {

    result.textContent =
      "Please select a spreadsheet.";

    return;
  }

  const classes =
    getClassConfig();

  if (classes.length === 0) {

    result.textContent =
      "Please add at least one class.";

    return;
  }

  const formData =
    new FormData();

  formData.append(
    "file",
    fileInput.files[0]
  );

  formData.append(
    "classConfig",
    JSON.stringify(classes)
  );

  formData.append(
    "minClassSize",
    document.getElementById(
      "minClassSize"
    ).value
  );

  formData.append(
    "maxClassSize",
    document.getElementById(
      "maxClassSize"
    ).value
  );

  formData.append(
    "genderPriority",
    document.getElementById(
      "genderPriority"
    ).value
  );

  formData.append(
    "friendPriority",
    document.getElementById(
      "friendPriority"
    ).value
  );

  formData.append(
    "schoolPriority",
    document.getElementById(
      "schoolPriority"
    ).value
  );

  formData.append(
    "siblingPriority",
    document.getElementById(
      "siblingPriority"
    ).value
  );

  result.textContent =
    "Generating allocation...";

  try {

    const response =
      await fetch(
        "/api/generate",
        {
          method: "POST",
          body: formData
        }
      );

    const data =
      await response.json();

    sessionStorage.setItem(
      "lastAllocation",
      JSON.stringify(data)
    );

    result.textContent =
      JSON.stringify(
        data,
        null,
        2
      );

    document.getElementById(
      "viewSummaryBtn"
    ).disabled = false;

    document.getElementById(
      "exportBtn"
    ).disabled = false;

  } catch (error) {

    result.textContent =
      "Error: " + error.message;
  }
}

function openSummary() {

  window.open(
    "summary.html",
    "_blank"
  );
}

function exportExcel() {

  const data =
    sessionStorage.getItem(
      "lastAllocation"
    );

  if (!data) {

    alert(
      "Generate classes first."
    );

    return;
  }

  const blob =
    new Blob(
      [data],
      {
        type:
          "application/json"
      }
    );

  const url =
    window.URL.createObjectURL(blob);

  const a =
    document.createElement("a");

  a.href = url;

  a.download =
    "allocation-data.json";

  a.click();

  window.URL.revokeObjectURL(url);
}