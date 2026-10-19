// dashboard.js
(async () => {
  try {
    const d = await api("/analytics/overview");
    
    // Render Cards
    el("cards").innerHTML = [
      ["Total Record", d.total_records],
      ["Berlabel", d.total_labeled],
      ["Diprediksi", d.total_predicted],
      ["Rata-rata Like", d.avg_likes.toFixed(2)],
    ].map(([t,v]) => `<div class="card"><h3>${t}</h3><div class="value">${v}</div></div>`).join("");

    // Konfigurasi Chart
    const opt = {
      plugins: {
        legend: { labels: { color: "#e6ecff" } }
      }
    };

    // Render Chart Prediksi
    new Chart(el("chartPred"), {
      type: "doughnut",
      data: {
        labels: Object.keys(d.distribution_predicted), 
        datasets: [{ data: Object.values(d.distribution_predicted) }]
      },
      options: opt
    });

    // Render Chart Label
    new Chart(el("chartLabel"), {
      type: "pie",
      data: {
        labels: Object.keys(d.distribution_label), 
        datasets: [{ data: Object.values(d.distribution_label) }]
      },
      options: opt
    });

  } catch (e) { 
    el("alert").innerHTML = `<div class="alert err">⚠️ ${e.message}</div>`; 
  }
})();