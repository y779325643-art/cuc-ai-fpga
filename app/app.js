const samples = {
  uart_fifo_loopback: {
    projectName: "uart_fifo_demo", width: 8,
    requirement: "生成一个 UART FIFO 回环 FPGA 工程。接收端将串行数据写入同步 FIFO，发送端在数据可用时读出并回传。",
  },
  fifo: {
    projectName: "sync_fifo_demo", width: 8,
    requirement: "生成一个同步 FIFO 工程，包含读写使能、满空标志、溢出保护和下溢保护。",
  },
  counter: {
    projectName: "counter_demo", width: 8,
    requirement: "生成一个带使能和复位的参数化计数器工程。",
  },
  composed_event_counter: {
    projectName: "event_counter_demo", width: 8,
    requirement: "生成一个事件门控计数器工程：有效事件通过门控模块后驱动计数核心，并输出计数值。",
  },
  pwm_controller: {
    projectName: "pwm_demo", width: 8,
    requirement: "生成一个带使能和复位的 PWM 控制器，根据占空比输入输出 PWM 信号。",
  },
};

const elements = {
  toast: document.querySelector("#toast"), form: document.querySelector("#generateForm"),
  button: document.querySelector("#generateBtn"), backendStatus: document.querySelector("#backendStatus"),
  projectName: document.querySelector("#projectName"), topModule: document.querySelector("#topModule"),
  taskType: document.querySelector("#taskType"), width: document.querySelector("#dataWidth"),
  clockMHz: document.querySelector("#clockMHz"), resetPolarity: document.querySelector("#resetPolarity"),
  interfaceSpec: document.querySelector("#interfaceSpec"), ioSpec: document.querySelector("#ioSpec"),
  targetPlatform: document.querySelector("#targetPlatform"), verificationIntent: document.querySelector("#verificationIntent"),
  requirement: document.querySelector("#projectSpec"),
  taskField: document.querySelector("#taskField"), methodCondition: document.querySelector("#methodCondition"),
  methodMode: document.querySelector("#methodMode"),
  passLevel: document.querySelector("#passLevel"), artifactPath: document.querySelector("#artifactPath"),
  fileList: document.querySelector("#fileList"), output: document.querySelector("#projectOutput"),
  stageGrid: document.querySelector("#stageGrid"), stageHelp: document.querySelector("#stageHelp"),
  ambiguityButton: document.querySelector("#checkAmbiguityBtn"),
  ambiguityStatus: document.querySelector("#ambiguityStatus"),
  ambiguityList: document.querySelector("#ambiguityList"),
  inferredTask: document.querySelector("#inferredTask"),
  capabilityState: document.querySelector("#capabilityState"),
};

let activeFile = null;
let taskRegistry = [];
const API_BASE = window.location.protocol === "file:" ? null : "";

function taskDisplayName(taskType) {
  if (taskType === "auto") return "自动识别";
  if (taskType === "unclassified") return "未分类";
  if (taskType === "freeform") return "自由需求";
  return taskRegistry.find((task) => task.id === taskType)?.label || taskType || "自动识别";
}

function generationMode() {
  return document.querySelector('input[name="generationMode"]:checked')?.value || "template";
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  window.setTimeout(() => elements.toast.classList.remove("show"), 2400);
}

function applySample(taskType) {
  const sample = samples[taskType] || genericSample(taskType);
  const context = taskRegistry.find((task) => task.id === taskType)?.engineering_context;
  if (!context) {
    showToast("任务列表尚未加载，请稍后重试");
    return;
  }
  elements.projectName.value = sample.projectName;
  elements.width.value = sample.width;
  elements.requirement.value = sample.requirement;
  elements.topModule.value = context.top_module;
  elements.clockMHz.value = context.clock_mhz;
  elements.resetPolarity.value = context.reset_polarity;
  elements.interfaceSpec.value = context.interface_spec;
  elements.ioSpec.value = context.io_spec;
  elements.targetPlatform.value = context.target_platform;
  elements.verificationIntent.value = context.verification_intent;
}

