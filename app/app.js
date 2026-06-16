const sampleProject = {
  projectName: "uart_sensor_logger",
  topModule: "uart_sensor_logger_top",
  projectSpec:
    "设计一个完整 FPGA 项目：采集 8 位传感器数据，使用 FIFO 做缓存，通过 UART 以 115200 波特率发送到上位机。系统包含低电平复位、使能控制、忙闲状态输出、错误计数和可仿真的 testbench。",
  modulePlan:
    "clock_reset：统一复位同步\nsensor_capture：采集 sensor_data 和 sensor_valid\nfifo_buffer：缓存采集数据\nuart_tx：串口发送\ncontrol_fsm：调度采集、缓存和发送流程",
  constraintText:
    "系统时钟 50MHz；UART 波特率 115200；输入 sensor_data[7:0]、sensor_valid；输出 uart_tx、busy、error_count[7:0]；生成基础 XDC/SDC 约束模板。",
};

const toast = document.querySelector("#toast");
const projectOutput = document.querySelector("#projectOutput");
const projectName = document.querySelector("#projectName");
const topModule = document.querySelector("#topModule");
const projectSpec = document.querySelector("#projectSpec");
const modulePlan = document.querySelector("#modulePlan");
const constraintText = document.querySelector("#constraintText");
const temperature = document.querySelector("#temperature");
const tempValue = document.querySelector("#tempValue");

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2200);
}

function selectedDeliverables() {
  return {
    rtl: document.querySelector("#deliverRtl").checked,
    tb: document.querySelector("#deliverTb").checked,
    constraints: document.querySelector("#deliverConstraints").checked,
    readme: document.querySelector("#deliverReadme").checked,
  };
}

function updateCounts(deliverables) {
  document.querySelector("#rtlCount").textContent = deliverables.rtl ? "5" : "0";
  document.querySelector("#tbCount").textContent = deliverables.tb ? "1" : "0";
  document.querySelector("#constraintCount").textContent = deliverables.constraints ? "1" : "0";
  document.querySelector("#docCount").textContent = deliverables.readme ? "1" : "0";
}

