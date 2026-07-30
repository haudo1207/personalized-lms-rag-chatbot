"use strict";

const LEVEL_LABELS = { beginner: "Mới bắt đầu", intermediate: "Trung bình", advanced: "Nâng cao" };
const LS_USER = "rag_current_user_id";
const LS_COURSE = "rag_current_course_id";

const state = {
  users: [],
  courses: [],
  documents: [],
  currentUserId: null,
  currentCourseId: null,
  chatThreads: {},
  hydratedKeys: new Set(),
  quiz: null,
  quizDifficulty: "easy",
  quizTopic: "SQL JOIN",
  quizReview: null,
  profile: null,
  dashboard: null,
  dashboardKey: null,
};

// ----------------------------------------------------------------------------
// API CLIENT
// ----------------------------------------------------------------------------
async function api(method, path, { json, form, params } = {}) {
  let url = path;
  if (params) {
    const qs = new URLSearchParams(params).toString();
    url += (url.includes("?") ? "&" : "?") + qs;
  }
  const opts = { method };
  if (json !== undefined) {
    opts.headers = { "Content-Type": "application/json" };
    opts.body = JSON.stringify(json);
  } else if (form !== undefined) {
    opts.body = form;
  }
  try {
    const res = await fetch(url, opts);
    let data = null;
    try {
      data = await res.json();
    } catch (e) {
      data = null;
    }
    return { ok: res.ok, status: res.status, data };
  } catch (err) {
    return { ok: false, status: null, data: { detail: "Không kết nối được backend API: " + err } };
  }
}

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderMarkdown(text) {
  const safe = escapeHtml(text);
  try {
    return marked.parse(safe);
  } catch (e) {
    return safe.replace(/\n/g, "<br>");
  }
}

function showToast(message, kind = "error") {
  const root = document.getElementById("toast-root");
  const el = document.createElement("div");
  el.className = `toast toast-${kind}`;
  el.textContent = message;
  root.appendChild(el);
  requestAnimationFrame(() => el.classList.add("show"));
  setTimeout(() => {
    el.classList.remove("show");
    setTimeout(() => el.remove(), 300);
  }, 5000);
}

function showApiError(action, payload, status) {
  let label = `${action} thất bại`;
  if (status) label += ` (HTTP ${status})`;
  let detail = "";
  if (payload && typeof payload === "object" && payload.detail) detail = payload.detail;
  else if (payload) detail = String(payload);
  showToast(detail ? `${label}: ${detail}` : label, "error");
}

// ----------------------------------------------------------------------------
// DATA LOADING
// ----------------------------------------------------------------------------
async function loadUsers() {
  const { ok, data } = await api("GET", "/users/");
  state.users = ok && Array.isArray(data) ? data : [];
}
async function loadCourses() {
  const { ok, data } = await api("GET", "/courses/");
  state.courses = ok && Array.isArray(data) ? data : [];
}
async function loadDocuments() {
  const { ok, data } = await api("GET", "/documents/");
  state.documents = ok && Array.isArray(data) ? data : [];
}

function getCurrentUser() {
  return state.users.find((u) => u.id === state.currentUserId) || null;
}
function getCurrentCourse() {
  return state.courses.find((c) => c.id === state.currentCourseId) || null;
}
function persistSelection() {
  if (state.currentUserId) localStorage.setItem(LS_USER, String(state.currentUserId));
  if (state.currentCourseId) localStorage.setItem(LS_COURSE, String(state.currentCourseId));
}
function threadKey() {
  return `${state.currentUserId}:${state.currentCourseId}`;
}

// ----------------------------------------------------------------------------
// SIDEBAR: USER / COURSE PICKERS
// ----------------------------------------------------------------------------
function renderUserSelect() {
  const sel = document.getElementById("user-select");
  if (!state.users.length) {
    sel.innerHTML = `<option value="">Chưa có người dùng nào</option>`;
    state.currentUserId = null;
    renderLevelControl();
    return;
  }
  sel.innerHTML = state.users
    .map((u) => `<option value="${u.id}">${escapeHtml(u.full_name)} (${escapeHtml(u.email)})</option>`)
    .join("");
  if (!state.users.some((u) => u.id === state.currentUserId)) {
    state.currentUserId = state.users[0].id;
  }
  sel.value = String(state.currentUserId);
  renderLevelControl();
}

