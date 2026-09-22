// Public trends visualization: Chart.js trends, bar distribution, and Leaflet map.

document.addEventListener('DOMContentLoaded', async () => {
  try {
    const res = await fetch('/api/trends');
    const data = await res.json();

    renderWeeklyTrendChart(data);
    renderWardBarChart(data.ward_counts || []);
    renderGeospatialMap(data.ward_geo || []);
  } catch (err) {
    console.error('Failed to load public trend data:', err);
  }
});

function renderWeeklyTrendChart(data) {
  const ctx = document.getElementById('trendLineChart');
  if (!ctx) return;

  const weeks = data.weeks || [];
  const categories = data.categories || {};
  const palette = ['#1a3a5c', '#c92a2a', '#e67700', '#2b8a3e', '#7950f2'];

  const datasets = Object.keys(categories).map((catName, idx) => ({
    label: catName,
    data: categories[catName],
    borderColor: palette[idx % palette.length],
    backgroundColor: palette[idx % palette.length],
    borderWidth: 2,
    tension: 0.3,
    pointRadius: 3,
  }));

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: weeks,
      datasets: datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom' },
      },
      scales: {
        y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
        x: { grid: { display: false } },
      },
    },
  });
}

function renderWardBarChart(wardData) {
  const ctx = document.getElementById('wardBarChart');
  if (!ctx) return;

  const labels = wardData.map((d) => d.ward);
  const counts = wardData.map((d) => d.count);

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Complaint Volume',
          data: counts,
          backgroundColor: '#1a3a5c',
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
        x: { grid: { display: false } },
      },
    },
  });
}

function renderGeospatialMap(wardGeo) {
  const mapEl = document.getElementById('map');
  if (!mapEl) return;

  // Center around Tiruchirappalli coordinates
  const map = L.map('map').setView([10.8250, 78.6900], 13);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map);

  wardGeo.forEach((item) => {
    // Radius proportional to complaint density
    const radius = Math.min(30, Math.max(10, item.count * 0.15));
    const isSpike = item.count > 150;

    const circle = L.circleMarker([item.lat, item.lng], {
      color: isSpike ? '#c92a2a' : '#1a3a5c',
      fillColor: isSpike ? '#ef4444' : '#3b82f6',
      fillOpacity: 0.6,
      radius: radius,
    }).addTo(map);

    circle.bindPopup(`
      <strong>${item.ward}</strong><br/>
      Recorded Volume: <strong>${item.count} complaints</strong><br/>
      Status: ${isSpike ? '<span style="color:red;font-weight:bold;">Elevated Surge</span>' : 'Nominal'}
    `);
  });
}
