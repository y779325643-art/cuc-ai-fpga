
const P = {
  bg: "#F4F7FA",
  panel: "#FFFFFF",
  ink: "#102033",
  muted: "#5D6B7B",
  faint: "#DCE5EF",
  blue: "#1A4C8C",
  cyan: "#0097B8",
  mint: "#00A86B",
  amber: "#E86A17",
  red: "#D93A3A",
  navy: "#0D2340",
  navy2: "#143962",
  white: "#FFFFFF",
  pale: "#EAF2F8",
  warm: "#FFF4EA",
};

function text(slide, ctx, x, y, width, height, value, opts = {}) {
  ctx.addText(slide, {
    x, y, width, height,
    text: value ?? "",
    fontSize: opts.size ?? 16,
    bold: opts.bold ?? false,
    color: opts.color ?? P.ink,
    align: opts.align ?? "left",
    valign: opts.valign ?? "top",
    typeface: opts.face ?? "Microsoft YaHei",
    insets: opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
  });
}

function rect(slide, ctx, x, y, width, height, opts = {}) {
  return ctx.addShape(slide, {
    x, y, width, height,
    fill: opts.fill ?? P.panel,
    line: ctx.line(opts.line ?? "#00000000", opts.lineWidth ?? 0),
    geometry: opts.geometry ?? "rect",
  });
}

function line(slide, ctx, x1, y1, x2, y2, color = "#8FA2B8", weight = 1.5) {
  ctx.addShape(slide, {
    geometry: "line",
    x: x1,
    y: y1,
    width: x2 - x1,
    height: y2 - y1,
    line: ctx.line(color, weight),
  });
}

function arrow(slide, ctx, x1, y1, x2, y2, color = "#8FA2B8") {
  line(slide, ctx, x1, y1, x2, y2, color, 2);
  const dx = Math.sign(x2 - x1 || 1);
  rect(slide, ctx, x2 - 6 * dx, y2 - 6, 12, 12, { fill: color, line: color, geometry: "triangle" });
}

function chip(slide, ctx, x, y, label, color = P.cyan) {
  rect(slide, ctx, x, y + 5, 8, 20, { fill: color });
  text(slide, ctx, x + 18, y, 260, 28, label, { size: 15, bold: true, color, face: "Aptos" });
}

function pattern(slide, ctx, dark = false) {
  const c = dark ? "#FFFFFF12" : "#BFD1E344";
  for (let x = 72; x < 1280; x += 118) line(slide, ctx, x, 0, x, 720, c, 0.7);
  for (let y = 82; y < 720; y += 96) line(slide, ctx, 0, y, 1280, y, c, 0.7);
}

function footer(slide, ctx, n) {
  line(slide, ctx, 56, 674, 1160, 674, "#D4DEE9", 1);
  text(slide, ctx, 56, 688, 520, 18, "HNAI-FPGA | project overview redesign", { size: 9.5, color: "#728195", face: "Aptos" });
  text(slide, ctx, 1130, 688, 90, 18, String(n).padStart(2, "0") + " / 37", { size: 10, color: "#728195", face: "Aptos", align: "right" });
}

function frame(slide, ctx, data, n) {
  rect(slide, ctx, 0, 0, ctx.W, ctx.H, { fill: P.bg });
  pattern(slide, ctx, false);
  rect(slide, ctx, 0, 0, 1280, 92, { fill: P.navy });
  rect(slide, ctx, 0, 92, 1280, 4, { fill: P.cyan });
  text(slide, ctx, 56, 22, 820, 34, data.title, { size: 24.5, bold: true, color: P.white });
  text(slide, ctx, 56, 58, 900, 22, data.claim, { size: 12.5, color: "#C8D7E7" });
  text(slide, ctx, 1088, 28, 130, 22, "HNAI-FPGA", { size: 12, bold: true, color: "#75D7F2", face: "Aptos", align: "right" });
  footer(slide, ctx, n);
}

