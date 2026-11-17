#!/usr/bin/env python3
"""
HNAI-FPGA 项目讲解 PPT 生成脚本
32 页，8 章，约 40 分钟深度汇报版
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu, Cm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import copy
from pathlib import Path

# ═══════════════════════════════════════════════════
# 颜色方案
# ═══════════════════════════════════════════════════
# Primary: Deep navy blue (academic/tech)
PRIMARY = RGBColor(0x1A, 0x3C, 0x6E)  # #1A3C6E
PRIMARY_DARK = RGBColor(0x0F, 0x24, 0x45)  # #0F2445
ACCENT = RGBColor(0x00, 0x8A, 0xCC)  # #008ACC - cyan/blue accent
ACCENT_GREEN = RGBColor(0x00, 0xA8, 0x6B)  # #00A86B - green
ACCENT_ORANGE = RGBColor(0xE8, 0x6A, 0x17)  # #E86A17 - orange/warning
ACCENT_RED = RGBColor(0xDC, 0x35, 0x35)  # #DC3535 - red
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x1A, 0x1A, 0x1A)
DARK_GRAY = RGBColor(0x33, 0x33, 0x33)
MED_GRAY = RGBColor(0x66, 0x66, 0x66)
LIGHT_GRAY = RGBColor(0xE8, 0xEC, 0xF0)
BG_LIGHT = RGBColor(0xF5, 0xF7, 0xFA)
TABLE_HEADER = RGBColor(0x1A, 0x3C, 0x6E)
TABLE_ROW_ALT = RGBColor(0xED, 0xF1, 0xF7)

prs = Presentation()
prs.slide_width = Inches(13.333)  # 16:9 widescreen
prs.slide_height = Inches(7.5)

# ═══════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════


def add_blank_slide():
    """Add a blank slide."""
    layout = prs.slide_layouts[6]  # blank
    return prs.slides.add_slide(layout)


def add_textbox(slide, left, top, width, height, text="",
                font_size=18, bold=False, color=BLACK, font_name="Microsoft YaHei",
                alignment=PP_ALIGN.LEFT, line_spacing=1.3):
    """Add a text box with single paragraph."""
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top),
                                     Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font_name
    p.alignment = alignment
    p.space_after = Pt(line_spacing * font_size - font_size) if line_spacing else Pt(0)
    return tf


def add_rich_textbox(slide, left, top, width, height):
    """Add a text box and return its text frame for manual paragraph building."""
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top),
                                     Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    return tf


def add_paragraph(tf, text, font_size=16, bold=False, color=BLACK,
                  font_name="Microsoft YaHei", alignment=PP_ALIGN.LEFT,
                  space_after=6, level=0, bullet=False):
    """Add a paragraph to an existing text frame."""
    if len(tf.paragraphs) == 1 and tf.paragraphs[0].text == "":
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font_name
    p.alignment = alignment
    p.space_after = Pt(space_after)
    p.level = level
    return p


def add_slide_title(slide, title, subtitle=None):
    """Add a chapter/slide title bar at the top."""
    # Title background bar
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0), Inches(0),
        prs.slide_width, Inches(0.95)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = PRIMARY
    shape.line.fill.background()

    # Title text
    add_textbox(slide, 0.8, 0.15, 11.5, 0.6, title,
                font_size=28, bold=True, color=WHITE)

    if subtitle:
        add_textbox(slide, 0.8, 0.62, 11.5, 0.35, subtitle,
                    font_size=13, bold=False, color=RGBColor(0xBB, 0xCC, 0xDD))


def add_section_header(slide, section_num, section_title, section_subtitle=""):
    """Full-slide section header with chapter number."""
    # Full background
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0), Inches(0),
        prs.slide_width, prs.slide_height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = PRIMARY
    shape.line.fill.background()

    # Chapter number
    add_textbox(slide, 1.2, 1.8, 11, 1.0,
                f"第{section_num}章",
                font_size=24, bold=False, color=RGBColor(0x88, 0xAA, 0xCC))

    # Chapter title
    add_textbox(slide, 1.2, 2.8, 11, 1.2,
                section_title,
                font_size=42, bold=True, color=WHITE)

    if section_subtitle:
        add_textbox(slide, 1.2, 4.2, 11, 0.8,
                    section_subtitle,
                    font_size=18, bold=False, color=RGBColor(0xAA, 0xCC, 0xEE))

    # Accent line
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(1.2), Inches(4.0), Inches(1.5), Inches(0.04)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = ACCENT
    line.line.fill.background()


def add_table(slide, left, top, col_widths, headers, rows, font_size=11):
    """Add a formatted table."""
    n_rows = len(rows) + 1
    n_cols = len(headers)
    tbl_width = sum(col_widths)

    table_shape = slide.shapes.add_table(n_rows, n_cols,
                                         Inches(left), Inches(top),
                                         Inches(tbl_width),
                                         Inches(0.35 * n_rows))
    table = table_shape.table

    # Set column widths
    for i, w in enumerate(col_widths):
        table.columns[i].width = Inches(w)

    # Header row
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(font_size)
            p.font.bold = True
            p.font.color.rgb = WHITE
            p.font.name = "Microsoft YaHei"
            p.alignment = PP_ALIGN.CENTER
        cell.fill.solid()
        cell.fill.fore_color.rgb = TABLE_HEADER

    # Data rows
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            cell.text = str(val)
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(font_size)
                p.font.color.rgb = DARK_GRAY
                p.font.name = "Microsoft YaHei"
                p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            if i % 2 == 1:
                cell.fill.solid()
                cell.fill.fore_color.rgb = TABLE_ROW_ALT

    return table


def add_code_block(slide, left, top, width, height, code_text,
                   font_size=10, title=None):
    """Add a code-like block with dark background."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top),
        Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(0x1E, 0x2A, 0x38)
    shape.line.fill.background()

    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.15)
    tf.margin_right = Inches(0.15)
    tf.margin_top = Inches(0.1)
    tf.margin_bottom = Inches(0.1)

    if title:
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(font_size - 1)
        p.font.bold = True
        p.font.color.rgb = ACCENT
        p.font.name = "JetBrains Mono"
        p.space_after = Pt(4)
        p2 = tf.add_paragraph()
    else:
        p2 = tf.paragraphs[0]

    p2.text = code_text
    p2.font.size = Pt(font_size)
    p2.font.color.rgb = RGBColor(0xCC, 0xDD, 0xEE)
    p2.font.name = "JetBrains Mono"
    p2.line_spacing = Pt(16)

    return tf


