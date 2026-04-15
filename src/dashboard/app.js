const state = {
  rows: [],
  days: 90,
  keyword: "",
  rawAssetsRows: [],
  rawSurveyRows: [],
  wordCloudIntersection: false,
  files: {
    tickets: null, // V_OM_WORK_TASK.csv
    assets: null,  // V_OM_WORK_TASK_ASSET.csv
    space: null,   // V_SPACE_DETAIL.csv
}
};

state.panel1 = {
  rows: [],
  page: 1,
  pageSize: 100,
};

state.panel4 = {
  rows: [],
  filteredRows: [],
  page: 1,
  pageSize: 100,
  wordFreq: null,
};

const stopWords = new Set([
  // uninformative
  "the", "a", "an", "to", "for", "in", "of", "on", "and", "at",
  "with", "is", "are", "was", "were", "from", "by", "or", "as",
  "it", "this", "that", "be", "has", "have", "not", "non",

  // politeness filler
  "thank", "thanks", "hello", "hope", "please", "sure",

  // request / ticketing system language
  "contact", "questions", "question", "attached", "detail", "details",
  "info", "information", "request", "requesting", "requester",
  "order", "task", "service", "services", "support", "assist",
  "assistance", "provide", "provided", "generated", "assign",
  "assigned", "caller", "contacted", "regarding", "related",
  "billable", "vendor", "expenses", "charges", "charge", "cost",
  "requisitions", "department", "project", "team", "operations",

  // numeric
  "one", "any", "1st", "2nd", "3rd", "4th", "5th", "6th", "7th",
  "8th", "9th", "10th", "11th", "12th", "13th",

  // generic verbs 
  "need", "needs", "needed", "like", "just", "make", "made",
  "come", "coming", "go", "going", "get", "gets", "getting",
  "having", "use", "used", "using", "possible", "currently",
  "additional", "following", "good", "let", "know", "look",
  "looks", "want", "really", "able", "appears", "believe",
  "think", "said", "note", "see",

  // vague issues
  "issue", "issues", "problem", "problems", "out",

  // spatial terms
  "center", "room", "rooms", "floor", "floors", "hall", "hallway",
  "hallways", "office", "offices", "area", "areas", "space",
  "outside", "inside", "near", "located", "location", "main",
  "right", "left", "north", "south", "east", "west", "corner",
  "level", "suite", "basement", "lobby", "entry", "entrance",
  "storage", "closet", "dock", "loading", "station", "courtyard",
  "patio", "garage", "quad", "section", "middle", "rear",
  "building", "buildings", "house", "college", "commons",
  "lab", "classroom", "auditorium", "conference", "lecture",
  "library", "lounge", "servery", "dining", "venue", "campus",
  "university", "shop", "place",

  // time references
  "today", "tomorrow", "yesterday", "morning", "afternoon",
  "evening", "night", "day", "days", "week", "weeks",
  "monday", "tuesday", "wednesday", "thursday", "friday",
  "saturday", "sunday", "january", "february", "march", "april",
  "june", "july", "august", "september", "october", "november",
  "december", "jan", "feb", "oct",

  // event context 
  "event", "meeting", "game", "concert", "football", "annual",
  "student", "students", "staff", "faculty", "people", "public",
  "president", "alumni",

  // contact 
  "phone", "email", "ext", "number",

  // gendered labels
  "men", "women", "mens", "womens", "ladies",

  // campus identifiers
  "rice", "edu", "brc", "grb", "dbh", "alm", "coa", "fsc", "rmc", "rupd",
  "duncan", "brown", "baker", "lovett", "fondren", "hanszen",
  "martel", "mcmurtry", "sewall", "wiess", "brockman", "anderson",
  "kraft", "moody", "mcnair", "rawls", "huff", "keck", "ryon",
  "tudor", "garrett", "jones",

  // personal names 
  "rodriguez", "monica", "frydl", "juan", "david", "matt", "garcia",
  "munira", "vejlani", "olivia", "james", "dewayne", "sid", "allen",
  "mosquinski", "bradley", "calvin", "abbatessa", "gutierrez",
  "brad", "thang", "anh", "mike", "maria", "francisco", "rudy",
  "hannes", "jonathan", "sanchez", "minh", "harper", "urbano",
  "nguyen", "benny", "waldron", "thacker", "layton", "herring",
  "connor", "tegan", "tegang",

  // noise
  "doesn", "isn", "won", "don", "didn", "aren", "wasn", "weren",
  "hasn", "haven", "couldn", "wouldn", "shouldn", "attn", "xxxx",
  "00am",
]);

