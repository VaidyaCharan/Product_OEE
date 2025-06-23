let charts = {};

function renderGauge(id, value, valueId, color) {
  const ctx = document.getElementById(id).getContext('2d');
  charts[id] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [value, 100 - value],
        backgroundColor: [color, '#e0e0e0'],
        borderWidth: 0
      }]
    },
    options: {
      cutout: '70%',
      plugins: {
        tooltip: { enabled: false },
        doughnutlabel: { labels: [{ text: '' }] }
      }
    }
  });
  document.getElementById(valueId).textContent = value + '%';
}
function updateGauge(id, value, valueId) {
  const chart = charts[id];
  if (chart) {
    const roundedValue = parseFloat(value).toFixed(2); // Ensure 2 decimal places
    chart.data.datasets[0].data = [roundedValue, 100 - roundedValue];
    chart.update();
    document.getElementById(valueId).textContent = `${roundedValue}%`;
  }
}


async function fetchOEEData() {
  const machineId = document.body.dataset.machineId;
  const res = await fetch(`/api/oee/${machineId}`);
  const data = await res.json();

  updateGauge("gauge-availability", data.availability, "value-ava");
  updateGauge("gauge-quality", data.quality, "value-qua");
  updateGauge("gauge-performance", data.performance, "value-pfr");
  updateGauge("gauge-oee", data.oee, "value-oee");
}

window.onload = () => {
  renderGauge("gauge-availability", 0, "value-ava", "#363c85");
  renderGauge("gauge-quality", 0, "value-qua", "#43a047");
  renderGauge("gauge-performance", 0, "value-pfr", "#ef6c00");
  renderGauge("gauge-oee", 0, "value-oee", "#8e24aa");
  fetchOEEData();
  setInterval(fetchOEEData, 100);
};