function renderLevelControl() {
  const row = document.getElementById("level-row");
  const user = getCurrentUser();
  if (!user) {
    row.classList.add("hidden");
    return;
  }
  row.classList.remove("hidden");
  document.querySelectorAll("#level-segmented button").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.level === user.level);
  });
}

function renderCourseSelect() {
  const sel = document.getElementById("course-select");
  if (!state.courses.length) {
    sel.innerHTML = `<option value="">Chưa có môn học nào</option>`;
    state.currentCourseId = null;
    return;
  }
  sel.innerHTML = state.courses
    .map((c) => `<option value="${c.id}">${escapeHtml(c.course_code)} — ${escapeHtml(c.course_name)}</option>`)
    .join("");
  if (!state.courses.some((c) => c.id === state.currentCourseId)) {
    state.currentCourseId = state.courses[0].id;
  }
  sel.value = String(state.currentCourseId);
}

function updateGate() {
  const gate = document.getElementById("gate-overlay");
  const ready = !!(getCurrentUser() && getCurrentCourse());
  gate.classList.toggle("hidden", ready);
}

// ----------------------------------------------------------------------------
// CHAT
// ----------------------------------------------------------------------------
async function ensureThreadHydrated() {
  const key = threadKey();
  if (!state.chatThreads[key]) state.chatThreads[key] = [];
  if (state.hydratedKeys.has(key)) return;
  if (state.currentUserId && state.currentCourseId) {
    const { ok, data } = await api("GET", `/chat/history/${state.currentUserId}`);
    if (ok && Array.isArray(data)) {
      const rows = data.filter((r) => Number(r.course_id) === Number(state.currentCourseId));
      rows.sort((a, b) => String(a.created_at).localeCompare(String(b.created_at)));
      for (const row of rows) {
        state.chatThreads[key].push({ role: "user", content: row.question });
        let sources = [];
        try {
          sources = row.sources ? JSON.parse(row.sources) : [];
        } catch (e) {
          sources = [];
        }
        state.chatThreads[key].push({
          role: "assistant",
          content: row.answer,
          topic: row.topic,
          latency: row.latency,
          sources,
        });
      }
    }
  }
  state.hydratedKeys.add(key);
}

function renderSourcesHtml(sources) {
  const items = sources
    .map((s) => {
      const dist = s.distance;
      let simBar = "";
      if (dist !== undefined && dist !== null) {
        const sim = Math.max(0, 1 - Number(dist));
        simBar = `<div class="sim-bar"><div class="sim-bar-fill" style="width:${Math.min(100, sim * 100)}%"></div><span>🎯 ${(sim * 100).toFixed(1)}%</span></div>`;
      }
      return `<div class="source-card">
        <div class="source-title">📄 <b>${escapeHtml(s.document_name || "Tài liệu học tập")}</b> — Trang ${escapeHtml(s.page ?? "?")}</div>
        ${simBar}
        <div class="source-content">"${escapeHtml(s.content || "")}"</div>
      </div>`;
    })
    .join("");
  return `<details class="sources-toggle"><summary>🔗 ${sources.length} nguồn trích dẫn</summary>${items}</details>`;
}

function messageHtml(msg) {
  if (msg.role === "user") {
    return `<div class="msg msg-user"><div class="bubble">${escapeHtml(msg.content)}</div></div>`;
  }
  const metaBits = [];
  if (msg.topic) metaBits.push(`📌 ${escapeHtml(msg.topic)}`);
  if (msg.latency) metaBits.push(`⚡ ${escapeHtml(msg.latency)}s`);
  const meta = metaBits.length ? `<div class="msg-meta">${metaBits.join(" · ")}</div>` : "";
  const weak = msg.weak_topic
    ? `<div class="msg-warning">⚠️ Bạn đang gặp khó khăn ở chủ đề <b>${escapeHtml(msg.weak_topic)}</b>.</div>`
    : "";
  const sources = msg.sources && msg.sources.length ? renderSourcesHtml(msg.sources) : "";
  return `<div class="msg msg-assistant"><div class="bubble">${renderMarkdown(msg.content)}</div>${meta}${weak}${sources}</div>`;
}