function drawCover(slide, ctx, data) {
  rect(slide, ctx, 0, 0, ctx.W, ctx.H, { fill: P.navy });
  pattern(slide, ctx, true);
  rect(slide, ctx, 820, 0, 460, 720, { fill: "#12355E" });
  rect(slide, ctx, 818, 0, 5, 720, { fill: P.cyan });
  text(slide, ctx, 72, 70, 500, 28, data.kicker, { size: 14, bold: true, color: "#75D7F2", face: "Aptos" });
  text(slide, ctx, 72, 132, 700, 72, data.title, { size: 50, bold: true, color: P.white, face: "Aptos Display" });
  text(slide, ctx, 76, 232, 690, 44, data.subtitle, { size: 19, color: "#D4E4F3" });
  rect(slide, ctx, 76, 320, 90, 4, { fill: P.amber });
  text(slide, ctx, 76, 356, 680, 86, data.claim, { size: 22, bold: true, color: P.white });
  text(slide, ctx, 76, 638, 560, 22, data.meta, { size: 12, color: "#93A8BD", face: "Aptos" });
  data.metrics.forEach((m, i) => {
    const y = 92 + i * 128;
    rect(slide, ctx, 890, y, 230, 88, { fill: "#FFFFFF18", line: "#FFFFFF2A", lineWidth: 1 });
    text(slide, ctx, 914, y + 17, 180, 28, m[0], { size: 22, bold: true, color: P.white, face: "Aptos Display" });
    text(slide, ctx, 914, y + 51, 190, 20, m[1], { size: 12.5, color: "#D4E4F3" });
    rect(slide, ctx, 914, y + 74, 74, 3, { fill: [P.cyan, "#60A5FA", P.amber, P.mint][i] });
  });
}

function drawSection(slide, ctx, data, n) {
  rect(slide, ctx, 0, 0, ctx.W, ctx.H, { fill: P.navy });
  pattern(slide, ctx, true);
  rect(slide, ctx, 0, 560, 1280, 160, { fill: "#102A49" });
  text(slide, ctx, 92, 146, 400, 38, data.chapter, { size: 24, color: "#8DB8DE" });
  text(slide, ctx, 92, 230, 900, 70, data.title, { size: 44, bold: true, color: P.white });
  rect(slide, ctx, 94, 330, 115, 4, { fill: P.cyan });
  text(slide, ctx, 94, 370, 820, 34, data.subtitle, { size: 18, color: "#C8D7E7" });
  text(slide, ctx, 1110, 660, 90, 18, String(n).padStart(2, "0") + " / 37", { size: 10, color: "#7891A9", face: "Aptos", align: "right" });
}

function drawCards(slide, ctx, data) {
  const cards = data.cards || [];
  cards.forEach((c, i) => {
    const x = 74 + (i % 3) * 390;
    const y = 142 + Math.floor(i / 3) * 180;
    rect(slide, ctx, x, y, 330, 130, { fill: i % 2 ? "#F8FBFE" : P.white, line: P.faint, lineWidth: 1 });
    rect(slide, ctx, x, y, 9, 130, { fill: [P.blue, P.cyan, P.mint, P.amber, P.red, "#64748B"][i % 6] });
    text(slide, ctx, x + 26, y + 20, 260, 28, c[0], { size: 19, bold: true, color: P.ink });
    text(slide, ctx, x + 26, y + 58, 278, 50, c[1], { size: 14, color: P.muted });
  });
  if (data.note) noteBand(slide, ctx, data.note);
}

function noteBand(slide, ctx, value, y = 586, color = P.cyan) {
  rect(slide, ctx, 92, y, 1088, 56, { fill: P.white, line: "#CFDDEB", lineWidth: 1 });
  rect(slide, ctx, 92, y, 10, 56, { fill: color });
  text(slide, ctx, 126, y + 14, 980, 24, value, { size: 15, bold: true, color: P.ink });
}

