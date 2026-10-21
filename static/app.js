const motionOk = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;

document.querySelectorAll(".score-fill").forEach((bar) => {
  bar.style.setProperty("--score", bar.dataset.score || "0");
});

document.querySelectorAll("[data-count]").forEach((node) => {
  const target = Number(node.dataset.count || "0");
  if (!motionOk || !Number.isFinite(target)) return;
  const started = performance.now();
  const duration = 700;
  const tick = (now) => {
    const progress = Math.min(1, (now - started) / duration);
    const eased = 1 - Math.pow(1 - progress, 3);
    node.textContent = String(Math.round(target * eased));
    if (progress < 1) requestAnimationFrame(tick);
  };
  node.textContent = "0";
  requestAnimationFrame(tick);
});

const rows = Array.from(document.querySelectorAll("[data-student]"));
const search = document.querySelector("#buscar");
const chips = Array.from(document.querySelectorAll("[data-filter]"));
const emptyFilter = document.querySelector("#empty-filter");
let activeFilter = "riesgo";

function applyFilter() {
  const query = (search && search.value ? search.value : "").trim().toLowerCase();
  let visible = 0;
  rows.forEach((row) => {
    const levelOk =
      activeFilter === "todos" ||
      (activeFilter === "riesgo" && row.dataset.risk === "1") ||
      activeFilter === row.dataset.nivel;
    const textOk = !query || (row.dataset.blob || "").includes(query);
    const show = levelOk && textOk;
    row.hidden = !show;
    if (show) {
      visible += 1;
      const rank = row.querySelector("[data-rank]");
      if (rank) rank.textContent = String(visible);
    }
  });
  if (emptyFilter) emptyFilter.hidden = visible !== 0 || rows.length === 0;
}

chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    activeFilter = chip.dataset.filter || "todos";
    chips.forEach((item) => item.setAttribute("aria-pressed", item === chip ? "true" : "false"));
    applyFilter();
  });
});

if (search) search.addEventListener("input", applyFilter);
if (rows.length) applyFilter();

const dropzone = document.querySelector("#dropzone");
const fileInput = document.querySelector("#archivo");
const fileName = document.querySelector("#file-name");

if (dropzone && fileInput) {
  const showFile = () => {
    const file = fileInput.files && fileInput.files[0];
    if (!file || !fileName) return;
    fileName.hidden = false;
    fileName.textContent = file.name;
  };
  fileInput.addEventListener("change", showFile);
  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.add("is-drag");
    });
  });
  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.remove("is-drag");
    });
  });
  dropzone.addEventListener("drop", (event) => {
    const files = event.dataTransfer && event.dataTransfer.files;
    if (!files || !files.length) return;
    fileInput.files = files;
    showFile();
  });
}

const uploadForm = document.querySelector("#upload-form");
if (uploadForm) {
  uploadForm.addEventListener("submit", () => {
    const button = uploadForm.querySelector("button[type='submit']");
    if (!button) return;
    button.textContent = "Leyendo el archivo…";
    button.setAttribute("aria-busy", "true");
  });
}

const chartNode = document.querySelector("#chart-data");
if (chartNode && window.Chart) {
  const chart = JSON.parse(chartNode.textContent);
  const animation = motionOk ? { duration: 800 } : false;
  const niveles = document.querySelector("#chart-niveles");
  const programas = document.querySelector("#chart-programas");
  if (niveles) {
    new window.Chart(niveles, {
      type: "doughnut",
      data: {
        labels: chart.labels,
        datasets: [{
          data: chart.niveles,
          backgroundColor: ["#2f6f4e", "#a16207", "#c2410c", "#9f1239"],
          borderWidth: 0,
        }],
      },
      options: {
        animation,
        plugins: { legend: { position: "bottom" } },
        cutout: "62%",
      },
    });
  }
  if (programas) {
    new window.Chart(programas, {
      type: "bar",
      data: {
        labels: chart.programas.map((item) => item.nombre),
        datasets: [{
          data: chart.programas.map((item) => item.en_riesgo),
          backgroundColor: "#1b4332",
          borderRadius: 8,
        }],
      },
      options: {
        animation,
        indexAxis: "y",
        plugins: { legend: { display: false } },
        scales: {
          x: { beginAtZero: true, ticks: { precision: 0 } },
          y: { ticks: { font: { size: 11 } } },
        },
      },
    });
  }
}
