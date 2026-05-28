async function validateFile() {
  const fileInput = document.getElementById("pupilFile");
  const result = document.getElementById("result");

  if (!fileInput.files.length) {
    result.textContent = "Please select a pupil spreadsheet first.";
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  result.textContent = "Validating...";

  try {
    const response = await fetch("/api/validate", {
      method: "POST",
      body: formData
    });

    const data = await response.json();
    result.textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    result.textContent = "Error: " + error.message;
  }
}