const $ = (id) => document.getElementById(id);

const sampleAssetsCsv = `WORK_TASK_ID,WORK_TASK_NAME_ticket,WORK_TASK_STATUS_ticket,RICE_WORK_STATUS,ASSIGNMENT_STATUS,DESCRIPTION,TASK_TYPE,TASK_PRIORITY,REQUEST_CLASS,SERVICE_CLASS,CREATE_DATE_LTZ,WORK_TASK_NAME_asset,WORK_TASK_STATUS_asset,ASSET_ID,ASSET_NAME,ASSET_STATUS,ASSET_PRIMARY_LOCATION,ASSET_PRIMARY_LOCATION_BUILDING,ACCOUNT_STRING
WT-001,AHU vibration ticket,Open,In Progress,Assigned,air handler high vibration and noise,Corrective,High,Maintenance,HVAC,2025-12-11T08:00:00Z,Air Handler 101,Active,AHU-101,North Air Handler,Online,North Tower 1,North Tower,100-100
WT-002,AHU repeat vibration,Open,In Progress,Assigned,repeat vibration alarm on air handler,Corrective,High,Maintenance,HVAC,2025-12-15T08:00:00Z,Air Handler 101,Active,AHU-101,North Air Handler,Online,North Tower 1,North Tower,100-100
WT-003,Pump PM,Closed,Complete,Done,quarterly pump lubrication and inspection,Preventative,Medium,Maintenance,Mechanical,2025-12-10T08:00:00Z,Pump 550,Active,PMP-550,Transfer Pump,Online,West Annex Mech,West Annex,100-200`;

const sampleSurveyCsv = `WORK_TASK_ID,work_task_name,survey_id,survey_type,responsible_organization,request_class,service_request_id,building,floor,average_survey_score,BASELINE_START_LTZ
WT-001,AHU vibration ticket,SV-101,Work Order,Facilities,Maintenance,SR-1,North Tower,2,3.8,2025-12-11T08:00:00Z
WT-002,AHU repeat vibration,SV-102,Work Order,Facilities,Maintenance,SR-2,North Tower,2,4.1,2025-12-15T08:00:00Z
WT-003,Pump PM,SV-103,Work Order,Facilities,Maintenance,SR-3,West Annex,1,4.8,2025-12-10T08:00:00Z`;

function parseCsv(text) {
  const lines = [];
  let cur = "";
  let row = [];
  let insideQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];

    if (ch === '"') {
      if (insideQuotes && next === '"') {
        cur += '"';
        i += 1;
      } else {
        insideQuotes = !insideQuotes;
      }
    } else if (ch === "," && !insideQuotes) {
      row.push(cur.trim());
      cur = "";
    } else if ((ch === "\n" || ch === "\r") && !insideQuotes) {
      if (ch === "\r" && next === "\n") i += 1;
      if (cur.length || row.length) {
        row.push(cur.trim());
        lines.push(row);
      }
      row = [];
      cur = "";
    } else {
      cur += ch;
    }
  }

  if (cur.length || row.length) {
    row.push(cur.trim());
    lines.push(row);
  }

  if (!lines.length) return [];
  const headers = lines[0].map((h) => h.toLowerCase());

  return lines.slice(1).map((cells) => {
    const obj = {};
    headers.forEach((h, idx) => {
      obj[h] = cells[idx] ?? "";
    });
    return obj;
  });
}

function parseNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function parseDate(value) {
  if (!value) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

function cleanDescription(text) {
  return (text || "")
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((w) => w && w.length > 2 && !stopWords.has(w))
    .join(" ");
}

function parseGroupValuesInput(text) {
  return (text || "")
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}

function tokenizeDescription(text) {
  return (text || "")
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((w) => w && w.length > 2 && !stopWords.has(w));
}

function buildUnionFreq(rows) {
  const freq = new Map();

  rows.forEach((r) => {
    tokenizeDescription(r.description).forEach((w) => {
      freq.set(w, (freq.get(w) || 0) + 1);
    });
  });

  return freq;
}

function buildIntersectionFreq(rows, selectedValues) {
  const normalizedSelected = selectedValues.map((v) => v.trim().toLowerCase());
  const byGroupFreq = new Map();

  rows.forEach((r) => {
    const groupValue = (r.group_value || "").trim().toLowerCase();
    if (!normalizedSelected.includes(groupValue)) return;

    if (!byGroupFreq.has(groupValue)) {
      byGroupFreq.set(groupValue, new Map());
    }

    const freq = byGroupFreq.get(groupValue);
    tokenizeDescription(r.description).forEach((w) => {
      freq.set(w, (freq.get(w) || 0) + 1);
    });
  });

  if (byGroupFreq.size < 2) {
    return buildUnionFreq(rows);
  }

  const groupMaps = [...byGroupFreq.values()];
  const sharedWords = [...groupMaps[0].keys()].filter((word) =>
    groupMaps.every((m) => m.has(word))
  );

  const intersectionFreq = new Map();
  sharedWords.forEach((word) => {
    const total = groupMaps.reduce((sum, m) => sum + (m.get(word) || 0), 0);
    intersectionFreq.set(word, total);
  });

  return intersectionFreq;
}

function normalizeRows(rawRows) {
  return rawRows.map((r) => {
    const dateSource = r.baseline_start_ltz || r.create_date_ltz || r.created_at;
    const eventDate = parseDate(dateSource);

    return {
      ticket_id: r.work_task_id || r.ticket_id || "",
      description: r.description || "",
      ticket_type: r.task_type || "",
      task_priority: r.task_priority || "",
      asset_id: r.asset_id || "",
      asset_name: r.asset_name || "",
      asset_status: r.asset_status || "",
      building: r.asset_primary_location_building || r.building || r.asset_primary_location || "Unknown",
      request_class: r.request_class || "",
      service_class: r.service_class || "",
      survey_score: parseNumber(r.average_survey_score || r.survey_score),
      created_at: dateSource || "",
      event_date: eventDate,
    };
  });
}

function normalizeRepetitiveApiRows(rows) {
  return rows.map((r) => ({
    ticket_id: r.WORK_TASK_ID || "",
    building: r.BUILDING || "Unknown",
    object_id: r.OBJECT_ID || "",
    ticket_type: r.TASK_TYPE || "",
    created_at: r.CREATE_DATE_LTZ || "",
    repetitive: Number(r.REPETITIVE || 0),
    description: r.DESCRIPTION || "",
  }));
}

function normalizeApiTicketRows(rows) {
  return rows.map((r) => ({
    ticket_id: r.WORK_TASK_ID || "",
    building: r.BUILDING || "Unknown",
    description: r.DESCRIPTION || "",
    group_value: r.GROUP_VALUE || "",
  }));
}

function paginate(rows, page, pageSize) {
  const start = (page - 1) * pageSize;
  return rows.slice(start, start + pageSize);
}

function getTotalPages(rows, pageSize) {
  return Math.max(1, Math.ceil(rows.length / pageSize));
}

function mergeRawRowsByTicketId(assetRows, surveyRows) {
  const merged = new Map();

  assetRows.forEach((r) => {
    const id = r.work_task_id || "";
    if (!id) return;
    merged.set(id, { ...r });
  });

  surveyRows.forEach((r) => {
    const id = r.work_task_id || "";
    if (!id) return;
    const existing = merged.get(id) || {};
    merged.set(id, { ...existing, ...r });
  });

  const orphanAssetRows = assetRows.filter((r) => !(r.work_task_id || ""));
  const orphanSurveyRows = surveyRows.filter((r) => !(r.work_task_id || ""));

  return [...merged.values(), ...orphanAssetRows, ...orphanSurveyRows];
}

function refreshRowsFromLoadedFiles() {
  const mergedRaw = mergeRawRowsByTicketId(state.rawAssetsRows, state.rawSurveyRows);
  setRows(normalizeRows(mergedRaw));
}

function setRows(rows) {
  state.rows = rows;
  render();
}

function formatPct(n) {
  return `${(n * 100).toFixed(1)}%`;
}

function repetitiveTasksWithinWindow(rows, windowDays) {
  const ninetyDaysMs = windowDays * 24 * 60 * 60 * 1000;
  const byAsset = new Map();

  rows
    .filter((r) => r.asset_id && r.event_date)
    .sort((a, b) => {
      if (a.asset_id !== b.asset_id) return a.asset_id.localeCompare(b.asset_id);
      return a.event_date.getTime() - b.event_date.getTime();
    })
    .forEach((r) => {
      if (!byAsset.has(r.asset_id)) byAsset.set(r.asset_id, []);
      byAsset.get(r.asset_id).push(r);
    });

  const repeatedTasks = [];

  byAsset.forEach((group) => {
    for (let i = 0; i < group.length; i += 1) {
      const currentTask = group[i];
      const currentTime = currentTask.event_date.getTime();

      for (let j = i + 1; j < group.length; j += 1) {
        const otherTask = group[j];
        const otherTime = otherTask.event_date.getTime();
        const timeDifference = otherTime - currentTime;

        if (!Number.isFinite(timeDifference)) continue;

        if (timeDifference <= ninetyDaysMs) {
          repeatedTasks.push(currentTask);
          break;
        }

        if (timeDifference > ninetyDaysMs) {
          break;
        }
      }
    }
  });

  return repeatedTasks;
}

async function fetchRepetitiveObjectsFromApi() {
  const ticketsFile = state.files.tickets;
  const assetsFile = state.files.assets;
  const spaceFile = state.files.space;

  if (!ticketsFile || !assetsFile || !spaceFile) {
    throw new Error("Upload Tickets, Assets, and Space CSVs in the global controls first.");
  }

  const fd = new FormData();
  fd.append("tickets_csv", ticketsFile);
  fd.append("assets_csv", assetsFile);
  fd.append("space_csv", spaceFile);
  fd.append("num_days", String(state.days));
  fd.append("min_days", "3");
  fd.append("repetitive_only", "true");
  fd.append("drop_missing_space", "true");
  fd.append("corrective_only", "true");

  const resp = await fetch("http://localhost:8000/repetitive-objects", {
    method: "POST",
    body: fd,
  });

  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error(`API ${resp.status}: ${txt}`);
  }

  return await resp.json();
}

