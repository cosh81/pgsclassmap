async function validateFile() {
  await sendFile("/api/validate", "Validating...");
}

async function generateClasses() {
  await sendFile("/api/generate", "Generating dummy class allocation...");
}

async function sendFile(endpoint, loadingText) {
  const fileInput = document.getElementById("pupilFile");
  const result = document.getElementById("result");

  if (!fileInput.files.length) {
    result.textContent = "Please select a pupil spreadsheet first.";
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  formData.append("minClassSize", document.getElementById("minClassSize").value);
  formData.append("maxClassSize", document.getElementById("maxClassSize").value);
  formData.append("maxGenderPercent", document.getElementById("maxGenderPercent").value);

  result.textContent = loadingText;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      body: formData
    });

    const data = await response.json();
    result.textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    result.textContent = "Error: " + error.message;
  }
}
