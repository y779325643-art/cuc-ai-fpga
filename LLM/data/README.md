# Training Data

Put cloud-server training data here after cloning the repository. Raw data and converted training files are ignored by Git.

Supported raw JSONL formats:

```jsonl
{"instruction":"Write Verilog for a counter.","input":"Use an async reset.","output":"module ... endmodule"}
{"prompt":"Explain FPGA timing closure.","completion":"Timing closure means ..."}
{"messages":[{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}
```

Convert raw data before training:

```bash
python -m LLM.src.prepare_dataset --input LLM/data/raw.jsonl --output LLM/data/train.jsonl
```

For the first pipeline test, use the tracked smoke dataset:

```bash
python -m LLM.src.prepare_dataset \
  --input LLM/data/examples/smoke_verilog_raw.jsonl \
  --output LLM/data/train.jsonl
```

Then run:

```bash
bash LLM/scripts/train_lora.sh LLM/configs/train_qwen_smoke.yaml
```