function fallbackProject() {
  const name = projectName.value || "generated_fpga_project";
  const top = topModule.value || `${name}_top`;
  const deliverables = selectedDeliverables();

  const sections = [
    `# ${name}`,
    "",
    "## Project Tree",
    "```text",
    `${name}/`,
    deliverables.rtl ? "  rtl/" : "",
    deliverables.rtl ? `    ${top}.v` : "",
    deliverables.rtl ? "    clock_reset.v" : "",
    deliverables.rtl ? "    sensor_capture.v" : "",
    deliverables.rtl ? "    fifo_buffer.v" : "",
    deliverables.rtl ? "    uart_tx.v" : "",
    deliverables.tb ? "  sim/" : "",
    deliverables.tb ? `    tb_${top}.v` : "",
    deliverables.constraints ? "  constraints/" : "",
    deliverables.constraints ? `    ${name}.xdc` : "",
    deliverables.readme ? "  README.md" : "",
    "```",
    "",
    "## Architecture",
    "- clock_reset synchronizes the active-low reset into the system clock domain.",
    "- sensor_capture qualifies 8-bit sensor samples and raises a write request.",
    "- fifo_buffer decouples sensor input from UART output.",
    "- control_fsm schedules capture, FIFO read, UART transmit, busy, and error states.",
    "- uart_tx serializes data at the configured baud rate.",
    "",
  ].filter(Boolean);

  if (deliverables.rtl) {
    sections.push(
      "## rtl/" + top + ".v",
      "```verilog",
      `module ${top} (`,
      "    input  wire       clk,",
      "    input  wire       rst_n,",
      "    input  wire       en,",
      "    input  wire [7:0] sensor_data,",
      "    input  wire       sensor_valid,",
      "    output wire       uart_tx,",
      "    output wire       busy,",
      "    output reg  [7:0] error_count",
      ");",
      "",
      "wire rst_sync;",
      "wire sample_valid;",
      "wire [7:0] sample_data;",
      "wire fifo_wr_en;",
      "wire fifo_rd_en;",
      "wire fifo_empty;",
      "wire fifo_full;",
      "wire [7:0] fifo_dout;",
      "wire uart_start;",
      "wire uart_busy;",
      "",
      "clock_reset u_clock_reset (.clk(clk), .rst_n(rst_n), .rst_sync(rst_sync));",
      "sensor_capture u_sensor_capture (.clk(clk), .rst(rst_sync), .en(en), .sensor_data(sensor_data), .sensor_valid(sensor_valid), .sample_data(sample_data), .sample_valid(sample_valid));",
      "fifo_buffer u_fifo_buffer (.clk(clk), .rst(rst_sync), .wr_en(fifo_wr_en), .rd_en(fifo_rd_en), .din(sample_data), .dout(fifo_dout), .empty(fifo_empty), .full(fifo_full));",
      "control_fsm u_control_fsm (.clk(clk), .rst(rst_sync), .en(en), .sample_valid(sample_valid), .fifo_empty(fifo_empty), .fifo_full(fifo_full), .uart_busy(uart_busy), .fifo_wr_en(fifo_wr_en), .fifo_rd_en(fifo_rd_en), .uart_start(uart_start), .busy(busy));",
      "uart_tx #(.CLK_HZ(50000000), .BAUD(115200)) u_uart_tx (.clk(clk), .rst(rst_sync), .start(uart_start), .data(fifo_dout), .tx(uart_tx), .busy(uart_busy));",
      "",
      "always @(posedge clk) begin",
      "    if (rst_sync) begin",
      "        error_count <= 8'd0;",
      "    end else if (sample_valid && fifo_full) begin",
      "        error_count <= error_count + 8'd1;",
      "    end",
      "end",
      "",
      "endmodule",
      "```",
      "",
      "## rtl/control_fsm.v",
      "```verilog",
      "module control_fsm (",
      "    input  wire clk, rst, en, sample_valid, fifo_empty, fifo_full, uart_busy,",
      "    output reg  fifo_wr_en, fifo_rd_en, uart_start, busy",
      ");",
      "localparam IDLE = 2'd0, CAPTURE = 2'd1, SEND = 2'd2;",
      "reg [1:0] state;",
      "always @(posedge clk) begin",
      "    if (rst) begin",
      "        state <= IDLE;",
      "        fifo_wr_en <= 1'b0;",
      "        fifo_rd_en <= 1'b0;",
      "        uart_start <= 1'b0;",
      "        busy <= 1'b0;",
      "    end else begin",
      "        fifo_wr_en <= en && sample_valid && !fifo_full;",
      "        fifo_rd_en <= 1'b0;",
      "        uart_start <= 1'b0;",
      "        busy <= en;",
      "        case (state)",
      "            IDLE: state <= en ? CAPTURE : IDLE;",
      "            CAPTURE: if (!fifo_empty && !uart_busy) begin fifo_rd_en <= 1'b1; state <= SEND; end",
      "            SEND: begin uart_start <= 1'b1; state <= CAPTURE; end",
      "            default: state <= IDLE;",
      "        endcase",
      "    end",
      "end",
      "endmodule",
      "```",
      "",
      "## Other RTL Files",
      "- clock_reset.v: two-stage reset synchronizer.",
      "- sensor_capture.v: registers valid sensor samples.",
      "- fifo_buffer.v: small synchronous FIFO with full and empty flags.",
      "- uart_tx.v: parameterized UART transmitter."
    );
  }

  if (deliverables.tb) {
    sections.push(
      "",
      "## sim/tb_" + top + ".v",
      "```verilog",
      `module tb_${top};`,
      "reg clk = 1'b0;",
      "reg rst_n = 1'b0;",
      "reg en = 1'b0;",
      "reg [7:0] sensor_data = 8'd0;",
      "reg sensor_valid = 1'b0;",
      "wire uart_tx;",
      "wire busy;",
      "wire [7:0] error_count;",
      "",
      "always #10 clk = ~clk;",
      "",
      `${top} dut (.clk(clk), .rst_n(rst_n), .en(en), .sensor_data(sensor_data), .sensor_valid(sensor_valid), .uart_tx(uart_tx), .busy(busy), .error_count(error_count));`,
      "",
      "initial begin",
      "    #100 rst_n = 1'b1;",
      "    en = 1'b1;",
      "    repeat (16) begin",
      "        @(posedge clk);",
      "        sensor_data <= sensor_data + 8'd1;",
      "        sensor_valid <= 1'b1;",
      "        @(posedge clk);",
      "        sensor_valid <= 1'b0;",
      "    end",
      "    #20000 $finish;",
      "end",
      "endmodule",
      "```"
    );
  }

  if (deliverables.constraints) {
    sections.push(
      "",
      "## constraints/" + name + ".xdc",
      "```tcl",
      "create_clock -period 20.000 [get_ports clk]",
      "set_property IOSTANDARD LVCMOS33 [get_ports {clk rst_n en sensor_valid uart_tx busy}]",
      "set_property IOSTANDARD LVCMOS33 [get_ports {sensor_data[*] error_count[*]}]",
      "```"
    );
  }

  if (deliverables.readme) {
    sections.push(
      "",
      "## README.md",
      "Run simulation first, then synthesize the top module. Replace placeholder pin locations in the constraint file before implementation."
    );
  }

  return sections.join("\n");
}