async function loadPanel1FromApi() {
  const summary = $("repetitiveSummary");

  try {
    summary.textContent = "Loading repetitive tickets...";
    const data = await fetchRepetitiveObjectsFromApi();

    state.panel1.rows = normalizeRepetitiveApiRows(data.ticket_rows || []);
    state.panel1.page = 1;

    const info = data.summary || {};
    summary.textContent =
      `Found ${info.repetitive_rows ?? state.panel1Rows.length} repetitive rows ` +
      `out of ${info.total_rows ?? 0} total rows within ${info.num_days ?? state.days} days.`;

    renderPanel1();
  } catch (e) {
    console.error(e);
    state.panel1Rows = [];
    summary.textContent = `Repetitive objects API failed: ${e.message}`;
    renderPanel1();
  }
}

async function fetchWordCloudFromApi() {
  const ticketsFile = state.files.tickets;
  const assetsFile = state.files.assets;
  const spaceFile = state.files.space;

  if (!ticketsFile || !assetsFile || !spaceFile) {
    throw new Error("Upload Tickets, Assets, and Space CSVs for the word cloud.");
  }

  const groupCol = $("wcGroupCol").value.trim();
  const groupValue = $("wcGroupValue").value.trim();

  const fd = new FormData();
  fd.append("tickets_csv", ticketsFile);
  fd.append("assets_csv", assetsFile);
  fd.append("space_csv", spaceFile);

  if (groupCol) fd.append("group_col", groupCol);
  if (groupCol && groupValue) fd.append("group_values", groupValue);

  const resp = await fetch("http://localhost:8000/wordcloud", {
    method: "POST",
    body: fd,
  });

  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error(`API ${resp.status}: ${txt}`);
  }

  const data = await resp.json();

  return {
    ticketRows: data.ticket_rows || []
  };
}



