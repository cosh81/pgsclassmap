javascript
function getClassConfig() {

  const rows = document.querySelectorAll("#classTable tbody tr");

  const classes = [];

  rows.forEach(row => {

    const inputs = row.querySelectorAll("input");

    classes.push({
      className: inputs[0].value,
      island: inputs[1].value
    });

  });

  return classes;
}

function addClassRow() {

  const tbody = document.querySelector("#classTable tbody");

  const row = document.createElement("tr");

  row.innerHTML = `
    <td><input value=""></td>
    <td><input value=""></td>
  `;

  tbody.appendChild(row);
}

async function validateFile() {
  await sendFile("/api/validate", "Validating spreadsheet...");
}

async function generateClasses() {
  await sendFile("/api/generate", "Generating classes...");
}

async function sendFile(endpoint, loadingText) {

  const fileInput = document.getElementById("pupilFile");

  const result = document.getElementById("result");

  if (!fileInput.files.length) {

    result.textContent = "Please select a spreadsheet first.";

    return;
  }

  const formData = new FormData();

  formData.append("file", fileInput.files[0]);

  formData.append(
    "classConfig",
    JSON.stringify(getClassConfig())
  );

  formData.append(
    "minClassSize",
    document.getElementById("minClassSize").value
  );

  formData.append(
    "maxClassSize",
    document.getElementById("maxClassSize").value
  );

  formData.append(
    "maxGenderPercent",
    document.getElementById("maxGenderPercent").value
  );

  formData.append(
    "friendPriority",
    document.getElementById("friendPriority").value
  );

  formData.append(
    "schoolPriority",
    document.getElementById("schoolPriority").value
  );

  result.textContent = loadingText;

  try {

    const response = await fetch(endpoint, {
      method: "POST",
      body: formData
    });

    const data = await response.json();

    result.textContent = JSON.stringify(data, null, 2);

    renderSummaryCards(data);

  } catch (error) {

    result.textContent = "Error: " + error.message;
  }
}

function renderSummaryCards(data) {

  const container = document.getElementById("summaryCards");

  container.innerHTML = "";

  if (!data.summary) {
    return;
  }

  for (const className in data.summary) {

    const classData = data.summary[className];

    const card = document.createElement("div");

    card.className = "summary-card";

    card.innerHTML = `
      <h3>${className}</h3>
      <p><strong>Total:</strong> ${classData.total}</p>
      <p><strong>Male:</strong> ${classData.male}</p>
      <p><strong>Female:</strong> ${classData.female}</p>
      <p><strong>Schools:</strong> ${Object.keys(classData.schools).length}</p>
    `;

    container.appendChild(card);
  }
}