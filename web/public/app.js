const DATA_URL = "./data/dashboard_2026-06-15.json";

const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});
const number = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const percent = new Intl.NumberFormat("en-US", {
  style: "percent",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

let dashboard = null;

function byId(id) {
  return document.getElementById(id);
}

function formatBps(value) {
  return `${number.format(value)} bps`;
}

function formatDateTime(value) {
  if (!value) return "--";
  return new Date(value).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function setText(id, value) {
  byId(id).textContent = value;
}

function initSummary(data) {
  const etf = data.etf;
  setText("tradeDate", `Trade date ${data.tradeDate}`);
  setText("generatedAt", `Generated ${formatDateTime(data.generatedAt)}`);
  setText("indicativeNav", money.format(etf.indicative_nav));
  setText("midPrice", money.format(etf.mid_price));
  setText("premiumDiscount", formatBps(etf.premium_discount_bps));
  setText("arbSignal", etf.arbitrage_signal.replaceAll("_", " "));
  setText("totalExceptions", data.summary.totalExceptions);
  setText("highCount", data.summary.severity.HIGH);
  setText("mediumCount", data.summary.severity.MEDIUM);
  setText("lowCount", data.summary.severity.LOW);
  setText("createEdge", formatBps(etf.create_edge_bps));
  setText("redeemEdge", formatBps(etf.redeem_edge_bps));
  setText("componentCount", data.summary.componentCount);
  setText("pricedCount", data.summary.pricedComponentCount);
  setText("grossValue", money.format(etf.gross_basket_value));
}

function initFilters(data) {
  const typeFilter = byId("typeFilter");
  const types = [...new Set(data.exceptions.map((item) => item.exception_type))].sort();
  types.forEach((type) => {
    const option = document.createElement("option");
    option.value = type;
    option.textContent = type.replaceAll("_", " ");
    typeFilter.appendChild(option);
  });

  byId("severityFilter").addEventListener("change", renderExceptions);
  byId("typeFilter").addEventListener("change", renderExceptions);
  byId("searchBox").addEventListener("input", renderExceptions);
}

function renderExceptionTypes(data) {
  const container = byId("exceptionTypeList");
  container.innerHTML = "";
  data.exceptionTypes.forEach((item) => {
    const pill = document.createElement("div");
    pill.className = "type-pill";
    pill.innerHTML = `<span>${item.type.replaceAll("_", " ")}</span><strong>${item.count}</strong>`;
    container.appendChild(pill);
  });
}

function exceptionMatches(item) {
  const severity = byId("severityFilter").value;
  const type = byId("typeFilter").value;
  const query = byId("searchBox").value.trim().toLowerCase();
  const haystack = [
    item.severity,
    item.rule_id,
    item.entity_id,
    item.exception_type,
    item.message,
    item.evidence,
  ]
    .join(" ")
    .toLowerCase();

  return (
    (severity === "ALL" || item.severity === severity) &&
    (type === "ALL" || item.exception_type === type) &&
    (!query || haystack.includes(query))
  );
}

function renderExceptions() {
  const body = byId("exceptionRows");
  body.innerHTML = "";
  const rows = dashboard.exceptions.filter(exceptionMatches);
  setText("visibleCount", `${rows.length} shown`);

  if (!rows.length) {
    body.appendChild(byId("emptyState").content.cloneNode(true));
    return;
  }

  rows.forEach((item) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><span class="severity ${item.severity}">${item.severity}</span></td>
      <td>${item.rule_id}</td>
      <td><strong>${item.entity_id}</strong></td>
      <td>${item.exception_type.replaceAll("_", " ")}</td>
      <td>${item.message}</td>
    `;
    body.appendChild(tr);
  });
}

function renderBasket(data) {
  const container = byId("basketBars");
  container.innerHTML = "";
  data.basket.forEach((item) => {
    const weight = Number(item.component_weight || 0);
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `
      <strong>${item.ticker}</strong>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.max(weight * 100, 1)}%"></div></div>
      <span>${percent.format(weight)}</span>
    `;
    container.appendChild(row);
  });
}

function renderPrices(data) {
  const body = byId("priceRows");
  body.innerHTML = "";
  data.selectedPrices.forEach((item) => {
    const price = item.selected_price === null ? "--" : number.format(item.selected_price);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${item.ticker}</strong></td>
      <td>${item.selected_source}</td>
      <td>${price} ${item.currency}</td>
      <td><span class="status ${item.price_status}">${item.price_status}</span></td>
    `;
    body.appendChild(tr);
  });
}

function renderAudit(data) {
  const container = byId("auditList");
  container.innerHTML = "";
  data.audit.slice(0, 8).forEach((item) => {
    const node = document.createElement("div");
    node.className = "audit-item";
    node.innerHTML = `
      <strong>${item.file_type}</strong>
      <div>${item.status} · ${item.row_count} rows</div>
      <div>${formatDateTime(item.created_at)}</div>
    `;
    container.appendChild(node);
  });
}

async function boot() {
  const response = await fetch(DATA_URL);
  if (!response.ok) {
    throw new Error(`Unable to load ${DATA_URL}`);
  }
  dashboard = await response.json();
  initSummary(dashboard);
  initFilters(dashboard);
  renderExceptionTypes(dashboard);
  renderExceptions();
  renderBasket(dashboard);
  renderPrices(dashboard);
  renderAudit(dashboard);
}

boot().catch((error) => {
  document.body.innerHTML = `
    <main class="panel" style="margin: 32px;">
      <h1>Dashboard data not found</h1>
      <p>Run <code>etfctl dashboard --date 2026-06-15 --db storage/etf_control.duckdb --output web/public/data</code>, then serve <code>web/public</code>.</p>
      <p>${error.message}</p>
    </main>
  `;
});