function genericSample(taskType) {
  const normalized = taskType && taskType !== "auto" ? taskType : "fifo";
  const readable = normalized.replaceAll("_", " ");
  return {
    projectName: `${normalized}_demo`.replace(/[^A-Za-z0-9_-]/g, "_"),
    width: 8,
    requirement: `生成一个 ${readable} FPGA 工程，包含顶层集成、RTL 子模块、自检 testbench、约束模板和 README。`,
  };
}

function statusClass(status) {
  const normalized = String(status || "not_run").toLowerCase();
  if (["pass", "passed", "ready"].includes(normalized) || /^l[0-4]$/.test(normalized)) return "pass";
  if (["fail", "failed", "error"].some((word) => normalized.includes(word))) return "fail";
  if (normalized === "not_applicable") return "na";
  return "not-run";
}

function renderStages(stages) {
  elements.stageGrid.innerHTML = "";
  Object.entries(stages).forEach(([name, detail]) => {
    const item = document.createElement("div");
    item.className = `stage-card ${statusClass(detail.status)}`;
    item.title = detail.reason || detail.status;
    const label = document.createElement("strong");
    label.textContent = name;
    const state = document.createElement("span");
    state.textContent = detail.status;
    item.append(label, state);
    elements.stageGrid.appendChild(item);
  });
}

function requestPayload() {
  const mode = generationMode();
  return {
    project_name: elements.projectName.value.trim(),
    task_type: mode === "free" ? "freeform" : elements.taskType.value || "auto",
    width: Number(elements.width.value),
    requirement: elements.requirement.value.trim(),
    generation_mode: mode,
    engineering_context: engineeringContext(),
  };
}

function engineeringContext() {
  return {
    top_module: elements.topModule.value.trim(),
    clock_mhz: elements.clockMHz.value.trim(),
    reset_polarity: elements.resetPolarity.value,
    interface_spec: elements.interfaceSpec.value,
    io_spec: elements.ioSpec.value.trim(),
    target_platform: elements.targetPlatform.value.trim(),
    verification_intent: elements.verificationIntent.value,
    deliverables: selectedDeliverables(),
  };
}

function selectedDeliverables() {
  return [
    ["RTL", document.querySelector("#deliverRtl").checked],
    ["Testbench", document.querySelector("#deliverTb").checked],
    ["Constraints", document.querySelector("#deliverConstraints").checked],
    ["README", document.querySelector("#deliverReadme").checked],
  ].filter(([, enabled]) => enabled).map(([name]) => name);
}

function renderAmbiguityAudit(data) {
  const disposition = data.disposition || "unknown";
  if (data.inferred_task_type && elements.taskType.querySelector(`option[value="${data.inferred_task_type}"]`)) {
    elements.taskType.value = data.inferred_task_type;
  }
  elements.inferredTask.textContent = taskDisplayName(data.inferred_task_type || data.task_type || "unclassified");
  elements.capabilityState.textContent =
    disposition === "capability_gap"
      ? "capability gap"
      : disposition === "needs_clarification"
        ? "missing facts"
        : disposition;
  elements.ambiguityStatus.textContent =
    disposition === "ready"
      ? "需求明确"
      : disposition === "needs_clarification"
        ? "需要澄清"
        : disposition === "capability_gap"
          ? "能力缺口"
          : "无法判断";
  elements.ambiguityStatus.className = `audit-status ${statusClass(disposition)}`;
  elements.ambiguityList.innerHTML = "";

  const questions = data.clarification_questions || [];
  const gaps = data.capability_gap_ids || [];
  const items = questions.length
    ? questions
    : gaps.length
      ? data.capability_gap_messages || gaps.map((gap) => `当前确定性后端不支持能力：${gap}`)
      : ["需求边界评估为 ready，可以继续运行项目生成与验证。"];

  items.forEach((text) => {
    const item = document.createElement("li");
    item.textContent = text;
    elements.ambiguityList.appendChild(item);
  });
}