function renderChatWindow() {
  const win = document.getElementById("chat-window");
  const key = threadKey();
  const thread = state.chatThreads[key] || [];
  if (!thread.length) {
    win.innerHTML = `<div class="empty-hint">Chưa có hội thoại nào trong môn học này. Hãy đặt câu hỏi bên dưới!</div>`;
  } else {
    win.innerHTML = thread.map(messageHtml).join("");
  }
  win.scrollTop = win.scrollHeight;
  const course = getCurrentCourse();
  document.getElementById("chat-course-name").textContent = course ? `— ${course.course_name}` : "";
}

async function openChatPage() {
  await ensureThreadHydrated();
  renderChatWindow();
}

async function sendChatMessage(question) {
  if (!question || !question.trim() || !state.currentUserId || !state.currentCourseId) return;
  await ensureThreadHydrated();
  const key = threadKey();
  const thread = state.chatThreads[key];
  thread.push({ role: "user", content: question });
  renderChatWindow();

  const win = document.getElementById("chat-window");
  const typingId = "typing-" + Math.random().toString(36).slice(2);
  win.insertAdjacentHTML(
    "beforeend",
    `<div class="msg msg-assistant" id="${typingId}"><div class="bubble typing"><span></span><span></span><span></span></div></div>`
  );
  win.scrollTop = win.scrollHeight;

  const topK = Number(document.getElementById("topk-slider").value) || 3;
  const filterIds = [...document.querySelectorAll("#doc-filter-list input:checked")].map((el) => Number(el.value));

  const { ok, data } = await api("POST", "/chat/", {
    json: {
      user_id: state.currentUserId,
      course_id: state.currentCourseId,
      question,
      top_k: topK,
      document_ids: filterIds.length ? filterIds : null,
    },
  });

  document.getElementById(typingId)?.remove();

  if (ok && data) {
    thread.push({
      role: "assistant",
      content: data.answer || "",
      topic: data.topic,
      latency: data.latency,
      weak_topic: data.weak_topic,
      sources: data.sources || [],
    });
  } else {
    const detail = data && typeof data === "object" && data.detail ? data.detail : data;
    thread.push({ role: "assistant", content: `⚠️ Không lấy được câu trả lời: ${detail}` });
  }
  renderChatWindow();
}

function renderDocFilterList() {
  const wrap = document.getElementById("doc-filter-list");
  const courseDocs = state.documents.filter((d) => Number(d.course_id) === Number(state.currentCourseId));
  if (!courseDocs.length) {
    wrap.innerHTML = `<p class="muted small">Chưa có tài liệu nào để lọc.</p>`;
    return;
  }
  wrap.innerHTML = courseDocs
    .map(
      (d) => `<label class="checkbox-row"><input type="checkbox" value="${d.id}"> #${d.id} - ${escapeHtml(d.file_name)}</label>`
    )
    .join("");
}

// ----------------------------------------------------------------------------
// DOCUMENTS
// ----------------------------------------------------------------------------
function statusBadgeHtml(status) {
  if (status === "indexed") return `<span class="badge ok">🟢 Sẵn sàng</span>`;
  return `<span class="badge error">🔴 Lỗi xử lý</span>`;
}

