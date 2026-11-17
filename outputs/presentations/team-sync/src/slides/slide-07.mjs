
const P = {
  "bg": "#F7F9FC",
  "ink": "#162033",
  "muted": "#5B6475",
  "line": "#D8DEE9",
  "blue": "#2457D6",
  "cyan": "#00A6A6",
  "green": "#2E8B57",
  "amber": "#C47A1B",
  "red": "#B23B3B",
  "navy": "#0E1B2A",
  "white": "#FFFFFF",
  "chip": "#EAF0FF"
};

function addBg(slide, ctx, title, claim) {
  ctx.addShape(slide, { x: 0, y: 0, width: ctx.W, height: ctx.H, fill: P.bg });
  ctx.addShape(slide, { x: 0, y: 0, width: 12, height: ctx.H, fill: P.blue });
  ctx.addText(slide, { x: 54, y: 34, width: 820, height: 42, text: title, fontSize: 28, bold: true, color: P.ink, typeface: "Microsoft YaHei" });
  ctx.addText(slide, { x: 54, y: 80, width: 930, height: 42, text: claim, fontSize: 17, color: P.muted, typeface: "Microsoft YaHei" });
  ctx.addText(slide, { x: 1110, y: 42, width: 110, height: 24, text: "HNAI-FPGA", fontSize: 13, bold: true, color: P.blue, align: "right", typeface: "Aptos" });
}

function addFooter(slide, ctx, n) {
  ctx.addShape(slide, { x: 54, y: 674, width: 1070, height: 1.2, fill: P.line });
  ctx.addText(slide, { x: 54, y: 686, width: 520, height: 20, text: "团队内部技术同步 | source: project manuscript & business plan", fontSize: 10, color: P.muted, typeface: "Aptos" });
  ctx.addText(slide, { x: 1160, y: 686, width: 44, height: 20, text: String(n).padStart(2, "0"), fontSize: 11, color: P.muted, align: "right", typeface: "Aptos" });
}

function card(slide, ctx, x, y, w, h, opts = {}) {
  ctx.addShape(slide, { x, y, width: w, height: h, fill: opts.fill || P.white, line: ctx.line(opts.line || P.line, opts.lineWidth || 1) });
}

function label(slide, ctx, x, y, w, h, text, opts = {}) {
  ctx.addText(slide, { x, y, width: w, height: h, text, fontSize: opts.size || 15, bold: opts.bold || false, color: opts.color || P.ink, typeface: opts.face || "Microsoft YaHei", align: opts.align || "left", valign: opts.valign || "top", insets: opts.insets || { left: 0, right: 0, top: 0, bottom: 0 } });
}

function bullet(slide, ctx, x, y, title, body, color = P.blue) {
  ctx.addShape(slide, { x, y: y + 5, width: 8, height: 8, fill: color });
  label(slide, ctx, x + 20, y, 250, 22, title, { size: 16, bold: true });
  label(slide, ctx, x + 20, y + 26, 470, 48, body, { size: 13, color: P.muted });
}

function arrow(slide, ctx, x1, y1, x2, y2, color = P.blue) {
  ctx.addShape(slide, { geometry: "line", x: x1, y: y1, width: x2 - x1, height: y2 - y1, line: ctx.line(color, 2) });
  ctx.addShape(slide, { geometry: "triangle", x: x2 - 8, y: y2 - 6, width: 12, height: 12, fill: color, line: ctx.line(color, 0) });
}

const data = {
  "type": "metrics",
  "title": "资源/功耗/性能：把 Vivado 报告转成可决策指标",
  "claim": "BRAM、DSP、LUT、FF、功耗和 timing slack 都应进入结构化预算检查，而不是停留在长日志里。",
  "cards": [
    [
      "资源预算",
      "LUT / FF / DSP / BRAM / URAM",
      "超过 80% 预警，超过 100% 阻断"
    ],
    [
      "时序质量",
      "WNS / TNS / critical path",
      "WNS >= 0 才能进入交付候选"
    ],
    [
      "功耗估计",
      "static / dynamic / total power",
      "结合 SAIF/VCD 活动文件可提高可信度"
    ],
    [
      "模板调参",
      "并行度 / 流水深度 / 位宽",
      "资源超限时自动降并行或换存储策略"
    ]
  ],
  "examples": [
    [
      "GA-KP",
      "48 DSP",
      "36 BRAM",
      "7.2 W"
    ],
    [
      "RL-PONG",
      "112 DSP",
      "68 BRAM",
      "6.4 W"
    ]
  ]
};

