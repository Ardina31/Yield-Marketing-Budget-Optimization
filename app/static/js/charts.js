(function () {
  "use strict";

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function baseFont() {
    return { family: "Inter, sans-serif", size: 11 };
  }

  function gridColor() {
    return cssVar("--color-border") || "#E4E9F1";
  }
  function textMuted() {
    return cssVar("--color-text-muted") || "#8B98AC";
  }

  const PALETTE = ["#0F766E", "#4F46E5", "#D97706", "#E11D48", "#0284C7", "#7C3AED", "#059669", "#DB2777"];

  function paletteColor(i) {
    return PALETTE[i % PALETTE.length];
  }

  /** Line chart comparing cost vs revenue across periods. */
  function renderTrendChart(canvasId, labels, costSeries, revenueSeries) {
    const el = document.getElementById(canvasId);
    if (!el || !window.Chart) return null;
    return new Chart(el, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Revenue",
            data: revenueSeries,
            borderColor: "#0F766E",
            backgroundColor: "rgba(15,118,110,0.12)",
            tension: 0.35,
            fill: true,
            pointRadius: 3,
            pointBackgroundColor: "#0F766E",
            borderWidth: 2.5,
          },
          {
            label: "Spend",
            data: costSeries,
            borderColor: "#E8543F",
            backgroundColor: "rgba(232,84,63,0.08)",
            tension: 0.35,
            fill: true,
            pointRadius: 3,
            pointBackgroundColor: "#E8543F",
            borderWidth: 2.5,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { position: "top", align: "end", labels: { boxWidth: 8, boxHeight: 8, usePointStyle: true, font: baseFont(), color: textMuted() } },
          tooltip: {
            backgroundColor: "#0B1220", padding: 10, cornerRadius: 8, titleFont: baseFont(), bodyFont: baseFont(),
            callbacks: { label: (ctx) => ` ${ctx.dataset.label}: $${ctx.parsed.y.toLocaleString()}` },
          },
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: textMuted(), font: baseFont() } },
          y: {
            grid: { color: gridColor() },
            ticks: { color: textMuted(), font: baseFont(), callback: (v) => "$" + (v >= 1000 ? v / 1000 + "K" : v) },
          },
        },
      },
    });
  }

  /** Donut chart for budget allocation by channel. */
  function renderAllocationDonut(canvasId, labels, values, colors) {
    const el = document.getElementById(canvasId);
    if (!el || !window.Chart) return null;
    return new Chart(el, {
      type: "doughnut",
      data: {
        labels,
        datasets: [{ data: values, backgroundColor: colors || labels.map((_, i) => paletteColor(i)), borderWidth: 0, hoverOffset: 6 }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "72%",
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 8, boxHeight: 8, usePointStyle: true, font: baseFont(), color: textMuted(), padding: 14 } },
          tooltip: {
            backgroundColor: "#0B1220", padding: 10, cornerRadius: 8,
            callbacks: { label: (ctx) => ` ${ctx.label}: $${ctx.parsed.toLocaleString()}` },
          },
        },
      },
    });
  }

  /** Grouped bar chart: original vs optimized spend per campaign/channel. */
  function renderAllocationBar(canvasId, labels, originalSeries, optimizedSeries) {
    const el = document.getElementById(canvasId);
    if (!el || !window.Chart) return null;
    return new Chart(el, {
      type: "bar",
      data: {
        labels,
        datasets: [
          { label: "Current spend", data: originalSeries, backgroundColor: "#CBD5E1", borderRadius: 6, maxBarThickness: 26 },
          { label: "Recommended spend", data: optimizedSeries, backgroundColor: "#0F766E", borderRadius: 6, maxBarThickness: 26 },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", align: "end", labels: { boxWidth: 8, boxHeight: 8, usePointStyle: true, font: baseFont(), color: textMuted() } },
          tooltip: {
            backgroundColor: "#0B1220", padding: 10, cornerRadius: 8,
            callbacks: { label: (ctx) => ` ${ctx.dataset.label}: $${ctx.parsed.y.toLocaleString()}` },
          },
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: textMuted(), font: baseFont() } },
          y: { grid: { color: gridColor() }, ticks: { color: textMuted(), font: baseFont(), callback: (v) => "$" + (v >= 1000 ? v / 1000 + "K" : v) } },
        },
      },
    });
  }

  /** Horizontal bar for top campaigns by ROI. */
  function renderRoiBar(canvasId, labels, values) {
    const el = document.getElementById(canvasId);
    if (!el || !window.Chart) return null;
    return new Chart(el, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor: values.map((v) => (v >= 0 ? "#0F766E" : "#E8543F")),
          borderRadius: 6,
          maxBarThickness: 18,
        }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { backgroundColor: "#0B1220", padding: 10, cornerRadius: 8, callbacks: { label: (ctx) => ` ROI: ${ctx.parsed.x.toFixed(1)}%` } } },
        scales: {
          x: { grid: { color: gridColor() }, ticks: { color: textMuted(), font: baseFont(), callback: (v) => v + "%" } },
          y: { grid: { display: false }, ticks: { color: textMuted(), font: baseFont() } },
        },
      },
    });
  }

  window.YieldCharts = {
    renderTrendChart,
    renderAllocationDonut,
    renderAllocationBar,
    renderRoiBar,
    paletteColor,
  };
})();