function renderDocList() {
  const course = getCurrentCourse();
  document.getElementById("docs-course-name").textContent = course ? `— ${course.course_name}` : "";
  const courseDocs = state.documents.filter((d) => Number(d.course_id) === Number(state.currentCourseId));
  const wrap = document.getElementById("doc-list");
  if (!courseDocs.length) {
    wrap.innerHTML = `<p class="muted">Chưa có tài liệu nào được upload cho môn học này.</p>`;
    return;
  }
  wrap.innerHTML = courseDocs
    .map(
      (d) => `<div class="doc-card">
        <div class="doc-info">
          <div class="doc-name">📄 ${escapeHtml(d.file_name)}</div>
          <div class="muted small">ID #${d.id} · Ngày tải lên: ${escapeHtml(String(d.uploaded_at || "").slice(0, 10))}</div>
          ${d.status !== "indexed" ? '<div class="muted small">Có thể là file ảnh/scan không có chữ.</div>' : ""}
        </div>
        <div class="doc-status">${statusBadgeHtml(d.status)}</div>
        <div class="doc-actions">
          ${d.status !== "indexed" ? `<button class="btn btn-ghost btn-sm retry-btn" data-id="${d.id}" type="button">🔁 Thử lại</button>` : ""}
        </div>
      </div>`
    )
    .join("");
  wrap.querySelectorAll(".retry-btn").forEach((btn) => {
    btn.addEventListener("click", () => retryIndex(btn.dataset.id));
  });
}

async function retryIndex(docId) {
  const { ok, data, status } = await api("POST", `/documents/${docId}/index`);
  if (ok) {
    showToast("Đã xử lý xong!", "success");
    await loadDocuments();
    renderDocList();
    renderDocFilterList();
  } else {
    showApiError("Thử lại", data, status);
  }
}

let selectedUploadFile = null;
function updateUploadUI() {
  const selectedLabel = document.getElementById("upload-selected");
  const uploadBtn = document.getElementById("upload-btn");
  if (selectedUploadFile) {
    selectedLabel.textContent = `📎 Đã chọn: ${selectedUploadFile.name}`;
    selectedLabel.classList.remove("hidden");
    uploadBtn.disabled = false;
  } else {
    selectedLabel.classList.add("hidden");
    uploadBtn.disabled = true;
  }
}

function setupUpload() {
  const dz = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const browseBtn = document.getElementById("browse-btn");
  const uploadBtn = document.getElementById("upload-btn");

  browseBtn.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => {
    selectedUploadFile = fileInput.files[0] || null;
    updateUploadUI();
  });

  ["dragover", "dragenter"].forEach((evt) =>
    dz.addEventListener(evt, (e) => {
      e.preventDefault();
      dz.classList.add("drag");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    dz.addEventListener(evt, (e) => {
      e.preventDefault();
      dz.classList.remove("drag");
    })
  );
  dz.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) {
      selectedUploadFile = file;
      updateUploadUI();
    }
  });

  uploadBtn.addEventListener("click", async () => {
    if (!selectedUploadFile || !state.currentUserId || !state.currentCourseId) return;
    uploadBtn.disabled = true;
    uploadBtn.textContent = "Đang xử lý...";
    const form = new FormData();
    form.append("course_id", state.currentCourseId);
    form.append("user_id", state.currentUserId);
    form.append("file", selectedUploadFile);
    const { ok, data, status } = await api("POST", "/documents/upload", { form });
    uploadBtn.textContent = "Tải lên & Đánh chỉ mục";
    if (ok) {
      showToast(`✅ '${selectedUploadFile.name}' đã sẵn sàng để Chatbot trả lời (${data.chunks} đoạn văn bản).`, "success");
      selectedUploadFile = null;
      fileInput.value = "";
      updateUploadUI();
      await loadDocuments();
      renderDocList();
      renderDocFilterList();
    } else {
      showApiError("Upload tài liệu", data, status);
      uploadBtn.disabled = false;
    }
  });
}