export async function slide07(presentation, ctx) {
  const slide = presentation.slides.add();
  const n = 7;
  if (data.type === "cover") {
    ctx.addShape(slide, { x: 0, y: 0, width: ctx.W, height: ctx.H, fill: P.navy });
    ctx.addShape(slide, { x: 0, y: 520, width: ctx.W, height: 200, fill: "#102C45" });
    ctx.addShape(slide, { x: 830, y: 0, width: 450, height: ctx.H, fill: "#173B5F" });
    label(slide, ctx, 70, 66, 760, 40, data.kicker, { size: 18, color: "#A7D8FF" });
    label(slide, ctx, 70, 124, 780, 110, data.title, { size: 48, bold: true, color: P.white });
    label(slide, ctx, 74, 244, 740, 56, data.subtitle, { size: 22, color: "#D7DEE8" });
    label(slide, ctx, 74, 336, 640, 70, data.claim, { size: 22, bold: true, color: P.white });
    label(slide, ctx, 70, 640, 300, 28, data.date, { size: 15, color: "#AAB8C8" });
    data.metrics.forEach((m, i) => {
      const y = 118 + i * 118;
      card(slide, ctx, 885, y, 280, 82, { fill: "#FFFFFF12", line: "#FFFFFF30" });
      label(slide, ctx, 908, y + 12, 150, 34, m[0], { size: 31, bold: true, color: P.white, face: "Aptos Display" });
      label(slide, ctx, 908, y + 52, 220, 22, m[1], { size: 14, color: "#D7DEE8" });
    });
  } else {
    addBg(slide, ctx, data.title, data.claim);

    if (data.type === "problem") {
      data.points.forEach((p, i) => {
        const x = 68 + (i % 2) * 570;
        const y = 165 + Math.floor(i / 2) * 190;
        card(slide, ctx, x, y, 500, 145);
        ctx.addShape(slide, { x, y, width: 6, height: 145, fill: [P.blue, P.cyan, P.amber, P.red][i] });
        label(slide, ctx, x + 24, y + 22, 250, 28, p[0], { size: 20, bold: true });
        label(slide, ctx, x + 24, y + 62, 420, 58, p[1], { size: 15, color: P.muted });
      });
    }

    if (data.type === "architecture") {
      const xs = [62, 233, 404, 575, 746, 917, 1088];
      data.layers.forEach((l, i) => {
        const x = xs[i];
        const y = i % 2 === 0 ? 170 : 318;
        card(slide, ctx, x, y, 140, 112, { fill: i % 2 === 0 ? P.white : P.chip, line: P.line });
        label(slide, ctx, x + 14, y + 10, 34, 28, l[0], { size: 22, bold: true, color: P.blue, face: "Aptos Display" });
        label(slide, ctx, x + 14, y + 42, 112, 26, l[1], { size: 14, bold: true });
        label(slide, ctx, x + 14, y + 74, 108, 34, l[2], { size: 10.5, color: P.muted });
        if (i < data.layers.length - 1) arrow(slide, ctx, x + 142, y + 55, xs[i + 1] - 8, (i + 1) % 2 === 0 ? 225 : 373, "#96A3B8");
      });
      card(slide, ctx, 160, 510, 940, 76, { fill: "#EAF7F7", line: "#B7E1E1" });
      label(slide, ctx, 186, 530, 900, 34, "约束逐层递进：任何违反硬约束的候选都携带诊断信息返回上一层，而不是继续消耗综合资源。", { size: 19, bold: true, color: P.navy });
    }

    if (data.type === "workflow") {
      data.steps.forEach((s, i) => {
        const col = i % 4;
        const row = Math.floor(i / 4);
        const x = 66 + col * 286;
        const y = 170 + row * 190;
        card(slide, ctx, x, y, 230, 110, { fill: row === 0 ? P.white : "#F0FBFA" });
        label(slide, ctx, x + 16, y + 15, 35, 26, String(i + 1), { size: 20, bold: true, color: P.cyan, face: "Aptos Display" });
        label(slide, ctx, x + 58, y + 17, 150, 24, s[0], { size: 18, bold: true });
        label(slide, ctx, x + 18, y + 55, 190, 36, s[1], { size: 13, color: P.muted });
        if (i !== 3 && i !== 7) arrow(slide, ctx, x + 232, y + 55, x + 278, y + 55, "#9AA7BB");
      });
      arrow(slide, ctx, 1080, 226, 1080, 360, "#9AA7BB");
    }

    if (data.type === "tools") {
      data.groups.forEach((g, i) => {
        const x = 70 + i * 390;
        card(slide, ctx, x, 170, 330, 300, { fill: P.white });
        label(slide, ctx, x + 24, 194, 260, 30, g[0], { size: 21, bold: true, color: [P.blue, P.green, P.amber][i] });
        g[1].forEach((item, j) => label(slide, ctx, x + 28, 250 + j * 58, 270, 34, item, { size: 15, color: P.ink, face: "Aptos" }));
      });
      card(slide, ctx, 112, 520, 1030, 52, { fill: "#FFF7E8", line: "#F2D3A7" });
      label(slide, ctx, 135, 535, 980, 24, data.note, { size: 16, color: P.amber, bold: true });
    }

    if (data.type === "xdc") {
      data.checks.forEach((c, i) => {
        const x = 70 + (i % 3) * 370;
        const y = 160 + Math.floor(i / 3) * 118;
        card(slide, ctx, x, y, 316, 86, { fill: P.white });
        label(slide, ctx, x + 18, y + 14, 130, 24, c[0], { size: 17, bold: true, color: P.blue });
        label(slide, ctx, x + 18, y + 42, 270, 30, c[1], { size: 12.5, color: P.muted });
      });
      card(slide, ctx, 104, 470, 1050, 110, { fill: "#101827", line: "#101827" });
      data.snippet.forEach((line, i) => label(slide, ctx, 132, 495 + i * 27, 900, 22, line, { size: 17, color: "#EAF0FF", face: "Aptos Mono" }));
    }

    if (data.type === "metrics") {
      data.cards.forEach((c, i) => {
        const x = 70 + (i % 2) * 555;
        const y = 160 + Math.floor(i / 2) * 150;
        card(slide, ctx, x, y, 500, 112, { fill: P.white });
        label(slide, ctx, x + 24, y + 17, 160, 24, c[0], { size: 19, bold: true });
        label(slide, ctx, x + 24, y + 50, 220, 23, c[1], { size: 15, color: P.blue, face: "Aptos" });
        label(slide, ctx, x + 260, y + 35, 205, 42, c[2], { size: 13, color: P.muted });
      });
      data.examples.forEach((e, i) => {
        const x = 250 + i * 400;
        card(slide, ctx, x, 506, 330, 64, { fill: "#F0FBFA", line: "#B7E1E1" });
        label(slide, ctx, x + 20, 522, 90, 24, e[0], { size: 18, bold: true, color: P.green, face: "Aptos" });
        label(slide, ctx, x + 118, 523, 190, 22, e.slice(1).join(" | "), { size: 15, color: P.ink, face: "Aptos" });
      });
    }

    if (data.type === "evidence") {
      data.bars.forEach((b, i) => {
        const y = 166 + i * 78;
        label(slide, ctx, 80, y, 180, 26, b[0], { size: 16, bold: true });
        ctx.addShape(slide, { x: 280, y: y + 5, width: 520, height: 22, fill: "#E5EAF2" });
        ctx.addShape(slide, { x: 280, y: y + 5, width: Math.max(18, 520 * b[1] / 100), height: 22, fill: i === 3 ? P.amber : P.blue });
        label(slide, ctx, 820, y - 2, 90, 30, b[1] + "%", { size: 23, bold: true, color: i === 3 ? P.amber : P.blue, face: "Aptos Display" });
        label(slide, ctx, 920, y + 1, 250, 24, b[2], { size: 13, color: P.muted });
      });
      data.callouts.forEach((c, i) => bullet(slide, ctx, 110, 500 + i * 38, "", c, [P.green, P.cyan, P.amber][i]));
    }

    if (data.type === "templates") {
      data.templates.forEach((t, i) => {
        const x = 80 + (i % 2) * 555;
        const y = 160 + Math.floor(i / 2) * 145;
        card(slide, ctx, x, y, 500, 104, { fill: i < 2 ? P.white : "#F8FBFF" });
        label(slide, ctx, x + 24, y + 18, 95, 28, t[0], { size: 21, bold: true, color: [P.blue, P.green, P.cyan, P.amber][i], face: "Aptos Display" });
        label(slide, ctx, x + 125, y + 20, 335, 52, t[1], { size: 13.5, color: P.muted });
      });
      card(slide, ctx, 166, 512, 945, 58, { fill: "#EAF0FF", line: "#C8D5FF" });
      label(slide, ctx, 195, 531, 900, 24, data.formula, { size: 19, bold: true, color: P.blue, face: "Aptos" });
    }

    if (data.type === "mvp") {
      data.lanes.forEach((l, i) => {
        const x = 82 + i * 280;
        card(slide, ctx, x, 170, 230, 150, { fill: P.white });
        label(slide, ctx, x + 22, 194, 160, 28, l[0], { size: 21, bold: true, color: [P.blue, P.cyan, P.green, P.amber][i] });
        label(slide, ctx, x + 22, 238, 180, 48, l[1], { size: 14, color: P.muted });
        if (i < 3) arrow(slide, ctx, x + 232, 245, x + 272, 245, "#9AA7BB");
      });
      card(slide, ctx, 130, 410, 1020, 124, { fill: "#101827", line: "#101827" });
      label(slide, ctx, 160, 433, 180, 28, "MVP 完成标准", { size: 21, bold: true, color: P.white });
      data.done.forEach((d, i) => label(slide, ctx, 390, 430 + i * 33, 680, 26, d, { size: 17, color: "#EAF0FF" }));
    }

    if (data.type === "team") {
      data.roles.forEach((r, i) => {
        const y = 150 + i * 84;
        card(slide, ctx, 82, y, 1090, 58, { fill: i % 2 === 0 ? P.white : "#F0FBFA" });
        label(slide, ctx, 108, y + 15, 160, 24, r[0], { size: 18, bold: true, color: [P.blue, P.green, P.cyan, P.amber, P.red][i] });
        label(slide, ctx, 310, y + 16, 760, 24, r[1], { size: 15, color: P.ink });
      });
    }

    if (data.type === "roadmap") {
      data.roadmap.forEach((r, i) => {
        const x = 74 + i * 292;
        card(slide, ctx, x, 158, 245, 250, { fill: P.white });
        label(slide, ctx, x + 20, 184, 140, 26, r[0], { size: 19, bold: true, color: P.blue });
        label(slide, ctx, x + 20, 226, 180, 32, r[1], { size: 18, bold: true });
        label(slide, ctx, x + 20, 278, 195, 72, r[2], { size: 13.5, color: P.muted });
      });
      card(slide, ctx, 144, 486, 980, 84, { fill: "#FFF7E8", line: "#F2D3A7" });
      label(slide, ctx, 174, 510, 110, 28, "本周需要", { size: 20, bold: true, color: P.amber });
      data.asks.forEach((a, i) => label(slide, ctx, 330 + i * 250, 505, 220, 38, a, { size: 15, color: P.ink }));
    }

    addFooter(slide, ctx, n);
  }
  return slide;
}
