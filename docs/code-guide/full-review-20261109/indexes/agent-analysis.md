# agent-analysis：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `agent/src/sr2fpga_agent/analysis/__init__.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/analysis/__init__.py) · 21 行 · SHA-256 `bd8c6aa8e9a3a5d2737e3c5fff1ce8614f94b9b5c23ec270e5a41d56c783e391`

> Offline, manifest-led analysis for the current six-method PC 2.1 protocol.

导入模块：`sr2fpga_agent.analysis.core`

无命名类/函数定义；检查模块级代码和导出符号。

## `agent/src/sr2fpga_agent/analysis/__main__.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/analysis/__main__.py) · 145 行 · SHA-256 `c3c14b5181f5f81d152b5cb59f81d89c5912e34b03001f8644a973bed7ee0d0d`

> Offline manifest validation, cluster analysis and synthetic code checks.

导入模块：`__future__`、`argparse`、`json`、`pathlib`、`sr2fpga_agent.analysis.core`、`sr2fpga_agent.analysis.simulation`、`sr2fpga_agent.contract_registry`、`sr2fpga_agent.repository_paths`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_pairs` — `_pairs(pairs)` | function / [17](../../../../agent/src/sr2fpga_agent/analysis/__main__.py#L17) | `AnalysisInputError` |
| `_nonfinite` — `_nonfinite(value)` | function / [26](../../../../agent/src/sr2fpga_agent/analysis/__main__.py#L26) | `AnalysisInputError` |
| `_load` — `_load(path)` | function / [30](../../../../agent/src/sr2fpga_agent/analysis/__main__.py#L30) | `AnalysisInputError`、`json.loads`、`len`、`path.open`、`raw.decode`、`stream.read` |
| `_write` — `_write(output, value)` | function / [40](../../../../agent/src/sr2fpga_agent/analysis/__main__.py#L40) | `<dynamic>.join`、`<dynamic>.load_schema`、`<dynamic>.resolve`、`<dynamic>.validate`、`AnalysisInputError`、`ContractRegistry`、`RepositoryPaths.discover`、`destination.is_relative_to`、`destination.open`、`destination.parent.mkdir`、`json.dumps`、`output.resolve`、`print`、`str`、`stream.write`、`value.get` |
| `main` — `main(argv)` | function / [61](../../../../agent/src/sr2fpga_agent/analysis/__main__.py#L61) | `<dynamic>.join`、`<dynamic>.summary`、`<dynamic>.validate`、`AnalysisInputError`、`AnalysisPolicy.from_dict`、`ContractRegistry`、`_load`、`_write`、`analyze`、`argparse.ArgumentParser`、`command.add_argument`、`commands.add_parser`、`parser.add_subparsers`、`parser.exit`、`parser.parse_args`、`registry.load_schema`、`simulate`、`str`、`synthetic.add_argument`、`validate_dataset` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`SystemExit`、`main`

## `agent/src/sr2fpga_agent/analysis/core.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/analysis/core.py) · 744 行 · SHA-256 `f7c0d1fe5617550d685a444d4eec56ca13f250734948ebcea525161f50859b19`

> Paired, stratified design-cluster analysis with explicit missingness.