// ----------------------------------------------------------------------------
// QUIZ
// ----------------------------------------------------------------------------
function renderQuizBody() {
  const wrap = document.getElementById("quiz-body");
  if (!state.quiz || !state.quiz.length) {
    wrap.innerHTML = "";
    return;
  }
  if (state.quizReview) {
    renderQuizReview(wrap);
    return;
  }
  wrap.innerHTML =
    state.quiz
      .map((item, idx) => {
        const options = item.options || {};
        const optHtml = Object.entries(options)
          .filter(([k]) => ["A", "B", "C", "D"].includes(k))
          .map(([k, v]) => `<button type="button" class="quiz-option" data-q="${idx}" data-key="${k}">${k}. ${escapeHtml(v)}</button>`)
          .join("");
        const explanation = item.explanation
          ? `<details class="explanation"><summary>💡 Xem giải thích</summary><p>${escapeHtml(item.explanation)}</p></details>`
          : "";
        return `<div class="quiz-question" data-idx="${idx}">
          <div class="quiz-q-title">Câu ${idx + 1}: ${escapeHtml(item.question || "")}</div>
          <div class="quiz-options">${optHtml}</div>
          ${explanation}
        </div>`;
      })
      .join("") + `<button id="quiz-submit-btn" class="btn btn-primary" type="button">📥 Nộp bài Quiz</button>`;

  wrap.querySelectorAll(".quiz-option").forEach((btn) => {
    btn.addEventListener("click", () => {
      const qIdx = btn.dataset.q;
      wrap.querySelectorAll(`.quiz-option[data-q="${qIdx}"]`).forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
    });
  });
  document.getElementById("quiz-submit-btn").addEventListener("click", submitQuiz);
}

async function submitQuiz() {
  const wrap = document.getElementById("quiz-body");
  const review = [];
  let correctCount = 0;
  state.quiz.forEach((item, idx) => {
    const selectedBtn = wrap.querySelector(`.quiz-option[data-q="${idx}"].selected`);
    const selected = selectedBtn ? selectedBtn.dataset.key : null;
    const correct = String(item.correct_answer || "").trim().toUpperCase();
    const isCorrect = selected === correct;
    if (isCorrect) correctCount++;
    review.push({ question: item.question, options: item.options || {}, selected, correct, is_correct: isCorrect });
  });
  const total = review.length;
  const { ok, data, status } = await api("POST", "/quiz/submit", {
    json: {
      user_id: state.currentUserId,
      course_id: state.currentCourseId,
      topic: state.quizTopic,
      total_questions: total,
      correct_answers: correctCount,
    },
  });
  state.quizReview = review;
  state.dashboardKey = null;
  if (!ok) showApiError("Lưu kết quả Quiz", data, status);
  renderQuizBody();
}

function renderQuizReview(wrap) {
  const total = state.quizReview.length;
  const correct = state.quizReview.filter((r) => r.is_correct).length;
  const pct = total ? Math.round((correct / total) * 100) : 0;
  let html = `<div class="quiz-result-banner">🏆 Kết quả bài làm: <b>${correct}/${total}</b> câu đúng (${pct}%)</div>`;
  state.quizReview.forEach((r, idx) => {
    const icon = r.is_correct ? "✅" : "❌";
    const optsHtml = Object.entries(r.options)
      .map(([k, v]) => {
        let cls = "";
        let suffix = "";
        if (k === r.correct) {
          cls = "correct";
          suffix = " ✅ (đáp án đúng)";
        } else if (k === r.selected) {
          cls = "incorrect";
          suffix = " ❌ (bạn đã chọn)";
        }
        return `<div class="quiz-review-option ${cls}">${k}. ${escapeHtml(v)}${suffix}</div>`;
      })
      .join("");
    html += `<div class="quiz-question"><div class="quiz-q-title">${icon} Câu ${idx + 1}: ${escapeHtml(r.question)}</div>${optsHtml}</div>`;
  });
  wrap.innerHTML = html;
}