function renderPanel1() {
  const tbody = $("repetitiveTable");
  const pageInfo = $("panel1PageInfo");
  const prevBtn = $("panel1PrevBtn");
  const nextBtn = $("panel1NextBtn");

  const rows = state.panel1.rows;
  const page = state.panel1.page;
  const pageSize = state.panel1.pageSize;

  const totalPages = getTotalPages(rows, pageSize);
  const pageRows = paginate(rows, page, pageSize);

  tbody.innerHTML = "";
  const fragment = document.createDocumentFragment();

  pageRows.forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.ticket_id || "N/A"}</td>
      <td>${r.building || "N/A"}</td>
      <td>${r.object_id || "N/A"}</td>
      <td>${r.ticket_type || "N/A"}</td>
      <td>${r.created_at || "N/A"}</td>
      <td>${r.repetitive}</td>
      <td>${r.cleaned_description || ""}</td>
    `;
    fragment.appendChild(tr);
  });

  tbody.appendChild(fragment);

  if (pageInfo) pageInfo.textContent = `Page ${page} of ${totalPages}`;
  if (prevBtn) prevBtn.disabled = page <= 1;
  if (nextBtn) nextBtn.disabled = page >= totalPages;
}

async function renderPanel2() {
  const legend = $("heatmapLegend");
  const frame = $("mapFrame");

  try {
    legend.textContent = "Loading map...";
    const resp = await fetch("http://localhost:8000/map-html");

    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error(`API ${resp.status}: ${txt}`);
    }

    const html = await resp.text();
    frame.srcdoc = html;
    legend.textContent = "Interactive map loaded.";
  } catch (e) {
    console.error(e);
    legend.textContent = `Map failed: ${e.message}`;
  }
}

function renderBars(targetId, items, color = "var(--accent)") {
  const el = $(targetId);
  el.innerHTML = "";
  const max = Math.max(...items.map((i) => i.value), 1);
  items.forEach((i) => {
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `<div>${i.label}</div><div class="bar-fill" style="width:${(i.value / max) * 100}%; background:${color};"></div><div>${i.value}</div>`;
    el.appendChild(row);
  });
}

function renderPanel3() {
  const pmStats = $("pmStats");
  const pmTable = $("pmTable");

  pmTable.innerHTML = "";

  const assetTickets = new Map();
  state.rows.filter((r) => r.asset_id).forEach((r) => {
    if (!assetTickets.has(r.asset_id)) assetTickets.set(r.asset_id, []);
    assetTickets.get(r.asset_id).push(r);
  });

  const withPm = [];
  const withoutPm = [];

  [...assetTickets.entries()].forEach(([assetId, tickets]) => {
    const hasPm = tickets.some((t) => (t.ticket_type || "").toLowerCase().includes("prevent"));
    const corrective = tickets.filter((t) => (t.ticket_type || "").toLowerCase().includes("correct")).length;
    const scoreRows = tickets.filter((t) => t.survey_score > 0);
    const score = scoreRows.length ? scoreRows.reduce((sum, t) => sum + t.survey_score, 0) / scoreRows.length : 0;
    (hasPm ? withPm : withoutPm).push({ assetId, corrective, score });
  });

  const metrics = [
    {
      k: "Assets",
      pm: withPm.length,
      no: withoutPm.length,
    },
    {
      k: "Avg Corrective Tickets/Asset",
      pm: withPm.length ? (withPm.reduce((s, x) => s + x.corrective, 0) / withPm.length).toFixed(2) : "0",
      no: withoutPm.length ? (withoutPm.reduce((s, x) => s + x.corrective, 0) / withoutPm.length).toFixed(2) : "0",
    },
    {
      k: "Avg Survey Score",
      pm: withPm.length ? (withPm.reduce((s, x) => s + x.score, 0) / withPm.length).toFixed(2) : "n/a",
      no: withoutPm.length ? (withoutPm.reduce((s, x) => s + x.score, 0) / withoutPm.length).toFixed(2) : "n/a",
    },
  ];

  metrics.forEach((m) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${m.k}</td><td>${m.pm}</td><td>${m.no}</td>`;
    pmTable.appendChild(tr);
  });

  renderBars(
    "pmBars",
    [
      { label: "Assets with PM", value: withPm.length },
      { label: "Assets without PM", value: withoutPm.length },
    ],
    "linear-gradient(90deg, var(--accent-2), #4ecdc4)"
  );

  pmStats.textContent = `Compared ${withPm.length + withoutPm.length} unique assets with IDs.`;
}

