const motionOk = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const story = document.querySelector(".login-story");
if (story && motionOk) {
  story.addEventListener("pointermove", (event) => {
    const rect = story.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width - 0.5;
    const y = (event.clientY - rect.top) / rect.height - 0.5;
    story.style.setProperty("--mx", x.toFixed(3));
    story.style.setProperty("--my", y.toFixed(3));
  });
  story.addEventListener("pointerleave", () => {
    story.style.setProperty("--mx", "0");
    story.style.setProperty("--my", "0");
  });
}

document.querySelectorAll(".score-fill, .program-fill").forEach((bar) => {
  bar.style.setProperty("--score", bar.dataset.score || bar.dataset.share || "0");
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
  window.Chart.defaults.font.family = "Manrope, sans-serif";
  window.Chart.defaults.color = "#5c6778";
  const niveles = document.querySelector("#chart-niveles");
  if (niveles) {
    new window.Chart(niveles, {
      type: "doughnut",
      data: {
        labels: chart.labels,
        datasets: [{
          data: chart.niveles,
          backgroundColor: ["#004A93", "#FFD300", "#C45C26", "#9f1239"],
          borderWidth: 0,
        }],
      },
      options: {
        animation,
        cutout: "62%",
        plugins: {
          legend: {
            position: "bottom",
            labels: { font: { family: "Manrope, sans-serif", size: 13 }, padding: 14 },
          },
        },
      },
    });
  }
}
