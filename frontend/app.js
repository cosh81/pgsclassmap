function addClassRow() {
  const tbody = document.querySelector("#classTable tbody");
  const row = document.createElement("tr");

  row.innerHTML = `
    <td><input placeholder="e.g. Lewis1"></td>
    <td><input placeholder="e.g. Lewis"></td>
  `;

  tbody.appendChild(row);
}

function getClassConfig() {
  const rows = document.querySelectorAll("#classTable tbody tr");
  const classes = [];

  rows.forEach(row => {
    const inputs = row.querySelectorAll("input");
    const className = inputs[0].value.trim();
    const island = inputs[1].value.trim();

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

function enablePostGenerationButtons() {
  const summaryButton = document.getElementById("viewSummaryBtn");
  const exportButton = document.getElementById("exportExcelBtn");

  if (summaryButton) {
    summaryButton.disabled = false;
  }

  if (exportButton) {
    exportButton.disabled = false;
  }
}

async function generateClasses() {
  const fileInput = document.getElementById("pupilFile");
  const result = document.getElementById("result");

  if (!fileInput.files.length) {
    result.textContent = "Please select a spreadsheet.";
    return;
  }

  const classes = getClassConfig();

  if (classes.length === 0) {
    result.textContent = "Please add at least one class.";
    return;
  }

  const formData = new FormData();

  formData.append("file", fileInput.files[0]);
  formData.append("classConfig", JSON.stringify(classes));
  formData.append("minClassSize", document.getElementById("minClassSize").value);
  formData.append("maxClassSize", document.getElementById("maxClassSize").value);
  formData.append("genderPriority", document.getElementById("genderPriority").value);
  formData.append("friendPriority", document.getElementById("friendPriority").value);
  formData.append("schoolPriority", document.getElementById("schoolPriority").value);
  formData.append("siblingPriority", document.getElementById("siblingPriority").value);

  result.textContent = "Generating allocation...";

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      body: formData
    });

    const data = await response.json();

    result.textContent = JSON.stringify(data, null, 2);

    if (data.status === "success") {
      sessionStorage.setItem("lastAllocation", JSON.stringify(data));
      enablePostGenerationButtons();
    }
  } catch (error) {
    result.textContent = "Error: " + error.message;
  }
}

function openSummary() {
  window.open("summary.html", "_blank");
}

async function exportExcel() {
  const result = document.getElementById("result");
  const saved = sessionStorage.getItem("lastAllocation");

  if (!saved) {
    result.textContent = "Generate classes before exporting.";
    return;
  }

  result.textContent = "Creating Excel export...";

  try {
    const response = await fetch("/api/export", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: saved
    });

    if (!response.ok) {
      throw new Error("Excel export failed.");
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = "PGSClassMap_Allocation.xlsx";
    document.body.appendChild(link);
    link.click();
    link.remove();

    window.URL.revokeObjectURL(url);

    result.textContent = "Excel export created.";
  } catch (error) {
    result.textContent = "Error: " + error.message;
  }
}
