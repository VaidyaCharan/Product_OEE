let productionChart;

// ================== CHART.JS SETUP & AUTO UPDATE ===================
function fetchAndUpdateChart(filteredData = null) {
  const machineId = document.body.dataset.machineId;

  const fetchData = filteredData
    ? Promise.resolve(filteredData) // Use filtered data directly
    : fetch(`/api/production_data/${machineId}`).then(res => res.json());

  fetchData
    .then(data => {
      // Show last 10 (or at least last 4)
      let startIndex = Math.max(data.length - 10, 0);
      let recentData = data.slice(startIndex);

      // Labels and dataset values
      const labels = recentData.map((_, i) => `ID ${startIndex + i + 1}`);
      const planned = recentData.map(d => d.plan);
      const actual = recentData.map(d => d.actual);

      // Chart.js Update or Create
      if (productionChart) {
        productionChart.data.labels = labels;
        productionChart.data.datasets[0].data = planned;
        productionChart.data.datasets[1].data = actual;
        productionChart.update();
      } else {
        productionChart = new Chart(document.getElementById('productionChart'), {
          type: 'line',
          data: {
            labels,
            datasets: [
              {
                label: 'Planned',
                data: planned,
                borderColor: 'blue',
                backgroundColor: 'rgba(0, 0, 255, 0.1)',
                fill: true,
                tension: 0.4
              },
              {
                label: 'Actual',
                data: actual,
                borderColor: 'green',
                backgroundColor: 'rgba(0, 128, 0, 0.1)',
                fill: true,
                tension: 0.4
              }
            ]
          },
          options: {
            responsive: true,
            plugins: {
              legend: { position: 'top' }
            },
            scales: {
              y: { beginAtZero: true }
            }
          }
        });
      }
    })
    .catch(err => console.error("Chart fetch error:", err));
}

// ================== FILTER + CHART UPDATE ===================
function applyDateFilterToChart() {
  const from = new Date(document.getElementById('fromDate').value);
  const to = new Date(document.getElementById('toDate').value);

  const machineId = document.body.dataset.machineId;

  fetch(`/api/production_data/${machineId}`)
    .then(res => res.json())
    .then(data => {
      if (!isNaN(from) && !isNaN(to)) {
        const filtered = data.filter(d => {
          const dDate = new Date(d.date); // Assuming `date` field is in your data
          return dDate >= from && dDate <= to;
        });
        fetchAndUpdateChart(filtered);
      } else {
        fetchAndUpdateChart(); // Reset to original if no date selected
      }
    });
}

// ================== TABLE DATE FILTER ===================
function filterByDate() {
  const from = new Date(document.getElementById('fromDate').value);
  const to = new Date(document.getElementById('toDate').value);
  const rows = document.querySelectorAll("#dataTable tbody tr");

  rows.forEach(row => {
    const dateCell = row.cells[0].innerText;
    const rowDate = new Date(dateCell);
    row.style.display = (!isNaN(from) && !isNaN(to) && (rowDate < from || rowDate > to)) ? 'none' : '';
  });

  applyDateFilterToChart(); // Apply the same filter to chart
}

function clearFilter() {
  document.getElementById("fromDate").value = "";
  document.getElementById("toDate").value = "";

  const rows = document.querySelectorAll("#dataTable tbody tr");
  rows.forEach(row => (row.style.display = ""));

  fetchAndUpdateChart(); // Reset chart
}

// ================== INIT ===================
document.addEventListener("DOMContentLoaded", () => {
  fetchAndUpdateChart();
  setInterval(() => fetchAndUpdateChart(), 1000); // Chart update every 10s
});
