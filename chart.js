const statusEl = document.getElementById("status");
const startEl = document.getElementById("start");
const endEl = document.getElementById("end");
const refreshBtn = document.getElementById("refreshBtn");
const canvas = document.getElementById("chart");
 
function setStatus(type, msg){
  statusEl.className = `alert alert-${type} py-2`;
  statusEl.textContent = msg;
}
 
function isoDaysAgo(days){
  const d = new Date();
  d.setDate(d.getDate()-days);
  const y = d.getFullYear();
  const m = String(d.getMonth()+1).padStart(2,"0");
  const day = String(d.getDate()).padStart(2,"0");
  return `${y}-${m}-${day}`;
}
 
startEl.value = isoDaysAgo(14);
endEl.value = isoDaysAgo(0);
 
const chart = new Chart(canvas, {
  type: "bar",
  data: { labels: [], datasets: [{ label: "Rainfall (mm)", data: [] }] },
  options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }
});
 

async function load(){
  const start = startEl.value;
  const end = endEl.value;
  
  if (start > end) {
      setStatus("warning", "Start date must be before end date.");
      return;
  }

  setStatus("info", "Fetching data from server...");

  try {
      // Send a GET request with our dates in the URL
      const response = await fetch(`/api/rain?start=${start}&end=${end}`);
      
      if (response.ok) {
          const data = await response.json(); // Convert response to a JavaScript array
          
          setStatus("success", `Showing ${data.length} recorded day(s).`);

          // Update the chart using map() to extract arrays of dates and rainfall numbers
          chart.data.labels = data.map(item => item.date);
          chart.data.datasets[0].data = data.map(item => item.rainfall_mm);
          chart.update(); // Redraw chart
      } else {
          setStatus("danger", "Failed to load data.");
      }
  } catch (error) {
      console.error(error);
      setStatus("danger", "Server error. Is the Flask server running?");
  }
}
 
startEl.addEventListener("change", load);
endEl.addEventListener("change", load);
refreshBtn.addEventListener("click", load);
 
load();