function renderPanel4() {
  const key = state.keyword.toLowerCase().trim();
  const summary = $("keywordSummary");
  const tbody = $("keywordTable");
  const cloud = $("wordCloud");

  const sourceRows = state.panel4Rows.length ? state.panel4Rows : state.rows;
  const rows = key
    ? sourceRows.filter((r) => cleanDescription(r.description).includes(key))
    : sourceRows;

  const selectedValues = parseGroupValuesInput($("wcGroupValue").value);
  const canIntersect =
    state.panel4Rows.length &&
    $("wcGroupCol").value.trim() &&
    selectedValues.length > 1;

  summary.textContent = key
    ? `${rows.length} ticket descriptions contain "${key}".`
    : `Showing all ${rows.length} descriptions. Enter a keyword to filter.`;

  tbody.innerHTML = "";
  rows.forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.ticket_id || "N/A"}</td>
      <td>${r.building || "N/A"}</td>
      <td>${r.group_value || "N/A"}</td>
      <td>${cleanDescription(r.description)}</td>
    `;
    tbody.appendChild(tr);
  });

  const unionFreq = buildUnionFreq(rows);
  const intersectionFreq = buildIntersectionFreq(rows, selectedValues);

  console.log("union word count:", unionFreq.size);
  console.log("intersection word count:", intersectionFreq.size);
  console.log(
    "union top 10:",
    [...unionFreq.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10)
  );
  console.log(
    "intersection top 10:",
    [...intersectionFreq.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10)
  );

  const freq =
  state.wordCloudIntersection && canIntersect
    ? intersectionFreq
    : unionFreq;

  const topWords = [...freq.entries()].sort((a, b) => b[1] - a[1]);
  const max = Math.max(...topWords.map((x) => x[1]), 1);

  cloud.innerHTML = "";
  topWords.forEach(([word, count]) => {
    const span = document.createElement("span");
    const size = 0.78 + (count / max) * 1.2;
    span.style.fontSize = `${size}rem`;
    span.textContent = `${word} (${count})`;
    cloud.appendChild(span);
  });

  const toggle = $("wcIntersectionToggle");
  if (toggle) {
    toggle.disabled = !canIntersect;
  }
}

function renderPanel5() {
  const summary = $("sparsitySummary");
  const bars = $("sparsityBars");

  const total = state.rows.length || 1;
  const withAsset = state.rows.filter((r) => r.asset_id).length;
  const withoutAsset = total - withAsset;

  summary.textContent = `${withAsset}/${total} tickets include ASSET_ID (${formatPct(withAsset / total)}).`;

  const byBuilding = new Map();
  state.rows.forEach((r) => {
    const b = r.building || "Unknown";
    if (!byBuilding.has(b)) byBuilding.set(b, { total: 0, withAsset: 0 });
    const cur = byBuilding.get(b);
    cur.total += 1;
    if (r.asset_id) cur.withAsset += 1;
  });

  const items = [...byBuilding.entries()]
    .map(([label, v]) => ({ label, value: Number((v.withAsset / v.total).toFixed(3)) }))
    .sort((a, b) => a.value - b.value);

  bars.innerHTML = "";
  items.forEach((i) => {
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `<div>${i.label}</div><div class="bar-fill" style="width:${i.value * 100}%; background:linear-gradient(90deg, #b8d8ba, #2a9d8f);"></div><div>${formatPct(i.value)}</div>`;
    bars.appendChild(row);
  });

  const overall = document.createElement("div");
  overall.className = "bar-row";
  overall.innerHTML = `<div>Overall Missing</div><div class="bar-fill" style="width:${(withoutAsset / total) * 100}%; background:linear-gradient(90deg, #f4a261, #e76f51);"></div><div>${formatPct(withoutAsset / total)}</div>`;
  bars.prepend(overall);
}

function renderPanel6() {
  const summary = $("outlierSummary");
  const tbody = $("outlierTable");

  const descLengths = state.rows.map((r) => (r.description || "").length);
  const scores = state.rows.map((r) => r.survey_score || 0);

  const mean = (arr) => (arr.length ? arr.reduce((s, x) => s + x, 0) / arr.length : 0);
  const std = (arr, m) => {
    if (!arr.length) return 1;
    const v = arr.reduce((s, x) => s + (x - m) ** 2, 0) / arr.length;
    return Math.sqrt(v) || 1;
  };

  const mLen = mean(descLengths);
  const sdLen = std(descLengths, mLen);
  const nonZeroScores = scores.filter((x) => x > 0);
  const mScore = mean(nonZeroScores);
  const sdScore = std(nonZeroScores, mScore);

  const ranked = state.rows
    .map((r) => {
      const zLen = Math.abs(((r.description || "").length - mLen) / sdLen);
      const zScore = r.survey_score > 0 ? Math.abs((r.survey_score - mScore) / sdScore) : 0;
      const noAssetPenalty = r.asset_id ? 0 : 0.75;
      return {
        r,
        score: zLen + zScore + noAssetPenalty,
      };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, 10);

  summary.textContent = "Temporary outlier heuristic = |z(description length)| + |z(survey)| + missing-asset penalty.";

  tbody.innerHTML = "";
  ranked.forEach((x) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${x.r.ticket_id || "n/a"}</td><td>${x.r.asset_id || "missing"}</td><td>${x.r.building || "n/a"}</td><td>${x.score.toFixed(2)}</td>`;
    tbody.appendChild(tr);
  });
}