function drawTable(slide, ctx, data) {
  const left = 72, top = 140, width = 1136;
  const cols = data.headers.length;
  const rowH = data.rows.length > 6 ? 42 : 58;
  const colW = width / cols;
  data.headers.forEach((h, i) => {
    rect(slide, ctx, left + i * colW, top, colW, 42, { fill: P.blue, line: P.white, lineWidth: 1 });
    text(slide, ctx, left + i * colW + 10, top + 10, colW - 20, 20, h, { size: 13.5, bold: true, color: P.white, align: "center" });
  });
  data.rows.forEach((row, r) => {
    const y = top + 42 + r * rowH;
    row.forEach((cell, c) => {
      rect(slide, ctx, left + c * colW, y, colW, rowH, { fill: r % 2 ? "#EEF4FA" : P.white, line: "#D2DCE7", lineWidth: 1 });
      text(slide, ctx, left + c * colW + 12, y + 10, colW - 24, rowH - 16, cell, { size: data.rows.length > 6 ? 11.8 : 13.5, bold: c === 0, color: c === 0 ? P.blue : P.ink, valign: "mid" });
    });
  });
  if (data.note) noteBand(slide, ctx, data.note, 610, P.amber);
}

function drawTimeline(slide, ctx, data) {
  data.stages.forEach((s, i) => {
    const x = 70 + (i % 4) * 295;
    const y = 140 + Math.floor(i / 4) * 210;
    rect(slide, ctx, x, y, 244, 148, { fill: P.white, line: P.faint, lineWidth: 1 });
    rect(slide, ctx, x, y, 244, 8, { fill: [P.blue, P.cyan, P.mint, P.amber][i % 4] });
    text(slide, ctx, x + 18, y + 22, 72, 26, s[0], { size: 19, bold: true, color: P.blue, face: "Aptos Display" });
    text(slide, ctx, x + 96, y + 24, 128, 24, s[1], { size: 15.5, bold: true, color: P.ink });
    text(slide, ctx, x + 18, y + 62, 200, 30, s[2], { size: 12.5, color: "#1F7665", bold: true });
    text(slide, ctx, x + 18, y + 100, 204, 30, s[3], { size: 11.8, color: P.muted });
    if (i < data.stages.length - 1 && i % 4 !== 3) arrow(slide, ctx, x + 248, y + 74, x + 286, y + 74);
  });
  noteBand(slide, ctx, data.note, 600, P.cyan);
}

function drawCompare(slide, ctx, data) {
  const x1 = 76, x2 = 668, y = 144, h = 420;
  rect(slide, ctx, x1, y, 520, h, { fill: P.white, line: P.faint, lineWidth: 1 });
  rect(slide, ctx, x2, y, 520, h, { fill: "#F7FCFA", line: "#CDE7DE", lineWidth: 1 });
  rect(slide, ctx, x1, y, 520, 58, { fill: "#344154" });
  rect(slide, ctx, x2, y, 520, 58, { fill: P.mint });
  text(slide, ctx, x1 + 28, y + 17, 430, 24, data.leftTitle, { size: 18, bold: true, color: P.white });
  text(slide, ctx, x2 + 28, y + 17, 430, 24, data.rightTitle, { size: 18, bold: true, color: P.white });
  data.left.forEach((v, i) => bullet(slide, ctx, x1 + 38, y + 95 + i * 70, v, "#64748B"));
  data.right.forEach((v, i) => bullet(slide, ctx, x2 + 38, y + 95 + i * 70, v, P.mint));
  if (data.note) noteBand(slide, ctx, data.note, 600, P.cyan);
}

function bullet(slide, ctx, x, y, value, color = P.cyan) {
  rect(slide, ctx, x, y + 6, 10, 10, { fill: color, geometry: "ellipse" });
  text(slide, ctx, x + 24, y, 330, 32, value, { size: 16.5, color: P.ink });
}

