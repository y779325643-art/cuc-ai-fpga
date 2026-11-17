# 全量代码与函数导航索引

补充导航：[167个生产Python模块依赖](production-dependencies.md) · [JavaScript/MJS全部函数及回调](javascript-functions.md) · [公开配置与安装命令](configuration-index.md)。

生成日期：2026-11-09。范围是当前工作区 Git 已跟踪与未忽略未跟踪、且实际存在的文件；不把已删除文件还算作现存代码。

这是静态导航，不是逐函数正确性证明，也不是一次运行轨迹。Python 用 AST 提取全部命名类、函数及嵌套定义；参数只显示名字，不展开默认值。调用列列出源代码中直接出现的调用表达式（去重），不展开闭包、回调、反射、工厂和对象真实类型。类的 dataclass 自动方法、lambda 及字符串内嵌 RTL 不是 Python 命名定义。详情与全部调用位置在 [source-index.json](source-index.json)。

链接中的 #L 是供代码托管阅读器使用的源行标记；本地打开后可按符号名或表中行号定位。所有源码路径相对仓库根目录。

| 分组 | 代码文件 | 源文本行 | Python命名定义 | 索引 |
| --- | ---: | ---: | ---: | --- |
| agent-analysis | 4 | 1144 | 29 | [agent-analysis.md](agent-analysis.md) |
| agent-execution | 14 | 3379 | 184 | [agent-execution.md](agent-execution.md) |
| agent-generation | 9 | 1319 | 75 | [agent-generation.md](agent-generation.md) |
| agent-legacy-shared | 84 | 50622 | 1788 | [agent-legacy-shared.md](agent-legacy-shared.md) |
| agent-oracles | 7 | 2604 | 118 | [agent-oracles.md](agent-oracles.md) |
| agent-other | 3 | 877 | 21 | [agent-other.md](agent-other.md) |
| agent-pc | 12 | 2299 | 93 | [agent-pc.md](agent-pc.md) |
| agent-task_families | 8 | 11657 | 82 | [agent-task_families.md](agent-task_families.md) |
| agent-tasks | 21 | 2781 | 91 | [agent-tasks.md](agent-tasks.md) |
| agent-tests | 126 | 58054 | 2792 | [agent-tests.md](agent-tests.md) |
| app-other | 4 | 2663 | 31 | [app-other.md](app-other.md) |
| app-tests | 1 | 365 | 28 | [app-tests.md](app-tests.md) |
| compatibility_tests-tests | 4 | 510 | 25 | [compatibility_tests-tests.md](compatibility_tests-tests.md) |
| contracts-other | 6 | 2784 | 88 | [contracts-other.md](contracts-other.md) |
| contracts-tests | 41 | 5997 | 346 | [contracts-tests.md](contracts-tests.md) |
| docs-other | 1 | 305 | 11 | [docs-other.md](docs-other.md) |
| outputs-other | 71 | 12241 | 23 | [outputs-other.md](outputs-other.md) |
| training-other | 15 | 1646 | 54 | [training-other.md](training-other.md) |
| training-tests | 9 | 1573 | 79 | [training-tests.md](training-tests.md) |

合计：440 个自有实现/测试/展示代码文件；3370 个数据集和留存候选代码文件另见 [archive-code.md](archive-code.md)。历史候选工程属于被测数据，不能据数量推断系统有同样多的独立运行模块。

[返回审查总入口](../README.md)
