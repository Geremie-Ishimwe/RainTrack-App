const statusEl = document.getElementById("status");
const dateEl = document.getElementById("date");
const rainEl = document.getElementById("rain");
const saveBtn = document.getElementById("saveBtn");


const photoInput = document.getElementById("photo");
const uploadBtn = document.getElementById("uploadBtn");
const photoDisplay = document.getElementById("photoDisplay");

function setStatus(type, msg){
  statusEl.className = `alert alert-${type} py-2`;
  statusEl.textContent = msg;
}

function todayISO(){
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth()+1).padStart(2,"0");
  const day = String(d.getDate()).padStart(2,"0");
  return `${y}-${m}-${day}`;
}


async function loadDayData() {
    const date = dateEl.value;
    if (!date) return;

    try {
        const response = await fetch(`/api/rainfall/${date}`);
        const result = await response.json();

        if (result.ok && result.data) {
            rainEl.value = result.data.rainfall_mm;
            
            if (result.data.photo_filename) {
                photoDisplay.src = `/media/${result.data.photo_filename}`;
                photoDisplay.style.display = "block";
            } else {
                photoDisplay.style.display = "none";
            }
        } else {
            rainEl.value = "";
            photoDisplay.style.display = "none";
        }
    } catch (err) {
        console.error("Failed to load day data", err);
    }
}


dateEl.addEventListener("change", loadDayData);


uploadBtn.addEventListener("click", async () => {
    const date = dateEl.value;
    const file = photoInput.files[0];

    if (!date) return setStatus("warning", "Please select a date first.");
    if (!file) return setStatus("warning", "Please select a file to upload.");

    setStatus("info", "Uploading photo...");

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(`/api/rainfall/${date}/photo`, {
            method: "POST",
            body: formData
        });
        
        const result = await response.json();

        if (response.ok) {
            setStatus("success", "Photo uploaded successfully!");
            photoDisplay.src = `/media/${result.data.photo_filename}`;
            photoDisplay.style.display = "block";
            photoInput.value = ""; 
        } else {
            setStatus("danger", result.error || "Failed to upload photo.");
        }
    } catch (err) {
        setStatus("danger", "Server error during upload.");
    }
});


saveBtn.addEventListener("click", async () => {
  const date = dateEl.value;
  const rain = rainEl.value;

  if (!date || rain === "") {
    setStatus("warning", "Please fill in both fields");
    return;
  }

  try {
    const response = await fetch("/api/rain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ date: date, rainfall: parseFloat(rain) })
    });

    if (response.ok) {
      setStatus("success", "Saved successfully!");
    } else {
      setStatus("danger", "Failed to save data");
    }
  } catch (error) {
    setStatus("danger", "Server error: " + error.message);
  }
});


dateEl.value = todayISO();
loadDayData();

// ---- PHASE 7: Register Service Worker ----
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/static/sw.js")
      .then((registration) => {
        console.log("Service Worker registered with scope:", registration.scope);
      })
      .catch((error) => {
        console.error("Service Worker registration failed:", error);
      });
  });
}