function drawFlow(slide, ctx, data) {
  const cols = Math.min(data.steps.length, 6);
  data.steps.forEach((s, i) => {
    const x = 58 + i * (1140 / cols);
    const w = 150;
    const y = i % 2 ? 330 : 180;
    rect(slide, ctx, x, y, w, 112, { fill: P.white, line: P.faint, lineWidth: 1 });
    rect(slide, ctx, x, y, w, 7, { fill: [P.blue, P.cyan, P.mint, P.amber, P.red, "#64748B"][i % 6] });
    text(slide, ctx, x + 14, y + 22, w - 28, 24, s[0], { size: 16, bold: true, color: P.ink, align: "center" });
    text(slide, ctx, x + 14, y + 58, w - 28, 34, s[1], { size: 11.5, color: P.muted, align: "center" });
    if (i < data.steps.length - 1) arrow(slide, ctx, x + w + 6, y + 56, x + 184, (i + 1) % 2 ? 386 : 236);
  });
  noteBand(slide, ctx, data.note, 558, P.cyan);
}

function drawArchitecture(slide, ctx, data) {
  data.lanes.forEach((l, i) => {
    const x = 80 + i * 190;
    rect(slide, ctx, x, 180, 150, 252, { fill: P.white, line: "#CEDBE8", lineWidth: 1 });
    rect(slide, ctx, x, 180, 150, 9, { fill: l[2] });
    text(slide, ctx, x + 16, 214, 118, 28, l[0], { size: 17, bold: true, color: l[2], align: "center" });
    text(slide, ctx, x + 16, 270, 118, 70, l[1], { size: 16, bold: true, color: P.ink, align: "center", valign: "mid" });
    if (i < data.lanes.length - 1) arrow(slide, ctx, x + 154, 306, x + 186, 306, "#8193A8");
  });
  rect(slide, ctx, 266, 468, 748, 68, { fill: "#102A49", line: "#102A49" });
  text(slide, ctx, 310, 490, 660, 26, "EDA Feedback Loop: report → diagnosis → HIS-L1 parameter update", { size: 18, bold: true, color: P.white, align: "center", face: "Aptos" });
  noteBand(slide, ctx, data.note, 592, P.amber);
}

function drawDefinition(slide, ctx, data) {
  rect(slide, ctx, 74, 144, 1130, 94, { fill: "#102A49", line: "#102A49" });
  text(slide, ctx, 106, 174, 1060, 34, data.statement, { size: 20, bold: true, color: P.white, align: "center", face: "Aptos" });
  data.choices.forEach((row, i) => {
    const y = 292 + i * 82;
    text(slide, ctx, 96, y + 13, 60, 24, row[0], { size: 15, bold: true, color: P.red });
    text(slide, ctx, 160, y + 13, 310, 24, row[1], { size: 15.5, color: P.muted });
    text(slide, ctx, 520, y + 13, 50, 24, row[2], { size: 15, bold: true, color: P.mint });
    text(slide, ctx, 580, y + 13, 600, 24, row[3], { size: 15.5, bold: true, color: P.ink });
    line(slide, ctx, 92, y + 58, 1160, y + 58, "#D5E0EA", 1);
  });
}

function drawConcepts(slide, ctx, data) {
  data.concepts.forEach((c, i) => {
    const x = 70 + (i % 4) * 292;
    const y = 142 + Math.floor(i / 4) * 178;
    rect(slide, ctx, x, y, 240, 126, { fill: P.white, line: P.faint, lineWidth: 1 });
    text(slide, ctx, x + 18, y + 18, 170, 24, c[0], { size: 18, bold: true, color: [P.blue, P.cyan, P.mint, P.amber][i % 4], face: "Aptos Display" });
    text(slide, ctx, x + 18, y + 52, 204, 26, c[1], { size: 13.5, bold: true, color: P.ink });
    text(slide, ctx, x + 18, y + 86, 204, 24, c[2] || "", { size: 11.5, color: P.muted });
  });
}

