const money = (n) =>
  typeof n === "number"
    ? n.toLocaleString("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0,
      })
    : "—";

const WATCH_STORAGE_KEY = "solis-watch-seen-v1";
const PULSE_DISMISS_KEY = "solis-watch-pulse-dismissed";
const POLL_MS = 60 * 60 * 1000;
const DRIVE_ALERT_MILES = 200;

let activeNewIds = new Set();

const fmtDate = (iso) => {
  try {
    return new Date(iso).toLocaleString("en-US", {
      timeZone: "America/Los_Angeles",
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
};

function render(report) {
  const c = report.criteria;
  const m = report.marketSummary;
  const expected = report.projections.scenarios.find((s) => s.id === "expected");
  const newIds = activeNewIds;

  document.getElementById("generatedAt").textContent = fmtDate(report.generatedAt);
  document.getElementById("budgetPill").innerHTML = `Budget <strong>${money(c.maxBudget)}</strong>`;
  const agePref = c.preferredMaxModelYear ?? c.maxModelYear;
  document.getElementById("agePill").innerHTML = agePref
    ? `Prefer ≤<strong>${agePref}</strong> · any year if good deal`
    : `Any year <strong>if good deal</strong>`;
  document.getElementById("radiusPill").innerHTML = `Radius <strong>${c.preferredRadiusMiles} mi</strong> of WA`;
  document.getElementById("targetPill").innerHTML = `Target <strong>Oct 2026</strong>`;

  const floor = m.nwDealFloor ?? m.nwAgeEligibleFloor;
  document.getElementById("statFloor").textContent = money(floor);
  document.getElementById("statGap").textContent = money(m.gapToBudget);
  document.getElementById("statGapHint").textContent = `vs ${money(c.maxBudget)} target`;
  document.getElementById("statNational").textContent = money(m.nationalUsedFloor);
  const nationalHint = document.getElementById("statNationalHint");
  if (nationalHint) {
    const solis = m.solisNationalUsedFloor;
    const travato = m.travatoNationalUsedFloor;
    nationalHint.textContent =
      solis != null && travato != null
        ? `Solis ${money(solis)} · Travato ${money(travato)}`
        : "Solis & Travato combined";
  }
  document.getElementById("statCut").textContent = `${Math.round((expected?.changePct || 0) * 100)}%`;

  document.getElementById("verdict").textContent = m.verdict;
  document.getElementById("budgetReach").textContent = report.projections.budgetReachability;

  const scenarios = document.getElementById("scenarios");
  scenarios.innerHTML = report.projections.scenarios
    .map(
      (s) => `
      <div class="proj-cell">
        <div class="k">${s.label} (${Math.round(s.changePct * 100)}%)</div>
        <div class="v">${s.rationale}</div>
      </div>`
    )
    .join("");

  const alerts = document.getElementById("alerts");
  alerts.innerHTML = report.alerts
    .map((a) => `<div class="alert ${a.level}">${a.text}</div>`)
    .join("");

  const active = report.candidates.filter((x) => x.status === "active");
  const top = active.slice().sort((a, b) => a.rank - b.rank).slice(0, 4);
  document.getElementById("cards").innerHTML = top
    .map(
      (x) => `
      <article class="card${newIds.has(x.id) ? " is-new" : ""}">
        <div><span class="tier ${x.tier}">${x.tier}</span> <span class="proj">${x.model || "Solis"}</span>${newIds.has(x.id) ? '<span class="badge-new">new</span>' : ""}</div>
        <h3>${x.year} ${x.model || "Solis"} ${x.trim}</h3>
        <div class="sub">${x.city}, ${x.state} · ${x.distanceMiles} mi · ${x.seller}</div>
        <div class="big-price">${money(x.price)}</div>
        <div class="proj-grid">
          <div class="proj-cell"><div class="k">Oct mild</div><div class="v">${money(x.projectedOct.mild)}</div></div>
          <div class="proj-cell"><div class="k">Oct expected</div><div class="v">${money(x.projectedOct.expected)}</div></div>
          <div class="proj-cell"><div class="k">Oct aggressive</div><div class="v">${money(x.projectedOct.aggressive)}</div></div>
        </div>
        <p class="sub">${x.notes}</p>
        <div><a href="${x.url}" target="_blank" rel="noopener">Open listing</a></div>
      </article>`
    )
    .join("");

  const rows = active
    .slice()
    .sort((a, b) => a.rank - b.rank)
    .map((x) => {
      const delta =
        typeof x.priceChange === "number"
          ? `<div class="delta down">${money(x.priceChange)}</div>`
          : `<div class="delta flat">—</div>`;
      return `
        <tr>
          <td>
            <div><span class="tier ${x.tier}">${x.tier}</span></div>
            <div><strong>${x.year} ${x.model || "Solis"} ${x.trim}</strong>${newIds.has(x.id) ? ' <span class="badge-new">new</span>' : ""}</div>
            <div class="proj">${
              x.preferredAge || x.ageEligible ? "Preferred age" : "Newer · listed for deal"
            }</div>
          </td>
          <td>
            <div class="price">${money(x.price)}</div>
            ${delta}
          </td>
          <td>
            <div class="proj">mild ${money(x.projectedOct.mild)}</div>
            <div class="proj">exp ${money(x.projectedOct.expected)}</div>
            <div class="proj">agg ${money(x.projectedOct.aggressive)}</div>
          </td>
          <td>
            <div>${x.city}, ${x.state}</div>
            <div class="proj">${x.distanceMiles} mi · ${x.withinRadius ? "in radius" : "fly"}</div>
          </td>
          <td>
            <div>${x.miles != null ? x.miles.toLocaleString() + " mi" : "miles TBD"}</div>
            <div class="proj">${x.seller}</div>
          </td>
          <td><a href="${x.url}" target="_blank" rel="noopener">Listing</a></td>
        </tr>`;
    })
    .join("");

  document.getElementById("tableBody").innerHTML = rows;
  document.getElementById("sources").textContent = m.sources.join(" · ");

  renderFinancing(report.financing);
  renderRunAnalysis(report.runAnalysis);
}

function renderRunAnalysis(analysis) {
  const section = document.getElementById("runAnalysisSection");
  if (!section || !analysis) {
    if (section) section.hidden = true;
    return;
  }
  section.hidden = false;
  document.getElementById("runAnalysisSummary").textContent = analysis.summary || "";
  const dropped = analysis.droppedThisRun || [];
  const droppedEl = document.getElementById("runAnalysisDropped");
  if (droppedEl) {
    droppedEl.innerHTML = dropped.length
      ? dropped
          .map(
            (x) =>
              `<li><strong>${x.year} ${x.model} ${x.trim}</strong> (${x.city}) — ${money(x.price)} · ${x.notes}</li>`
          )
          .join("")
      : "<li>No listings dropped on the latest run.</li>";
  }
  document.getElementById("runAnalysisRuns").innerHTML = (analysis.runs || [])
    .map(
      (r) => `
      <tr>
        <td><strong>${r.date}</strong></td>
        <td>${r.activeCount ?? "—"}</td>
        <td>${typeof r.nwDealFloor === "number" ? money(r.nwDealFloor) : "—"}</td>
        <td>${typeof r.nationalFloor === "number" ? money(r.nationalFloor) : "—"}</td>
        <td class="proj">${r.notes || ""}</td>
      </tr>`
    )
    .join("");
  document.getElementById("runAnalysisRemoved").innerHTML = (analysis.removed || [])
    .map(
      (x) =>
        `<li><code>${x.id}</code> — ${x.removedOn || "?"} (${x.reason})${x.lastPrice ? ` · last ${money(x.lastPrice)}` : ""}</li>`
    )
    .join("");
}

function renderFinancing(fin) {
  const section = document.getElementById("financingSection");
  if (!fin) {
    if (section) section.hidden = true;
    return;
  }
  if (section) section.hidden = false;

  document.getElementById("financingRec").textContent = fin.recommendation || "";
  const down = fin.downPaymentTarget ?? 0;
  document.getElementById("finDown").textContent = money(down);
  const downHint = document.getElementById("finDownHint");
  if (downHint) {
    downHint.textContent =
      fin.downPaymentPolicy?.includes("$100")
        ? "BECU: none under $100k"
        : down > 0
          ? "target cash down"
          : "full loan amount";
  }
  const loanHeader = document.getElementById("finLoanHeader");
  if (loanHeader) {
    loanHeader.textContent = down > 0 ? `Loan after ${money(down)}` : "Full loan amount";
  }
  const extra = fin.extraCashNeeded || {};
  document.getElementById("finExtra").textContent =
    typeof extra.low === "number" && typeof extra.high === "number"
      ? `${money(extra.low)}–${money(extra.high)}`
      : "—";
  const term = fin.paymentAssumptions?.termMonths || 120;
  document.getElementById("finTerm").textContent = `${Math.round(term / 12)} yrs`;

  const budgetScenario =
    (fin.paymentScenarios || []).find((s) => s.id === "budget") ||
    (fin.paymentScenarios || [])[0];
  document.getElementById("finBestPay").textContent = money(
    budgetScenario?.monthly?.apr6_5
  );
  document.getElementById("finBestHint").textContent = budgetScenario
    ? `${budgetScenario.label} · 6.5% APR`
    : "at 6.5% APR";
  document.getElementById("finDisclaimer").textContent =
    fin.paymentAssumptions?.disclaimer ||
    extra.notes ||
    "Illustrative planning estimates only.";

  document.getElementById("financingPayments").innerHTML = (fin.paymentScenarios || [])
    .map(
      (s) => `
      <tr>
        <td><strong>${s.label}</strong><div class="proj">${money(s.purchasePrice)} ask</div></td>
        <td class="price">${money(s.loanAmount)}</td>
        <td>${s.ltvPct}%</td>
        <td class="price">${money(s.monthly?.apr6_5)}</td>
        <td>${money(s.monthly?.apr7_5)}</td>
        <td>${money(s.monthly?.apr9_0)}</td>
        <td>${money(s.monthly?.apr11_0)}</td>
      </tr>`
    )
    .join("");

  document.getElementById("financingLenders").innerHTML = (fin.lenders || [])
    .map(
      (l) => `
      <tr>
        <td><strong>${l.name}</strong></td>
        <td>${l.type}</td>
        <td>${l.rates}</td>
        <td>${l.terms}</td>
        <td class="proj">${l.notes}</td>
        <td>${l.fit}</td>
      </tr>`
    )
    .join("");

  document.getElementById("financingSteps").innerHTML = (fin.nextSteps || [])
    .map((step) => `<li>${step}</li>`)
    .join("");
  document.getElementById("financingSources").textContent = (fin.sources || []).length
    ? `Loan sources: ${fin.sources.join(" · ")}`
    : "";
}

function renderCudlNotes(cudl, dealerData) {
  const section = document.getElementById("cudlSection");
  if (!section || !cudl) {
    if (section) section.hidden = true;
    return;
  }

  section.hidden = false;
  document.getElementById("cudlSummary").textContent = cudl.summary || "";
  document.getElementById("cudlFindings").innerHTML = (cudl.findings || [])
    .map((item) => `<li>${item}</li>`)
    .join("");

  const dealers = dealerData?.dealers || cudl.nearbyDealers || [];
  const hint = document.getElementById("cudlDealerHint");
  if (hint && dealerData) {
    hint.textContent = `${dealerData.dealerCount} dealers · ${dealerData.withSyncedInventory} with stock`;
  }

  const tbody = document.getElementById("cudlDealers");
  const filterInput = document.getElementById("cudlDealerFilter");

  const renderRows = (list) => {
    tbody.innerHTML = list
      .map(
        (d) => `
      <tr>
        <td>
          <strong>${d.name}</strong>
          ${d.isBecuPlus ? '<span class="badge-plus">BECU Plus</span>' : ""}
          <div class="proj">${d.city || ""}${d.city && d.state ? ", " : ""}${d.state || ""}</div>
        </td>
        <td>${d.distanceMiles} mi</td>
        <td>${d.cudlInventory ?? "—"}</td>
        <td>${d.winnebagoCount ?? "—"}</td>
        <td class="proj">${d.note || ""}</td>
        <td>${d.searchUrl ? `<a href="${d.searchUrl}" target="_blank" rel="noopener">CUDL</a>` : "—"}</td>
      </tr>`
      )
      .join("");
  };

  renderRows(dealers);
  if (filterInput) {
    filterInput.oninput = () => {
      const q = filterInput.value.trim().toLowerCase();
      if (!q) {
        renderRows(dealers);
        return;
      }
      renderRows(
        dealers.filter(
          (d) =>
            d.name?.toLowerCase().includes(q) ||
            d.city?.toLowerCase().includes(q) ||
            d.note?.toLowerCase().includes(q)
        )
      );
    };
  }

  document.getElementById("cudlImplication").textContent = cudl.implication || "";
  const link = document.getElementById("cudlLink");
  if (link && cudl.sourceUrl) link.href = cudl.sourceUrl;
}

function loadSeenState() {
  try {
    return JSON.parse(localStorage.getItem(WATCH_STORAGE_KEY) || "{}");
  } catch {
    return {};
  }
}

function saveSeenState(report) {
  const active = (report.candidates || []).filter((x) => x.status === "active");
  localStorage.setItem(
    WATCH_STORAGE_KEY,
    JSON.stringify({
      generatedAt: report.generatedAt,
      ids: Object.fromEntries(
        active.map((x) => [x.id, { price: x.price, url: x.url, distanceMiles: x.distanceMiles }])
      ),
    })
  );
}

function driveableCandidates(report, maxMiles = DRIVE_ALERT_MILES) {
  return (report.candidates || []).filter(
    (x) =>
      x.status === "active" &&
      (x.withinRadius || (x.distanceMiles != null && x.distanceMiles <= maxMiles)) &&
      (x.distanceMiles == null || x.distanceMiles <= maxMiles)
  );
}

function newSinceLastVisit(report) {
  const seen = loadSeenState();
  if (!seen.ids) return [];
  const prevIds = seen.ids || {};
  return driveableCandidates(report).filter((x) => !(x.id in prevIds));
}

function pulseListings(pulse) {
  if (!pulse) return [];
  return (pulse.newListings || []).length ? pulse.newListings : [];
}

function listingLine(x) {
  const dist =
    x.distanceMiles != null ? `${x.distanceMiles} mi` : x.city ? `${x.city}` : "";
  const price = typeof x.price === "number" ? money(x.price) : "price TBD";
  const title = x.title || `${x.year || ""} ${x.model || "Solis"} ${x.trim || ""}`.trim();
  const url = x.url || "#";
  return `<li><a href="${url}" target="_blank" rel="noopener"><strong>${title}</strong></a> · ${price}${dist ? ` · ${dist}` : ""}</li>`;
}

function renderSiteAlertBar(report, pulse, { persistSeen = false } = {}) {
  const bar = document.getElementById("siteAlertBar");
  if (!bar) return;

  const dismissed = localStorage.getItem(PULSE_DISMISS_KEY);
  const pulseNew = pulseListings(pulse);
  const visitNew = newSinceLastVisit(report);
  const showPulse = pulseNew.length && pulse?.updatedAt !== dismissed;
  const items = showPulse ? pulseNew : visitNew;

  activeNewIds = new Set([
    ...pulseNew.map((x) => x.id),
    ...visitNew.map((x) => x.id),
  ]);

  if (!items.length) {
    bar.hidden = true;
    bar.innerHTML = "";
    if (persistSeen) saveSeenState(report);
    return;
  }

  const headline = showPulse
    ? `${items.length} new driveable listing${items.length > 1 ? "s" : ""} found`
    : `${items.length} new since your last visit`;

  bar.hidden = false;
  bar.classList.toggle("has-new", true);
  bar.innerHTML = `
    <div class="site-alert-inner">
      <div>
        <strong>${headline}</strong> (within ${DRIVE_ALERT_MILES} mi)
        <ul>${items.map(listingLine).join("")}</ul>
      </div>
      <button type="button" class="site-alert-dismiss" id="dismissSiteAlert">Dismiss</button>
    </div>`;

  document.getElementById("dismissSiteAlert")?.addEventListener("click", () => {
    if (pulse?.updatedAt) localStorage.setItem(PULSE_DISMISS_KEY, pulse.updatedAt);
    saveSeenState(report);
    bar.hidden = true;
    activeNewIds = new Set();
    render(report);
  });

  if (persistSeen && !showPulse) saveSeenState(report);
}

function maybeBrowserNotify(report, pulse) {
  if (!("Notification" in window) || Notification.permission !== "granted") return;
  const pulseNew = pulseListings(pulse);
  const visitNew = newSinceLastVisit(report);
  const items = pulseNew.length ? pulseNew : visitNew;
  if (!items.length) return;
  const x = items[0];
  const title = x.title || `${x.model || "Solis"} listing`;
  const body =
    items.length > 1
      ? `${title} (+${items.length - 1} more within ${DRIVE_ALERT_MILES} mi)`
      : `${money(x.price)} · ${x.city || "nearby"}`;
  new Notification("Solis Watch — new listing", { body, tag: "solis-watch-new" });
}

function setupBrowserAlerts() {
  const btn = document.getElementById("enableNotifyBtn");
  if (!btn || !("Notification" in window)) return;
  if (Notification.permission === "granted") {
    btn.hidden = true;
    return;
  }
  btn.hidden = false;
  btn.addEventListener("click", async () => {
    const perm = await Notification.requestPermission();
    btn.hidden = perm === "granted" || perm === "denied";
  });
}

async function fetchWatchPulse() {
  try {
    const res = await fetch("./data/watch-pulse.json", { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

async function refreshReport({ notify = false, persistSeen = false } = {}) {
  const [reportRes, pulse] = await Promise.all([
    fetch("./data/report.json", { cache: "no-store" }),
    fetchWatchPulse(),
  ]);
  if (!reportRes.ok) throw new Error(`report.json HTTP ${reportRes.status}`);
  const report = await reportRes.json();
  renderSiteAlertBar(report, pulse, { persistSeen });
  render(report);
  const cudlRes = await fetch("./data/cudl-dealers.json", { cache: "no-store" }).catch(() => null);
  if (cudlRes?.ok) renderCudlNotes(report.financing?.cudlNotes, await cudlRes.json());
  if (notify) maybeBrowserNotify(report, pulse);
  return report;
}

function startWatchPolling() {
  setInterval(() => {
    if (document.hidden) return;
    refreshReport({ notify: true }).catch(() => {});
  }, POLL_MS);
}

async function boot() {
  const pulse = await fetchWatchPulse();
  const reportRes = await fetch("./data/report.json", { cache: "no-store" });
  if (!reportRes.ok) throw new Error(`report.json HTTP ${reportRes.status}`);
  const report = await reportRes.json();

  renderSiteAlertBar(report, pulse);
  render(report);

  const cudlRes = await fetch("./data/cudl-dealers.json", { cache: "no-store" }).catch(() => null);
  if (cudlRes?.ok) renderCudlNotes(report.financing?.cudlNotes, await cudlRes.json());

  setupBrowserAlerts();
  maybeBrowserNotify(report, pulse);
  startWatchPolling();

  window.addEventListener("beforeunload", () => saveSeenState(report));
}

boot().catch((err) => {
  document.getElementById("alerts").innerHTML =
    `<div class="alert warning">Could not load report data: ${err.message}</div>`;
});
