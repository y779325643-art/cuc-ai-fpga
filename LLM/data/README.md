# Training Data

Put cloud-server training data here after cloning the repository. Raw data and converted training files are ignored by Git.

Supported raw JSONL formats:

```jsonl
{"instruction":"Write Verilog for a counter.","input":"Use an async reset.","output":"module ... endmodule"}
{"prompt":"Explain FPGA timing closure.","completion":"Timing closure means ..."}
{"messages":[{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}
```

`LLM.src.prepare_dataset` also accepts SR2FPGA training views exported by
`DatasetRecorder`:

- `requirement_to_his.jsonl`
- `his_to_project.jsonl`
- `requirement_to_project.jsonl`
- `requirement_to_file.jsonl`
- `failure_to_diagnosis.jsonl`
- `failure_to_patch.jsonl`
- `project_to_predicted_qor.jsonl`
- `project_to_measured_qor.jsonl`

Convert raw data before training:

```bash
python -m LLM.src.prepare_dataset --input LLM/data/raw.jsonl --output LLM/data/train.jsonl
```

For the current deterministic T0-T4 dataset sanity gate, each non-empty
canonical smoke export view converts to chat JSONL:

```bash
python -m LLM.src.prepare_dataset \
  --input datasets/sr2fpga_rtl_v1_exports/requirement_to_project.jsonl \
  --output tmp/t0_t4_requirement_to_project.chat.jsonl
```

Run a no-model dry-run before training to validate chat rows and length risk:

```bash
python -m LLM.src.training_dry_run \
  --input tmp/t0_t4_requirement_to_project.chat.jsonl \
  --max-seq-length 65536 \
  --fail-on-truncation
```

The current T0-T4 `requirement_to_project` rows exceed short smoke settings
such as 2048 estimated tokens because they contain complete project files.
Use a long-context setting or split/chunk the task before real training.
For short-context SFT, use `requirement_to_file.jsonl` and exclude
`system_his.json` rows; the canonical T0-T4 smoke has 187 non-HIS file rows and
all fit a 2048-token dry-run gate.

Build the current short-context `REQ2FILE` training file:

```bash
python -m LLM.src.prepare_dataset \
  --input datasets/sr2fpga_rtl_v1_exports/requirement_to_file.jsonl \
  --output LLM/data/t0_t4_req2file_short.chat.jsonl \
  --sample-id-prefix sample_t0_t4_deterministic_smoke_ \
  --exclude-file-path system_his.json

python -m LLM.src.training_dry_run \
  --config LLM/configs/train_qwen_req2file_short.yaml \
  --fail-on-truncation
```

Then train the short-context file-level adapter:

```bash
bash LLM/scripts/train_lora.sh LLM/configs/train_qwen_req2file_short.yaml
```

Build the matching post-training evaluation prompt set:

```bash
python -m LLM.src.req2file_eval build \
  --input datasets/sr2fpga_rtl_v1_exports/requirement_to_file.jsonl \
  --output tmp/req2file_eval/t0_t4_req2file_eval.jsonl \
  --sample-id-prefix sample_t0_t4_deterministic_smoke_ \
  --exclude-file-path system_his.json
```

After serving the trained adapter, run inference through the local
OpenAI-compatible vLLM endpoint and score the no-tool file-level signals:

```bash
python -m LLM.src.req2file_eval infer \
  --input tmp/req2file_eval/t0_t4_req2file_eval.jsonl \
  --output tmp/req2file_eval/t0_t4_req2file_predictions.jsonl \
  --base-url http://127.0.0.1:8000/v1 \
  --api-key EMPTY \
  --model Qwen2.5-Coder-7B-Instruct \
  --max-tokens 4096

python -m LLM.src.req2file_eval score \
  --input tmp/req2file_eval/t0_t4_req2file_predictions.jsonl \
  --output tmp/req2file_eval/t0_t4_req2file_score.json

python -m LLM.src.req2file_eval assemble \
  --input tmp/req2file_eval/t0_t4_req2file_predictions.jsonl \
  --output-root tmp/req2file_eval/assembled \
  --reference-dataset-root datasets/sr2fpga_rtl_v1 \
  --backfill-reference-path system_his.json

python -m LLM.src.req2file_eval verify-static \
  --project-root tmp/req2file_eval/assembled \
  --output tmp/req2file_eval/t0_t4_req2file_static_report.json

python -m LLM.src.req2file_eval verify-tools \
  --project-root tmp/req2file_eval/assembled \
  --output tmp/req2file_eval/t0_t4_req2file_tools_report.json

python -m LLM.src.req2file_eval verify-synth \
  --project-root tmp/req2file_eval/assembled \
  --output tmp/req2file_eval/t0_t4_req2file_synth_report.json
```

`system_his.json` is backfilled from the reference dataset only for static
project-consistency checking. It is not part of the short-context `REQ2FILE`
training target. `verify-tools` runs Verilator lint plus Icarus compile/run, and
`verify-synth` runs Yosys synthesis and records parsed QoR cell counts when
those tools are installed.

For the first pipeline test, use the tracked smoke dataset:

```bash
python -m LLM.src.prepare_dataset \
  --input LLM/data/examples/smoke_verilog_raw.jsonl \
  --output LLM/data/train.jsonl
```

Then run:

```bash
mkdir -p /mnt/e/Aowen/runs
bash LLM/scripts/train_lora.sh LLM/configs/train_qwen_smoke.yaml
```