function drawPipeline(slide, ctx, data) {
  data.steps.forEach((s, i) => {
    const x = 78 + i * 232;
    rect(slide, ctx, x, 224, 180, 148, { fill: P.white, line: P.faint, lineWidth: 1 });
    text(slide, ctx, x + 18, 246, 42, 42, s[0], { size: 32, bold: true, color: [P.blue, P.cyan, P.mint, P.amber, P.red][i], face: "Aptos Display", align: "center" });
    text(slide, ctx, x + 70, 254, 94, 24, s[1], { size: 17, bold: true, color: P.ink });
    text(slide, ctx, x + 18, 306, 142, 38, s[2], { size: 12.8, color: P.muted, align: "center" });
    if (i < data.steps.length - 1) arrow(slide, ctx, x + 184, 298, x + 222, 298);
  });
  noteBand(slide, ctx, data.note, 514, P.cyan);
}

function drawSplitList(slide, ctx, data) {
  const areas = [[80, 154, data.leftTitle, data.left, P.blue], [672, 154, data.rightTitle, data.right, P.mint]];
  areas.forEach(([x, y, title, items, color]) => {
    rect(slide, ctx, x, y, 500, 360, { fill: P.white, line: P.faint, lineWidth: 1 });
    rect(slide, ctx, x, y, 500, 58, { fill: color });
    text(slide, ctx, x + 24, y + 17, 420, 24, title, { size: 18, bold: true, color: P.white });
    items.forEach((item, i) => bullet(slide, ctx, x + 34, y + 94 + i * 64, item, color));
  });
  noteBand(slide, ctx, data.note, 590, P.amber);
}

function drawFeedback(slide, ctx, data) {
  data.mappings.forEach((m, i) => {
    const y = 142 + i * 82;
    rect(slide, ctx, 82, y, 230, 54, { fill: P.white, line: P.faint, lineWidth: 1 });
    rect(slide, ctx, 390, y, 300, 54, { fill: "#F8FBFE", line: P.faint, lineWidth: 1 });
    rect(slide, ctx, 770, y, 380, 54, { fill: i % 2 ? P.warm : "#F0FBF8", line: P.faint, lineWidth: 1 });
    text(slide, ctx, 104, y + 14, 188, 22, m[0], { size: 15.5, bold: true, color: i === 0 ? P.red : P.blue, face: "Aptos" });
    text(slide, ctx, 414, y + 14, 250, 22, m[1], { size: 15, color: P.ink });
    text(slide, ctx, 794, y + 14, 330, 22, m[2], { size: 15, bold: true, color: P.ink });
    arrow(slide, ctx, 322, y + 27, 382, y + 27);
    arrow(slide, ctx, 700, y + 27, 760, y + 27);
  });
  noteBand(slide, ctx, data.note, 590, P.cyan);
}

function drawCodePair(slide, ctx, data) {
  const panels = [[78, data.leftTitle, data.left], [672, data.rightTitle, data.right]];
  panels.forEach(([x, title, rows], idx) => {
    rect(slide, ctx, x, 152, 508, 350, { fill: "#101827", line: "#101827" });
    rect(slide, ctx, x, 152, 508, 44, { fill: idx ? "#0F766E" : "#1E3A5F" });
    text(slide, ctx, x + 24, 164, 430, 20, title, { size: 15.5, bold: true, color: P.white });
    rows.forEach((r, i) => {
      text(slide, ctx, x + 34, 224 + i * 45, 430, 24, r, { size: 15.5, color: "#EAF2FF", face: "Aptos Mono" });
    });
  });
  noteBand(slide, ctx, data.note, 584, P.cyan);
}