function buildPrompt() {
  const deliverables = selectedDeliverables();
  return [
    "你是 FPGA 项目生成助手。请生成一个完整、可落地的 FPGA 工程，而不是单一模块。",
    "",
    `项目名称：${projectName.value}`,
    `顶层模块：${topModule.value}`,
    `项目类型：${document.querySelector("#projectType").value}`,
    `目标语言：${document.querySelector("#hdlType").value}`,
    "",
    "系统级需求：",
    projectSpec.value,
    "",
    "期望模块划分：",
    modulePlan.value,
    "",
    "时钟、接口与约束：",
    constraintText.value,
    "",
    "必须输出：",
    deliverables.rtl ? "- rtl/ 下的顶层模块和子模块代码" : "",
    deliverables.tb ? "- sim/ 下的 testbench" : "",
    deliverables.constraints ? "- constraints/ 下的 XDC 或 SDC 约束模板" : "",
    deliverables.readme ? "- README.md，说明工程结构、仿真步骤和综合注意事项" : "",
    "",
    "输出格式要求：先给项目目录树，再按文件路径逐个给完整文件内容。不要只给一个模块。",
  ]
    .filter(Boolean)
    .join("\n");
}

document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
    button.classList.add("active");
    document.querySelector(`#${button.dataset.view}`).classList.add("active");
  });
});

temperature.addEventListener("input", () => {
  tempValue.textContent = temperature.value;
});

document.querySelectorAll(".deliverables input").forEach((input) => {
  input.addEventListener("change", () => {
    updateCounts(selectedDeliverables());
    projectOutput.textContent = fallbackProject();
  });
});

document.querySelector("#sampleBtn").addEventListener("click", () => {
  projectName.value = sampleProject.projectName;
  topModule.value = sampleProject.topModule;
  projectSpec.value = sampleProject.projectSpec;
  modulePlan.value = sampleProject.modulePlan;
  constraintText.value = sampleProject.constraintText;
  projectOutput.textContent = fallbackProject();
  showToast("已填入完整项目示例");
});

document.querySelector("#generateForm").addEventListener("submit", async (event) => {
  event.preventDefault();

  const apiUrl = document.querySelector("#apiUrl").value.replace(/\/$/, "");
  const model = document.querySelector("#modelName").value;
  projectOutput.textContent = "正在生成完整 FPGA 工程...";

  try {
    const response = await fetch(`${apiUrl}/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        messages: [{ role: "user", content: buildPrompt() }],
        temperature: Number(temperature.value),
        max_tokens: 4096,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    projectOutput.textContent = data.choices?.[0]?.message?.content?.trim() || fallbackProject();
    showToast("完整项目生成完成");
  } catch (error) {
    projectOutput.textContent = fallbackProject();
    showToast("未连接到本地服务，已显示完整项目演示输出");
  }
});

document.querySelector("#copyBtn").addEventListener("click", async () => {
  await navigator.clipboard.writeText(projectOutput.textContent);
  showToast("项目输出已复制");
});

document.querySelector("#downloadBtn").addEventListener("click", () => {
  const blob = new Blob([projectOutput.textContent], { type: "text/markdown;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${projectName.value || "generated_fpga_project"}_project.md`;
  link.click();
  URL.revokeObjectURL(link.href);
  showToast("已下载项目说明");
});

updateCounts(selectedDeliverables());
projectOutput.textContent = fallbackProject();
