export const deckData = [
  {
    "type": "cover",
    "kicker": "PROJECT OVERVIEW",
    "title": "HNAI-FPGA",
    "subtitle": "面向非 DNN AI 算法的自然语言到 FPGA 自动设计框架",
    "claim": "核心不是“AI 写 Verilog”，而是用分层硬件意图 IR 把需求、架构、约束、验证和 EDA 反馈串成可检查闭环。",
    "meta": "项目讲解 | 清晰重排版 | 2026.06",
    "metrics": [
      [
        "HIS",
        "分层硬件意图 IR"
      ],
      [
        "CIRCT/RTL",
        "确定性 lowering"
      ],
      [
        "EDA feedback",
        "结构化诊断回写"
      ],
      [
        "Non-DNN AI",
        "GA / RL / 规划 / 调度"
      ]
    ]
  },
  {
    "type": "timeline",
    "title": "技术演进全景：设计自动化正在从代码生成走向架构生成",
    "claim": "HNAI-FPGA 站在 HLS、DSE、LLM RTL、Agent 与 MLIR/CIRCT 交汇的位置，补足高层意图与反馈闭环。",
    "stages": [
      [
        "1980s+",
        "手工 RTL",
        "完全可控",
        "周期长、门槛高"
      ],
      [
        "2000s+",
        "HLS",
        "C/C++ 到 RTL",
        "不能发明架构"
      ],
      [
        "2010s+",
        "DSE",
        "搜索 Pipeline / PE / Tile",
        "本质仍是调参"
      ],
      [
        "2023",
        "LLM 生成 RTL",
        "证明模型可写硬件代码",
        "片段级、不可部署"
      ],
      [
        "2024",
        "生成-验证-修复",
        "提升 RTL 正确率",
        "反馈难追溯到架构"
      ],
      [
        "2025",
        "Spec2RTL-Agent",
        "规格到 RTL Agent",
        "缺少可检查 IR"
      ],
      [
        "2020s+",
        "MLIR/CIRCT",
        "硬件编译基础设施",
        "缺上层意图表达"
      ],
      [
        "Now",
        "HNAI-FPGA",
        "HIS + lowering + feedback",
        "面向非 DNN AI 闭环"
      ]
    ],
    "note": "演进趋势：AI 从“帮人写代码”转向“协同设计硬件架构并自动优化”。"
  },
  {
    "type": "table",
    "title": "演进的核心洞察：每一代工具都留下了一个上层空白",
    "claim": "现有技术各解决了一段链路，但自然语言、硬件意图、物理约束和 EDA 反馈仍没有被统一表达。",
    "headers": [
      "阶段",
      "解决了什么",
      "留下的空白"
    ],
    "rows": [
      [
        "HLS",
        "把软件描述转成硬件实现",
        "不会主动选择架构"
      ],
      [
        "DSE",
        "自动探索设计参数",
        "搜索空间依赖人工建模"
      ],
      [
        "LLM RTL",
        "生成可读 Verilog 片段",
        "缺约束、验证、部署边界"
      ],
      [
        "Spec2RTL",
        "把规格文档接入 Agent 流程",
        "中间没有可检查 IR"
      ],
      [
        "CIRCT",
        "提供硬件 IR 与编译基础",
        "缺少自然语言意图层"
      ]
    ],
    "note": "HNAI-FPGA 的切入点：把“意图表达”和“工具链反馈”变成系统的核心研究对象。"
  },
  {
    "type": "compare",
    "title": "Spec2RTL 是最接近的参照系，但还不是完整闭环",
    "claim": "Spec2RTL 证明从规格到 RTL 的方向可行；HNAI-FPGA 补的是分层 IR、约束检查和 EDA 反馈回写。",
    "leftTitle": "Spec2RTL 已做到",
    "rightTitle": "HNAI-FPGA 补足",
    "left": [
      "读取真实规格文档",
      "多 Agent 协同生成 RTL",
      "接入仿真/编译检查",
      "证明方向可行"
    ],
    "right": [
      "HIS-L0/L1/L2 分层表示",
      "生成前进行架构约束检查",
      "EDA 诊断回写到 HIS 参数",
      "输出完整 FPGA 工程包"
    ],
    "note": "从“规格直接到 RTL”升级为“规格到意图、意图到硬件、反馈再回意图”。"
  },
  {
    "type": "table",
    "title": "为什么非 DNN AI 是一个特殊问题",
    "claim": "GA、RL、路径规划和调度优化不是规整张量计算，现有 DNN FPGA 工具的架构假设覆盖不到。",
    "headers": [
      "维度",
      "DNN 推理",
      "非 DNN AI"
    ],
    "rows": [
      [
        "计算模式",
        "规整张量运算",
        "控制流 + 数据流交织"
      ],
      [
        "存储访问",
        "规则层级 buffer",
        "数据依赖和随机访问"
      ],
      [
        "工具覆盖",
        "Vitis AI / hls4ml / FINN",
        "系统性空白"
      ],
      [
        "算法模板",
        "Conv / MatMul / Activation",
        "种群维护、Q-table、搜索与调度"
      ],
      [
        "硬件诉求",
        "吞吐与批量推理",
        "低时延、低功耗、确定性执行"
      ]
    ],
    "note": "这个空白同时具有学术价值和工程价值。"
  },
  {
    "type": "flow",
    "title": "HNAI-FPGA 在演进脉络中的位置",
    "claim": "项目把自然语言需求、硬件意图 IR、模板/CIRCT lowering 与 EDA 反馈放进同一个闭环。",
    "steps": [
      [
        "自然语言 / SPEC",
        "人类可读需求与验收边界"
      ],
      [
        "HIS-L0",
        "算法、平台、接口、验证目标"
      ],
      [
        "HIS-L1",
        "模块、数据流、控制流、并行与存储"
      ],
      [
        "HIS-L2",
        "RTL/CIRCT 路径、XDC、testbench"
      ],
      [
        "RTL / CIRCT",
        "可综合硬件实现"
      ],
      [
        "EDA 反馈",
        "timing / resource / function 诊断回写"
      ]
    ],
    "note": "关键不是多一个 Agent，而是让 Agent 的每一步都有可审计的表示和工具证据。"
  },
  {
    "type": "section",
    "chapter": "第二章",
    "title": "HNAI-FPGA 是什么",
    "subtitle": "一句话定位 · 整体架构 · 关键概念"
  },
  {
    "type": "definition",
    "title": "一句话定位：HNAI-FPGA 是自动设计框架，不是代码补全工具",
    "claim": "它从自然语言/功能需求出发，经过 HIS、模板实例化、lowering、EDA 验证和反馈优化，生成可验证 FPGA 工程包。",
    "statement": "HNAI-FPGA = Natural Language / SPEC → HIS → Architecture Constraints → RTL/CIRCT → EDA Feedback → Deployable FPGA Package",
    "choices": [
      [
        "不是",
        "单纯 AI 写 Verilog",
        "是",
        "有 IR 与验证闭环的自动设计框架"
      ],
      [
        "不是",
        "RTL 片段生成器",
        "是",
        "输出工程包、约束、testbench 与报告"
      ],
      [
        "不是",
        "只服务 DNN",
        "是",
        "面向 GA/RL/规划/调度等非 DNN AI"
      ],
      [
        "不是",
        "黑盒 prompt 工程",
        "是",
        "每层表示可检查、可追踪、可优化"
      ]
    ]
  },
  {
    "type": "architecture",
    "title": "整体架构图：从需求到硬件的六层闭环",
    "claim": "系统把自然语言输入拆成可检查层级，并在 EDA 反馈后回写到 HIS-L1 参数空间。",
    "lanes": [
      [
        "输入层",
        "SPEC / 自然语言需求",
        "#0EA5E9"
      ],
      [
        "意图层",
        "HIS-L0 / L1 / L2",
        "#2563EB"
      ],
      [
        "模板层",
        "算法模板 + 约束检查",
        "#14B8A6"
      ],
      [
        "实现层",
        "CIRCT / RTL / HLS",
        "#0F766E"
      ],
      [
        "验证层",
        "Verilator / Vivado / UVM",
        "#F97316"
      ],
      [
        "反馈层",
        "结构化诊断 → 参数回写",
        "#DC2626"
      ]
    ],
    "note": "主闭环：需求约束向下传递，物理实现反馈向上追溯。"
  },
  {
    "type": "concepts",
    "title": "关键概念速查：把术语固定成工程边界",
    "claim": "每个术语都对应项目里的一个责任边界，避免 HIS、CIRCT、RTL 和 Agent 混成一团。",
    "concepts": [
      [
        "SPEC",
        "人类可读需求规格",
        "对齐目标、场景、验收"
      ],
      [
        "HIS",
        "分层硬件意图 IR",
        "核心研究对象"
      ],
      [
        "MLIR",
        "多层中间表示框架",
        "承载 dialect 与 pass"
      ],
      [
        "CIRCT",
        "硬件领域 MLIR 工具链",
        "输出 SystemVerilog"
      ],
      [
        "RTL/HLS",
        "硬件实现形式",
        "可综合代码"
      ],
      [
        "EDA",
        "验证与实现工具",
        "提供结构化反馈"
      ],
      [
        "UVM",
        "专业验证方法学",
        "组织验证环境"
      ],
      [
        "Agent",
        "工具调度层",
        "调度、解释、迭代"
      ]
    ]
  },
  {
    "type": "section",
    "chapter": "第三章",
    "title": "核心：分层 HIS 设计",
    "subtitle": "L0 需求意图 · L1 架构意图 · L2 实现映射"
  },
  {
    "type": "compare",
    "title": "为什么需要 HIS：在自然语言和 RTL 之间增加可检查层",
    "claim": "没有 HIS，错误只能在 RTL 或 EDA 阶段暴露；有 HIS，约束可以在生成前被检查并追溯。",
    "leftTitle": "没有 HIS",
    "rightTitle": "有 HIS",
    "left": [
      "LLM 输出什么就是什么",
      "架构决策隐式藏在代码里",
      "需求变化无法定位影响范围",
      "EDA 反馈不知道回写给谁"
    ],
    "right": [
      "生成前检查并行度、资源和接口",
      "L1 显式表达模块、数据流与 FSM",
      "L0 → L1 → L2 逐层可追踪",
      "诊断定位到具体 HIS 参数"
    ],
    "note": "HIS 不是把需求翻译成 JSON，而是把硬件意图变成可验证对象。"
  },
  {
    "type": "cards",
    "title": "HIS-L0：需求意图层回答“要做什么”",
    "claim": "L0 不涉及实现细节，负责把算法、平台、性能、接口和验证目标固定下来。",
    "cards": [
      [
        "算法维度",
        "类别、规模、数据类型、精度、终止条件"
      ],
      [
        "平台维度",
        "目标 FPGA、频率、资源上限"
      ],
      [
        "性能目标",
        "吞吐、延迟、功耗预算"
      ],
      [
        "接口维度",
        "AXI / GPIO / BRAM 接口与位宽"
      ],
      [
        "验证维度",
        "Golden Model / UVM / 形式验证"
      ],
      [
        "产出",
        "机器可解析 HIS-L0 JSON"
      ]
    ],
    "note": "示例：GA-Knapsack, N=256, Artix-7, 100MHz, AXI-Stream + AXI-Lite + GPIO。"
  },
  {
    "type": "cards",
    "title": "HIS-L1：架构意图层是约束检查的主战场",
    "claim": "L1 显式表达硬件怎么组织、数据怎么流动、并行和流水如何受资源约束。",
    "cards": [
      [
        "模块划分",
        "PopulationMemory / FitnessArray / ControlFSM"
      ],
      [
        "数据流图",
        "模块间流向、位宽、握手协议"
      ],
      [
        "控制流",
        "FSM 状态、转移条件、stall 逻辑"
      ],
      [
        "存储结构",
        "BRAM bank、端口数、深度和位宽"
      ],
      [
        "并行流水",
        "PE 数、pipeline stage、关键路径预算"
      ],
      [
        "接口绑定",
        "AXI 地址映射、burst、data width"
      ]
    ],
    "note": "生成 RTL 前检查：资源预算、接口一致性、并行合法性、时序可行性。"
  },
  {
    "type": "flow",
    "title": "HIS-L2：实现映射层把架构绑定到工具链",
    "claim": "L2 不引入新架构信息，而是说明 L1 如何落到 CIRCT/RTL、XDC、testbench 和 EDA 工具。",
    "steps": [
      [
        "IR 路径选择",
        "CIRCT hw/sv 或模板化 RTL"
      ],
      [
        "RTL 生成策略",
        "模板参数 / HLS pragma / lowering pass"
      ],
      [
        "XDC 约束",
        "时钟、IO、管脚、时序例外"
      ],
      [
        "Testbench",
        "激励生成与 Golden Vector"
      ],
      [
        "EDA 绑定",
        "Vivado Tcl / Verilator / UVM"
      ],
      [
        "报告解析",
        "utilization / timing / power / DRC"
      ]
    ],
    "note": "MVP 用模板化 RTL 跑通全链路，中长期逐步引入 CIRCT 后端。"
  },
  {
    "type": "section",
    "chapter": "第四章",
    "title": "从意图到硬件：Lowering 机制",
    "subtitle": "五层转译 · 程序化保证 · 反馈回写"
  },
  {
    "type": "pipeline",
    "title": "五层 Lowering 全景：把不可控生成变成可验证转译",
    "claim": "相同 HIS 输入应产生相同 RTL/CIRCT 输出；每一层 lowering 都可独立检查。",
    "steps": [
      [
        "1",
        "Intent",
        "SPEC/HIS-L0 → HIS-L1"
      ],
      [
        "2",
        "Architecture",
        "算法块 → 硬件块"
      ],
      [
        "3",
        "Compiler",
        "硬件块 → CIRCT/模板 DSL"
      ],
      [
        "4",
        "RTL",
        "IR → SystemVerilog"
      ],
      [
        "5",
        "Feedback",
        "EDA 报告 → 结构化诊断"
      ]
    ],
    "note": "程序化 Lowering 的价值：确定性、类型安全、错误可定位、优化可复现。"
  },
  {
    "type": "splitList",
    "title": "Lowering-1 & 2：先把问题变成硬件结构",
    "claim": "前两层负责把“要解决什么问题”变成“硬件模块、互联和参数长什么样”。",
    "leftTitle": "Lowering-1：Intent",
    "rightTitle": "Lowering-2：Architecture",
    "left": [
      "算法模板匹配",
      "约束传播",
      "架构参数实例化",
      "输出 HIS-L1 JSON"
    ],
    "right": [
      "Population → BRAM",
      "Fitness → PE Array",
      "Selection/Crossover/Mutation → Pipeline",
      "ControlFSM 生成状态机"
    ],
    "note": "这一步决定后续 RTL 是否在资源、接口和并行度上可行。"
  },
  {
    "type": "splitList",
    "title": "Lowering-3 & 4：硬件块到 RTL 的确定性转译",
    "claim": "LLM 不直接写 MLIR 或 RTL；它生成结构简单的 HIS，程序化 pass 负责类型安全的实现转译。",
    "leftTitle": "路径 A：CIRCT（中长期）",
    "rightTitle": "路径 B：模板化 RTL（MVP）",
    "left": [
      "HIS → CIRCT hw/comb/seq/fsm/sv",
      "verifier 保证结构合法",
      "ExportVerilog 输出 .sv"
    ],
    "right": [
      "HIS → 参数化模板",
      "模板引擎渲染 RTL/HLS",
      "同步输出 XDC 与 testbench"
    ],
    "note": "MVP 先保证可控和可调试，再逐步替换为 CIRCT 后端。"
  },
  {
    "type": "feedback",
    "title": "Lowering-5：EDA 反馈不是日志，而是可回写诊断",
    "claim": "报告解析器把 timing/resource/power/function 信号定位到 HIS-L1 或 HIS-L2 参数。",
    "mappings": [
      [
        "WNS < 0",
        "时序违规",
        "增加 pipeline stage"
      ],
      [
        "LUT > 100%",
        "资源超限",
        "降低 PE 并行度"
      ],
      [
        "power > budget",
        "功耗超标",
        "降频或启用门控"
      ],
      [
        "function mismatch",
        "功能不正确",
        "检查 FSM 和数据通路"
      ],
      [
        "DRC failure",
        "规则违规",
        "修正 IO / 时钟 / XDC"
      ]
    ],
    "note": "诊断必须结构化，否则下一轮只是把长日志重新丢给 LLM。"
  },
  {
    "type": "cards",
    "title": "MLIR/CIRCT 的项目定位：低层硬件 IR，不替代 HIS",
    "claim": "HIS 表达高层架构意图，CIRCT 表达低层电路实现；二者是上下游关系。",
    "cards": [
      [
        "原则 1",
        "CIRCT 不替代 HIS；HIS 负责表达架构和约束"
      ],
      [
        "原则 2",
        "MVP 不强依赖 CIRCT；先用模板化 RTL 跑通闭环"
      ],
      [
        "原则 3",
        "LLM 不直接生成 MLIR；程序化 pass 保证合法性"
      ],
      [
        "MVP",
        "HIS JSON → 模板化 RTL/HLS → Vivado/Verilator"
      ],
      [
        "中期",
        "HIS JSON → CIRCT hw/sv + 模板 RTL"
      ],
      [
        "长期",
        "HNAI MLIR Dialect → CIRCT → FPGA/ASIC"
      ]
    ],
    "note": "CIRCT 是硬件版 LLVM；HIS 是项目自己的上层意图语言。"
  },
  {
    "type": "section",
    "chapter": "第五章",
    "title": "端到端案例：GA-Knapsack",
    "subtitle": "自然语言输入 · HIS 实例化 · 验证 · 反馈回写"
  },
  {
    "type": "codePair",
    "title": "案例设定：自然语言需求先进入 HIS-L0",
    "claim": "自然语言输入被解析为算法、平台、性能、接口和验证目标，而不是直接生成 RTL。",
    "leftTitle": "自然语言需求",
    "rightTitle": "HIS-L0 摘要",
    "left": [
      "实现 0/1 背包遗传算法",
      "N=256，种群规模 128",
      "目标 Artix-7，100MHz",
      "AXI-Stream 输入，GPIO 输出"
    ],
    "right": [
      "algorithm: genetic_algorithm",
      "problem: knapsack_01",
      "population_size: 128",
      "target_freq: 100MHz",
      "verify: python_golden_model"
    ],
    "note": "L0 的职责是把需求边界固定到机器可解析字段。"
  },
  {
    "type": "pipeline",
    "title": "L0 → L1：算法模板实例化并前置约束检查",
    "claim": "GA 模板被展开为存储、适应度计算、选择、交叉、变异和控制 FSM。",
    "steps": [
      [
        "1",
        "Template",
        "匹配 GA-Knapsack 模板"
      ],
      [
        "2",
        "Memory",
        "PopulationMemory 双端口 BRAM"
      ],
      [
        "3",
        "Fitness",
        "4 并行 PE + 3 级流水"
      ],
      [
        "4",
        "Operators",
        "Selection / Crossover / Mutation"
      ],
      [
        "5",
        "FSM",
        "INIT → EVAL → SELECT → UPDATE → CHECK"
      ]
    ],
    "note": "约束检查通过后才进入 RTL 生成；失败则回到参数空间调整。"
  },
  {
    "type": "codePair",
    "title": "L1 → RTL → Golden Model：输出工程包而不是片段",
    "claim": "模板引擎生成 top.sv、子模块、constraints.xdc 和 testbench，并用 Golden Model 做功能对比。",
    "leftTitle": "FPGA 工程输出",
    "rightTitle": "Golden Model 验证",
    "left": [
      "top.sv",
      "population_memory.sv",
      "fitness_array.sv",
      "selection_unit.sv",
      "constraints.xdc",
      "testbench.sv"
    ],
    "right": [
      "generate_vectors()",
      "run_rtl_sim()",
      "compare(expected, actual)",
      "assert pass_rate == 100%"
    ],
    "note": "交付目标是可验证工程包，验证失败必须回写到 HIS。"
  },
  {
    "type": "feedback",
    "title": "EDA 反馈示例：时序失败如何回写到 HIS-L1",
    "claim": "WNS 失败会被解析为结构化诊断，并映射到 pipeline stage、PE 数或频率目标。",
    "mappings": [
      [
        "report_timing",
        "WNS = -0.82ns",
        "关键路径：fitness_array"
      ],
      [
        "诊断",
        "timing_violation",
        "路径过长，不是语法问题"
      ],
      [
        "回写目标",
        "HIS-L1.fitness_array.pipeline",
        "stage 3 → 4"
      ],
      [
        "再生成",
        "重新 lowering RTL",
        "保持接口和功能不变"
      ],
      [
        "再验证",
        "Vivado + Golden Model",
        "确认 timing 与 function"
      ]
    ],
    "note": "这页从原来的代码+表格混排改成诊断链路，让讲解顺序更清楚。"
  },
  {
    "type": "section",
    "chapter": "第六章",
    "title": "工具链与 Agent 设计",
    "subtitle": "工具白名单 · EDA 调用 · Agent 边界"
  },
  {
    "type": "concepts",
    "title": "工具层设计原则与白名单：每个工具都有输入、输出和审计记录",
    "claim": "MVP 不追求工具越多越好，而是每个工具都能被确定性调用并返回结构化结果。",
    "concepts": [
      [
        "parse_his",
        "解析 SPEC/HIS",
        "输出字段完整性报告"
      ],
      [
        "instantiate_template",
        "实例化算法模板",
        "输出 HIS-L1 与参数检查"
      ],
      [
        "gen_rtl",
        "生成 RTL/HLS",
        "输出工程文件"
      ],
      [
        "gen_testbench",
        "生成测试平台",
        "输出激励与对比逻辑"
      ],
      [
        "run_verilator",
        "快速仿真",
        "输出功能诊断"
      ],
      [
        "run_vivado",
        "综合/实现",
        "输出资源与时序报告"
      ],
      [
        "parse_feedback",
        "报告解析",
        "输出结构化诊断"
      ],
      [
        "optimize_his",
        "参数优化",
        "输出下一轮候选"
      ]
    ]
  },
  {
    "type": "cards",
    "title": "Vivado / Verilator / UVM：验证工具各司其职",
    "claim": "不同验证工具的报告统一进入结构化诊断层，供 Agent 解释和下一轮调度。",
    "cards": [
      [
        "Verilator",
        "快速编译、lint、单元级功能仿真"
      ],
      [
        "Vivado Batch",
        "综合、实现、资源、时序、功耗、DRC"
      ],
      [
        "UVM",
        "sequence / driver / monitor / scoreboard 专业验证环境"
      ],
      [
        "Tcl 调用",
        "create_project → synth_design → report_timing"
      ],
      [
        "诊断统一",
        "function / timing / resource / power / DRC"
      ],
      [
        "工程记录",
        "每轮输入、输出、报告、决策都可审计"
      ]
    ],
    "note": "工具链不是附属项，它决定反馈是否能被可靠回写。"
  },
  {
    "type": "compare",
    "title": "Agent 的角色边界：调度者，不是核心研究对象",
    "claim": "Agent 维护状态、调用工具、解释诊断并发起下一轮；核心仍是 HIS、约束和反馈抽象。",
    "leftTitle": "Agent 做什么",
    "rightTitle": "Agent 不能做什么",
    "left": [
      "解析任务与维护状态",
      "选择工具并传递结构化输入",
      "解释诊断和触发下一轮",
      "记录每一步证据"
    ],
    "right": [
      "替代 HIS 表达",
      "绕过约束检查",
      "直接相信 RTL 输出",
      "把 EDA 日志当自然语言长文处理"
    ],
    "note": "把 Agent 降到调度层，反而让研究贡献更聚焦、更可验证。"
  },
  {
    "type": "section",
    "chapter": "第七章",
    "title": "创新点与路线图",
    "subtitle": "五大创新点 · MVP 状态 · 学术表达"
  },
  {
    "type": "pipeline",
    "title": "五大创新点总览：一条相互咬合的技术链",
    "claim": "创新点不是孤立功能，而是从应用空白、意图表示、转译机制到反馈闭环的完整链路。",
    "steps": [
      [
        "1",
        "应用场景",
        "非 DNN AI 的 FPGA 自动设计"
      ],
      [
        "2",
        "核心表示",
        "分层硬件意图 HIS"
      ],
      [
        "3",
        "转译机制",
        "HIS → RTL/CIRCT lowering"
      ],
      [
        "4",
        "反馈闭环",
        "EDA 诊断回写 HIS"
      ],
      [
        "5",
        "交付边界",
        "完整 FPGA 工程包"
      ]
    ],
    "note": "每个创新点都对应一个可验证的工程对象。"
  },
  {
    "type": "roadmap",
    "title": "MVP 现状与中期路线：先跑通闭环，再提升后端能力",
    "claim": "MVP 用 HIS JSON + 模板化 RTL 保证可控性；中期补 CIRCT、UVM 和更多算法模板。",
    "phases": [
      [
        "MVP 当前",
        [
          "HIS schema",
          "GA-Knapsack 模板",
          "Verilator/Vivado 调用",
          "反馈解析 demo"
        ]
      ],
      [
        "中期 下一步",
        [
          "CIRCT 后端",
          "UVM 验证环境",
          "多算法模板库",
          "RTL++ 图增强"
        ]
      ],
      [
        "长期",
        [
          "HNAI MLIR Dialect",
          "DSE/pass pipeline",
          "跨层优化",
          "FPGA/ASIC 泛化"
        ]
      ]
    ],
    "note": "路线图核心：先证明闭环，再扩展编译后端和算法覆盖。"
  },
  {
    "type": "table",
    "title": "学术表达与讨论话题：把工程系统凝练为研究问题",
    "claim": "博士研究定位可以表达为“基于分层硬件意图 IR 的自然语言到 FPGA 自动设计与约束优化方法”。",
    "headers": [
      "关键词",
      "学术含义",
      "对应章节"
    ],
    "rows": [
      [
        "非 DNN AI 算法",
        "限定应用领域，区别于 DNN FPGA 工具",
        "第一章"
      ],
      [
        "分层硬件意图 IR",
        "核心贡献：HIS-L0/L1/L2",
        "第三章"
      ],
      [
        "自然语言到 FPGA",
        "覆盖输入到工程交付的跨度",
        "第二~五章"
      ],
      [
        "自动设计",
        "非人工架构设计与工具调度",
        "第二、四章"
      ],
      [
        "约束优化",
        "EDA 反馈闭环 + 前置约束检查",
        "第四、五章"
      ]
    ],
    "note": "开放问题：算法模板边界、HIS 表达力、LLM 与程序化分工、CIRCT 引入时机、评价体系。"
  },
  {
    "type": "section",
    "chapter": "第八章",
    "title": "总结与收束",
    "subtitle": "三句话总结 · 全篇回顾 · 关键概念速查"
  },
  {
    "type": "recap",
    "title": "全篇回顾：三句话收束项目定位",
    "claim": "HNAI-FPGA 用 HIS 把自然语言、硬件架构、验证工具和反馈优化连接成可解释闭环。",
    "sentences": [
      [
        "定位",
        "不是 AI 写 Verilog 工具，而是自然语言 → HIS → lowering → EDA 反馈 → FPGA 工程包的自动设计框架。"
      ],
      [
        "核心",
        "研究对象不是 Agent 循环本身，而是循环中可解释、可检查、可优化的硬件意图 IR 与反馈抽象。"
      ],
      [
        "路线",
        "MVP 先用 HIS JSON + 模板化 RTL 跑通全链路，中长期引入 CIRCT、UVM、RTL++ 和 HNAI MLIR dialect。"
      ]
    ],
    "chapters": [
      "技术演进",
      "项目定位",
      "分层 HIS",
      "Lowering 机制",
      "GA-Knapsack 案例",
      "工具链与 Agent",
      "创新点与路线图"
    ]
  },
  {
    "type": "glossary",
    "title": "团队速查：关键概念对照表",
    "claim": "最后保留概念速查，但改成三列卡片矩阵，避免原表格在投影时看不清。",
    "concepts": [
      [
        "SPEC",
        "人类可读需求规格"
      ],
      [
        "HIS-L0",
        "需求意图层"
      ],
      [
        "HIS-L1",
        "架构意图层"
      ],
      [
        "HIS-L2",
        "实现映射层"
      ],
      [
        "MLIR",
        "多层中间表示框架"
      ],
      [
        "CIRCT",
        "硬件领域 MLIR 工具链"
      ],
      [
        "Lowering",
        "程序化逐层转译机制"
      ],
      [
        "Golden Model",
        "功能正确性的参考实现"
      ],
      [
        "Agent",
        "工具调度与决策层"
      ],
      [
        "结构化诊断",
        "EDA 报告的机器可解析抽象"
      ],
      [
        "Spec2RTL",
        "当前最接近的 Agent 系统"
      ],
      [
        "RTL++",
        "CFG/DFG 图增强的 RTL 生成"
      ]
    ]
  }
];