function setupQuizControls() {
  document.querySelectorAll("#quiz-difficulty button").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.quizDifficulty = btn.dataset.value;
      document.querySelectorAll("#quiz-difficulty button").forEach((b) => b.classList.toggle("active", b === btn));
    });
  });

  document.getElementById("quiz-generate-btn").addEventListener("click", async () => {
    if (!state.currentUserId || !state.currentCourseId) return;
    const topic = document.getElementById("quiz-topic").value.trim() || "SQL JOIN";
    const count = Number(document.getElementById("quiz-count").value) || 5;
    const btn = document.getElementById("quiz-generate-btn");
    btn.disabled = true;
    btn.textContent = "🤖 Đang tạo câu hỏi...";
    const { ok, data, status } = await api("POST", "/quiz/generate", {
      json: {
        user_id: state.currentUserId,
        course_id: state.currentCourseId,
        topic,
        num_questions: count,
        difficulty: state.quizDifficulty,
      },
    });
    btn.disabled = false;
    btn.textContent = "🎯 Tạo bài Quiz mới";
    if (ok && data) {
      state.quiz = data.quiz;
      state.quizTopic = topic;
      state.quizReview = null;
      showToast(`🎉 Tạo Quiz thành công! (Độ khó thích ứng: ${String(data.adaptive_difficulty || "easy").toUpperCase()})`, "success");
    } else {
      state.quiz = null;
      showApiError("Tạo Quiz", data, status);
    }
    renderQuizBody();
  });
}

// ----------------------------------------------------------------------------
// DASHBOARD
// ----------------------------------------------------------------------------
let chartTopics = null;
let chartScores = null;

async function maybeLoadDashboard(force = false) {
  if (!state.currentUserId || !state.currentCourseId) return;
  const key = `${state.currentUserId}:${state.currentCourseId}`;
  if (!force && state.dashboardKey === key) return;
  const [profRes, dashRes] = await Promise.all([
    api("GET", `/chat/profile/${state.currentUserId}/${state.currentCourseId}`),
    api("GET", `/dashboard/student/${state.currentUserId}`, { params: { course_id: state.currentCourseId } }),
  ]);
  state.profile = profRes.ok && profRes.data ? profRes.data : {};
  state.dashboard = dashRes.ok && dashRes.data ? dashRes.data : {};
  state.dashboardKey = key;
  if (!dashRes.ok) showApiError("Tải Dashboard", dashRes.data, dashRes.status);
  renderDashboard();
}

function renderDashboard() {
  const profile = state.profile || {};
  const profCard = document.getElementById("profile-card");
  if (profile && profile.full_name) {
    profCard.innerHTML = `
      <div class="profile-avatar">${escapeHtml((profile.full_name || "?").slice(0, 1).toUpperCase())}</div>
      <div>
        <div class="profile-name">${escapeHtml(profile.full_name)}</div>
        <div style="opacity:0.9">Trình độ: ${escapeHtml(LEVEL_LABELS[profile.level] || profile.level || "—")} · ${(profile.recent_questions || []).length} câu hỏi gần đây</div>
      </div>`;
  } else {
    profCard.innerHTML = "";
  }

  const dash = state.dashboard || {};
  const avg = dash.average_quiz_score;
  const weakCount = (dash.weak_topics || []).length;
  document.getElementById("metrics-row").innerHTML = `
    <div class="metric-card"><div class="metric-label">Tổng câu hỏi đã đặt</div><div class="metric-value">${dash.total_questions ?? 0}</div></div>
    <div class="metric-card"><div class="metric-label">Điểm Quiz Trung bình</div><div class="metric-value">${avg !== null && avg !== undefined ? avg + "%" : "N/A"}</div></div>
    <div class="metric-card ${weakCount ? "metric-warn" : ""}"><div class="metric-label">Chủ đề còn yếu</div><div class="metric-value">${weakCount} topic</div></div>
  `;

  renderTopicsChart(dash.questions_by_topic || {});
  renderScoresChart(dash.quiz_results || []);

  const weakList = document.getElementById("weak-topics-list");
  const weakTopics = dash.weak_topics || [];
  weakList.innerHTML = weakTopics.length
    ? weakTopics
        .map((wt) => `<div class="info-card warn"><b>🔴 Chủ đề: ${escapeHtml(wt.topic)}</b><div class="muted small">${escapeHtml(wt.reason || "")}</div></div>`)
        .join("")
    : `<div class="muted">🎉 Bạn chưa có chủ đề yếu nào!</div>`;

  const recList = document.getElementById("recommendations-list");
  const recs = dash.recommendations || [];
  recList.innerHTML = recs.length
    ? recs
        .map(
          (r) =>
            `<div class="info-card"><b>💡 Gợi ý học tập: ${escapeHtml(r.topic)}</b><div class="small">${escapeHtml(r.recommendation || "").replace(/\n/g, "<br>")}</div></div>`
        )
        .join("")
    : `<div class="muted">Chưa có gợi ý bài tập cụ thể.</div>`;
}

