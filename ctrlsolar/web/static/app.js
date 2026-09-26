const chart = echarts.init(document.getElementById("chart"));
const summary = document.getElementById("summary");
const warnings = document.getElementById("warnings");
const buttons = [...document.querySelectorAll("button[data-view]")];

const hours = Array.from({ length: 24 }, (_, hour) => `${hour}:00`);
const wh = (value) => value == null ? "N/A" : `${formatNumber(value / 1000)} kWh`;
const watt = (value) => value == null ? "N/A" : `${formatNumber(value)} W`;
const pct = (value) => value == null ? "N/A" : `${formatNumber(value)}%`;

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
  renderWarnings([]);
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
    forecastLine("Forecast", forecast.hourly_wh || []),
    forecastLine("Raw forecast", forecast.raw_hourly_wh || []),
    actualLine("Actual solar", Object.values(actuals.solar_hourly_wh || {})),
  ]), true);
}

async function day() {
  const data = await loadJson(`/api/history/day?date=${today()}`);
  const forecast = data.forecast || [];
  const samples = data.samples || [];
  renderWarnings((data.quality_spans || []).map(spanWarning));

  summary.innerHTML = [
    metric("Samples", samples.length),
    metric("Forecast", wh(sum(forecast.map((row) => row.calibrated_wh)))),
    metric("Actual solar", wh(sum(data.solar_hourly_wh || []))),
    metric("Actual AC", wh(sum(data.ac_hourly_wh || []))),
  ].join("");

  chart.setOption(hourlyOption("Today", [
    forecastLine("Forecast", forecast.map((row) => row.calibrated_wh)),
    forecastLine("Raw forecast", forecast.map((row) => row.predicted_wh)),
    actualLine("Actual solar", data.solar_hourly_wh || []),
    actualLine("Actual AC", data.ac_hourly_wh || []),
  ]), true);
}

async function history() {
  const data = await loadJson("/api/history/range?days=30");
  const rows = data.days || [];
  renderWarnings(rows
    .filter((row) => row.invalid_sample_count)
    .map((row) => {
      const reasons = (row.quality_reasons || []).join(", ");
      return `${row.date}: ${row.invalid_sample_count} invalid samples (${reasons}).`;
    }));

  summary.innerHTML = [
    metric("Days", rows.length),
    metric("Forecast", wh(sum(rows.map((row) => row.forecast_wh)))),
    metric("Actual", wh(sum(rows.map((row) => row.actual_wh)))),
    metric("Error", wh(sum(rows.map((row) => row.error_wh)))),
  ].join("");

  chart.setOption({
    tooltip: tooltipOption(),
    legend: legendOption(),
    xAxis: { type: "category", data: rows.map((row) => row.date) },
    yAxis: valueAxis("Wh"),
    series: [
      forecastLine("Forecast", rows.map((row) => row.forecast_wh)),
      actualLine("Actual solar", rows.map((row) => row.actual_wh)),
      { name: "Error %", type: "line", smooth: true, data: rows.map((row) => row.error_percent) },
    ],
    title: titleOption("30 Day History"),
    grid: chartGrid(),
  }, true);
}

async function calibration() {
  const data = await loadJson("/api/calibration");
  const factors = data.factors || Array(24).fill(1);
  renderWarnings(calibrationWarnings(data));

  summary.innerHTML = [
    metric("Status", data.status || "N/A"),
    metric("Valid days", data.valid_day_count || 0),
    metric("Learned at", data.learned_at || "N/A"),
  ].join("");

  chart.setOption(hourlyOption("Calibration Factors", [
    markerLine("Factor", factors),
  ], "factor"), true);
}

function hourlyOption(title, series, yName = "Wh") {
  return {
    tooltip: tooltipOption(),
    legend: legendOption(),
    xAxis: { type: "category", data: hours },
    yAxis: valueAxis(yName),
    series,
    title: titleOption(title),
    grid: chartGrid(),
  };
}

function forecastLine(name, data) {
  return {
    name,
    type: "line",
    smooth: true,
    showSymbol: false,
    data,
  };
}

function actualLine(name, data) {
  return {
    ...forecastLine(name, data),
    areaStyle: { opacity: 0.22 },
  };
}

function markerLine(name, data) {
  return {
    name,
    type: "line",
    symbol: "circle",
    symbolSize: 9,
    lineStyle: { width: 3 },
    data,
  };
}

function titleOption(text) {
  return { text, left: "center", top: 0 };
}

function legendOption() {
  return { top: 40 };
}

function chartGrid() {
  return { top: 96, left: 54, right: 28, bottom: 44 };
}

function valueAxis(name) {
  return {
    type: "value",
    name,
    axisLabel: {
      formatter: (value) => formatNumber(value),
    },
  };
}

function tooltipOption() {
  return {
    trigger: "axis",
    formatter: (params) => {
      const points = Array.isArray(params) ? params : [params];
      const label = points[0]?.axisValueLabel || points[0]?.name || "";
      const values = points.map((point) => {
        return `${point.marker}${point.seriesName}: ${formatTooltipValue(point.value)}`;
      });
      return [label, ...values].join("<br>");
    },
    axisPointer: {
      label: {
        formatter: (params) => formatTooltipValue(params.value),
      },
    },
  };
}

function formatNumber(value) {
  return Number(value).toFixed(2);
}

function formatTooltipValue(value) {
  const number = Array.isArray(value) ? value.at(-1) : value;
  return number == null ? "N/A" : formatNumber(number);
}

function renderWarnings(items) {
  if (!items.length) {
    warnings.classList.remove("visible");
    warnings.innerHTML = "";
    return;
  }
  warnings.classList.add("visible");
  warnings.innerHTML = [
    "<strong>Data quality warning</strong>",
    "<ul>",
    ...items.map((item) => `<li>${item} Calibration ignores invalid samples.</li>`),
    "</ul>",
  ].join("");
}

function spanWarning(span) {
  return `${shortTime(span.start_timestamp)}-${shortTime(span.end_timestamp)}: ${span.message} (${span.sample_count} samples).`;
}

function shortTime(timestamp) {
  return timestamp ? timestamp.slice(11, 16) : "N/A";
}

function calibrationWarnings(data) {
  if (!data.ignored_invalid_samples) return [];
  return [
    `${data.ignored_invalid_samples} invalid samples across ${data.ignored_invalid_days} days were ignored.`,
  ];
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