function drawRoadmap(slide, ctx, data) {
  data.phases.forEach((p, i) => {
    const x = 86 + i * 390;
    rect(slide, ctx, x, 156, 320, 384, { fill: P.white, line: P.faint, lineWidth: 1 });
    rect(slide, ctx, x, 156, 320, 10, { fill: [P.mint, P.blue, P.amber][i] });
    text(slide, ctx, x + 24, 198, 260, 28, p[0], { size: 20, bold: true, color: [P.mint, P.blue, P.amber][i] });
    p[1].forEach((item, j) => bullet(slide, ctx, x + 30, 258 + j * 62, item, [P.mint, P.blue, P.amber][i]));
  });
  noteBand(slide, ctx, data.note, 590, P.cyan);
}

function drawRecap(slide, ctx, data) {
  data.sentences.forEach((s, i) => {
    const y = 138 + i * 112;
    rect(slide, ctx, 80, y, 1088, 78, { fill: P.white, line: P.faint, lineWidth: 1 });
    text(slide, ctx, 110, y + 22, 90, 24, s[0], { size: 18, bold: true, color: [P.blue, P.cyan, P.amber][i] });
    text(slide, ctx, 220, y + 18, 920, 32, s[1], { size: 15.2, color: P.ink });
  });
  chip(slide, ctx, 82, 510, "章节回顾", P.blue);
  data.chapters.forEach((c, i) => {
    text(slide, ctx, 112 + (i % 4) * 278, 556 + Math.floor(i / 4) * 38, 240, 22, String(i + 1).padStart(2, "0") + "  " + c, { size: 12.8, bold: true, color: P.ink });
  });
}

function drawGlossary(slide, ctx, data) {
  data.concepts.forEach((c, i) => {
    const x = 76 + (i % 3) * 386;
    const y = 136 + Math.floor(i / 3) * 112;
    rect(slide, ctx, x, y, 326, 82, { fill: i % 2 ? "#F8FBFE" : P.white, line: P.faint, lineWidth: 1 });
    text(slide, ctx, x + 20, y + 17, 110, 22, c[0], { size: 17, bold: true, color: [P.blue, P.cyan, P.mint][i % 3], face: "Aptos Display" });
    text(slide, ctx, x + 136, y + 17, 170, 34, c[1], { size: 13.8, color: P.ink });
  });
  text(slide, ctx, 156, 626, 968, 24, "感谢聆听 | HNAI-FPGA · 基于分层硬件意图 IR 的自然语言到 FPGA 自动设计与约束优化框架", { size: 15, bold: true, color: P.blue, align: "center" });
}

export async function renderSlide(presentation, ctx, data, n) {
  const slide = presentation.slides.add();
  if (data.type === "cover") { drawCover(slide, ctx, data); return slide; }
  if (data.type === "section") { drawSection(slide, ctx, data, n); return slide; }
  frame(slide, ctx, data, n);
  if (data.type === "timeline") drawTimeline(slide, ctx, data);
  else if (data.type === "table") drawTable(slide, ctx, data);
  else if (data.type === "compare") drawCompare(slide, ctx, data);
  else if (data.type === "flow") drawFlow(slide, ctx, data);
  else if (data.type === "definition") drawDefinition(slide, ctx, data);
  else if (data.type === "architecture") drawArchitecture(slide, ctx, data);
  else if (data.type === "concepts") drawConcepts(slide, ctx, data);
  else if (data.type === "cards") drawCards(slide, ctx, data);
  else if (data.type === "pipeline") drawPipeline(slide, ctx, data);
  else if (data.type === "splitList") drawSplitList(slide, ctx, data);
  else if (data.type === "feedback") drawFeedback(slide, ctx, data);
  else if (data.type === "codePair") drawCodePair(slide, ctx, data);
  else if (data.type === "roadmap") drawRoadmap(slide, ctx, data);
  else if (data.type === "recap") drawRecap(slide, ctx, data);
  else if (data.type === "glossary") drawGlossary(slide, ctx, data);
  else drawCards(slide, ctx, { cards: [["未定义版式", data.type || "unknown"]], note: "This slide used the fallback layout." });
  return slide;
}