function renderTopicsChart(data) {
  const ctx = document.getElementById("chart-topics");
  const labels = Object.keys(data);
  const values = Object.values(data);
  if (chartTopics) chartTopics.destroy();
  if (!labels.length) return;
  chartTopics = new Chart(ctx, {
    type: "bar",
    data: { labels, datasets: [{ label: "Số lượng", data: values, backgroundColor: "#7c3aed", borderRadius: 6 }] },
    options: {
      indexAxis: "y",
      plugins: { legend: { display: false } },
      scales: { x: { beginAtZero: true, ticks: { precision: 0 } } },
    },
  });
}

function renderScoresChart(results) {
  const ctx = document.getElementById("chart-scores");
  const sorted = [...results].sort((a, b) => String(a.created_at).localeCompare(String(b.created_at)));
  const labels = sorted.map((r) => String(r.created_at).slice(0, 16).replace("T", " "));
  const values = sorted.map((r) => Number(r.score));
  if (chartScores) chartScores.destroy();
  if (!labels.length) return;
  chartScores = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Điểm số (%)",
          data: values,
          borderColor: "#4f46e5",
          backgroundColor: "rgba(79,70,229,0.15)",
          fill: true,
          tension: 0.3,
          pointRadius: 4,
        },
      ],
    },
    options: { scales: { y: { min: 0, max: 100 } }, plugins: { legend: { display: false } } },
  });
}

// ----------------------------------------------------------------------------
// NAVIGATION
// ----------------------------------------------------------------------------
function switchPage(page) {
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  document.getElementById(`page-${page}`).classList.add("active");
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.page === page));
  if (page === "chat") openChatPage();
  if (page === "docs") renderDocList();
  if (page === "dashboard") maybeLoadDashboard();
}

// ----------------------------------------------------------------------------
// HEALTH CHECK
// ----------------------------------------------------------------------------
async function checkHealth() {
  const { ok } = await api("GET", "/health");
  document.getElementById("api-status").classList.toggle("ok", ok);
  document.getElementById("api-status").classList.toggle("error", !ok);
  document.getElementById("api-status-text").textContent = ok ? "API Backend: Connected" : "API Backend: Disconnected";
}