async function readJsonResponse(response) {
  const text = await response.text();
  try {
    return text ? JSON.parse(text) : {};
  } catch {
    return { error: text || `HTTP ${response.status}` };
  }
}

async function auditRequirement() {
  if (API_BASE === null) {
    throw new Error("请先启动本地服务，并用 http://127.0.0.1:8000 打开页面后再检查。");
  }
  const response = await fetch("/api/audit-requirement", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestPayload()),
  });
  const data = await readJsonResponse(response);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("后端尚未部署需求歧义检查接口，请更新 app/server.py 后重新部署。");
    }
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  renderAmbiguityAudit(data);
  return data;
}

function showClarificationStop(audit) {
  elements.passLevel.textContent = "NEEDS CLARIFICATION";
  elements.passLevel.className = "result-chip not-run";
  elements.artifactPath.textContent = "需求仍有关键歧义，未生成工程产物。";
  elements.output.textContent = [
    "需求歧义检查未通过。请先补充以下问题，再运行项目生成：",
    "",
    ...(audit.clarification_questions || []).map((question, index) => `${index + 1}. ${question}`),
  ].join("\n");
  elements.fileList.innerHTML = '<div class="empty-state">等待需求澄清</div>';
  updateCounts({}, 0);
  renderStages(Object.fromEntries(["H0", "H1", "H2", "H3", "L0", "L1", "L2", "L3", "L4"].map((name) => [name, { status: "not_run" }])));
  elements.stageHelp.textContent = `本次停止原因：${(audit.reason_codes || []).join(", ") || "needs_clarification"}`;
}

function freeModeFiles(audit) {
  const payload = requestPayload();
  const prompt = [
    "你是 FPGA 项目生成助手。请基于以下自由需求生成完整多文件 FPGA 工程。",
    "",
    `项目名称：${payload.project_name}`,
    `顶层模块：${elements.topModule.value.trim()}`,
    `参考位宽：${payload.width}`,
    `需求边界结论：${audit.disposition}`,
    `能力缺口：${(audit.capability_gap_ids || []).join(", ") || "无"}`,
    "",
    "系统级需求：",
    payload.requirement,
    "",
    "输出要求：",
    "1. 先给工程目录树。",
    "2. 再按路径给出 RTL、testbench、约束模板和 README。",
    "3. 标明未确认假设，不要把未验证内容称为通过。",
  ].join("\n");
  return [
    {
      path: "requirement.md",
      role: "requirement",
      content: [
        `# ${payload.project_name}`,
        "",
        "## 自由需求",
        payload.requirement,
        "",
        "## 需求边界",
        `- disposition: ${audit.disposition}`,
        `- reason_codes: ${(audit.reason_codes || []).join(", ") || "ready"}`,
        `- capability_gap_ids: ${(audit.capability_gap_ids || []).join(", ") || "none"}`,
      ].join("\n"),
    },
    {
      path: "generation_prompt.md",
      role: "prompt",
      content: prompt,
    },
    {
      path: "boundary.json",
      role: "boundary",
      content: JSON.stringify(audit.boundary || audit, null, 2),
    },
  ];
}

function renderFreeHandoff(audit) {
  const files = freeModeFiles(audit);
  elements.passLevel.textContent = "HANDOFF";
  elements.passLevel.className = "result-chip not-run";
  elements.artifactPath.textContent = "自由需求模式：已生成需求交接包，未运行工程验证。";
  renderFiles(files);
  updateCounts({}, files.length);
  renderStages(Object.fromEntries(["H0", "H1", "H2", "H3", "L0", "L1", "L2", "L3", "L4"].map((name) => [name, { status: "not_run" }])));
  elements.stageHelp.textContent = `自由需求模式只完成需求边界评估：${audit.disposition}。`;
  showToast("已生成自由需求交接包");
}

function selectFile(file) {
  activeFile = file;
  elements.output.textContent = file.content;
  elements.fileList.querySelectorAll("button").forEach((button) => button.classList.toggle("active", button.dataset.path === file.path));
}

