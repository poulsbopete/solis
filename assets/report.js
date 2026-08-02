const money = (n) =>
  typeof n === "number"
    ? n.toLocaleString("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0,
      })
    : "—";

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

  const active = report.candidates.filter((x) => x.status !== "sold");
  const primary = active.filter((x) => x.tier === "primary").slice(0, 4);
  document.getElementById("cards").innerHTML = primary
    .map(
      (x) => `
      <article class="card">
        <div><span class="tier ${x.tier}">${x.tier}</span> <span class="proj">${x.model || "Solis"}</span></div>
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
            <div><strong>${x.year} ${x.model || "Solis"} ${x.trim}</strong></div>
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
  renderCudlNotes(report.financing?.cudlNotes);
  renderAlternatives(report.alternatives);
}

function renderFinancing(fin) {
  if (!fin) {
    document.getElementById("financingPanel").hidden = true;
    return;
  }

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

function renderCudlNotes(cudl) {
  const panel = document.getElementById("cudlPanel");
  if (!panel || !cudl) {
    if (panel) panel.hidden = true;
    return;
  }

  panel.hidden = false;
  document.getElementById("cudlSummary").textContent = cudl.summary || "";
  document.getElementById("cudlFindings").innerHTML = (cudl.findings || [])
    .map((item) => `<li>${item}</li>`)
    .join("");
  document.getElementById("cudlDealers").innerHTML = (cudl.nearbyDealers || [])
    .map(
      (d) => `
      <tr>
        <td><strong>${d.name}</strong></td>
        <td>${d.distanceMiles} mi</td>
        <td>${d.cudlInventory}</td>
        <td class="proj">${d.note || ""}</td>
      </tr>`
    )
    .join("");
  document.getElementById("cudlImplication").textContent = cudl.implication || "";
  const link = document.getElementById("cudlLink");
  if (link && cudl.sourceUrl) link.href = cudl.sourceUrl;
}

function renderAlternatives(alts) {
  const section = document.getElementById("alternativesSection");
  if (!section) return;
  const items = (alts || []).filter((a) => a.status === "lead" || a.status === "active");
  if (!items.length) {
    section.hidden = true;
    return;
  }
  section.hidden = false;
  document.getElementById("alternativesCards").innerHTML = items
    .map(
      (x) => `
      <article class="card alt-card">
        <div><span class="tier primary">${x.status === "lead" ? "lead" : "alt"}</span></div>
        <h3>${x.year} ${x.make} ${x.model} ${x.trim}</h3>
        <div class="sub">${x.city}, ${x.state} · ${x.distanceMiles} mi · ${x.seller}</div>
        <div class="big-price">${money(x.price)}</div>
        <div class="proj-grid">
          <div class="proj-cell"><div class="k">Miles</div><div class="v">${x.miles?.toLocaleString() ?? "—"}</div></div>
          <div class="proj-cell"><div class="k">Chassis</div><div class="v">${x.chassis || "—"}</div></div>
          <div class="proj-cell"><div class="k">BECU</div><div class="v">${x.becuEligible ? "Eligible" : "Check"}</div></div>
        </div>
        <p class="sub">${x.notes}</p>
        ${x.vsSolis ? `<p class="sub"><em>${x.vsSolis}</em></p>` : ""}
        <div><a href="${x.url}" target="_blank" rel="noopener">Open listing</a></div>
      </article>`
    )
    .join("");
}

async function boot() {
  const res = await fetch("./data/report.json", { cache: "no-store" });
  if (!res.ok) throw new Error(`report.json HTTP ${res.status}`);
  render(await res.json());
}

boot().catch((err) => {
  document.getElementById("alerts").innerHTML =
    `<div class="alert warning">Could not load report data: ${err.message}</div>`;
});