// ----------------------------------------------------------------------------
// EVENT WIRING
// ----------------------------------------------------------------------------
function setupSidebarEvents() {
  document.getElementById("user-select").addEventListener("change", (e) => {
    state.currentUserId = Number(e.target.value) || null;
    persistSelection();
    renderLevelControl();
    updateGate();
    onSelectionChanged();
  });

  document.getElementById("course-select").addEventListener("change", (e) => {
    state.currentCourseId = Number(e.target.value) || null;
    persistSelection();
    updateGate();
    renderDocFilterList();
    onSelectionChanged();
  });

  document.getElementById("btn-new-user").addEventListener("click", () => {
    document.getElementById("new-user-form").classList.toggle("hidden");
  });
  document.getElementById("submit-new-user").addEventListener("click", async () => {
    const name = document.getElementById("new-user-name").value.trim();
    const email = document.getElementById("new-user-email").value.trim();
    const level = document.getElementById("new-user-level").value;
    if (!name || !email) {
      showToast("Nhập đầy đủ họ tên & email.", "error");
      return;
    }
    const { ok, data, status } = await api("POST", "/users/", { json: { full_name: name, email, role: "student", level } });
    if (ok && data) {
      await loadUsers();
      state.currentUserId = data.id;
      renderUserSelect();
      persistSelection();
      updateGate();
      document.getElementById("new-user-form").classList.add("hidden");
      document.getElementById("new-user-name").value = "";
      document.getElementById("new-user-email").value = "";
      showToast("Đã tạo người dùng!", "success");
      onSelectionChanged();
    } else {
      showApiError("Tạo người dùng", data, status);
    }
  });

  document.getElementById("btn-new-course").addEventListener("click", () => {
    document.getElementById("new-course-form").classList.toggle("hidden");
  });
  document.getElementById("submit-new-course").addEventListener("click", async () => {
    const code = document.getElementById("new-course-code").value.trim();
    const name = document.getElementById("new-course-name").value.trim();
    const desc = document.getElementById("new-course-desc").value.trim();
    if (!code || !name) {
      showToast("Nhập đầy đủ mã và tên môn học.", "error");
      return;
    }
    const { ok, data, status } = await api("POST", "/courses/", {
      json: { course_code: code, course_name: name, description: desc || null },
    });
    if (ok && data) {
      await loadCourses();
      state.currentCourseId = data.id;
      renderCourseSelect();
      persistSelection();
      updateGate();
      document.getElementById("new-course-form").classList.add("hidden");
      document.getElementById("new-course-code").value = "";
      document.getElementById("new-course-name").value = "";
      document.getElementById("new-course-desc").value = "";
      showToast("Đã tạo môn học!", "success");
      onSelectionChanged();
    } else {
      showApiError("Tạo môn học", data, status);
    }
  });

  document.getElementById("level-segmented").addEventListener("click", async (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;
    const user = getCurrentUser();
    if (!user || btn.dataset.level === user.level) return;
    const { ok, data, status } = await api("PATCH", `/users/${user.id}/level`, { params: { level: btn.dataset.level } });
    if (ok) {
      await loadUsers();
      renderLevelControl();
    } else {
      showApiError("Cập nhật trình độ", data, status);
    }
  });

  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => switchPage(btn.dataset.page));
  });
}

function onSelectionChanged() {
  const activePage = document.querySelector(".nav-item.active")?.dataset.page || "chat";
  renderDocFilterList();
  if (activePage === "chat") openChatPage();
  if (activePage === "docs") renderDocList();
  if (activePage === "dashboard") maybeLoadDashboard();
}

function setupChatEvents() {
  const input = document.getElementById("chat-input");
  document.getElementById("chat-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const q = input.value;
    input.value = "";
    input.style.height = "auto";
    sendChatMessage(q);
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      document.getElementById("chat-form").requestSubmit();
    }
  });
  input.addEventListener("input", (e) => {
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + "px";
  });
  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => sendChatMessage(chip.dataset.prompt));
  });
  document.getElementById("chat-options-btn").addEventListener("click", () => {
    document.getElementById("chat-options-panel").classList.toggle("hidden");
  });
  document.getElementById("topk-slider").addEventListener("input", (e) => {
    document.getElementById("topk-value").textContent = e.target.value;
  });
}

function setupDashboardEvents() {
  document.getElementById("dashboard-refresh-btn").addEventListener("click", () => maybeLoadDashboard(true));
}

// ----------------------------------------------------------------------------
// INIT
// ----------------------------------------------------------------------------
async function init() {
  state.currentUserId = Number(localStorage.getItem(LS_USER)) || null;
  state.currentCourseId = Number(localStorage.getItem(LS_COURSE)) || null;

  await Promise.all([loadUsers(), loadCourses(), loadDocuments()]);
  renderUserSelect();
  renderCourseSelect();
  persistSelection();
  updateGate();
  renderDocFilterList();

  setupSidebarEvents();
  setupChatEvents();
  setupQuizControls();
  setupDashboardEvents();
  setupUpload();

  await openChatPage();
  checkHealth();
}

document.addEventListener("DOMContentLoaded", init);