function renderFiles(files) {
  elements.fileList.innerHTML = "";
  if (!files.length) {
    elements.fileList.innerHTML = '<div class="empty-state">本次运行没有生成工程文件</div>';
    elements.output.textContent = "请查看门禁状态与错误提示。";
    activeFile = null;
    return;
  }
  files.forEach((file) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.path = file.path;
    const role = document.createElement("span");
    role.className = "file-role";
    role.textContent = file.role;
    const path = document.createElement("span");
    path.textContent = file.path;
    button.append(role, path);
    button.addEventListener("click", () => selectFile(file));
    elements.fileList.appendChild(button);
  });
  selectFile(files.find((file) => file.path === "system_his.json") || files.find((file) => file.path.startsWith("rtl/")) || files[0]);
}

function updateCounts(counts, total) {
  document.querySelector("#rtlCount").textContent = counts.rtl || 0;
  document.querySelector("#tbCount").textContent = counts.verification || 0;
  document.querySelector("#constraintCount").textContent = counts.constraints || 0;
  document.querySelector("#fileCount").textContent = total;
}

function setBusy(busy) {
  elements.button.disabled = busy;
  elements.button.classList.toggle("loading", busy);
  elements.button.querySelector(".button-label").textContent = busy
    ? "正在处理..."
    : generationMode() === "free"
      ? "生成自由需求交接包"
      : "生成完整工程并验证";
}

function updateModeUi() {
  const free = generationMode() === "free";
  elements.taskField.classList.toggle("is-disabled", free);
  elements.taskType.disabled = free;
  elements.taskType.value = free ? "auto" : elements.taskType.value || "auto";
  elements.methodCondition.value = free ? "free_requirement_handoff" : "reference_deterministic";
  elements.methodMode.textContent = free ? "自由需求交接" : "确定性参考";
  document.querySelector("#topbarMode").textContent = free ? "自由需求" : "System-HIS 解析";
  document.querySelector(".scope-note p").textContent = free
    ? "自由需求模式会复用后端需求边界评估，并输出交接包；当前不会伪造 RTL 生成、综合或仿真通过。"
    : "后端先给出 requirement boundary，再由当前确定性参考后端生成可检查工程；缺失事实不会被静默默认成 ready。";
  setBusy(false);
}

async function checkBackend() {
  try {
    if (API_BASE === null) {
      throw new Error("file mode");
    }
    const response = await fetch("/api/health", { cache: "no-store" });
    if (!response.ok) throw new Error();
    elements.backendStatus.textContent = "已连接";
    elements.backendStatus.className = "ok";
  } catch {
    elements.backendStatus.textContent = "未连接";
    elements.backendStatus.className = "status-error";
  }
}

async function loadTaskRegistry() {
  if (API_BASE === null) return;
  try {
    const response = await fetch("/api/tasks", { cache: "no-store" });
    const data = await readJsonResponse(response);
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    taskRegistry = Array.isArray(data.tasks) ? data.tasks : [];
    renderTaskRegistry(taskRegistry, data.family_count);
  } catch (error) {
    showToast(`任务族列表加载失败：${error.message}`);
  }
}

function renderTaskRegistry(tasks, familyCount) {
  const current = elements.taskType.value || "auto";
  elements.taskType.innerHTML = "";
  const auto = document.createElement("option");
  auto.value = "auto";
  auto.textContent = tasks.length
    ? `根据需求自动识别（${familyCount || tasks.length} 个任务族）`
    : "根据需求自动识别";
  elements.taskType.appendChild(auto);
  tasks.forEach((task) => {
    const option = document.createElement("option");
    option.value = task.id;
    option.textContent = task.label;
    elements.taskType.appendChild(option);
  });
  elements.taskType.value = elements.taskType.querySelector(`option[value="${current}"]`) ? current : "auto";
}

function setAuditBusy(busy) {
  elements.ambiguityButton.disabled = busy;
  elements.ambiguityButton.textContent = busy ? "正在解析..." : "解析需求边界";
}