def add_flow_box(slide, left, top, width, height, text, fill_color=PRIMARY,
                 text_color=WHITE, font_size=12, bold=True):
    """Add a rounded rectangle with text (flow diagram box)."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top),
        Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()

    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = text_color
    p.font.name = "Microsoft YaHei"
    p.alignment = PP_ALIGN.CENTER
    return tf


def add_arrow_down(slide, left, top):
    """Add a down arrow symbol."""
    add_textbox(slide, left, top, 0.4, 0.3, "▼",
                font_size=12, color=MED_GRAY, alignment=PP_ALIGN.CENTER)


def add_check_cross(slide, left, top, check=True):
    """Add a checkmark or cross."""
    symbol = "✓" if check else "✗"
    color = ACCENT_GREEN if check else ACCENT_RED
    add_textbox(slide, left, top, 0.3, 0.25, symbol,
                font_size=14, bold=True, color=color, alignment=PP_ALIGN.CENTER)


def add_page_number(slide, num, total=32):
    """Add page number to bottom right."""
    add_textbox(slide, 11.5, 7.05, 1.5, 0.35,
                f"{num} / {total}",
                font_size=9, color=MED_GRAY, alignment=PP_ALIGN.RIGHT)


# ═══════════════════════════════════════════════════
# 第一章：为什么需要 HNAI-FPGA (页 1-6)
# ═══════════════════════════════════════════════════

# --- 页 1: 封面 ---
slide = add_blank_slide()
# Full background
shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0),
                               prs.slide_width, prs.slide_height)
shape.fill.solid()
shape.fill.fore_color.rgb = PRIMARY_DARK
shape.line.fill.background()

# Decorative top accent
shape2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0),
                                prs.slide_width, Inches(0.06))
shape2.fill.solid()
shape2.fill.fore_color.rgb = ACCENT
shape2.line.fill.background()

add_textbox(slide, 1.5, 1.5, 10.5, 1.2, "HNAI-FPGA",
            font_size=56, bold=True, color=WHITE, font_name="Calibri")

add_textbox(slide, 1.5, 2.8, 10.5, 1.2,
            "面向非 DNN AI 算法的自然语言到 FPGA 自动设计与约束优化框架",
            font_size=22, bold=False, color=RGBColor(0xBB, 0xCC, 0xDD))

# Accent line
shape3 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                Inches(1.5), Inches(4.1), Inches(2.5), Inches(0.04))
shape3.fill.solid()
shape3.fill.fore_color.rgb = ACCENT
shape3.line.fill.background()

add_textbox(slide, 1.5, 4.4, 10.5, 0.5,
            "基于分层硬件意图 IR（HIS） | MLIR/CIRCT 编译链路 | EDA 反馈闭环",
            font_size=14, bold=False, color=RGBColor(0x88, 0x9A, 0xAA))

add_textbox(slide, 1.5, 5.8, 10.5, 0.4,
            "2026.06",
            font_size=14, bold=False, color=MED_GRAY)
add_page_number(slide, 1)

# --- 页 2: 技术演进时间轴 ---
slide = add_blank_slide()
add_slide_title(slide, "技术演进全景：从手写 RTL 到自动架构设计",
                "AI 驱动硬件自动设计，十年走过了九个阶段")

stages = [
    ("1980s", "手工 RTL", "工程师直接设计 FSM/Datapath\nPipeline/Cache/BRAM/接口协议\n完全可控，但周期长、成本高", 0xFFF5F0),
    ("2000s", "HLS", "Vitis HLS / Intel HLS / Bambu\nC/C++ → Scheduling → RTL\n提高效率，但只能实现设计\n不能发明架构", 0xF0F5FF),
    ("2010s", "DSE", "AutoDSE / AutoSA / FINN / hls4ml\n搜索 Pipeline深度/PE数量/Tile大小\n本质是自动调参，不是自动设计", 0xFFF5F0),
    ("2023", "LLM→RTL", "NVIDIA VerilogEval (ICCAD)\n首次系统评估：LLM能否生成RTL？", 0xF0F5FF),
    ("23-25", "RTL专用模型", "HKUST RTLCoder\n引入 Code Quality Feedback\n仍解决代码生成，非架构设计", 0xFFF5F0),
    ("2024", "生成-修复闭环", "Generate → Compile → Repair\n显著提高 RTL 正确率，片段级", 0xF0F5FF),
    ("2025", "Agent系统", "NVIDIA Spec2RTL-Agent ⬅ SOTA\n多Agent协同，处理真实规格文档", 0xE8F4FD),
    ("24-25", "结构化表示", "RTL++ / Graph / AST / IR\n真正重要的是数据流、并行结构\n不是 RTL 文本本身", 0xF0F5FF),
    ("20-至今", "MLIR/CIRCT", "LLVM社区 (Google/Intel/AMD/SiFive)\n硬件版LLVM：结构化硬件设计", 0xFFF5F0),
]

y_start = 1.5
for i, (era, title, desc, bg) in enumerate(stages):
    x = 0.3 + (i % 5) * 2.55
    y = y_start + (i // 5) * 2.5

    # Stage box
    box = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(x), Inches(y), Inches(2.4), Inches(2.1)
    )
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor((bg >> 16) & 0xFF, (bg >> 8) & 0xFF, bg & 0xFF)
    box.line.color.rgb = RGBColor(0xCC, 0xDD, 0xEE)
    box.line.width = Pt(0.5)

    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.12)
    tf.margin_right = Inches(0.08)
    tf.margin_top = Inches(0.08)

    p_era = tf.paragraphs[0]
    p_era.text = era
    p_era.font.size = Pt(10)
    p_era.font.bold = True
    p_era.font.color.rgb = ACCENT
    p_era.font.name = "Calibri"

    p_title = tf.add_paragraph()
    p_title.text = title
    p_title.font.size = Pt(12)
    p_title.font.bold = True
    p_title.font.color.rgb = PRIMARY
    p_title.font.name = "Microsoft YaHei"
    p_title.space_after = Pt(4)

    p_desc = tf.add_paragraph()
    p_desc.text = desc
    p_desc.font.size = Pt(8.5)
    p_desc.font.color.rgb = DARK_GRAY
    p_desc.font.name = "Microsoft YaHei"
    p_desc.line_spacing = Pt(13)

# Arrows between stages
for i in range(4):
    add_textbox(slide, 2.45 + i * 2.55, y_start + 0.8, 0.5, 0.3, "→",
                font_size=18, bold=True, color=ACCENT, alignment=PP_ALIGN.CENTER)
for i in range(4):
    add_textbox(slide, 2.45 + i * 2.55, y_start + 3.3, 0.5, 0.3, "→",
                font_size=18, bold=True, color=ACCENT, alignment=PP_ALIGN.CENTER)

# Bottom insight
add_textbox(slide, 0.5, 6.5, 12.5, 0.5,
            "趋势：从 「AI 帮人写代码」 → 「AI 设计硬件架构并自动优化」  |  Spec2RTL 站在第七个台阶，HNAI-FPGA 瞄准第九和第十个",
            font_size=13, bold=True, color=PRIMARY, alignment=PP_ALIGN.CENTER)
add_page_number(slide, 2)

# --- 页 3: 核心洞察 ---
slide = add_blank_slide()
add_slide_title(slide, "演进的核心洞察", "每一代工具解决的问题 vs 留下的空白")

headers = ["阶段", "代表工作", "解决了什么", "没解决什么"]
rows = [
    ["HLS", "Vitis HLS, Bambu", "C → RTL 自动化", "架构由人设计"],
    ["DSE", "AutoDSE, AutoSA", "参数自动搜索", "架构模板由人定义"],
    ["LLM+RTL模型", "VerilogEval, RTLCoder", "从描述生成代码片段", "约束检查、时序闭环、非代码任务"],
    ["Agent系统", "Spec2RTL-Agent", "多Agent协作 + 规格文档", "无分层IR、无EDA反馈到架构\n不覆盖非DNN AI"],
    ["结构化表示", "RTL++", "图结构增强生成质量", "缺少编译链路和验证闭环"],
    ["MLIR/CIRCT", "LLVM社区", "硬件设计结构化IR", "缺少上层意图表达\n和自动架构搜索"],
]
add_table(slide, 0.5, 1.3, [1.5, 2.2, 3.0, 5.5], headers, rows, font_size=12)

# Key pattern box
box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                             Inches(0.5), Inches(4.6), Inches(12.3), Inches(2.2))
box.fill.solid()
box.fill.fore_color.rgb = RGBColor(0xE8, 0xF4, 0xFD)
box.line.color.rgb = ACCENT
box.line.width = Pt(1.5)

tf = box.text_frame
tf.word_wrap = True
tf.margin_left = Inches(0.3)
tf.margin_top = Inches(0.15)

add_paragraph(tf, "关键模式", font_size=18, bold=True, color=PRIMARY)
add_paragraph(tf, "每一代进步都在往上游走——从实现自动化 → 参数自动化 → 代码自动化 → 架构自动化。", font_size=14, color=DARK_GRAY)
add_paragraph(tf, "", font_size=6, color=DARK_GRAY)
add_paragraph(tf, "但没有人把「分层意图 IR + 编译级 lowering + EDA 反馈闭环」串成一条完整链路。这就是 HNAI-FPGA 要做的事。", font_size=15, bold=True, color=ACCENT)
add_page_number(slide, 3)

# --- 页 4: Spec2RTL 对比 ---
slide = add_blank_slide()
add_slide_title(slide, "Spec2RTL：最接近的参照系", "Spec2RTL 证明了这条路可行，也暴露了这条路还缺什么")

# Left: what Spec2RTL does
add_textbox(slide, 0.5, 1.3, 5.5, 0.4, "✅  Spec2RTL 做到了", font_size=20, bold=True, color=ACCENT_GREEN)
spec_done = [
    "自然语言 → 结构化 Spec",
    "多 Agent 协作（推理/编码/反思）",
    "处理真实规格文档",
    "基于 LLM 的生成能力",
]
for i, item in enumerate(spec_done):
    add_textbox(slide, 1.0, 1.85 + i * 0.42, 5.5, 0.35,
                f"✓  {item}", font_size=14, color=DARK_GRAY)

# Right: what Spec2RTL doesn't do
add_textbox(slide, 7.0, 1.3, 6.0, 0.4, "❌  Spec2RTL 没做到", font_size=20, bold=True, color=ACCENT_RED)
spec_undone = [
    "Spec 直接到 RTL，中间无可检查的 IR 层",
    "没有硬件意图表示承载约束和验证条件",
    "没有 EDA 反馈回写架构参数的闭环",
    "不覆盖 GA/RL/路径规划等非 DNN AI 算法",
    "输出是 RTL 片段，不是可部署的 FPGA 工程包",
]
for i, item in enumerate(spec_undone):
    add_textbox(slide, 6.5, 1.85 + i * 0.42, 6.5, 0.35,
                f"✗  {item}", font_size=14, color=DARK_GRAY)

# Comparison diagram
add_textbox(slide, 0.5, 4.3, 12, 0.35, "路径对比", font_size=16, bold=True, color=PRIMARY)

# Spec2RTL path
add_flow_box(slide, 0.5, 4.8, 5.8, 1.2,
             "Spec2RTL:\nSpec → [Reasoning → Coding → Reflection Agent] → HLS → RTL (片段)\n\n⚠ 缺 IR 层 · 缺约束检查 · 缺 EDA 反馈闭环",
             fill_color=RGBColor(0xEE, 0xEE, 0xEE), text_color=MED_GRAY, font_size=11, bold=False)

# Arrow
add_textbox(slide, 6.2, 5.2, 0.8, 0.5, "⟹", font_size=28, bold=True, color=ACCENT, alignment=PP_ALIGN.CENTER)

# HNAI path
add_flow_box(slide, 7.0, 4.8, 5.8, 1.2,
             "HNAI-FPGA（本课题）:\nNL → SPEC → HIS-L0 → HIS-L1 → HIS-L2\n→ CIRCT/RTL → Vivado/Verilator/UVM → 反馈回写 HIS\n\n↑分层IR ↑lowering 机制 ↑EDA反馈闭环",
             fill_color=PRIMARY, text_color=WHITE, font_size=11, bold=False)
add_page_number(slide, 4)

# --- 页 5: 非 DNN AI 的特殊性 ---
slide = add_blank_slide()
add_slide_title(slide, "为什么非 DNN AI 是一个特殊的问题",
                "现有 FPGA 工具链的架构假设，系统性排除了非 DNN AI")

headers = ["维度", "DNN 推理", "非 DNN AI（GA / RL / 调度 / 规划）"]
rows = [
    ["计算模式", "规整的张量运算", "不规则的控制流 + 数据流"],
    ["存储访问", "规则的层级 buffer", "随机的、依赖数据的访问模式"],
    ["工具覆盖", "Vitis AI / hls4ml / FINN ✓", "空白 ✗"],
    ["算法模板", "Conv/MatMul/Activation 固定", "种群维护、适应度评估、Q-table 更新、路径搜索"],
    ["为什么不行", "—", "架构假设绑定 DNN 计算图，泛化不过去"],
]
add_table(slide, 0.5, 1.3, [2.0, 4.5, 5.5], headers, rows, font_size=12)

# Bottom insight
box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                             Inches(0.5), Inches(4.2), Inches(12.3), Inches(2.6))
box.fill.solid()
box.fill.fore_color.rgb = RGBColor(0xFF, 0xF5, 0xEE)
box.line.color.rgb = ACCENT_ORANGE
box.line.width = Pt(1.5)
tf = box.text_frame
tf.word_wrap = True
tf.margin_left = Inches(0.3)
tf.margin_top = Inches(0.15)

add_paragraph(tf, "非 DNN AI 为什么需要 FPGA？", font_size=18, bold=True, color=PRIMARY)
add_paragraph(tf, "低时延、低功耗、确定性执行——边端推理和实时控制的刚需。", font_size=14, color=DARK_GRAY)
add_paragraph(tf, "", font_size=6, color=DARK_GRAY)
add_paragraph(tf, "但这些算法的 FPGA 实现需要专家手写，门槛极高。DNN 专用工具的架构假设（规整张量运算）与 GA/RL 的计算模式（不规则控制流+随机存储访问）有本质差异。", font_size=14, color=DARK_GRAY)
add_paragraph(tf, "", font_size=6, color=DARK_GRAY)
add_paragraph(tf, "这个空白既有学术价值，也有工程价值。", font_size=15, bold=True, color=ACCENT_ORANGE)
add_page_number(slide, 5)

# --- 页 6: HNAI 在演进中的位置 ---
slide = add_blank_slide()
add_slide_title(slide, "HNAI-FPGA 在演进脉络中的位置",
                "站在这条演进线的下一个节点，融合四条技术线")

# Evolution line
lines = [
    "手写 RTL  ──→  HLS  ──→  DSE  ──→  LLM生成  ──→  专用模型  ──→  Agent系统  ──→  结构化表示  ──→  MLIR/CIRCT",
]
add_textbox(slide, 0.5, 1.4, 12.3, 0.5,
            "技术演进主线：手写 RTL → HLS → DSE → LLM生成 → 专用模型 → Agent系统 → 结构化表示 → MLIR/CIRCT",
            font_size=13, bold=False, color=MED_GRAY, alignment=PP_ALIGN.CENTER)

# Four fusion lines
fusion_items = [
    ("① 结构化表示", "分层 HIS（L0/L1/L2）", 0.5),
    ("② MLIR/CIRCT", "硬件 IR + lowering 编译后端", 3.5),
    ("③ Agent 调度", "工具编排与反馈解释", 6.5),
    ("④ EDA 反馈闭环", "诊断回写 HIS 参数空间", 9.5),
]

for title, desc, x in fusion_items:
    # Arrow down to merge
    add_flow_box(slide, x, 2.3, 2.8, 0.9, f"{title}\n{desc}",
                 fill_color=RGBColor(0xE8, 0xF4, 0xFD), text_color=PRIMARY,
                 font_size=12, bold=True)

# Down arrows
for x in [1.5, 4.4, 7.4, 10.6]:
    add_textbox(slide, x + 0.9, 3.2, 0.5, 0.3, "▼", font_size=14, color=ACCENT, alignment=PP_ALIGN.CENTER)

# Merge box
add_flow_box(slide, 1.5, 3.6, 10.3, 1.2,
             "HNAI-FPGA\n面向非 DNN AI 的完整 FPGA 自动设计框架",
             fill_color=PRIMARY, text_color=WHITE, font_size=20, bold=True)

add_textbox(slide, 1.5, 5.2, 10.3, 0.4, "▼", font_size=14, color=ACCENT, alignment=PP_ALIGN.CENTER)

# Final output
add_flow_box(slide, 1.5, 5.6, 10.3, 0.7,
             "从自然语言出发 → 可验证 FPGA 工程包（RTL + XDC + Testbench + 验证报告）",
             fill_color=ACCENT_GREEN, text_color=WHITE, font_size=15, bold=True)

# Bottom note
add_textbox(slide, 0.5, 6.7, 12.3, 0.5,
            "HNAI-FPGA 不是替代前面的技术，而是把它们中缺失的结构性组件补上：HIS 提供意图 IR，CIRCT 提供编译后端，EDA 提供验证闭环，Agent 负责调度。",
            font_size=12, color=MED_GRAY, alignment=PP_ALIGN.CENTER)
add_page_number(slide, 6)

# ═══════════════════════════════════════════════════
# 第二章：HNAI-FPGA 是什么 (页 7-9)
# ═══════════════════════════════════════════════════

# --- Section Header ---
slide = add_blank_slide()
add_section_header(slide, "二", "HNAI-FPGA 是什么",
                   "一句话定位 · 整体架构 · 关键概念")
add_page_number(slide, 7)

# --- 页 8: 一句话定位 ---
slide = add_blank_slide()
add_slide_title(slide, "一句话定位", "HNAI-FPGA 不是「AI 写 Verilog」工具")

# Core statement
box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                             Inches(0.5), Inches(1.4), Inches(12.3), Inches(1.5))
box.fill.solid()
box.fill.fore_color.rgb = PRIMARY
box.line.fill.background()
tf = box.text_frame
tf.word_wrap = True
tf.margin_left = Inches(0.5)
tf.margin_top = Inches(0.2)
add_paragraph(tf,
              "HNAI-FPGA 是一个从自然语言需求出发，经过分层硬件意图 IR（HIS）、"
              "IR 层约束检查、CIRCT/RTL lowering、EDA 工具验证与反馈优化，"
              "最终生成可验证 FPGA 工程包的自动设计框架。",
              font_size=17, color=WHITE, bold=False, alignment=PP_ALIGN.LEFT)

# Five key choices
add_textbox(slide, 0.5, 3.3, 12, 0.4, "五个关键选择", font_size=16, bold=True, color=PRIMARY)

choices = [
    ("分层硬件意图 IR", "不是 JSON 需求文档", "是可检查、可追踪、可优化的三层硬件中间表示"),
    ("IR 层约束检查", "不是生成后再修", "在生成 RTL 前检查并行度/流水线/资源/时序"),
    ("Lowering 机制", "不是 LLM 直接到 RTL", "是程序化、可验证的逐层下沉"),
    ("EDA 反馈闭环", "不是把 Vivado 日志扔给 LLM", "是结构化诊断 → 回写 HIS 参数 → 约束引导重生成"),
    ("可验证 FPGA 工程包", "不是 RTL 代码片段", "是 RTL + XDC + testbench + 验证报告 + 诊断日志"),
]
for i, (keyword, not_what, is_what) in enumerate(choices):
    y = 3.85 + i * 0.6
    add_textbox(slide, 1.0, y, 2.8, 0.5, keyword, font_size=14, bold=True, color=ACCENT)
    add_textbox(slide, 3.9, y, 3.2, 0.5, f"❌ {not_what}", font_size=12, color=MED_GRAY)
    add_textbox(slide, 7.2, y, 5.5, 0.5, f"✅ {is_what}", font_size=12, color=DARK_GRAY)
add_page_number(slide, 8)

# --- 页 9: 整体架构图 ---
slide = add_blank_slide()
add_slide_title(slide, "整体架构图", "一张图看懂 HNAI-FPGA 的全链路")

# Architecture diagram - built with flow boxes
components = [
    # (left, top, width, height, text, color)
    (4.5, 1.3, 4.3, 0.6, "自然语言需求", RGBColor(0x55, 0x55, 0x55)),
    (5.3, 2.05, 2.5, 0.35, "▼", RGBColor(0x88, 0x88, 0x88)),
    (4.5, 2.4, 4.3, 0.55, "SPEC（人类可读需求规格）", RGBColor(0x66, 0x66, 0x66)),
]

for left, top, w, h, text, color in components:
    add_flow_box(slide, left, top, w, h, text, fill_color=color, text_color=WHITE, font_size=13)

# HIS box - big and prominent
box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                             Inches(1.0), Inches(3.2), Inches(11.3), Inches(2.1))
box.fill.solid()
box.fill.fore_color.rgb = RGBColor(0xE8, 0xF4, 0xFD)
box.line.color.rgb = ACCENT
box.line.width = Pt(2)

tf = box.text_frame
tf.word_wrap = True
tf.margin_left = Inches(0.3)
tf.margin_top = Inches(0.1)
add_paragraph(tf, "HIS（分层硬件意图 IR）", font_size=16, bold=True, color=PRIMARY)

# L0
add_flow_box(slide, 1.3, 3.75, 3.3, 0.65,
             "L0 需求意图层\n算法类别·问题规模·目标FPGA\n资源预算·接口类型·验证方式",
             fill_color=ACCENT, text_color=WHITE, font_size=9.5)

add_textbox(slide, 4.65, 3.85, 0.4, 0.4, "→", font_size=14, bold=True, color=PRIMARY, alignment=PP_ALIGN.CENTER)

# L1
add_flow_box(slide, 5.0, 3.75, 3.3, 0.65,
             "L1 架构意图层\n模块划分·数据流/控制流·存储结构\n并行度·流水线·状态机",
             fill_color=PRIMARY, text_color=WHITE, font_size=9.5)

add_textbox(slide, 8.35, 3.85, 0.4, 0.4, "→", font_size=14, bold=True, color=PRIMARY, alignment=PP_ALIGN.CENTER)

# L2
add_flow_box(slide, 8.7, 3.75, 3.3, 0.65,
             "L2 实现映射层\nCIRCT/MLIR映射·RTL/HLS策略\nXDC·UVM绑定·报告解析规则",
             fill_color=PRIMARY_DARK, text_color=WHITE, font_size=9.5)

# Below HIS
add_textbox(slide, 5.3, 4.7, 2.5, 0.35, "▼", font_size=16, bold=True, color=ACCENT, alignment=PP_ALIGN.CENTER)

add_flow_box(slide, 3.8, 5.05, 5.7, 0.5,
             "五层 Lowering：Intent → Architecture → Compiler → RTL → Feedback",
             fill_color=ACCENT_ORANGE, text_color=WHITE, font_size=13)

# Bottom row: 3 parallel paths
add_textbox(slide, 2.0, 5.7, 3.0, 0.35, "▼", font_size=12, color=MED_GRAY, alignment=PP_ALIGN.CENTER)
add_textbox(slide, 5.6, 5.7, 3.0, 0.35, "▼", font_size=12, color=MED_GRAY, alignment=PP_ALIGN.CENTER)
add_textbox(slide, 9.2, 5.7, 3.0, 0.35, "▼", font_size=12, color=MED_GRAY, alignment=PP_ALIGN.CENTER)

add_flow_box(slide, 0.5, 6.05, 3.5, 0.45, "CIRCT/MLIR\nhw/comb/seq/fsm/sv", fill_color=RGBColor(0x55, 0x77, 0x99), text_color=WHITE, font_size=10)
add_flow_box(slide, 4.4, 6.05, 3.5, 0.45, "模板化 RTL/HLS", fill_color=RGBColor(0x55, 0x77, 0x99), text_color=WHITE, font_size=10)
add_flow_box(slide, 8.3, 6.05, 3.5, 0.45, "Golden Model\n(Python/C++)", fill_color=RGBColor(0x55, 0x77, 0x99), text_color=WHITE, font_size=10)

add_textbox(slide, 2.0, 6.55, 3.0, 0.3, "▼", font_size=10, color=MED_GRAY, alignment=PP_ALIGN.CENTER)
add_textbox(slide, 5.6, 6.55, 3.0, 0.3, "▼", font_size=10, color=MED_GRAY, alignment=PP_ALIGN.CENTER)
add_textbox(slide, 9.2, 6.55, 3.0, 0.3, "▼", font_size=10, color=MED_GRAY, alignment=PP_ALIGN.CENTER)

add_flow_box(slide, 1.0, 6.8, 11.3, 0.4,
             "EDA 工具链 & 验证：Verilator（语法/功能仿真） | Vivado（综合/时序/功耗/DRC） | UVM（验证环境）",
             fill_color=DARK_GRAY, text_color=WHITE, font_size=10)

# Right annotation
add_textbox(slide, 0.3, 5.1, 3.5, 0.35,
            "Agent 负责调度工具、维护状态、\n解释诊断、发起下一轮\n→ 核心是 IR + 约束 + 反馈",
            font_size=8, color=MED_GRAY)
add_page_number(slide, 9)

# --- 页 10: 关键概念速查 ---
slide = add_blank_slide()
add_slide_title(slide, "关键概念速查", "这些术语在 HNAI-FPGA 中的确切含义")

headers = ["概念", "一句话定位", "在本项目中的角色"]
rows = [
    ["SPEC", "人类可读需求规格", "对齐目标、场景、验收标准和交付边界"],
    ["HIS", "分层硬件意图 IR", "核心研究对象——表达需求、架构、约束、接口、验证和实现映射"],
    ["MLIR", "多层中间表示框架", "承载自定义 dialect、verifier、pass 和 lowering 基础设施"],
    ["CIRCT", "硬件领域 MLIR 工具链", "提供 hw/comb/seq/fsm/sv dialect 与 SV 输出能力"],
    ["RTL/HLS", "硬件实现形式", "可综合 Verilog/SV 或 HLS C++ 代码"],
    ["Vivado/Verilator", "验证与实现工具层", "提供语法检查、仿真、综合、时序、功耗和功能验证的结构化反馈"],
    ["UVM", "通用验证方法学", "将 sequence/driver/monitor/scoreboard 组织成专业验证环境"],
    ["Agent", "工具调度与决策层", "调度工具、维护状态、解释诊断——但不是核心研究对象"],
]
add_table(slide, 0.5, 1.2, [2.0, 4.0, 6.3], headers, rows, font_size=12)
add_page_number(slide, 10)

# ═══════════════════════════════════════════════════
# 第三章：核心——分层 HIS 设计 (页 11-15)
# ═══════════════════════════════════════════════════

slide = add_blank_slide()
add_section_header(slide, "三", "核心——分层 HIS 设计",
                   "L0 需求意图 · L1 架构意图 · L2 实现映射 · 三层协同")
add_page_number(slide, 11)

# --- 页 12: 为什么需要 HIS ---
slide = add_blank_slide()
add_slide_title(slide, "为什么需要 HIS",
                "在自然语言和 RTL 之间，缺少一层可检查、可追踪的中间表示")

# Comparison
add_textbox(slide, 0.5, 1.3, 5.5, 0.4, "现有路径（Spec2RTL）", font_size=15, bold=True, color=MED_GRAY)
points_old = [
    "NL / SPEC → LLM 直接生成 → RTL 代码片段",
    "❌ 没有约束检查",
    "❌ 没有合法性验证",
    "❌ 没有可追溯性",
    "❌ 需求变化不知改哪里",
    "❌ EDA 反馈不知回写给谁",
]
for i, p in enumerate(points_old):
    add_textbox(slide, 0.8, 1.85 + i * 0.4, 5.5, 0.35, p, font_size=13, color=MED_GRAY)

add_textbox(slide, 6.0, 2.0, 1.5, 0.8, "⟹", font_size=36, bold=True, color=ACCENT, alignment=PP_ALIGN.CENTER)

add_textbox(slide, 7.0, 1.3, 6.0, 0.4, "HNAI-FPGA 的路径", font_size=15, bold=True, color=PRIMARY)
points_new = [
    "NL → SPEC → HIS-L0 → HIS-L1 → HIS-L2 → CIRCT/RTL Lowering",
    "✅ 生成前 HIS 层约束检查（并行度、资源、时序）",
    "✅ L0→L1→L2 逐层可追踪",
    "✅ L1 显式表达模块/数据流/控制流/状态机",
    "✅ 需求变化知道改哪层",
    "✅ 结构化诊断 → 定位到具体 HIS 参数 → 精准回写",
]
for i, p in enumerate(points_new):
    add_textbox(slide, 7.3, 1.85 + i * 0.4, 6.0, 0.35, p, font_size=13, color=DARK_GRAY)

# Bottom: HIS philosophy
box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                             Inches(0.5), Inches(4.8), Inches(12.3), Inches(2.0))
box.fill.solid()
box.fill.fore_color.rgb = RGBColor(0xE8, 0xF4, 0xFD)
box.line.color.rgb = ACCENT
box.line.width = Pt(1.5)
tf = box.text_frame
tf.word_wrap = True
tf.margin_left = Inches(0.3)
tf.margin_top = Inches(0.15)
add_paragraph(tf, "HIS 的设计哲学", font_size=18, bold=True, color=PRIMARY)
add_paragraph(tf, "不是把需求翻译成 JSON，而是建立一层语义足够丰富、可被机器检查和优化、同时保留自然语言可追溯性的硬件中间表示。", font_size=14, color=DARK_GRAY)
add_paragraph(tf, "", font_size=4, color=DARK_GRAY)
add_paragraph(tf, "例：GA-Knapsack，100MHz → L0 记录目标频率 → L1 分配 3 级流水 → L2 映射 Vivado 时序约束 → 反馈闭环验证", font_size=13, bold=False, color=ACCENT)
add_page_number(slide, 12)

# --- 页 13: HIS-L0 ---
slide = add_blank_slide()
add_slide_title(slide, "HIS-L0：需求意图层", "回答「要做什么、在什么约束下做」")

# Dimensions
dims = [
    ("算法维度", "算法类别、问题规模、数据类型、精度要求、终止条件"),
    ("平台维度", "目标 FPGA 型号、目标频率、可用资源上限（LUT/FF/BRAM/DSP）"),
    ("性能目标", "吞吐量、延迟、功耗上限"),
    ("接口维度", "输入输出接口类型（AXI/AXI-Stream/GPIO/BRAM）、数据位宽"),
    ("验证维度", "验证方式（Golden Model 对比/UVM/形式验证）、验证指标"),
]

for i, (label, desc) in enumerate(dims):
    y = 1.3 + i * 0.75
    add_flow_box(slide, 0.5, y, 1.8, 0.6, label, fill_color=PRIMARY, text_color=WHITE, font_size=13)
    add_textbox(slide, 2.5, y + 0.1, 10, 0.4, desc, font_size=13, color=DARK_GRAY)

# L0 generation flow
add_textbox(slide, 0.5, 5.1, 12, 0.35, "L0 的来源与产出", font_size=16, bold=True, color=PRIMARY)

add_flow_box(slide, 0.5, 5.6, 3.0, 0.55, "自然语言需求\n→ SPEC", fill_color=RGBColor(0x55, 0x55, 0x55), text_color=WHITE, font_size=11)
add_textbox(slide, 3.6, 5.7, 0.5, 0.35, "→", font_size=16, bold=True, color=ACCENT, alignment=PP_ALIGN.CENTER)
add_flow_box(slide, 4.1, 5.6, 2.5, 0.55, "parse_his", fill_color=ACCENT, text_color=WHITE, font_size=13)
add_textbox(slide, 6.7, 5.7, 0.5, 0.35, "→", font_size=16, bold=True, color=ACCENT, alignment=PP_ALIGN.CENTER)
add_flow_box(slide, 7.2, 5.6, 3.0, 0.55, "HIS-L0 JSON\n（结构化需求意图）", fill_color=PRIMARY, text_color=WHITE, font_size=12)

# GA-Knapsack example
add_textbox(slide, 0.5, 6.5, 12, 0.35, "GA-Knapsack 示例 — 算法:GA · 问题:0/1 Knapsack N=256 · FPGA:Artix-7 xc7a35t · 频率:100MHz · 接口:AXI-Stream+AXI-Lite+GPIO · 验证:Python Golden Model", font_size=10.5, color=MED_GRAY)
add_page_number(slide, 13)

# --- 页 14: HIS-L1 ---
slide = add_blank_slide()
add_slide_title(slide, "HIS-L1：架构意图层", "回答「硬件怎么组织、数据怎么流动」——约束检查的主战场")

# Left side: dimensions
add_textbox(slide, 0.5, 1.25, 5.5, 0.35, "L1 包含的维度", font_size=15, bold=True, color=PRIMARY)
l1_dims = [
    "模块划分：顶层模块列表及其职责",
    "数据流图：模块间数据通路、流向、位宽、握手",
    "控制流与状态机：FSM 状态定义与转移条件",
    "存储结构：BRAM/Dist RAM 分配、Bank 数、端口数",
    "并行与流水：并行度、流水线级数、stall 条件",
    "时序预算：关键路径预估、跨时钟域策略",
    "接口协议绑定：AXI 地址映射、burst/width/handshake",
]
for i, d in enumerate(l1_dims):
    add_textbox(slide, 0.8, 1.7 + i * 0.38, 6.0, 0.35, f"• {d}", font_size=11.5, color=DARK_GRAY)

# Right side: GA-Knapsack L1 example
add_textbox(slide, 7.0, 1.25, 5.5, 0.35, "GA-Knapsack L1 示例", font_size=15, bold=True, color=ACCENT_GREEN)
ga_modules = [
    ("PopulationMemory", "256个体×256bit, 双端口BRAM"),
    ("FitnessArray", "256适应度, 3级流水, 4PE并行"),
    ("SelectionUnit", "锦标赛选择(tournament=4)"),
    ("CrossoverUnit", "单点交叉, 可配置交叉率"),
    ("MutationUnit", "按位变异, LFSR随机数"),
    ("ControlFSM", "5状态: INIT→EVAL→SELECT→XMUT→CHECK"),
    ("AXI_Interface", "AXI-Stream Slave + AXI-Lite + GPIO"),
]
for i, (mod, desc) in enumerate(ga_modules):
    add_textbox(slide, 7.3, 1.72 + i * 0.38, 5.8, 0.35,
                f"{mod}: {desc}", font_size=11, color=DARK_GRAY)

# Constraint check table
add_textbox(slide, 0.5, 4.65, 12, 0.35, "L1 层的约束检查（生成 RTL 前执行）", font_size=15, bold=True, color=ACCENT_RED)
headers = ["检查项", "约束来源", "检查内容"]
rows = [
    ["资源预算", "HIS-L0", "模块实例数×单模块预估资源 ≤ L0 预算"],
    ["并行合法性", "架构规则", "并行度 ≤ 数据依赖允许的最大并行度"],
    ["接口匹配", "接口规则", "AXI data width 与内部数据位宽一致"],
    ["时序可行性", "时序模型", "关键路径预估 ≤ 时钟周期/流水级数"],
    ["存储冲突", "存储规则", "同一 BRAM 端口不可同时读写"],
]
add_table(slide, 0.5, 5.05, [1.8, 1.8, 8.7], headers, rows, font_size=11)
add_page_number(slide, 14)

# --- 页 15: HIS-L2 + 三层协同 ---
slide = add_blank_slide()
add_slide_title(slide, "HIS-L2：实现映射层", "回答「如何映射到具体工具链和实现策略」")

# L2 dimensions
add_textbox(slide, 0.5, 1.25, 6.0, 0.35, "L2 包含的维度", font_size=15, bold=True, color=PRIMARY)
l2_items = [
    "IR 路径选择：CIRCT / 模板化 RTL / 混合路径",
    "RTL 生成策略：模板参数实例化 / HLS pragma / CIRCT lowering pass",
    "XDC 约束映射：时钟定义、IO 标准、管脚映射、时序例外",
    "Testbench 策略：激励生成、Golden Vector 格式、对比逻辑",
    "EDA 工具绑定：Vivado Tcl 模板、Verilator 参数、UVM 组件映射",
    "报告解析规则：utilization/timing/power/DRC → 结构化诊断",
]
for i, item in enumerate(l2_items):
    add_textbox(slide, 0.8, 1.7 + i * 0.42, 6.0, 0.35, f"• {item}", font_size=12, color=DARK_GRAY)

# MVP path selection
add_textbox(slide, 7.0, 1.25, 6.0, 0.35, "MVP 阶段的路径选择", font_size=15, bold=True, color=ACCENT_GREEN)
headers = ["路径", "适用场景", "关键特性"]
rows = [
    ["模板化 RTL/HLS", "MVP", "可控性高、调试方便、覆盖有限"],
    ["CIRCT lowering", "中长期", "通用性强、pass可复用、成本高"],
    ["混合路径", "渐进迁移", "MVP验证HIS→中期引入CIRCT"],
]
add_table(slide, 7.0, 1.7, [2.0, 1.3, 2.8], headers, rows, font_size=11)

# Three-layer synergy
add_textbox(slide, 0.5, 4.5, 12, 0.35, "三层协同：约束向下传递，反馈向上追溯", font_size=16, bold=True, color=PRIMARY)

# Flow diagram
add_flow_box(slide, 3.5, 5.0, 2.5, 0.55, "HIS-L0\n需求约束", fill_color=ACCENT, text_color=WHITE, font_size=12)
add_textbox(slide, 5.5, 5.1, 1.0, 0.35, "↓ 传递", font_size=11, color=PRIMARY, alignment=PP_ALIGN.CENTER)
add_flow_box(slide, 6.5, 5.0, 2.5, 0.55, "HIS-L1\n架构约束", fill_color=PRIMARY, text_color=WHITE, font_size=12)
add_textbox(slide, 8.5, 5.1, 1.0, 0.35, "↓ 传递", font_size=11, color=PRIMARY, alignment=PP_ALIGN.CENTER)
add_flow_box(slide, 9.5, 5.0, 2.5, 0.55, "HIS-L2\n实现约束", fill_color=PRIMARY_DARK, text_color=WHITE, font_size=12)

add_textbox(slide, 10.5, 5.65, 0.5, 0.35, "↓", font_size=12, color=ACCENT_ORANGE, alignment=PP_ALIGN.CENTER)
add_flow_box(slide, 9.5, 5.9, 2.5, 0.45, "RTL / CIRCT\n生成+验证", fill_color=ACCENT_ORANGE, text_color=WHITE, font_size=11)

add_textbox(slide, 8.0, 5.95, 1.5, 0.35, "↑ 反馈", font_size=11, color=ACCENT_RED, alignment=PP_ALIGN.CENTER)
add_flow_box(slide, 3.5, 6.5, 2.5, 0.45, "结构化诊断", fill_color=ACCENT_RED, text_color=WHITE, font_size=11)
add_textbox(slide, 5.3, 6.55, 1.0, 0.35, "→回写", font_size=11, color=ACCENT_RED, alignment=PP_ALIGN.CENTER)
add_flow_box(slide, 6.3, 6.5, 2.5, 0.45, "HIS-L1\n参数空间", fill_color=PRIMARY, text_color=WHITE, font_size=11)

add_page_number(slide, 15)

# ═══════════════════════════════════════════════════
# 第四章：Lowering 机制 (页 16-20)
# ═══════════════════════════════════════════════════

slide = add_blank_slide()
add_section_header(slide, "四", "从意图到硬件——Lowering 机制",
                   "五层 Lowering · 程序化逐层转译 · MLIR/CIRCT 定位")
add_page_number(slide, 16)

# --- 页 17: 五层 Lowering 全景 ---
slide = add_blank_slide()
add_slide_title(slide, "五层 Lowering 全景", "程序化转译机制——保证从意图到 RTL 的确定性和可验证性")

# Why not LLM directly
add_textbox(slide, 0.5, 1.2, 12, 0.35, "为什么需要程序化 Lowering？", font_size=16, bold=True, color=PRIMARY)
headers = ["", "LLM 直接生成 RTL", "程序化 Lowering"]
rows = [
    ["确定性", "每次生成可能不同", "相同 HIS → 相同 RTL"],
    ["可定位性", "RTL错了不知哪层的问题", "每层 lowering 独立可验证"],
    ["类型安全", "不保证 SSA 合法性", "程序化 pass 保证 IR 合法性"],
    ["可优化性", "依赖 prompt 工程", "pass pipeline 可组合、可复用"],
]
add_table(slide, 0.5, 1.65, [1.5, 3.5, 3.5], headers, rows, font_size=11)

# Five layers
layers = [
    ("Lowering-1\nIntent Lowering", "需求 → 架构意图", "SPEC/HIS-L0 → HIS-L1\n算法模板选择 + 架构参数实例化", ACCENT),
    ("Lowering-2\nArchitecture Lowering", "算法块 → 硬件块", "HIS-L1 算法块 → 硬件模块描述\nPopulationMemory, FitnessArray等", PRIMARY),
    ("Lowering-3\nCompiler Lowering", "硬件块 → CIRCT IR", "硬件模块 → CIRCT dialect/模板化DSL\nhw, comb, seq, fsm, sv", PRIMARY_DARK),
    ("Lowering-4\nRTL Lowering", "IR → Verilog", "CIRCT IR → SystemVerilog\n或模板实例化RTL + XDC + TB", RGBColor(0x33, 0x55, 0x77)),
    ("Lowering-5\nFeedback Lowering", "EDA报告 → 诊断", "Vivado/Verilator/UVM → 结构化诊断\n→ 回写 HIS-L1 参数空间", ACCENT_RED),
]

for i, (name, transform, detail, color) in enumerate(layers):
    x = 0.3 + i * 2.55
    add_flow_box(slide, x, 4.0, 2.4, 1.15, name, fill_color=color, text_color=WHITE, font_size=10)
    add_textbox(slide, x + 0.1, 4.6, 2.2, 0.3, detail, font_size=7.5, color=WHITE)
    if i < 4:
        add_textbox(slide, x + 2.35, 4.4, 0.3, 0.4, "→", font_size=16, bold=True, color=ACCENT, alignment=PP_ALIGN.CENTER)

add_page_number(slide, 17)

# --- 页 18: Lowering 1&2 详细 ---
slide = add_blank_slide()
add_slide_title(slide, "Lowering-1 & 2：意图到架构", "把「要解决什么问题」变成「硬件长什么样」")

# L1 detail
add_textbox(slide, 0.3, 1.25, 6.3, 0.35, "Lowering-1: Intent Lowering (SPEC/HIS-L0 → HIS-L1)", font_size=14, bold=True, color=ACCENT)
l1_steps = [
    "步骤 1: 算法模板匹配 — GA/RL/调度/规划 → 模板库检索 → 最佳模板",
    "步骤 2: 约束传播 — L0约束 → L1约束空间 (100MHz → 关键路径≤10ns)",
    "步骤 3: 架构参数实例化 — N=256 → pop=128, PE=4, Bank=2",
]
for i, s in enumerate(l1_steps):
    add_textbox(slide, 0.6, 1.7 + i * 0.35, 6.0, 0.3, f"• {s}", font_size=11, color=DARK_GRAY)

# L2 detail
add_textbox(slide, 6.8, 1.25, 6.3, 0.35, "Lowering-2: Architecture Lowering (算法块 → 硬件块)", font_size=14, bold=True, color=PRIMARY)

# Algorithm → Hardware mapping table
headers = ["算法概念", "硬件模块"]
rows = [
    ["种群（Population）", "PopulationMemory"],
    ["适应度函数", "FitnessArray (含流水线)"],
    ["选择算子", "SelectionUnit"],
    ["交叉算子", "CrossoverUnit"],
    ["变异算子", "MutationUnit (LFSR)"],
    ["进化循环控制", "ControlFSM"],
    ["数据输入输出", "AXI_Interface"],
]
add_table(slide, 6.8, 1.7, [2.5, 3.0], headers, rows, font_size=10.5)

# Hardware parameter filling
add_textbox(slide, 0.3, 3.7, 12.5, 0.35, "硬件参数填充与互联生成", font_size=14, bold=True, color=PRIMARY)
params = [
    "PopulationMemory: 深度=128, 位宽=256, 双端口BRAM, Bank=1",
    "FitnessArray: 并行度=4, 流水线=3级, 数据位宽=32bit",
    "ControlFSM: 5状态 (INIT→EVAL→SELECT→CROSSOVER_MUTATE→CHECK), 状态转移表自动生成",
    "模块互联: PopulationMemory → FitnessArray (128-bit, valid/ready) | FitnessArray → SelectionUnit (32-bit×4)",
]
for i, p in enumerate(params):
    add_textbox(slide, 0.6, 4.2 + i * 0.38, 12.0, 0.32, f"• {p}", font_size=11.5, color=DARK_GRAY)

# Bottom note
add_textbox(slide, 0.5, 6.6, 12.3, 0.5,
            "这两步是 LLM 做不好的——因为 LLM 不理解算法结构到硬件结构的映射规律。但程序化模板可以。",
            font_size=12, bold=True, color=ACCENT_ORANGE)
add_page_number(slide, 18)

# --- 页 19: Lowering 3&4 ---
slide = add_blank_slide()
add_slide_title(slide, "Lowering-3 & 4：硬件到 RTL 的转译",
                "把硬件模块描述变成可综合的 SystemVerilog 代码")

# Two paths
add_textbox(slide, 0.5, 1.25, 5.8, 0.35, "路径 A：CIRCT 路径（中长期）", font_size=14, bold=True, color=PRIMARY)
circt_steps = [
    "PopulationMemory → hw.module + seq clock gating",
    "FitnessArray → comb operations + seq pipeline registers",
    "ControlFSM → fsm.state + fsm.transition",
    "AXI_Interface → sv.interface + sv.modport",
    "互联关系 → hw.instance + hw.output/hw.input",
    "↓ 输出：CIRCT IR（MLIR in-memory）",
]
for i, s in enumerate(circt_steps):
    add_textbox(slide, 0.8, 1.72 + i * 0.35, 5.5, 0.3, s, font_size=11, color=DARK_GRAY)

add_textbox(slide, 6.5, 1.25, 6.0, 0.35, "路径 B：模板化 RTL 路径（MVP）", font_size=14, bold=True, color=ACCENT_GREEN)
tmpl_steps = [
    "硬件模块清单 → 参数化 Verilog 模板",
    'module PopulationMemory #(DEPTH=128, WIDTH=256) (...)',
    "模板引擎自动填充端口、参数、内部逻辑",
    "↓ 输出：RTL 代码（SystemVerilog .sv 文件）",
]
for i, s in enumerate(tmpl_steps):
    add_textbox(slide, 6.8, 1.72 + i * 0.35, 6.0, 0.3, s, font_size=11, color=DARK_GRAY)

# Lowering-4 output
add_textbox(slide, 0.5, 3.8, 12, 0.35, "Lowering-4: RTL Lowering — 输出物清单", font_size=14, bold=True, color=PRIMARY)

outputs = [
    "├── top.sv          (顶层模块)",
    "├── population_memory.sv",
    "├── fitness_array.sv",
    "├── selection_unit.sv / crossover_unit.sv / mutation_unit.sv",
    "├── control_fsm.sv / axi_interface.sv",
    "├── constraints.xdc (IO/时钟/时序约束)",
    "└── testbench.sv    (激励 + Golden Vector 对比)",
]
for i, o in enumerate(outputs):
    add_textbox(slide, 1.0, 4.25 + i * 0.35, 11, 0.3, o, font_size=11, color=DARK_GRAY, font_name="JetBrains Mono")

# Key insight
add_textbox(slide, 0.5, 6.7, 12, 0.5,
            "MVP 用模板 → 可控、可调试、快速验证 HIS 设计 | 中长期用 CIRCT → 复用 MLIR 生态的优化 pass | 两条路径共享同一套 HIS 输入，切换平滑",
            font_size=12, bold=True, color=PRIMARY)
add_page_number(slide, 19)

# --- 页 20: Lowering-5 反馈闭环 ---
slide = add_blank_slide()
add_slide_title(slide, "Lowering-5：EDA 反馈 → 结构化诊断 → 回写 HIS",
                "EDA 报告不是给 LLM 看的日志，而是可回写 HIS 的结构化诊断")

# Comparison: old vs new
add_textbox(slide, 0.5, 1.25, 5.5, 0.35, "错误做法：日志直接给 LLM", font_size=14, bold=True, color=ACCENT_RED)
add_textbox(slide, 0.8, 1.7, 5.5, 1.2,
            "Vivado 日志（几千行文本）\n  ↓\nLLM 自由解读\n  ↓\n❌ 可能误读  ❌ 可能漏警告  ❌ 无法精确定位",
            font_size=11, color=MED_GRAY, font_name="JetBrains Mono")

add_textbox(slide, 7.0, 1.25, 6.0, 0.35, "正确做法：程序化解析 + 结构化诊断", font_size=14, bold=True, color=ACCENT_GREEN)
add_textbox(slide, 7.3, 1.7, 6.0, 1.2,
            "Vivado 报告（结构化数据源）\n  ↓ parse_feedback\n结构化诊断 JSON\n  ↓\n✅ 回写 HIS-L1 参数空间",
            font_size=11, color=DARK_GRAY, font_name="JetBrains Mono")

# Feedback → HIS mapping table
add_textbox(slide, 0.5, 3.2, 12, 0.35, "诊断类型 → HIS 回写映射规则", font_size=14, bold=True, color=PRIMARY)
headers = ["诊断信号", "诊断含义", "回写目标", "调整策略"]
rows = [
    ["WNS < 0", "关键路径时序违规", "L1: 流水线级数", "增加 1-2 级流水"],
    ["LUT > 100%", "逻辑资源超限", "L1: 并行度", "减少 PE 数量"],
    ["WNS<0 且 LUT>100%", "时序+资源同时超限", "L0: 目标频率/模板", "降频或切换模板"],
    ["power > budget", "功耗超标", "L0: 目标频率", "降频，启用门控时钟"],
    ["function mismatch", "功能不正确", "L1: 架构结构", "检查 FSM 转移、数据通路"],
    ["DRC failure", "设计规则违规", "L2: XDC 约束", "修正 IO 标准、时钟定义"],
]
add_table(slide, 0.5, 3.65, [2.8, 2.5, 2.5, 4.5], headers, rows, font_size=10.5)

# Agent decision
add_textbox(slide, 0.5, 6.20, 12.5, 0.6,
            "Agent 决策点：确定性规则自动修复 → 规则无法覆盖时 DSE 搜索 → 超出规则时升级人工介入",
            font_size=12, bold=True, color=ACCENT_ORANGE)
add_page_number(slide, 20)

# --- 页 21: MLIR/CIRCT 定位 ---
slide = add_blank_slide()
add_slide_title(slide, "MLIR/CIRCT 的项目定位", "CIRCT 是什么、不是什么、以及何时引入")

# Three principles
add_textbox(slide, 0.5, 1.25, 12, 0.35, "定位三原则", font_size=18, bold=True, color=PRIMARY)
principles = [
    ("CIRCT 不替代 HIS", "HIS 是高层硬件意图 IR（表达架构）；CIRCT 是低层硬件 IR（表达电路实现）。两者各司其职，不是竞争关系。"),
    ("不在 MVP 中强依赖", "MVP 用 HIS JSON + 模板化 RTL 先跑通全链路，验证 HIS 设计的正确性，再逐步引入 CIRCT 后端。"),
    ("LLM 不直接生成 MLIR", "直接让 LLM 生成 MLIR 文本易出现 SSA 值引用错误、类型不匹配、dialect 混用。正确做法：LLM → HIS → 程序化 pass → CIRCT IR。"),
]
for i, (title, desc) in enumerate(principles):
    y = 1.75 + i * 0.8
    add_textbox(slide, 0.8, y, 2.8, 0.35, title, font_size=14, bold=True, color=ACCENT)
    add_textbox(slide, 3.7, y, 9.0, 0.6, desc, font_size=12, color=DARK_GRAY)

# Evolution timeline
add_textbox(slide, 0.5, 4.3, 12, 0.35, "三阶段演进路线", font_size=16, bold=True, color=PRIMARY)

add_flow_box(slide, 0.5, 4.8, 3.8, 1.0,
             "MVP（当前）\nHIS JSON → 模板化RTL/HLS\n→ SystemVerilog\n→ Vivado/Verilator",
             fill_color=ACCENT_GREEN, text_color=WHITE, font_size=11, bold=True)

add_textbox(slide, 4.4, 5.1, 0.6, 0.4, "⟹", font_size=24, bold=True, color=ACCENT, alignment=PP_ALIGN.CENTER)

add_flow_box(slide, 5.0, 4.8, 3.8, 1.0,
             "中期\nHIS JSON → CIRCT hw/sv\n+ 模板RTL（混合）\n→ SystemVerilog\n→ Vivado + UVM + XDC",
             fill_color=PRIMARY, text_color=WHITE, font_size=11, bold=True)

add_textbox(slide, 8.9, 5.1, 0.6, 0.4, "⟹", font_size=24, bold=True, color=ACCENT, alignment=PP_ALIGN.CENTER)

add_flow_box(slide, 9.5, 4.8, 3.5, 1.0,
             "长期\nHNAI MLIR Dialect\n→ verifier/canonicalize/DSE/lowering\n→ CIRCT → 跨层协同优化\n→ FPGA/ASIC",
             fill_color=PRIMARY_DARK, text_color=WHITE, font_size=11, bold=True)

add_page_number(slide, 21)

# ═══════════════════════════════════════════════════
# 第五章：端到端案例 (页 22-25)
# ═══════════════════════════════════════════════════

slide = add_blank_slide()
add_section_header(slide, "五", "端到端案例——GA-Knapsack 全链路追踪",
                   "从自然语言需求到可验证 FPGA 工程包 · 六阶段完整流转")
add_page_number(slide, 22)

# --- 页 23: 案例输入 ---
slide = add_blank_slide()
add_slide_title(slide, "案例设定：自然语言 → HIS-L0", "把自然语言需求变成机器可解析的 HIS-L0")

# Natural language input
add_textbox(slide, 0.5, 1.25, 12, 0.35, "自然语言需求输入", font_size=14, bold=True, color=PRIMARY)
add_code_block(slide, 0.5, 1.7, 12.3, 1.3,
               '"用遗传算法求解 0/1 背包问题，256 个物品，种群规模 128，100 代终止。\n'
               '部署到 Xilinx Artix-7 xc7a35t，目标频率 100MHz，资源不超过 FPGA 的 80%。\n'
               '通过 AXI-Stream 输入物品列表，结果通过 GPIO 输出。"',
               font_size=13, title="用户需求")

# HIS-L0 output
add_textbox(slide, 0.5, 3.3, 12, 0.35, "提取为 HIS-L0 JSON", font_size=14, bold=True, color=ACCENT_GREEN)

add_code_block(slide, 0.5, 3.75, 6.0, 3.2,
               '{\n'
               '  "algorithm": {\n'
               '    "category": "genetic_algorithm",\n'
               '    "problem": "0_1_knapsack",\n'
               '    "problem_size": {"items": 256},\n'
               '    "population_size": 128,\n'
               '    "max_generations": 100,\n'
               '    "crossover_rate": 0.8,\n'
               '    "mutation_rate": 0.02,\n'
               '    "selection": "tournament_4"\n'
               '  },',
               font_size=9.5, title="算法维度")

add_code_block(slide, 6.8, 3.75, 6.0, 3.2,
               '  "platform": {\n'
               '    "target_fpga": "xc7a35t-cpg236-1",\n'
               '    "target_frequency_mhz": 100,\n'
               '    "resource_budget": {\n'
               '      "lut_max": 16640,\n'
               '      "ff_max": 33280,\n'
               '      "bram_max": 40\n'
               '    },\n'
               '    "power_budget_w": 2.0\n'
               '  },\n'
               '  "interface": {\n'
               '    "input": {"type": "AXI-Stream"},\n'
               '    "output": {"type": "GPIO"},\n'
               '    "control": {"type": "AXI-Lite"}\n'
               '  },\n'
               '  "verification": {\n'
               '    "method": "golden_model",\n'
               '    "golden_model": "python_ga_knapsack"\n'
               '  }\n'
               '}',
               font_size=9.5, title="平台+接口+验证维度")

add_page_number(slide, 23)

# --- 页 24: L0 → L1 ---
slide = add_blank_slide()
add_slide_title(slide, "L0 → L1：算法模板实例化", "匹配 GA 模板，实例化架构参数，前置约束检查")

# Template matching
add_textbox(slide, 0.5, 1.25, 5.8, 0.35, "步骤 1: 算法模板匹配", font_size=14, bold=True, color=ACCENT)
add_textbox(slide, 0.8, 1.7, 5.5, 0.8,
            'HIS-L0.category = "genetic_algorithm"\n'
            '  ↓ 模板库检索\n'
            '匹配 GA-Knapsack 模板\n'
            '预定义: PopulationMemory / FitnessArray\n'
            '/ SelectionUnit / CrossoverUnit\n'
            '/ MutationUnit / ControlFSM / AXI_Interface',
            font_size=11, color=DARK_GRAY, font_name="JetBrains Mono")

add_textbox(slide, 6.8, 1.25, 6.0, 0.35, "步骤 2: 架构参数推导", font_size=14, bold=True, color=PRIMARY)
headers = ["L0 参数", "推导规则", "推导结果"]
rows = [
    ["N=256, pop=128", "pop=items/2", "PopulationMemory: 128×256bit"],
    ["目标100MHz", "周期10ns, 适应度≈3级", "FitnessArray pipeline=3"],
    ["LUT<16.6K", "各模块预算分配", "PE=4 (12.5K LUT ✓)"],
    ["AXI-Stream", "data_width=32", "AXI_Interface: 32-bit"],
]
add_table(slide, 6.8, 1.7, [1.8, 1.8, 2.4], headers, rows, font_size=10.5)

# Constraint check
add_textbox(slide, 0.5, 3.3, 12, 0.35, "步骤 3: L1 约束检查（生成 RTL 前）", font_size=14, bold=True, color=ACCENT_RED)

checks = [
    ("资源合计", "LUT 12.5K ≤ 16.6K", True),
    ("并行合法性", "PE=4, 个体间无数据依赖", True),
    ("时序预估", "3级流水, 每级≈3ns, 总≤10ns", True),
    ("接口匹配", "AXI-Stream 32bit = 内部 32bit", True),
    ("BRAM 端口", "1 Bank, 读写分时, 无冲突", True),
]
for i, (check, detail, ok) in enumerate(checks):
    x = 0.5 + (i % 3) * 4.1
    y = 3.8 + (i // 3) * 0.6
    symbol = "✓" if ok else "✗"
    color = ACCENT_GREEN if ok else ACCENT_RED
    add_textbox(slide, x, y, 3.8, 0.5,
                f"{symbol} {check}: {detail}",
                font_size=11, bold=False, color=color)

# L1 generation results
add_textbox(slide, 0.5, 4.9, 12, 0.35, "生成的 HIS-L1 架构", font_size=14, bold=True, color=PRIMARY)
l1_result = [
    "PopulationMemory: 双端口 BRAM, 深度=128, 位宽=256, Bank=1",
    "FitnessArray: 4 并行 PE, 3 级流水线, 32bit 输出, 评估一代=128/4=32 周期",
    "SelectionUnit: 锦标赛选择(tournament=4), 流水线化, 1 周期/winner",
    "ControlFSM: 5 状态: INIT→EVAL(32cyc)→SELECT(128cyc)→CROSSOVER_MUTATE(128cyc)→CHECK",
]
for i, l in enumerate(l1_result):
    add_textbox(slide, 0.8, 5.35 + i * 0.4, 11.5, 0.35, f"• {l}", font_size=11.5, color=DARK_GRAY)

add_page_number(slide, 24)

# --- 页 25: RTL 生成 + Golden Model ---
slide = add_blank_slide()
add_slide_title(slide, "L1 → RTL → Golden Model 验证",
                "生成可综合 FPGA 工程，用 Python 参考模型验证功能正确性")

# RTL generation
add_textbox(slide, 0.5, 1.25, 6.0, 0.35, "模板引擎 → FPGA 工程", font_size=14, bold=True, color=PRIMARY)
add_code_block(slide, 0.5, 1.7, 5.8, 3.8,
               '参数化 Verilog 模板引擎:\n'
               '─────────────────────\n'
               'template: population_memory.v.tmpl\n'
               '  → population_memory.v\n'
               '  (DEPTH=128, WIDTH=256)\n\n'
               'template: fitness_array.v.tmpl\n'
               '  → fitness_array.v\n'
               '  (PE=4, PIPELINE=3)\n\n'
               'template: control_fsm.v.tmpl\n'
               '  → control_fsm.v\n'
               '  (STATE_COUNT=5)\n\n'
               'template: top_wrapper.v.tmpl\n'
               '  → top.sv\n'
               '  (连接所有子模块+GPIO输出)\n\n'
               '同时生成:\n'
               '• constraints.xdc\n'
               '• testbench.sv',
               font_size=9.5, title=None)

# Golden Model verification
add_textbox(slide, 6.8, 1.25, 6.0, 0.35, "Python Golden Model 验证", font_size=14, bold=True, color=ACCENT_GREEN)

add_code_block(slide, 6.8, 1.7, 5.8, 3.8,
               '验证流程:\n'
               '─────────────────────\n'
               '① Python GA-Knapsack 参考实现\n'
               '   相同输入 → 运行100代\n'
               '   → 最优解: value=3847\n'
               '   → 每代适应度向量\n'
               '        ↓\n'
               '② expected_vectors.txt\n'
               '        ↓\n'
               '③ Verilator 仿真 DUT\n'
               '   相同输入 → 运行100代\n'
               '   → dut_output.txt\n'
               '        ↓\n'
               '④ 逐周期对比\n'
               '   ✓ 最优解: 3847 vs 3847\n'
               '   ✓ 每代适应度: 匹配\n'
               '   ✓ 收敛代数: 78 vs 78\n'
               '   ✓ Mismatch count: 0',
               font_size=9.5, title=None)

# Output package
add_textbox(slide, 0.5, 6.0, 12, 0.3, "输出：可验证 FPGA 工程包（不是 RTL 片段）", font_size=13, bold=True, color=ACCENT)
add_textbox(slide, 0.8, 6.4, 12, 0.6,
            "outputs/ga_knapsack/{rtl/{top,population_memory,fitness_array,selection,crossover,mutation,control_fsm,axi_interface}.sv, "
            "xdc/constraints.xdc, tb/testbench.sv, golden/{golden_model.py, expected_vectors.txt}, vivado/run.tcl, summary.json}",
            font_size=9, color=MED_GRAY, font_name="JetBrains Mono")
add_page_number(slide, 25)

# --- 页 26: Feedback loop example ---
slide = add_blank_slide()
add_slide_title(slide, "EDA 反馈 → 诊断 → 回写（示例）",
                "时序不收敛时，诊断信号如何驱动架构调整")

# Scenario
add_textbox(slide, 0.5, 1.25, 12, 0.35, "场景：第一轮生成 RTL 时序不收敛", font_size=14, bold=True, color=ACCENT_RED)

add_code_block(slide, 0.5, 1.7, 5.8, 2.5,
               'Vivado 报告:\n'
               '  report_timing_summary:\n'
               '    WNS = -1.8 ns\n'
               '    Critical Path:\n'
               '      FitnessArray/pipeline_s2/\n'
               '      mult_add → compare → accumulate\n'
               '      Total delay: 11.8 ns\n\n'
               '  report_utilization:\n'
               '    LUT: 68%  FF: 54%  BRAM: 48%\n\n'
               '  report_power:\n'
               '    Total: 1.6W (under 2.0W ✓)',
               font_size=9.5, title=None)

add_textbox(slide, 6.8, 1.7, 0.5, 0.8, "⟹", font_size=30, bold=True, color=ACCENT, alignment=PP_ALIGN.CENTER)

add_code_block(slide, 7.2, 1.7, 5.5, 2.5,
               'parse_feedback → 结构化诊断:\n'
               '{\n'
               '  "timing": {\n'
               '    "wns_ns": -1.8,\n'
               '    "critical_path":\n'
               '      "FitnessArray/\n'
               '       pipeline_s2/mult_add",\n'
               '    "status": "FAIL"\n'
               '  },\n'
               '  "resource": {"status": "PASS"},\n'
               '  "power":   {"status": "PASS"}\n'
               '}',
               font_size=9.5, title=None)

# Decision
add_textbox(slide, 0.5, 4.5, 12, 0.35, "诊断 → HIS-L1 回写决策", font_size=14, bold=True, color=PRIMARY)

add_code_block(slide, 0.5, 4.9, 12.3, 1.0,
               '时序违规 (WNS=-1.8ns, FitnessArray/pipeline_s2)\n'
               '  方案A: 增加流水线 3→5级 (每级≈2.4ns, LUT+5%)\n'
               '  方案B: 降频至 85MHz (周期=11.8ns, 无需改架构)\n'
               '  方案C: 保持3级, 约束mult_add到DSP (利用空闲DSP48, 资源/频率不变) ← Agent选择此方案\n'
               '回写: HIS-L1 → FitnessArray.pipeline_impl = "dsp_mapped"  |  HIS-L2 → XDC: USE_DSP48 YES\n'
               '重新生成 → Vivado → WNS = +0.3ns ✓',
               font_size=9.5, title=None)

# Mapping rules summary
add_textbox(slide, 0.5, 6.1, 12, 0.3, "完整诊断回写规则", font_size=13, bold=True, color=PRIMARY)
headers = ["诊断", "信号", "回写目标", "优先级"]
rows = [
    ["时序违规", "WNS < 0", "L1: 流水线 或 L0: 频率", "①"],
    ["资源超限", "LUT > 100%", "L1: 并行度 或 模板", "①"],
    ["功耗超标", "P > budget", "L0: 频率, 门控", "②"],
    ["功能不匹配", "mismatch > 0", "L1: FSM/数据通路", "①"],
    ["DRC 失败", "errors", "L2: XDC/IO", "①"],
]
add_table(slide, 0.5, 6.4, [1.5, 2.0, 4.0, 1.0], headers, rows, font_size=9.5)
add_page_number(slide, 26)

# ═══════════════════════════════════════════════════
# 第六章：工具链与 Agent (页 27-29)
# ═══════════════════════════════════════════════════

slide = add_blank_slide()
add_section_header(slide, "六", "工具链与 Agent 设计",
                   "工具白名单 · EDA 调用链 · Agent 角色边界")
add_page_number(slide, 27)

# --- 页 28: 工具白名单 ---
slide = add_blank_slide()
add_slide_title(slide, "工具层设计原则与白名单", "每个工具必须有确定的输入/输出、边界和可审计的记录")

add_textbox(slide, 0.5, 1.25, 12, 0.35, "MVP 工具白名单", font_size=15, bold=True, color=PRIMARY)
headers = ["工具名", "输入", "输出"]
rows = [
    ["parse_his", "自然语言 / SPEC", "HIS-L0 JSON"],
    ["instantiate_template", "HIS-L0 + 算法模板", "HIS-L1 架构意图 JSON"],
    ["generate_rtl", "HIS-L1/L2", "RTL + XDC + Testbench"],
    ["run_simulation", "RTL + Golden Vectors", "功能匹配报告 {match, mismatches}"],
    ["run_vivado_batch", "Vivado project + Tcl", "{utilization, timing, power, drc} 报告"],
    ["parse_feedback", "EDA 原始日志", "结构化诊断 JSON"],
    ["check_timing", "timing 报告", "{wns, tns, critical_paths}"],
    ["analyze_resources", "utilization 报告", "{lut, ff, bram, dsp: pct}"],
    ["analyze_power", "power 报告", "{total, dynamic, static}"],
    ["parse_xdc", "XDC 文件", "{clocks, ios, exceptions}"],
]
add_table(slide, 0.5, 1.7, [2.5, 4.0, 5.8], headers, rows, font_size=10.5)

# Constraints
add_textbox(slide, 0.5, 5.8, 12, 0.35, "每个工具的硬性约束", font_size=14, bold=True, color=PRIMARY)
constraints = [
    "固定 I/O Schema: 输入输出用 JSON Schema 类型检查",
    "Timeout: syntax_check=30s, vivado_batch=10min",
    "项目目录隔离: 每轮生成在独立目录，互不污染",
    "结构化日志: timestamp + input hash + output hash + duration",
    "错误即数据: 工具失败返回结构化 error，不抛异常",
]
for i, c in enumerate(constraints):
    add_textbox(slide, 0.8, 6.3 + i * 0.22, 12.0, 0.2, f"• {c}", font_size=11, color=DARK_GRAY)

add_page_number(slide, 28)

# --- 页 29: EDA 调用链 ---
slide = add_blank_slide()
add_slide_title(slide, "Vivado / Verilator / UVM 的调用方式", "三种验证工具各司其职，输出统一为结构化诊断")

# Three tools flow
tools = [
    ("Verilator --lint-only", "语法检查", "< 30s", "快速发现语法/连接错误", ACCENT_GREEN),
    ("Verilator 仿真", "功能验证", "< 2min", "确认功能正确性\n(Golden Vector 对比)", PRIMARY),
    ("Vivado Batch Tcl", "综合实现", "< 10min", "物理实现验证\n时序/资源/功耗/DRC 全报告", ACCENT_ORANGE),
    ("UVM 环境（成熟后）", "专业验证", "可配置", "sequence/driver/monitor\n/scoreboard/coverage", ACCENT_RED),
]

for i, (name, purpose, time, desc, color) in enumerate(tools):
    x = 0.3 + i * 3.2
    add_flow_box(slide, x, 1.4, 2.9, 1.8, f"{name}\n\n目的: {purpose}\n耗时: {time}\n{desc}",
                 fill_color=color, text_color=WHITE, font_size=10, bold=True)
    if i < 3:
        add_textbox(slide, x + 2.9, 2.0, 0.3, 0.4, "→", font_size=16, bold=True, color=ACCENT, alignment=PP_ALIGN.CENTER)

# Vivado Tcl details
add_textbox(slide, 0.5, 3.6, 12, 0.35, "Vivado Batch Tcl 调用详细", font_size=14, bold=True, color=PRIMARY)
add_code_block(slide, 0.5, 4.0, 6.0, 2.5,
               'Vivado Batch Tcl 脚本:\n'
               '  synth_design\n'
               '  place_design\n'
               '  route_design\n'
               '  report_utilization\n'
               '  report_timing_summary\n'
               '  report_power\n'
               '  report_drc\n'
               '  check_timing\n\n'
               '输出: 结构化报告 JSON\n'
               '→ parse_feedback\n'
               '→ 结构化诊断',
               font_size=10, title=None)

add_textbox(slide, 7.0, 3.6, 6.0, 0.35, "UVM 演进路径", font_size=14, bold=True, color=PRIMARY)
add_code_block(slide, 7.0, 4.0, 5.8, 2.5,
               'MVP（当前）:\n'
               '  Python Golden Model\n'
               '  → expected_vectors.txt\n'
               '  → Verilator仿真 → 逐周期对比\n'
               '  → 普通 SV testbench\n\n'
               '成熟（中长期）:\n'
               '  UVM 环境:\n'
               '    uvm_sequence (自动激励)\n'
               '    uvm_driver (AXI接口驱动)\n'
               '    uvm_monitor (DUT输出采样)\n'
               '    uvm_scoreboard (vs Golden)\n'
               '    uvm_coverage (功能覆盖率)\n\n'
               '  DPI-C: C++ Golden Model\n'
               '   直接集成到仿真，实时对比',
               font_size=9.5, title=None)

add_page_number(slide, 29)

# --- 页 30: Agent 角色 ---
slide = add_blank_slide()
add_slide_title(slide, "Agent 的角色边界", "Agent 是调度者，不是核心——核心是 IR + 约束 + 反馈抽象")

# What Agent does
add_textbox(slide, 0.5, 1.25, 5.8, 0.35, "Agent 做什么", font_size=15, bold=True, color=PRIMARY)
agent_does = [
    "① 维护状态：当前轮次、HIS 参数空间状态、历史诊断记录",
    "② 调度工具：根据阶段选择工具、管理调用顺序、处理 timeout/错误",
    "③ 解释诊断：接收结构化诊断、按规则匹配故障模式、决策调整策略",
    "④ 发起下一轮：回写 HIS 参数、触发生成-验证循环、判断终止条件",
]
for i, a in enumerate(agent_does):
    add_textbox(slide, 0.8, 1.75 + i * 0.45, 5.5, 0.4, a, font_size=12, color=DARK_GRAY)

add_textbox(slide, 7.0, 1.25, 6.0, 0.35, "Agent 不能做什么", font_size=15, bold=True, color=ACCENT_RED)
agent_dont = [
    "✗ 不能不相信工具结果（必须以工具输出为准）",
    "✗ 不能自由发挥生成策略",
    "✗ 不能绕过 HIS 约束检查",
]
for i, a in enumerate(agent_dont):
    add_textbox(slide, 7.3, 1.75 + i * 0.42, 5.5, 0.35, a, font_size=12, color=MED_GRAY)

# Core argument comparison
add_textbox(slide, 0.5, 3.9, 12, 0.35, "为什么 Agent 不是核心研究对象", font_size=15, bold=True, color=PRIMARY)
headers = ["如果把 Agent 当核心", "如果把 IR + 约束 + 反馈当核心"]
rows = [
    ["研究重点: prompt工程、多Agent对话策略", "研究重点: IR表达能力、约束完备性、lowering正确性"],
    ["难复现: 不同LLM表现不同", "可复现: 相同HIS输入→确定RTL输出"],
    ["难验证: Agent的决策对错？", "可验证: 约束检查通过/不通过、诊断是否收敛"],
    ["难泛化: 新算法需重新调prompt", "可泛化: 新算法=新模板+同样的HIS框架"],
    ["贡献边界模糊: Spec2RTL已做多Agent", "贡献清晰: 分层IR、约束检查、lowering、反馈闭环"],
]
add_table(slide, 0.5, 4.35, [5.5, 6.8], headers, rows, font_size=10.5)

# Core thesis box
box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                             Inches(0.5), Inches(6.4), Inches(12.3), Inches(0.8))
box.fill.solid()
box.fill.fore_color.rgb = PRIMARY
box.line.fill.background()
tf = box.text_frame
tf.word_wrap = True
tf.margin_left = Inches(0.5)
tf.margin_top = Inches(0.12)
add_paragraph(tf,
              "项目的核心研究对象不是 Agent 循环本身，而是循环中可解释、可检查、可优化的硬件中间表示（HIS）与工具链反馈抽象。",
              font_size=16, bold=True, color=WHITE)
add_page_number(slide, 30)

# ═══════════════════════════════════════════════════
# 第七章：创新点与路线图 (页 31-34)
# ═══════════════════════════════════════════════════

slide = add_blank_slide()
add_section_header(slide, "七", "创新点与路线图",
                   "五大创新点 · MVP 现状 · 中期/长期路线 · 博士研究定位")
add_page_number(slide, 31)

# --- 页 32: 五大创新点（总览+前三个） ---
slide = add_blank_slide()
add_slide_title(slide, "五大创新点总览", "五者不是孤立的愿望清单，而是一条环环相扣的技术链")

# Innovation chain
add_flow_box(slide, 0.5, 1.3, 2.3, 0.7, "创新点①\n分层 HIS IR\n（表示层）", fill_color=ACCENT, text_color=WHITE, font_size=10)
add_textbox(slide, 2.85, 1.45, 0.5, 0.4, "→", font_size=14, bold=True, color=PRIMARY, alignment=PP_ALIGN.CENTER)
add_flow_box(slide, 3.3, 1.3, 2.3, 0.7, "创新点②\n约束验证与\n架构搜索\n（检查与探索层）", fill_color=PRIMARY, text_color=WHITE, font_size=10)
add_textbox(slide, 5.65, 1.45, 0.5, 0.4, "→", font_size=14, bold=True, color=PRIMARY, alignment=PP_ALIGN.CENTER)
add_flow_box(slide, 6.1, 1.3, 2.3, 0.7, "创新点③\nHIS→CIRCT/RTL\nLowering\n（编译转译层）", fill_color=PRIMARY_DARK, text_color=WHITE, font_size=10)
add_textbox(slide, 8.45, 1.45, 0.5, 0.4, "→", font_size=14, bold=True, color=PRIMARY, alignment=PP_ALIGN.CENTER)
add_flow_box(slide, 8.9, 1.3, 2.3, 0.7, "创新点④\nEDA反馈→\nHIS参数闭环\n（验证优化层）", fill_color=ACCENT_ORANGE, text_color=WHITE, font_size=10)
add_textbox(slide, 11.25, 1.45, 0.4, 0.4, "→", font_size=14, bold=True, color=PRIMARY, alignment=PP_ALIGN.CENTER)
add_flow_box(slide, 11.6, 1.3, 1.5, 0.7, "创新点⑤\n面向非DNN AI\n（应用领域）", fill_color=ACCENT_GREEN, text_color=WHITE, font_size=9.5)

# Details
innovations = [
    ("① 分层 HIS IR", "现有方法缺少可检查、可追踪的中间表示\n→ 提出 HIS-L0/L1/L2，将需求/架构/约束/接口/验证/实现映射统一到可追踪 IR 中\n→ Spec2RTL 用 JSON 表达需求但不承载硬件约束；RTL++ 用 CFG/DFG 表达代码结构但不表达架构意图"),
    ("② IR 层约束验证与架构搜索", "直接生成 RTL 后靠仿真才发现问题 → 修正成本高\n→ 在 HIS-L1 层前置检查并行度/流水线/存储/接口/资源/时钟合法性\n→ 传统 DSE 搜 HLS pragma（实现层）；HNAI 搜 HIS-L1 架构参数（架构层）"),
    ("③ HIS→CIRCT/RTL Lowering", "LLM 直接生成 MLIR/RTL 不可控（SSA违规、类型不匹配）\n→ 设计五层 Lowering：Intent→Architecture→Compiler→RTL→Feedback\n→ LLM 生成结构简单的 HIS，程序化 pass 生成语法正确 RTL/CIRCT"),
    ("④ EDA 反馈→IR 参数闭环", "现有做法将 EDA 日志直接给 LLM → 可能误读\n→ parse_feedback 结构化解析 → timing/resource/power/function 诊断\n→ 诊断类型→HIS参数→调整策略的确定映射规则"),
    ("⑤ 面向非 DNN AI", "Vitis AI/hls4ml/FINN 等绑定 DNN 计算图\n→ 以 GA/RL/路径规划/调度为目标领域\n→ 算法模板编码硬件结构知识 → GA-Knapsack + RL-GridWorld 首批验证"),
]

for i, (title, desc) in enumerate(innovations):
    y = 2.3 + i * 1.0
    add_textbox(slide, 0.5, y, 2.5, 0.35, title, font_size=13, bold=True, color=ACCENT)
    lines = desc.split("\n")
    for j, line in enumerate(lines):
        add_textbox(slide, 3.0, y + j * 0.28, 10, 0.25, line, font_size=10, color=DARK_GRAY)

add_page_number(slide, 32)

# --- 页 33: MVP + 中期路线 ---
slide = add_blank_slide()
add_slide_title(slide, "MVP 现状与中期路线", "MVP 跑通全链路，中期补全关键组件")

# MVP modules
add_textbox(slide, 0.5, 1.2, 6.0, 0.35, "MVP 阶段（当前）", font_size=15, bold=True, color=ACCENT_GREEN)
mvp = [
    ("HIS 层", "HIS JSON Schema (L0/L1/L2), parse_his 模块"),
    ("算法模板", "GA-Knapsack ✓, RL-GridWorld"),
    ("生成层", "参数化 Verilog 模板引擎, generate_rtl"),
    ("验证层", "Python Golden Model ×2, Verilator 仿真, SV testbench"),
    ("EDA 集成", "Vivado batch Tcl, 资源/时序/功耗/DRC 报告解析, summary.json"),
    ("反馈层", "parse_feedback 模块, 结构化诊断生成"),
]
for i, (label, desc) in enumerate(mvp):
    add_textbox(slide, 0.8, 1.65 + i * 0.42, 5.5, 0.38, f"• {label}: {desc}", font_size=11, color=DARK_GRAY)

add_textbox(slide, 6.8, 1.2, 6.0, 0.35, "中期阶段（下一步）", font_size=15, bold=True, color=PRIMARY)
mid = [
    ("XDC 自动检查", "自动验证 IO标准/管脚/时钟/时序例外", "高"),
    ("UVM 验证环境", "sequence/driver/monitor/scoreboard", "高"),
    ("CFG/DFG 增强", "RTL++ 风格图约束生成+一致性检查", "中"),
    ("CIRCT hw/sv 后端", "替换模板化RTL为CIRCT lowering", "中"),
    ("性能预测器", "基于HIS-L1预测PPA, 减少Vivado调用", "中"),
    ("更多算法模板", "A*路径规划, GA-Scheduling", "低"),
]
add_textbox(slide, 6.8, 1.65, 3.5, 0.35, "", font_size=1, color=WHITE)  # spacer
for i, (label, desc, pri) in enumerate(mid):
    add_textbox(slide, 7.1, 1.65 + i * 0.42, 5.5, 0.38, f"• {label}: {desc} [优先级: {pri}]", font_size=11, color=DARK_GRAY)

# Three stage roadmap
add_textbox(slide, 0.5, 4.5, 12, 0.35, "三阶段演进总览", font_size=15, bold=True, color=PRIMARY)

stages_roadmap = [
    ("MVP（当前）", "HIS JSON\n+ 模板化RTL/HLS\n+ Golden Model\n+ Verilator/Vivado\n+ summary.json", ACCENT_GREEN),
    ("中期", "HIS JSON\n+ CIRCT hw/sv（混合）\n+ UVM + XDC\n+ CFG/DFG 增强\n+ 性能预测器", PRIMARY),
    ("长期", "HNAI MLIR Dialect\nverifier/canonicalize\n/DSE/lowering pass\n→ CIRCT\n→ 跨层协同优化\n→ FPGA/ASIC", PRIMARY_DARK),
]

for i, (label, content, color) in enumerate(stages_roadmap):
    x = 0.5 + i * 4.3
    add_flow_box(slide, x, 4.95, 3.8, 1.7, f"{label}\n\n{content}",
                 fill_color=color, text_color=WHITE, font_size=11, bold=True)
    if i < 2:
        add_textbox(slide, x + 3.8, 5.6, 0.5, 0.4, "⟹", font_size=22, bold=True, color=ACCENT, alignment=PP_ALIGN.CENTER)

add_page_number(slide, 33)

# --- 页 34: 博士研究 + 讨论 ---
slide = add_blank_slide()
add_slide_title(slide, "学术表达与讨论话题",
                "博士研究定位的学术凝练，以及需要团队共同讨论的开放问题")

# Academic expression
box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                             Inches(0.5), Inches(1.3), Inches(12.3), Inches(1.3))
box.fill.solid()
box.fill.fore_color.rgb = PRIMARY
box.line.fill.background()
tf = box.text_frame
tf.word_wrap = True
tf.margin_left = Inches(0.5)
tf.margin_top = Inches(0.25)
add_paragraph(tf, "博士研究学术表达：", font_size=14, bold=False, color=RGBColor(0xAA, 0xCC, 0xEE))
add_paragraph(tf, "面向非 DNN AI 算法的、基于分层硬件意图 IR 的自然语言到 FPGA 自动设计与约束优化方法研究", font_size=20, bold=True, color=WHITE)

# Keyword breakdown
add_textbox(slide, 0.5, 2.9, 12, 0.35, "关键词拆解", font_size=14, bold=True, color=PRIMARY)
headers = ["关键词", "学术含义", "对应章节"]
rows = [
    ["非 DNN AI 算法", "限定应用领域，区别于现有 DNN FPGA 工具", "第一章"],
    ["分层硬件意图 IR", "核心贡献——HIS-L0/L1/L2", "第三章"],
    ["自然语言到 FPGA", "输入端到输出端的跨度", "第二~五章"],
    ["自动设计", "非人工设计硬件架构", "第二、四章"],
    ["约束优化", "EDA 反馈闭环 + 约束检查", "第四、五章"],
]
add_table(slide, 0.5, 3.3, [2.5, 5.0, 2.0], headers, rows, font_size=11)

# Discussion topics
add_textbox(slide, 0.5, 5.5, 12, 0.35, "待讨论的开放问题", font_size=14, bold=True, color=ACCENT_ORANGE)
topics = [
    "算法模板覆盖边界：哪些非 DNN AI 算法适合模板化？哪些需要更灵活的生成策略？",
    "HIS 表达力验证：L1 能否覆盖所有必要的架构维度？是否有遗漏的结构需要补充？",
    "LLM vs 程序化的分工：哪些环节必须程序化保障确定性？哪些环节可以让 LLM 发挥灵活性？",
    "CIRCT 引入时机：MVP 验证到什么程度可以启动 CIRCT 后端替换？",
    "评价体系：如何量化评估 HNAI-FPGA 相较于 Spec2RTL 和其他基线的提升？",
]
for i, t in enumerate(topics):
    add_textbox(slide, 0.8, 5.95 + i * 0.28, 11.5, 0.25, f"• {t}", font_size=11, color=DARK_GRAY)

add_page_number(slide, 34)

# ═══════════════════════════════════════════════════
# 第八章：总结 (页 35-36)
# ═══════════════════════════════════════════════════

slide = add_blank_slide()
add_section_header(slide, "八", "总结与收束", "三句话总结 · 全篇回顾 · 关键概念对照")
add_page_number(slide, 35)

# --- 页 35: 全篇回顾 ---
slide = add_blank_slide()
add_slide_title(slide, "全篇回顾", "HNAI-FPGA 的三句话总结")

# Three sentences
sentences = [
    ("定位",
     "HNAI-FPGA 不是 AI 写 Verilog 工具，而是从自然语言出发，经过分层 HIS → IR 约束检查 → CIRCT/RTL lowering → EDA 反馈闭环，最终产出可验证 FPGA 工程包的自动设计框架。"),
    ("核心洞察",
     "项目的核心研究对象不是 Agent 循环本身，而是循环中可解释、可检查、可优化的硬件中间表示（HIS）与工具链反馈抽象。"),
    ("路线",
     "MVP 用 HIS JSON + 模板化 RTL 验证全链路可行性；中长期逐步引入 CIRCT、UVM、CFG/DFG 增强和 HNAI MLIR dialect，最终实现从自然语言到 FPGA/ASIC 的跨层协同优化。"),
]

for i, (label, content) in enumerate(sentences):
    y = 1.3 + i * 0.85
    add_textbox(slide, 0.5, y, 1.3, 0.4, label, font_size=16, bold=True, color=ACCENT)
    add_textbox(slide, 1.9, y, 10.8, 0.7, content, font_size=13, color=DARK_GRAY)

# Chapter review
add_textbox(slide, 0.5, 4.1, 12, 0.35, "全篇章节回顾", font_size=15, bold=True, color=PRIMARY)

chapters = [
    "第一章  技术的必然 —— 从手写 RTL 到 AI 自动架构设计的演进脉络",
    "第二章  我们做什么 —— 一句话定位 + 整体架构 + 关键概念",
    "第三章  核心表示 —— HIS-L0/L1/L2 分层设计与约束传递",
    "第四章  编译转译 —— 五层 Lowering 机制与 MLIR/CIRCT 定位",
    "第五章  端到端 —— GA-Knapsack 全链路追踪（输入→验证→反馈→回写）",
    "第六章  调度层 —— 工具链白名单与 Agent 角色边界",
    "第七章  创新与路线 —— 五大创新点 + MVP/中期/长期路线",
]
for i, c in enumerate(chapters):
    add_textbox(slide, 0.8, 4.55 + i * 0.38, 11.5, 0.35, c, font_size=12, color=DARK_GRAY)

add_page_number(slide, 36)

# --- 页 36: 关键概念对照 ---
slide = add_blank_slide()
add_slide_title(slide, "团队速查：关键概念对照表", "这些术语在 HNAI-FPGA 中的确切含义——作为团队长期参考")

headers = ["概念", "一句话定位", "在项目中的角色"]
rows = [
    ["SPEC", "人类可读需求规格", "对齐目标、场景、验收和交付边界"],
    ["HIS-L0", "需求意图层", "表达算法、平台、性能、接口、验证——机器可解析的需求"],
    ["HIS-L1", "架构意图层", "表达模块、数据流、控制流、存储、并行、流水、时序——约束检查主战场"],
    ["HIS-L2", "实现映射层", "绑定 CIRCT/RTL 路径、XDC、testbench、EDA 工具与报告解析规则"],
    ["MLIR", "多层中间表示框架", "承载自定义 dialect、verifier、pass 和 lowering 基础设施"],
    ["CIRCT", "硬件领域 MLIR 工具链", "提供 hw/comb/seq/fsm/sv dialect 与 SystemVerilog 输出"],
    ["Lowering", "程序化逐层转译机制", "五层 lowering 保证从意图到 RTL 的确定性和可验证性"],
    ["Golden Model", "功能正确性的参考实现", "Python/C++ 版算法实现，产出 expected vectors"],
    ["Agent", "工具调度与决策层", "调度工具、维护状态、解释诊断——但非核心研究对象"],
    ["结构化诊断", "EDA 报告的机器可解析抽象", "timing/resource/power/function 诊断 → 回写 HIS 参数"],
    ["Spec2RTL", "当前最接近的 Agent 系统", "证明方向可行，但缺 HIS/约束检查/lowering/反馈闭环"],
    ["RTL++", "CFG/DFG 图增强的 RTL 生成", "互补——HNAI 可吸收其图增强思想做约束和一致性检查"],
]
add_table(slide, 0.5, 0.95, [1.8, 3.5, 7.0], headers, rows, font_size=10.5)

add_textbox(slide, 0.5, 6.8, 12, 0.4,
            "感谢聆听 | HNAI-FPGA · 基于分层硬件意图 IR 的自然语言到 FPGA 自动设计与约束优化框架",
            font_size=13, bold=False, color=PRIMARY, alignment=PP_ALIGN.CENTER)
add_page_number(slide, 37)

# ═══════════════════════════════════════════════════
# 保存文件
# ═══════════════════════════════════════════════════

output_path = Path(__file__).resolve().parents[1] / "deliverables" / "HNAI-FPGA_项目讲解.pptx"
output_path.parent.mkdir(parents=True, exist_ok=True)
prs.save(output_path)
print(f"✅ PPT 已生成: {output_path}")
print(f"共 {len(prs.slides)} 页幻灯片")
