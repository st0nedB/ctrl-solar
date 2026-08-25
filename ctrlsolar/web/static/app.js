const chart = echarts.init(document.getElementById("chart"));
const summary = document.getElementById("summary");
const buttons = [...document.querySelectorAll("button[data-view]")];

const hours = Array.from({ length: 24 }, (_, hour) => `${hour}:00`);
const wh = (value) => value == null ? "N/A" : `${(value / 1000).toFixed(2)} kWh`;
const watt = (value) => value == null ? "N/A" : `${Number(value).toFixed(0)} W`;
const pct = (value) => value == null ? "N/A" : `${Number(value).toFixed(1)}%`;

function metric(label, value) {
  return `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`;
}

async function loadJson(url) {
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || response.statusText);
  return payload;
}

function setActive(view) {
  buttons.forEach((button) => button.classList.toggle("active", button.dataset.view === view));
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

async function live() {
  const data = await loadJson("/api/live");
  const battery = data.battery || {};
  const controller = data.controller || {};
  const forecast = data.forecast || {};
  const actuals = data.actuals || {};

  summary.innerHTML = [
    metric("Phase", controller.phase || "N/A"),
    metric("Target", watt(controller.last_target_power_w)),
    metric("Battery", battery.online ? "Online" : "Offline"),
    metric("Charge", pct((battery.state_of_charge || 0) * 100)),
    metric("Panel Power", watt(battery.panel_power_w)),
    metric("Missing", wh(battery.energy_missing_wh)),
  ].join("");

  chart.setOption(hourlyOption("Live", [
    { name: "Forecast", type: "bar", data: forecast.hourly_wh || [] },
    { name: "Raw forecast", type: "line", smooth: true, data: forecast.raw_hourly_wh || [] },
    { name: "Actual solar", type: "bar", data: Object.values(actuals.solar_hourly_wh || {}) },
  ]), true);
}

async function day() {
  const data = await loadJson(`/api/history/day?date=${today()}`);
  const forecast = data.forecast || [];
  const samples = data.samples || [];

  summary.innerHTML = [
    metric("Samples", samples.length),
    metric("Forecast", wh(sum(forecast.map((row) => row.calibrated_wh)))),
    metric("Actual solar", wh(sum(data.solar_hourly_wh || []))),
    metric("Actual AC", wh(sum(data.ac_hourly_wh || []))),
  ].join("");

  chart.setOption(hourlyOption("Today", [
    { name: "Forecast", type: "bar", data: forecast.map((row) => row.calibrated_wh) },
    { name: "Raw forecast", type: "line", smooth: true, data: forecast.map((row) => row.predicted_wh) },
    { name: "Actual solar", type: "bar", data: data.solar_hourly_wh || [] },
    { name: "Actual AC", type: "line", smooth: true, data: data.ac_hourly_wh || [] },
  ]), true);
}

async function history() {
  const data = await loadJson("/api/history/range?days=30");
  const rows = data.days || [];

  summary.innerHTML = [
    metric("Days", rows.length),
    metric("Forecast", wh(sum(rows.map((row) => row.forecast_wh)))),
    metric("Actual", wh(sum(rows.map((row) => row.actual_wh)))),
    metric("Error", wh(sum(rows.map((row) => row.error_wh)))),
  ].join("");

  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: {},
    xAxis: { type: "category", data: rows.map((row) => row.date) },
    yAxis: { type: "value", name: "Wh" },
    series: [
      { name: "Forecast", type: "bar", data: rows.map((row) => row.forecast_wh) },
      { name: "Actual solar", type: "bar", data: rows.map((row) => row.actual_wh) },
      { name: "Error %", type: "line", smooth: true, data: rows.map((row) => row.error_percent) },
    ],
    title: { text: "30 Day History", left: "center" },
  }, true);
}

async function calibration() {
  const data = await loadJson("/api/calibration");
  const factors = data.factors || Array(24).fill(1);

  summary.innerHTML = [
    metric("Status", data.status || "N/A"),
    metric("Valid days", data.valid_day_count || 0),
    metric("Learned at", data.learned_at || "N/A"),
  ].join("");

  chart.setOption(hourlyOption("Calibration Factors", [
    { name: "Factor", type: "bar", data: factors },
  ], "factor"), true);
}

function hourlyOption(title, series, yName = "Wh") {
  return {
    tooltip: { trigger: "axis" },
    legend: {},
    xAxis: { type: "category", data: hours },
    yAxis: { type: "value", name: yName },
    series,
    title: { text: title, left: "center" },
  };
}

function sum(values) {
  return values.reduce((total, value) => total + (Number(value) || 0), 0);
}

const views = { live, today: day, history, calibration };
buttons.forEach((button) => {
  button.addEventListener("click", async () => {
    setActive(button.dataset.view);
    try {
      await views[button.dataset.view]();
    } catch (error) {
      summary.innerHTML = metric("Error", error.message);
      chart.clear();
    }
  });
});

window.addEventListener("resize", () => chart.resize());
setActive("live");
live().catch((error) => {
  summary.innerHTML = metric("Error", error.message);
});