document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
    button.classList.add("active");
    document.querySelector(`#${button.dataset.view}`).classList.add("active");
  });
});

elements.taskType.addEventListener("change", () => {
  elements.inferredTask.textContent = taskDisplayName(elements.taskType.value);
});
document.querySelectorAll('input[name="generationMode"]').forEach((input) => {
  input.addEventListener("change", updateModeUi);
});
document.querySelector("#sampleBtn").addEventListener("click", () => {
  const current = elements.taskType.value === "auto" ? "fifo" : elements.taskType.value;
  applySample(current);
  showToast("已恢复该任务族的示例需求");
});
elements.ambiguityButton.addEventListener("click", async () => {
  setAuditBusy(true);
  elements.ambiguityStatus.textContent = "解析中";
  elements.ambiguityStatus.className = "audit-status running";
  try {
    const audit = await auditRequirement();
    showToast(audit.disposition === "ready" ? "需求边界解析通过" : "需求边界需要处理");
  } catch (error) {
    elements.ambiguityStatus.textContent = "检查失败";
    elements.ambiguityStatus.className = "audit-status fail";
    elements.ambiguityList.innerHTML = "";
    const item = document.createElement("li");
    item.textContent = error.message;
    elements.ambiguityList.appendChild(item);
    showToast(error.message);
  } finally {
    setAuditBusy(false);
  }
});

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setBusy(true);
  elements.passLevel.textContent = "RUNNING";
  elements.passLevel.className = "result-chip running";
  elements.output.textContent = "正在执行需求边界、项目生成和本机工具验证…";
  document.querySelectorAll("#pipeline .step").forEach((step) => step.classList.add("active"));
  try {
    const audit = await auditRequirement();
    if (audit.disposition === "needs_clarification") {
      showClarificationStop(audit);
      showToast("需求需要先澄清");
      return;
    }
    if (generationMode() === "free") {
      renderFreeHandoff(audit);
      return;
    }
    const response = await fetch("/api/generate", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestPayload()),
    });
    const data = await readJsonResponse(response);
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    const boundaryStop = ["capability_gap", "requirement_clarification_required"].includes(data.failure_type);
    elements.passLevel.textContent = data.failure_type === "capability_gap" ? "CAPABILITY GAP" : data.failure_type === "requirement_clarification_required" ? "NEEDS CLARIFICATION" : data.pass_level;
    elements.passLevel.className = `result-chip ${boundaryStop ? "not-run" : statusClass(data.pass_level)}`;
    elements.artifactPath.textContent = data.sample_id ? `${data.sample_id} · ${data.artifact_path}` : "未生成工程";
    renderFiles(data.files);
    renderStages(data.stages);
    updateCounts(data.counts, data.files.length);
    elements.stageHelp.textContent = data.failure_type ? `本次停止原因：${data.failure_type}` : `Requirement Boundary：${data.boundary.disposition}；结果来自本次 labels.json。`;
    document.querySelectorAll("#pipeline .step").forEach((step) => { step.classList.remove("active"); step.classList.add("done"); });
    showToast(`执行完成：${data.pass_level}`);
  } catch (error) {
    elements.passLevel.textContent = "ERROR";
    elements.passLevel.className = "result-chip fail";
    elements.output.textContent = `无法完成本次运行：${error.message}`;
    elements.stageHelp.textContent = "这是服务或输入错误，没有生成模拟结果。";
    showToast(error.message);
  } finally { setBusy(false); }
});

document.querySelector("#copyBtn").addEventListener("click", async () => {
  if (!activeFile) { showToast("当前没有可复制的文件"); return; }
  await navigator.clipboard.writeText(activeFile.content);
  showToast(`已复制 ${activeFile.path}`);
});

renderStages(Object.fromEntries(["H0", "H1", "H2", "H3", "L0", "L1", "L2", "L3", "L4"].map((name) => [name, { status: "not_run" }])));
updateModeUi();
checkBackend();
loadTaskRegistry();