function render() {
  renderPanel1();
  renderPanel2();
  renderPanel3();
  renderPanel4();
  renderPanel5();
  renderPanel6();
}

async function loadFileToRawRows(file, target) {
  const text = await file.text();
  state[target] = parseCsv(text);
  refreshRowsFromLoadedFiles();
}

function setupEvents() {
  $("xDaysInput").addEventListener("change", async (e) => {
    state.days = Number(e.target.value || 90);
    await loadPanel1FromApi();
  });

  $("refreshBtn").addEventListener("click", async () => {
    render();
    await loadPanel1FromApi();
  });

  $("keywordBtn").addEventListener("click", () => {
    state.keyword = $("keywordInput").value;
    renderPanel4();
  });

  $("keywordInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      state.keyword = e.target.value;
      renderPanel4();
    }
  });
  
  $("ticketsCsvInput").addEventListener("change", (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    state.files.tickets = file;
  });

  $("assetsCsvInput").addEventListener("change", (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    state.files.assets = file;
  });

  $("spaceCsvInput").addEventListener("change", (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    state.files.space = file;
  });

  $("wcRunBtn").addEventListener("click", async () => {
    const summary = $("keywordSummary");
    try {
      summary.textContent = "Computing word cloud...";
      const apiData = await fetchWordCloudFromApi();

      state.panel4Rows = normalizeApiTicketRows(apiData.ticketRows);

      // optionally respect whatever is currently typed in the keyword box
      state.keyword = $("keywordInput").value || "";
      state.wordCloudIntersection = $("wcIntersectionToggle").checked;
      renderPanel4();

      const groupCol = $("wcGroupCol").value.trim();
      const groupValue = $("wcGroupValue").value.trim();

      if (!groupCol) {
        summary.textContent = `Loaded ${state.panel4Rows.length} tickets and word cloud.`;
      } else if (groupValue) {
        summary.textContent = `Loaded ${state.panel4Rows.length} tickets for ${groupCol} = ${groupValue}.`;
      } else {
        summary.textContent = `Loaded ${state.panel4Rows.length} tickets for ${groupCol}.`;
      }
    } catch (e) {
      console.error(e);
      summary.textContent = `Word cloud API failed: ${e.message}`;
    }
  });

  $("wcIntersectionToggle").addEventListener("change", (e) => {
    state.wordCloudIntersection = e.target.checked;
    renderPanel4();
  });

  $("panel1PrevBtn").addEventListener("click", () => {
    if (state.panel1.page > 1) {
      state.panel1.page -= 1;
      renderPanel1();
    }
  });

$("panel1NextBtn").addEventListener("click", () => {
    const totalPages = getTotalPages(state.panel1.rows, state.panel1.pageSize);
    if (state.panel1.page < totalPages) {
      state.panel1.page += 1;
      renderPanel1();
    }
  });
}


setupEvents();
state.rawAssetsRows = parseCsv(sampleAssetsCsv);
state.rawSurveyRows = parseCsv(sampleSurveyCsv);
refreshRowsFromLoadedFiles();
