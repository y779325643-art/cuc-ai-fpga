# docs-other：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `docs/research-program/paper1-v1/figures/m3/render_m3_method_figures.py`

[打开源文件](../../../../docs/research-program/paper1-v1/figures/m3/render_m3_method_figures.py) · 305 行 · SHA-256 `9ab9df9517bf326d781bd866f2b46cb3f19644236aafb625eca0d11a30878d1d`

> Render SR2FPGA Paper-1 M3 explanatory figures with editable SVG text.

导入模块：`__future__`、`matplotlib`、`matplotlib.patches`、`matplotlib.pyplot`、`pathlib`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `setup` — `setup(width, height)` | function / [50](../../../../docs/research-program/paper1-v1/figures/m3/render_m3_method_figures.py#L50) | `ax.set_axis_off`、`ax.set_xlim`、`ax.set_ylim`、`plt.subplots` |
| `box` — `box(ax, x, y, w, h, text, fc, ec, lw, ls, fontsize, weight, color, radius, zorder)` | function / [58](../../../../docs/research-program/paper1-v1/figures/m3/render_m3_method_figures.py#L58) | `FancyBboxPatch`、`ax.add_patch`、`ax.text` |
| `arrow` — `arrow(ax, start, end, color, lw, style, connectionstyle, ls, zorder)` | function / [105](../../../../docs/research-program/paper1-v1/figures/m3/render_m3_method_figures.py#L105) | `FancyArrowPatch`、`ax.add_patch` |
| `label` — `label(ax, x, y, text, size, color, ha, weight)` | function / [132](../../../../docs/research-program/paper1-v1/figures/m3/render_m3_method_figures.py#L132) | `ax.text` |
| `legend` — `legend(ax, x, y)` | function / [145](../../../../docs/research-program/paper1-v1/figures/m3/render_m3_method_figures.py#L145) | `box` |
| `save` — `save(fig, stem)` | function / [150](../../../../docs/research-program/paper1-v1/figures/m3/render_m3_method_figures.py#L150) | `fig.savefig`、`plt.close` |
| `figure2_overview` — `figure2_overview()` | function / [158](../../../../docs/research-program/paper1-v1/figures/m3/render_m3_method_figures.py#L158) | `arrow`、`box`、`label`、`legend`、`save`、`setup` |
| `method_card` — `method_card(ax, y, method, label_text, fill, edge)` | function / [202](../../../../docs/research-program/paper1-v1/figures/m3/render_m3_method_figures.py#L202) | `box` |
| `figure3_matched_design` — `figure3_matched_design()` | function / [206](../../../../docs/research-program/paper1-v1/figures/m3/render_m3_method_figures.py#L206) | `arrow`、`box`、`label`、`method_card`、`save`、`setup` |
| `figure4_authority` — `figure4_authority()` | function / [248](../../../../docs/research-program/paper1-v1/figures/m3/render_m3_method_figures.py#L248) | `Rectangle`、`arrow`、`ax.add_patch`、`box`、`label`、`save`、`setup` |
| `main` — `main()` | function / [297](../../../../docs/research-program/paper1-v1/figures/m3/render_m3_method_figures.py#L297) | `OUT.mkdir`、`figure2_overview`、`figure3_matched_design`、`figure4_authority` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`<dynamic>.resolve`、`Path`、`main`、`mpl.rcParams.update`、`mpl.use`
