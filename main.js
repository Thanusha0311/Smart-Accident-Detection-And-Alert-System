document.addEventListener("DOMContentLoaded", () => {
  const uploadForm = document.getElementById("uploadForm");
  const statusDiv = document.getElementById("status");
  const historyList = document.getElementById("history");

  uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const file = document.getElementById("videoFile").files[0];
    const email = document.getElementById("emailInput").value.trim();

    if (!file || !email) {
      alert("Upload video and enter email");
      return;
    }

    statusDiv.innerHTML = "⏳ Processing video...";
    statusDiv.style.color = "black";

    const formData = new FormData();
    formData.append("file", file);
    formData.append("email", email);

    try {
      const res = await fetch("http://127.0.0.1:8000/detect_accident", {
        method: "POST",
        body: formData
      });

      const result = await res.json();

      if (result.status === "accident") {
        statusDiv.innerHTML = `
          ✅ <b>Accident Detected</b><br>
          🚨 Severity: <b>${result.severity}</b><br>
          🚗 Vehicles Involved: <b>${result.vehicles}</b><br>
          💥 Impact Score: <b>${result.impact}</b><br>
          📧 Alert sent to <b>${result.email}</b>
        `;
        statusDiv.style.color = "green";
      } else {
        statusDiv.innerHTML = "ℹ️ No accident detected.";
        statusDiv.style.color = "gray";
      }

      const historyRes = await fetch("http://127.0.0.1:8000/get_history");
      const logs = await historyRes.json();

      historyList.innerHTML = logs.map(log => `
        <li>
          <b>${log.timestamp}</b><br>
          📧 ${log.email}<br>
          🚨 ${log.severity}, 🚗 ${log.vehicles}
        </li>
      `).join("");

    } catch (err) {
      statusDiv.innerHTML = "❌ Backend not running.";
      statusDiv.style.color = "red";
      console.error(err);
    }
  });
});
