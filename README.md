# HNAI-FPGA

This repository collects project materials for HNAI-FPGA, including LLM-assisted FPGA design notes, manuscripts, presentation outputs, and supporting assets.

## Directory Layout

- `LLM/` - local LLM deployment and model-integration workspace.
- `assets/images/` - project images, screenshots, and visual references.
- `docs/` - planning documents and structured project notes.
- `outputs/` - generated project deliverables, scripts, and intermediate output packages.
- `references/` - background reading and reference notes.
- `reports/manuscripts/` - manuscript drafts, reports, and Word documents.
- `reports/rendered/` - rendered PDFs and page images generated from reports or presentations.

## Git Notes

Large model weights, local runtime files, assistant state, and generated preview folders are ignored by default. Keep source code, reproducible scripts, and final documents in Git; keep downloaded model files outside the repository or under ignored `models/` directories.

## Cloud Deployment Direction

This project is prepared on a local machine and deployed on a cloud server by cloning the GitHub repository. The `LLM/` workspace defaults to `google/gemma-4-12B-it` and deploys the base model first; fine-tuning can be enabled later:

```bash
git clone https://github.com/y779325643-art/cuc-ai-fpga.git
cd cuc-ai-fpga

bash LLM/scripts/setup_server.sh
bash LLM/scripts/serve_vllm.sh
```

Model weights, raw datasets, LoRA adapters, merged models, and server-specific environment files are intentionally ignored by Git.
