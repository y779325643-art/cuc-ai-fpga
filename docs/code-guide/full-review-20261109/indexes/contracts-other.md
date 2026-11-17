# contracts-other：文件、符号与调用表达式

[返回全量索引](README.md)。下列调用是源文本中的语法调用；同名对象或运行分支可能改变实际目标。

## `contracts/tools/build_dataset_inventory.py`

[打开源文件](../../../../contracts/tools/build_dataset_inventory.py) · 112 行 · SHA-256 `b26e6073bc75fc9f854137c3a261da86f8be8fc92611b6382b99db9313d95134`

> Build deterministic SHA-256 inventories for immutable dataset releases.

导入模块：`__future__`、`argparse`、`hashlib`、`pathlib`、`re`、`sys`、`tempfile`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `ensure_within_root` — `ensure_within_root(path, root)` | function / [17](../../../../contracts/tools/build_dataset_inventory.py#L17) | `ValueError`、`path.resolve`、`resolved.is_relative_to` |
| `sha256_file` — `sha256_file(path)` | function / [24](../../../../contracts/tools/build_dataset_inventory.py#L24) | `digest.hexdigest`、`digest.update`、`hashlib.sha256`、`iter`、`path.open`、`stream.read` |
| `release_directories` — `release_directories(root, release_id)` | function / [32](../../../../contracts/tools/build_dataset_inventory.py#L32) | `FileNotFoundError`、`RELEASE_ID_PATTERN.fullmatch`、`ValueError`、`ensure_within_root`、`path.is_dir` |
| `inventory_records` — `inventory_records(root, release_id)` | function / [44](../../../../contracts/tools/build_dataset_inventory.py#L44) | `<dynamic>.as_posix`、`candidate.is_file`、`candidate.relative_to`、`ensure_within_root`、`files.append`、`release_directories`、`release_root.rglob`、`sha256_file`、`sorted` |
| `write_inventory` — `write_inventory(root, release_id)` | function / [61](../../../../contracts/tools/build_dataset_inventory.py#L61) | `<dynamic>.encode`、`Path`、`ensure_within_root`、`inventory_records`、`output_dir.mkdir`、`tempfile.NamedTemporaryFile`、`temporary.write`、`temporary_path.exists`、`temporary_path.replace`、`temporary_path.unlink` |
| `parse_args` — `parse_args(argv)` | function / [87](../../../../contracts/tools/build_dataset_inventory.py#L87) | `argparse.ArgumentParser`、`parser.add_argument`、`parser.parse_args` |
| `main` — `main(argv)` | function / [94](../../../../contracts/tools/build_dataset_inventory.py#L94) | `<dynamic>.as_posix`、`args.root.resolve`、`output_path.relative_to`、`parse_args`、`print`、`root.is_dir`、`write_inventory` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`SystemExit`、`main`、`re.compile`

## `contracts/tools/curate_legacy_evidence.py`

[打开源文件](../../../../contracts/tools/curate_legacy_evidence.py) · 616 行 · SHA-256 `36fd2a68749a1fd82fc884201e92a0779cfd303b945629f04cb34731b17bee92`

> Preview or copy verified legacy evidence into stable report paths.

导入模块：`__future__`、`argparse`、`hashlib`、`json`、`os`、`pathlib`、`re`、`shutil`、`sys`、`tempfile`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_load_json` — `_load_json(path)` | function / [38](../../../../contracts/tools/curate_legacy_evidence.py#L38) | `ValueError`、`isinstance`、`json.loads`、`path.read_text` |
| `_sha256` — `_sha256(path)` | function / [45](../../../../contracts/tools/curate_legacy_evidence.py#L45) | `digest.hexdigest`、`digest.update`、`hashlib.sha256`、`iter`、`path.open`、`stream.read` |
| `_safe_relative` — `_safe_relative(value, field)` | function / [53](../../../../contracts/tools/curate_legacy_evidence.py#L53) | `PurePosixPath`、`ValueError`、`path.is_absolute`、`re.match` |
| `_repository_path` — `_repository_path(repository, value, field)` | function / [67](../../../../contracts/tools/curate_legacy_evidence.py#L67) | `<dynamic>.resolve`、`Path`、`ValueError`、`_safe_relative`、`candidate.is_relative_to` |
| `_backup_path` — `_backup_path(backup_workspace, value)` | function / [80](../../../../contracts/tools/curate_legacy_evidence.py#L80) | `<dynamic>.resolve`、`Path`、`ValueError`、`_safe_relative`、`candidate.is_relative_to` |
| `_manifest_records` — `_manifest_records(manifest)` | function / [91](../../../../contracts/tools/curate_legacy_evidence.py#L91) | `<dynamic>.as_posix`、`<dynamic>.lower`、`SHA256_PATTERN.fullmatch`、`ValueError`、`_safe_relative`、`int`、`isinstance`、`manifest.get`、`raw_record.get`、`str` |
| `_validate_recheck` — `_validate_recheck(repository, backup, recheck_path)` | function / [123](../../../../contracts/tools/curate_legacy_evidence.py#L123) | `<dynamic>.resolve`、`Path`、`SHA256_PATTERN.fullmatch`、`ValueError`、`_load_json`、`_sha256`、`int`、`recheck.get`、`str` |
| `_expand_reference` — `_expand_reference(records, source_reference, reference_kind)` | function / [147](../../../../contracts/tools/curate_legacy_evidence.py#L147) | `ValueError`、`path.startswith`、`records.get`、`records.items`、`sorted`、`source_reference.rstrip` |
| `_destination_for_record` — `_destination_for_record(source_reference, destination_reference, reference_kind, record_path)` | function / [175](../../../../contracts/tools/curate_legacy_evidence.py#L175) | `ValueError`、`record_path.relative_to` |
| `_scan_content` — `_scan_content(path)` | function / [189](../../../../contracts/tools/curate_legacy_evidence.py#L189) | `any`、`path.read_bytes`、`pattern.search` |
| `build_curation_preview` — `build_curation_preview(repository, backup_root, plan_path, recheck_path)` | function / [198](../../../../contracts/tools/curate_legacy_evidence.py#L198) | `<dynamic>.as_posix`、`<dynamic>.exists`、`<dynamic>.resolve`、`FileNotFoundError`、`PurePosixPath`、`ValueError`、`_backup_path`、`_destination_for_record`、`_expand_reference`、`_load_json`、`_manifest_records`、`_safe_relative`、`_scan_content`、`_sha256`、`_validate_recheck`、`backup.is_dir`、`backup.is_relative_to`、`backup_root.resolve`、`bool`、`destination.as_posix`、`destination_reference.is_relative_to`、`destination_sources.get`、`group.get`、`int`、`isinstance`、`len`、`plan.get`、`plan_path.is_relative_to`、`plan_path.relative_to`、`plan_path.resolve`、`private_paths.add`、`recheck_path.is_relative_to`、`recheck_path.relative_to`、`recheck_path.resolve`、`reference.get`、`repository.resolve`、`secret_paths.add`、`selected_files.get`、`selected_files.values`、`set`、`sorted`、`source.is_file`、`source.stat`、`source_reference.as_posix`、`str`、`sum`、`workspace.is_relative_to` |
| `apply_curation` — `apply_curation(repository, backup_root, preview)` | function / [371](../../../../contracts/tools/curate_legacy_evidence.py#L371) | `<dynamic>.resolve`、`FileNotFoundError`、`Path`、`ValueError`、`_backup_path`、`_repository_path`、`_safe_relative`、`_sha256`、`backup_root.resolve`、`destination.exists`、`destination.is_file`、`destination.parent.mkdir`、`destination.stat`、`destination_relative.as_posix`、`destination_relative.is_relative_to`、`dict`、`int`、`isinstance`、`operations.append`、`preview.get`、`record.get`、`repository.resolve`、`result.update`、`shutil.copyfile`、`source.is_file`、`source.stat`、`source_relative.as_posix`、`str`、`tempfile.NamedTemporaryFile`、`temporary_path.exists`、`temporary_path.replace`、`temporary_path.unlink` |
| `write_curation` — `write_curation(path, curation)` | function / [476](../../../../contracts/tools/curate_legacy_evidence.py#L476) | `<dynamic>.encode`、`Path`、`json.dumps`、`path.parent.mkdir`、`tempfile.NamedTemporaryFile`、`temporary.write`、`temporary_path.exists`、`temporary_path.replace`、`temporary_path.unlink` |
| `parse_args` — `parse_args(argv)` | function / [498](../../../../contracts/tools/curate_legacy_evidence.py#L498) | `Path`、`Path.cwd`、`argparse.ArgumentParser`、`os.environ.get`、`parser.add_argument`、`parser.parse_args` |
| `_inside_repository` — `_inside_repository(repository, candidate, field)` | function / [536](../../../../contracts/tools/curate_legacy_evidence.py#L536) | `<dynamic>.resolve`、`ValueError`、`candidate.is_absolute`、`candidate.resolve`、`resolved.is_relative_to` |
| `_output_path` — `_output_path(repository, candidate, apply)` | function / [547](../../../../contracts/tools/curate_legacy_evidence.py#L547) | `<dynamic>.as_posix`、`<dynamic>.resolve`、`ValueError`、`_inside_repository`、`allowed.relative_to`、`output.is_relative_to` |
| `main` — `main(argv)` | function / [568](../../../../contracts/tools/curate_legacy_evidence.py#L568) | `<dynamic>.as_posix`、`ValueError`、`_inside_repository`、`_output_path`、`apply_curation`、`args.root.resolve`、`build_curation_preview`、`output_path.relative_to`、`parse_args`、`print`、`write_curation` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`PurePosixPath`、`SystemExit`、`main`、`re.compile`

## `contracts/tools/inventory_tracked_tmp.py`

[打开源文件](../../../../contracts/tools/inventory_tracked_tmp.py) · 288 行 · SHA-256 `cf4258213bc55c381a5ba51befc16239f7f6aeff87ff8fe6d60a839bcc113c7f`

> Inventory tracked tmp files without moving or deleting repository content.

导入模块：`__future__`、`argparse`、`json`、`pathlib`、`subprocess`、`sys`、`tempfile`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_git` — `_git(root, *arguments, binary)` | function / [19](../../../../contracts/tools/inventory_tracked_tmp.py#L19) | `completed.stdout.decode`、`subprocess.run` |
| `resolve_repository_root` — `resolve_repository_root(candidate)` | function / [31](../../../../contracts/tools/inventory_tracked_tmp.py#L31) | `<dynamic>.exists`、`<dynamic>.resolve`、`<dynamic>.strip`、`Path`、`Path.cwd`、`ValueError`、`_git`、`str` |
| `tracked_tmp_entries` — `tracked_tmp_entries(root)` | function / [42](../../../../contracts/tools/inventory_tracked_tmp.py#L42) | `<dynamic>.split`、`<dynamic>.strip`、`ValueError`、`_git`、`bytes`、`entries.append`、`int`、`metadata.decode`、`raw_path.decode`、`raw_record.split`、`sorted`、`str` |
| `_safe_relative_path` — `_safe_relative_path(value, field)` | function / [70](../../../../contracts/tools/inventory_tracked_tmp.py#L70) | `PurePosixPath`、`ValueError`、`path.is_absolute` |
| `load_classification_map` — `load_classification_map(path)` | function / [77](../../../../contracts/tools/inventory_tracked_tmp.py#L77) | `<dynamic>.as_posix`、`ValueError`、`_safe_relative_path`、`destination_root.as_posix`、`destination_root.is_relative_to`、`isinstance`、`json.loads`、`mapping.get`、`normalized.append`、`normalized_paths.append`、`path.read_text`、`payload.get`、`relative.as_posix`、`selected_sources.add`、`set`、`sorted`、`source_root.as_posix`、`str` |
| `build_inventory` — `build_inventory(root, classification_path, external_backup_manifest)` | function / [135](../../../../contracts/tools/inventory_tracked_tmp.py#L135) | `<dynamic>.as_posix`、`<dynamic>.relative_to`、`PurePosixPath`、`ValueError`、`classification_path.resolve`、`dict`、`external_backup_manifest.strip`、`len`、`load_classification_map`、`record.update`、`records.append`、`selected.get`、`sum`、`tracked_tmp_entries` |
| `write_inventory` — `write_inventory(path, inventory)` | function / [203](../../../../contracts/tools/inventory_tracked_tmp.py#L203) | `<dynamic>.encode`、`Path`、`json.dumps`、`path.parent.mkdir`、`tempfile.NamedTemporaryFile`、`temporary.write`、`temporary_path.exists`、`temporary_path.replace`、`temporary_path.unlink` |
| `parse_args` — `parse_args(argv)` | function / [226](../../../../contracts/tools/inventory_tracked_tmp.py#L226) | `Path`、`argparse.ArgumentParser`、`parser.add_argument`、`parser.parse_args` |
| `main` — `main(argv)` | function / [242](../../../../contracts/tools/inventory_tracked_tmp.py#L242) | `<dynamic>.as_posix`、`<dynamic>.resolve`、`ValueError`、`args.classification_map.is_absolute`、`args.output.is_absolute`、`args.output.resolve`、`build_inventory`、`classification_path.is_relative_to`、`output_path.is_relative_to`、`output_path.relative_to`、`parse_args`、`print`、`resolve_repository_root`、`write_inventory` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`PurePosixPath`、`SystemExit`、`main`

## `contracts/tools/plan_legacy_evidence_migration.py`

[打开源文件](../../../../contracts/tools/plan_legacy_evidence_migration.py) · 266 行 · SHA-256 `621d816791f600044c7244c4b6b85022509cefbc1e6387250f83679dfe44c971`

> Plan migration of active legacy tmp evidence without copying any files.

导入模块：`__future__`、`argparse`、`json`、`pathlib`、`sys`、`tempfile`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_safe_relative_path` — `_safe_relative_path(value, field)` | function / [18](../../../../contracts/tools/plan_legacy_evidence_migration.py#L18) | `PurePosixPath`、`ValueError`、`path.is_absolute` |
| `_source_root` — `_source_root(reference)` | function / [30](../../../../contracts/tools/plan_legacy_evidence_migration.py#L30) | `PurePosixPath`、`ValueError`、`len` |
| `_run_id_from_summary` — `_run_id_from_summary(reference)` | function / [36](../../../../contracts/tools/plan_legacy_evidence_migration.py#L36) | `enumerate` |
| `_reference_kind` — `_reference_kind(reference)` | function / [44](../../../../contracts/tools/plan_legacy_evidence_migration.py#L44) | 无直接调用 |
| `build_plan` — `build_plan(ledger, source_ledger)` | function / [50](../../../../contracts/tools/plan_legacy_evidence_migration.py#L50) | `<dynamic>.add`、`<dynamic>.append`、`<dynamic>.as_posix`、`<dynamic>.strip`、`CURATED_ROOT.as_posix`、`PurePosixPath`、`ValueError`、`_reference_kind`、`_run_id_from_summary`、`_safe_relative_path`、`_source_root`、`destination.as_posix`、`destination.is_relative_to`、`destination_root.as_posix`、`destinations.add`、`family.get`、`groups.append`、`isinstance`、`iter`、`ledger.get`、`len`、`next`、`reference.as_posix`、`reference.relative_to`、`reference_families.setdefault`、`reference_text.startswith`、`relative.as_posix`、`root.as_posix`、`roots.get`、`roots.setdefault`、`run_groups.setdefault`、`set`、`sorted`、`source_ledger_path.as_posix`、`str`、`sum` |
| `write_plan` — `write_plan(path, plan)` | function / [184](../../../../contracts/tools/plan_legacy_evidence_migration.py#L184) | `<dynamic>.encode`、`Path`、`json.dumps`、`path.parent.mkdir`、`tempfile.NamedTemporaryFile`、`temporary.write`、`temporary_path.exists`、`temporary_path.replace`、`temporary_path.unlink` |
| `parse_args` — `parse_args(argv)` | function / [206](../../../../contracts/tools/plan_legacy_evidence_migration.py#L206) | `Path`、`Path.cwd`、`argparse.ArgumentParser`、`parser.add_argument`、`parser.parse_args` |
| `_within_root` — `_within_root(root, candidate, field)` | function / [226](../../../../contracts/tools/plan_legacy_evidence_migration.py#L226) | `<dynamic>.resolve`、`ValueError`、`candidate.is_absolute`、`candidate.resolve`、`resolved.is_relative_to` |
| `main` — `main(argv)` | function / [237](../../../../contracts/tools/plan_legacy_evidence_migration.py#L237) | `<dynamic>.as_posix`、`<dynamic>.exists`、`ValueError`、`_within_root`、`args.root.resolve`、`build_plan`、`json.loads`、`ledger_path.read_text`、`ledger_path.relative_to`、`output_path.relative_to`、`parse_args`、`print`、`write_plan` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`PurePosixPath`、`SystemExit`、`main`

## `contracts/tools/promote_regenerated_evidence.py`

[打开源文件](../../../../contracts/tools/promote_regenerated_evidence.py) · 1131 行 · SHA-256 `c76bdf61fe90cc4601750058c18760cfbdcb5c981103489dd0d77094c3e4508f`

> Promote regenerated evidence into stable, sanitized repository paths.

导入模块：`__future__`、`argparse`、`hashlib`、`json`、`pathlib`、`re`、`sys`、`tempfile`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_load_json` — `_load_json(path)` | function / [99](../../../../contracts/tools/promote_regenerated_evidence.py#L99) | `ValueError`、`isinstance`、`json.loads`、`path.read_text` |
| `_sha256_bytes` — `_sha256_bytes(data)` | function / [106](../../../../contracts/tools/promote_regenerated_evidence.py#L106) | `<dynamic>.hexdigest`、`hashlib.sha256` |
| `_sha256` — `_sha256(path)` | function / [110](../../../../contracts/tools/promote_regenerated_evidence.py#L110) | `digest.hexdigest`、`digest.update`、`hashlib.sha256`、`iter`、`path.open`、`stream.read` |
| `_safe_relative` — `_safe_relative(value, field)` | function / [118](../../../../contracts/tools/promote_regenerated_evidence.py#L118) | `PurePosixPath`、`ValueError`、`path.is_absolute`、`re.match` |
| `_repository_path` — `_repository_path(repository, value, field)` | function / [132](../../../../contracts/tools/promote_regenerated_evidence.py#L132) | `<dynamic>.resolve`、`Path`、`ValueError`、`_safe_relative`、`candidate.is_relative_to` |
| `_atomic_write` — `_atomic_write(path, data)` | function / [140](../../../../contracts/tools/promote_regenerated_evidence.py#L140) | `Path`、`path.parent.mkdir`、`tempfile.NamedTemporaryFile`、`temporary.write`、`temporary_path.exists`、`temporary_path.replace`、`temporary_path.unlink` |
| `_sanitize_text` — `_sanitize_text(value, repository)` | function / [159](../../../../contracts/tools/promote_regenerated_evidence.py#L159) | `<dynamic>.join`、`<dynamic>.lower`、`<dynamic>.replace`、`pattern.subn`、`re.escape`、`re.subn`、`repository.drive.rstrip`、`repository_variants.add`、`sorted`、`str` |
| `_sanitize_json_value` — `_sanitize_json_value(value, repository)` | function / [192](../../../../contracts/tools/promote_regenerated_evidence.py#L192) | `_sanitize_json_value`、`_sanitize_text`、`isinstance`、`sanitized_items.append`、`value.items` |
| `_curate_bytes` — `_curate_bytes(path, repository)` | function / [220](../../../../contracts/tools/promote_regenerated_evidence.py#L220) | `<dynamic>.encode`、`<dynamic>.join`、`ValueError`、`_sanitize_json_value`、`_sanitize_text`、`enumerate`、`json.dumps`、`json.loads`、`line.strip`、`lines.append`、`path.read_bytes`、`path.suffix.lower`、`raw.decode`、`sanitized_text.encode`、`text.splitlines`、`transformations.append`、`tuple` |
| `_is_excluded` — `_is_excluded(path)` | function / [282](../../../../contracts/tools/promote_regenerated_evidence.py#L282) | `path.suffix.lower` |
| `_load_source_groups` — `_load_source_groups(repository, source_map_path, plan)` | function / [286](../../../../contracts/tools/promote_regenerated_evidence.py#L286) | `<dynamic>.as_posix`、`<dynamic>.is_absolute`、`FileNotFoundError`、`PurePosixPath`、`ValueError`、`_load_json`、`_repository_path`、`_safe_relative`、`candidate_root.is_dir`、`group.get`、`groups.keys`、`isinstance`、`legacy_roots.add`、`plan.get`、`raw_group.get`、`replacement.get`、`replacements.append`、`run_root.is_dir`、`set`、`sorted`、`source_map.get`、`str`、`strip_prefix.endswith`、`summary.get`、`tuple` |
| `_map_legacy_relative` — `_map_legacy_relative(group, value)` | function / [377](../../../../contracts/tools/promote_regenerated_evidence.py#L377) | `ValueError`、`_safe_relative`、`len`、`mapped.replace`、`mapped.startswith` |
| `_source_for_relative` — `_source_for_relative(group, relative)` | function / [391](../../../../contracts/tools/promote_regenerated_evidence.py#L391) | `<dynamic>.resolve`、`Path`、`PurePosixPath`、`ValueError`、`len`、`source.is_relative_to` |
| `_relative_for_source` — `_relative_for_source(group, source)` | function / [415](../../../../contracts/tools/promote_regenerated_evidence.py#L415) | `<dynamic>.as_posix`、`PurePosixPath`、`ValueError`、`source.is_relative_to`、`source.relative_to`、`source.resolve` |
| `_destination_for_relative` — `_destination_for_relative(run_id, relative)` | function / [430](../../../../contracts/tools/promote_regenerated_evidence.py#L430) | 无直接调用 |
| `_scan_content` — `_scan_content(data)` | function / [437](../../../../contracts/tools/promote_regenerated_evidence.py#L437) | `any`、`pattern.search` |
| `_ledger_references` — `_ledger_references(ledger)` | function / [443](../../../../contracts/tools/promote_regenerated_evidence.py#L443) | `ValueError`、`all`、`family.get`、`isinstance`、`ledger.get`、`references.extend` |
| `build_promotion_preview` — `build_promotion_preview(repository, plan_path, source_map_path, ledger_path)` | function / [460](../../../../contracts/tools/promote_regenerated_evidence.py#L460) | `<dynamic>.add`、`<dynamic>.as_posix`、`<dynamic>.exists`、`FileNotFoundError`、`Path`、`PurePosixPath`、`ValueError`、`_curate_bytes`、`_destination_for_relative`、`_ledger_references`、`_load_json`、`_load_source_groups`、`_map_legacy_relative`、`_repository_path`、`_safe_relative`、`_scan_content`、`_sha256`、`_sha256_bytes`、`_source_for_relative`、`any`、`bool`、`destination.exists`、`destination.is_file`、`file_records.append`、`groups.items`、`int`、`isinstance`、`ledger_path.relative_to`、`ledger_path.resolve`、`len`、`list`、`path.is_relative_to`、`pattern.search`、`plan.get`、`plan_path.relative_to`、`plan_path.resolve`、`private_paths.append`、`raw_plan_group.get`、`reference.get`、`reference.startswith`、`reference_map.get`、`reference_map.items`、`repository.resolve`、`sample_root.is_dir`、`secret_paths.append`、`select_attempt_evidence`、`select_file`、`select_mutation_tree`、`select_tree`、`selected.items`、`set`、`sorted`、`source.read_bytes`、`source_map_path.relative_to`、`source_map_path.resolve`、`str`、`sum` |
| `build_promotion_preview.select_file` — `select_file(group, source, reason, required)` | function / [496](../../../../contracts/tools/promote_regenerated_evidence.py#L496) | `<dynamic>.add`、`<dynamic>.as_posix`、`FileNotFoundError`、`ValueError`、`_destination_for_relative`、`_is_excluded`、`_relative_for_source`、`destination_sources.get`、`excluded_files.add`、`selected.get`、`source.exists`、`source.is_file`、`source.relative_to` |
| `build_promotion_preview.select_tree` — `select_tree(group, root, reason, required)` | function / [537](../../../../contracts/tools/promote_regenerated_evidence.py#L537) | `<dynamic>.as_posix`、`FileNotFoundError`、`ValueError`、`_is_excluded`、`excluded_files.add`、`path.is_file`、`path.relative_to`、`root.exists`、`root.is_dir`、`root.rglob`、`select_file`、`sorted` |
| `build_promotion_preview.select_mutation_tree` — `select_mutation_tree(group, root)` | function / [561](../../../../contracts/tools/promote_regenerated_evidence.py#L561) | `<dynamic>.as_posix`、`FileNotFoundError`、`ValueError`、`_is_excluded`、`candidate.is_file`、`excluded_files.add`、`len`、`path.relative_to`、`path.suffix.lower`、`root.is_dir`、`root.rglob`、`select_file`、`sorted` |
| `build_promotion_preview.select_attempt_evidence` — `select_attempt_evidence(group, root)` | function / [596](../../../../contracts/tools/promote_regenerated_evidence.py#L596) | `<dynamic>.as_posix`、`FileNotFoundError`、`ValueError`、`_is_excluded`、`candidate.is_file`、`excluded_files.add`、`len`、`path.relative_to`、`relative.as_posix`、`root.is_dir`、`root.rglob`、`select_file`、`sorted` |
| `_encode_task_evidence_ledger` — `_encode_task_evidence_ledger(ledger)` | function / [839](../../../../contracts/tools/promote_regenerated_evidence.py#L839) | `<dynamic>.encode`、`<dynamic>.join`、`ValueError`、`enumerate`、`isinstance`、`json.dumps`、`len`、`lines.append`、`list` |
| `apply_promotion` — `apply_promotion(repository, preview)` | function / [869](../../../../contracts/tools/promote_regenerated_evidence.py#L869) | `FileNotFoundError`、`ValueError`、`_atomic_write`、`_curate_bytes`、`_encode_task_evidence_ledger`、`_ledger_references`、`_load_json`、`_repository_path`、`_safe_relative`、`_scan_content`、`_sha256`、`_sha256_bytes`、`destination.exists`、`destination.is_file`、`destination_relative.as_posix`、`destination_relative.is_relative_to`、`dict`、`family.get`、`isinstance`、`ledger.get`、`operations.append`、`preview.get`、`record.get`、`reference.startswith`、`reference_map.get`、`reference_map.keys`、`repository.resolve`、`result.update`、`rewritten.append`、`seen_sources.add`、`set`、`sorted`、`source.is_file`、`source.read_bytes`、`str` |
| `write_promotion` — `write_promotion(path, promotion)` | function / [1015](../../../../contracts/tools/promote_regenerated_evidence.py#L1015) | `<dynamic>.encode`、`_atomic_write`、`json.dumps` |
| `_inside_repository` — `_inside_repository(repository, candidate, field)` | function / [1028](../../../../contracts/tools/promote_regenerated_evidence.py#L1028) | `<dynamic>.resolve`、`ValueError`、`candidate.is_absolute`、`candidate.resolve`、`resolved.is_relative_to` |
| `_output_path` — `_output_path(repository, candidate, apply)` | function / [1039](../../../../contracts/tools/promote_regenerated_evidence.py#L1039) | `<dynamic>.as_posix`、`<dynamic>.resolve`、`ValueError`、`_inside_repository`、`allowed.relative_to`、`output.is_relative_to` |
| `parse_args` — `parse_args(argv)` | function / [1055](../../../../contracts/tools/promote_regenerated_evidence.py#L1055) | `Path`、`Path.cwd`、`argparse.ArgumentParser`、`parser.add_argument`、`parser.parse_args` |
| `main` — `main(argv)` | function / [1091](../../../../contracts/tools/promote_regenerated_evidence.py#L1091) | `<dynamic>.as_posix`、`_inside_repository`、`_output_path`、`apply_promotion`、`args.root.resolve`、`build_promotion_preview`、`output_path.relative_to`、`parse_args`、`print`、`write_promotion` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`PurePosixPath`、`SystemExit`、`frozenset`、`main`、`re.compile`

## `contracts/tools/verify_phase_a_backup.py`

[打开源文件](../../../../contracts/tools/verify_phase_a_backup.py) · 371 行 · SHA-256 `ab0caf63ccb5731c9944a1903319d65276c5a97763a681bca7ea751f816256ab`

> Reverify an explicitly supplied Phase A external workspace backup.

导入模块：`__future__`、`argparse`、`datetime`、`hashlib`、`json`、`os`、`pathlib`、`re`、`sys`、`tempfile`、`typing`

| 符号（参数名） | 类型 / 行 | 直接调用表达式（静态） |
| --- | --- | --- |
| `_load_json` — `_load_json(path)` | function / [34](../../../../contracts/tools/verify_phase_a_backup.py#L34) | `ValueError`、`isinstance`、`json.loads`、`path.read_text` |
| `_integer` — `_integer(document, key, label)` | function / [41](../../../../contracts/tools/verify_phase_a_backup.py#L41) | `ValueError`、`int` |
| `_safe_member` — `_safe_member(root, relative_text)` | function / [48](../../../../contracts/tools/verify_phase_a_backup.py#L48) | `<dynamic>.resolve`、`Path`、`PurePosixPath`、`ValueError`、`candidate.is_relative_to`、`re.match`、`relative.is_absolute` |
| `_sha256` — `_sha256(path)` | function / [65](../../../../contracts/tools/verify_phase_a_backup.py#L65) | `digest.hexdigest`、`digest.update`、`hashlib.sha256`、`iter`、`path.open`、`stream.read` |
| `_normalized_records` — `_normalized_records(manifest)` | function / [73](../../../../contracts/tools/verify_phase_a_backup.py#L73) | `<dynamic>.lower`、`<dynamic>.resolve`、`Path.cwd`、`SHA256_PATTERN.fullmatch`、`ValueError`、`_safe_member`、`int`、`isinstance`、`manifest.get`、`raw_record.get`、`records.append`、`seen_paths.add`、`set`、`sorted`、`str` |
| `_assert_external_backup` — `_assert_external_backup(repository, backup)` | function / [104](../../../../contracts/tools/verify_phase_a_backup.py#L104) | `ValueError`、`backup.is_relative_to` |
| `_verify_required_layout` — `_verify_required_layout(backup)` | function / [109](../../../../contracts/tools/verify_phase_a_backup.py#L109) | `<dynamic>.is_dir`、`<dynamic>.is_file`、`FileNotFoundError` |
| `_contained_directory` — `_contained_directory(backup, name)` | function / [120](../../../../contracts/tools/verify_phase_a_backup.py#L120) | `<dynamic>.resolve`、`ValueError`、`directory.is_relative_to` |
| `_verify_checksum_ledger` — `_verify_checksum_ledger(backup, records)` | function / [127](../../../../contracts/tools/verify_phase_a_backup.py#L127) | `<dynamic>.read_text`、`<dynamic>.splitlines`、`ValueError`、`len` |
| `_workspace_files` — `_workspace_files(workspace)` | function / [142](../../../../contracts/tools/verify_phase_a_backup.py#L142) | `<dynamic>.as_posix`、`ValueError`、`path.is_file`、`path.resolve`、`resolved.is_relative_to`、`resolved.relative_to`、`workspace.rglob` |
| `_verify_workspace` — `_verify_workspace(workspace, records)` | function / [155](../../../../contracts/tools/verify_phase_a_backup.py#L155) | `ValueError`、`_sha256`、`_workspace_files`、`path.stat`、`set`、`sorted` |
| `_verify_restore_samples` — `_verify_restore_samples(restore_root, verification, records)` | function / [178](../../../../contracts/tools/verify_phase_a_backup.py#L178) | `FileNotFoundError`、`ValueError`、`_safe_member`、`_sha256`、`isinstance`、`len`、`record_map.get`、`restored.is_file`、`restored.stat`、`str`、`verification.get` |
| `verify_phase_a_backup` — `verify_phase_a_backup(repository, backup_root, checked_utc)` | function / [205](../../../../contracts/tools/verify_phase_a_backup.py#L205) | `<dynamic>.exists`、`<dynamic>.isoformat`、`FileNotFoundError`、`ValueError`、`_assert_external_backup`、`_contained_directory`、`_integer`、`_load_json`、`_normalized_records`、`_sha256`、`_verify_checksum_ledger`、`_verify_required_layout`、`_verify_restore_samples`、`_verify_workspace`、`backup.is_dir`、`backup_root.resolve`、`datetime.now`、`len`、`manifest.get`、`repository.resolve`、`str`、`sum`、`verification.get` |
| `write_recheck` — `write_recheck(path, recheck)` | function / [283](../../../../contracts/tools/verify_phase_a_backup.py#L283) | `<dynamic>.encode`、`Path`、`json.dumps`、`path.parent.mkdir`、`tempfile.NamedTemporaryFile`、`temporary.write`、`temporary_path.exists`、`temporary_path.replace`、`temporary_path.unlink` |
| `_output_path` — `_output_path(repository, candidate)` | function / [305](../../../../contracts/tools/verify_phase_a_backup.py#L305) | `<dynamic>.resolve`、`ValueError`、`candidate.is_absolute`、`candidate.resolve`、`output.is_relative_to` |
| `parse_args` — `parse_args(argv)` | function / [322](../../../../contracts/tools/verify_phase_a_backup.py#L322) | `Path`、`Path.cwd`、`argparse.ArgumentParser`、`os.environ.get`、`parser.add_argument`、`parser.parse_args` |
| `main` — `main(argv)` | function / [344](../../../../contracts/tools/verify_phase_a_backup.py#L344) | `<dynamic>.as_posix`、`ValueError`、`_output_path`、`args.root.resolve`、`output.relative_to`、`parse_args`、`print`、`verify_phase_a_backup`、`write_recheck` |

模块级语法调用（含条件块和 `__main__`，**不等于导入时一定执行**）：`SystemExit`、`main`、`re.compile`
