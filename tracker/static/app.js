async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || `request failed: ${response.status}`);
  }
  return response.json();
}

function el(id) {
  return document.getElementById(id);
}

function renderAthletes(rows) {
  const root = el("athleteList");
  root.innerHTML = "";
  rows.forEach((row) => {
    const li = document.createElement("li");
    const club = row.club || "-";
    li.innerHTML = `<strong>${row.display_name}</strong> <span>(${club})</span> <button data-name="${row.display_name}">Remove</button>`;
    li.querySelector("button").addEventListener("click", async () => {
      await api(`/api/athletes/${encodeURIComponent(row.display_name)}`, { method: "DELETE" });
      await loadAthletes();
      await loadResults();
    });
    root.appendChild(li);
  });
}

function renderSources(rows) {
  const root = el("sourceList");
  root.innerHTML = "";
  rows.forEach((row) => {
    const li = document.createElement("li");
    li.textContent = `[${row.tag}] ${row.url}`;
    root.appendChild(li);
  });
}

function renderResults(rows) {
  const body = el("resultsBody");
  body.innerHTML = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${row.captured_at || "-"}</td><td>${row.athlete_name}</td><td>${row.event_name}</td><td>${row.time_text}</td><td>${row.meet_name}</td><td><a href="${row.source_url}" target="_blank" rel="noreferrer">link</a></td>`;
    body.appendChild(tr);
  });
}

async function loadAthletes() {
  const data = await api("/api/athletes");
  renderAthletes(data.athletes || []);
}

async function loadSources() {
  const data = await api("/api/sources");
  renderSources(data.sources || []);
}

async function loadResults() {
  const athlete = el("filterAthlete").value.trim();
  const suffix = athlete ? `?athlete=${encodeURIComponent(athlete)}` : "";
  const data = await api(`/api/results${suffix}`);
  renderResults(data.results || []);
}

async function init() {
  el("athleteForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const name = el("athleteName").value.trim();
    const club = el("athleteClub").value.trim();
    if (!name) return;
    await api("/api/athletes", {
      method: "POST",
      body: JSON.stringify({ name, club }),
    });
    el("athleteName").value = "";
    el("athleteClub").value = "";
    await loadAthletes();
  });

  el("refreshSources").addEventListener("click", async () => {
    await api("/api/sources/refresh", { method: "POST" });
    await loadSources();
  });

  el("runOnce").addEventListener("click", async () => {
    const status = el("runStatus");
    status.textContent = "Running...";
    const dry_run = el("dryRun").checked;
    const result = await api("/api/run/once", {
      method: "POST",
      body: JSON.stringify({ dry_run }),
    });
    status.textContent = `Finished (exit=${result.exit_code})`;
    await loadResults();
  });

  el("loadResults").addEventListener("click", loadResults);

  await loadAthletes();
  await loadSources();
  await loadResults();
}

init().catch((error) => {
  el("runStatus").textContent = `Error: ${error.message}`;
});
