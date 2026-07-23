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
  document.getElementById("agePill").innerHTML = `Max year <strong>${c.maxModelYear}</strong> (5+ yrs)`;
  document.getElementById("radiusPill").innerHTML = `Radius <strong>${c.preferredRadiusMiles} mi</strong> of WA`;
  document.getElementById("targetPill").innerHTML = `Target <strong>Oct 2026</strong>`;

  document.getElementById("statFloor").textContent = money(m.nwAgeEligibleFloor);
  document.getElementById("statGap").textContent = money(m.gapToBudget);
  document.getElementById("statNational").textContent = money(m.nationalUsedFloor);
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

  const primary = report.candidates.filter(
    (x) => x.tier === "primary" && x.status === "active"
  );
  document.getElementById("cards").innerHTML = primary
    .map(
      (x) => `
      <article class="card">
        <div><span class="tier ${x.tier}">${x.tier}</span></div>
        <h3>${x.year} Solis ${x.trim}</h3>
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

  const rows = report.candidates
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
            <div><strong>${x.year} ${x.trim}</strong></div>
            <div class="proj">${x.ageEligible ? "Age eligible" : "Watchlist / too new"} · ${x.status}</div>
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
          <td><a href="${x.url}" target="_blank" rel="noopener">${x.status === "active" ? "Listing" : "Last listing"}</a></td>
        </tr>`;
    })
    .join("");

  document.getElementById("tableBody").innerHTML = rows;
  document.getElementById("sources").textContent = m.sources.join(" · ");
}

async function boot() {
  const res = await fetch("./data/report.json", { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load report.json");
  const report = await res.json();
  render(report);
}

boot().catch((err) => {
  document.getElementById("alerts").innerHTML =
    `<div class="alert warning">Could not load report data: ${err.message}</div>`;
});