导入模块：`__future__`、`collections`、`dataclasses`、`json`、`math`、`random`、`re`、`sr2fpga_agent.models`、`statistics`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `AnalysisInputError` — `AnalysisInputError` | class / [37](../../../../agent/src/sr2fpga_agent/analysis/core.py#L37) | 无直接调用 |
| `canonical_sha256` — `canonical_sha256(value)` | function / [41](../../../../agent/src/sr2fpga_agent/analysis/core.py#L41) | `AnalysisInputError`、`json.dumps`、`sha256_json` |
| `_require` — `_require(condition, message)` | function / [51](../../../../agent/src/sr2fpga_agent/analysis/core.py#L51) | `AnalysisInputError` |
| `_identifier` — `_identifier(value, field)` | function / [56](../../../../agent/src/sr2fpga_agent/analysis/core.py#L56) | `_require`、`bool`、`isinstance`、`value.strip` |
| `_hash` — `_hash(value, field)` | function / [64](../../../../agent/src/sr2fpga_agent/analysis/core.py#L64) | `_SHA.fullmatch`、`_require`、`isinstance` |
| `_number` — `_number(value, field, low, high, exclusive_low)` | function / [72](../../../../agent/src/sr2fpga_agent/analysis/core.py#L72) | `_require`、`float`、`math.isfinite`、`type` |
| `_integer` — `_integer(value, field, low, high)` | function / [86](../../../../agent/src/sr2fpga_agent/analysis/core.py#L86) | `_require`、`type` |
| `AnalysisPolicy` — `AnalysisPolicy` | class / [95](../../../../agent/src/sr2fpga_agent/analysis/core.py#L95) | 无直接调用 |
| `AnalysisPolicy.__post_init__` — `__post_init__(self)` | function / [107](../../../../agent/src/sr2fpga_agent/analysis/core.py#L107) | `_integer`、`_number`、`_require`、`dict`、`isinstance`、`object.__setattr__`、`set` |
| `AnalysisPolicy.from_dict` — `from_dict(cls, payload)` | function / [141](../../../../agent/src/sr2fpga_agent/analysis/core.py#L141) | `_require`、`cls`、`dict`、`payload.pop`、`set` |
| `AnalysisPolicy.to_dict` — `to_dict(self)` | function / [155](../../../../agent/src/sr2fpga_agent/analysis/core.py#L155) | `asdict` |
| `JoinedDataset` — `JoinedDataset` | class / [160](../../../../agent/src/sr2fpga_agent/analysis/core.py#L160) | 无直接调用 |
| `JoinedDataset.summary` — `summary(self)` | function / [167](../../../../agent/src/sr2fpga_agent/analysis/core.py#L167) | `Counter`、`dict`、`len`、`sum` |
| `validate_dataset` — `validate_dataset(manifest, results)` | function / [187](../../../../agent/src/sr2fpga_agent/analysis/core.py#L187) | `<dynamic>.add`、`JoinedDataset`、`_hash`、`_identifier`、`_number`、`_require`、`all`、`block_methods.values`、`bool`、`by_result.get`、`by_slot.items`、`by_slot.values`、`canonical_sha256`、`configuration_weights.setdefault`、`defaultdict`、`dependency_members.values`、`dict`、`enumerate`、`instance_mapping.setdefault`、`isinstance`、`len`、`manifest.get`、`natural.add`、`raw_manifest.pop`、`result.get`、`row.get`、`rows.append`、`set`、`slot.get`、`sorted`、`task_clusters.setdefault`、`tuple`、`type` |
| `holm_adjust` — `holm_adjust(p_values)` | function / [422](../../../../agent/src/sr2fpga_agent/analysis/core.py#L422) | `_number`、`enumerate`、`len`、`max`、`min`、`range`、`sorted` |
| `_aggregate` — `_aggregate(dataset, mode)` | function / [441](../../../../agent/src/sr2fpga_agent/analysis/core.py#L441) | `<dynamic>.add`、`<dynamic>.append`、`by_block.items`、`clusters.items`、`configurations.items`、`defaultdict`、`float`、`len`、`mean`、`range`、`sorted`、`sum`、`tuple`、`vector.append` |
| `_estimate` — `_estimate(vectors, index)` | function / [500](../../../../agent/src/sr2fpga_agent/analysis/core.py#L500) | `any`、`len`、`math.sqrt`、`mean`、`sum`、`variance` |
| `_quantile` — `_quantile(values, probability)` | function / [518](../../../../agent/src/sr2fpga_agent/analysis/core.py#L518) | `len`、`math.floor`、`min`、`sorted` |
| `_bootstrap` — `_bootstrap(vectors, policy)` | function / [528](../../../../agent/src/sr2fpga_agent/analysis/core.py#L528) | `<dynamic>.append`、`_estimate`、`_quantile`、`any`、`enumerate`、`len`、`max`、`min`、`output.append`、`random.Random`、`range`、`reasons.append`、`rng.randrange`、`sum`、`vectors.values` |
| `_qualification` — `_qualification(dataset, policy, x, y)` | function / [608](../../../../agent/src/sr2fpga_agent/analysis/core.py#L608) | `abs`、`any`、`len`、`reasons.append`、`sum` |
| `_rates` — `_rates(dataset)` | function / [631](../../../../agent/src/sr2fpga_agent/analysis/core.py#L631) | `<dynamic>.append`、`clusters.values`、`configs.items`、`defaultdict`、`families.values`、`len`、`mean`、`sum` |
| `analyze` — `analyze(manifest, results, policy)` | function / [676](../../../../agent/src/sr2fpga_agent/analysis/core.py#L676) | `AnalysisPolicy.from_dict`、`_aggregate`、`_bootstrap`、`_estimate`、`_qualification`、`_rates`、`all`、`canonical_sha256`、`dataset.summary`、`enumerate`、`holm_adjust`、`isinstance`、`len`、`mean`、`policy.to_dict`、`validate_dataset` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`dataclass`、`re.compile`

## `agent/src/sr2fpga_agent/analysis/simulation.py`

[打开源文件](../../../../agent/src/sr2fpga_agent/analysis/simulation.py) · 234 行 · SHA-256 `ab3ba0620144652889f838358f04a433a6d09541cc23866c24162f93ac9982a2`

> Small, explicitly synthetic checks of the statistical procedure.

导入模块：`__future__`、`math`、`random`、`sr2fpga_agent.analysis.core`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `synthetic_dataset` — `synthetic_dataset(clusters_per_family, configurations, replicates, seed, system_effect, build_effect, baseline_probability, cluster_heterogeneity, missing_probability, effect_heterogeneity, shared_pair_fraction)` | function / [24](../../../../agent/src/sr2fpga_agent/analysis/simulation.py#L24) | `AnalysisInputError`、`canonical_sha256`、`int`、`math.isfinite`、`max`、`min`、`random.Random`、`range`、`results.append`、`rng.random`、`rng.uniform`、`slots.append`、`str`、`type` |
| `simulate` — `simulate(policy, trials, clusters_per_family, configurations, replicates, seed, boundary_null, baseline_probability, cluster_heterogeneity, missing_probability, effect_heterogeneity, shared_pair_fraction)` | function / [161](../../../../agent/src/sr2fpga_agent/analysis/simulation.py#L161) | `AnalysisInputError`、`all`、`analyze`、`decisions.append`、`dict`、`policy.to_dict`、`range`、`rejections.items`、`synthetic_dataset`、`type` |
