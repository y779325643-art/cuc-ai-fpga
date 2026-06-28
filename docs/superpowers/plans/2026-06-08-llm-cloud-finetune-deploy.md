# LLM Cloud Fine-Tune Deploy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Status (added 2026-06-27):** Delivered. The `LLM/` workspace, serving scripts, and
> LoRA training infrastructure are in place. **Post-delivery context:** this plan predates
> the Actor/Critic model-stack definition in the reframe spec. The infrastructure here
> supports Actor training tasks (`REQ2HIS`, `HIS2PROJECT`, `LOG2DIAG`, `FAILURE2PATCH`)
> and Critic training tasks (`PROJECT2RISK`, `PROJECT2LEVEL`, `PROJECT2QOR`). Model size
> is intentionally not fixed here — see the reframe spec "Method (the model)" section.
> Preferred serving path is Qwen2.5-Coder-7B-Instruct via vLLM (see `LLM/README.md`).

**Goal:** Build a GitHub-ready `LLM/` workspace for cloud-server LoRA/QLoRA fine-tuning and vLLM deployment.

**Architecture:** The repository stores reproducible code, configs, scripts, and documentation only. Cloud servers clone the repo, install dependencies, prepare JSONL data, train LoRA adapters with Transformers/PEFT/TRL, optionally merge adapters, and serve the result with vLLM's OpenAI-compatible API.

**Tech Stack:** Python, PyTorch, Transformers, Datasets, PEFT, TRL, Accelerate, BitsAndBytes, vLLM, shell scripts.

---

### Task 1: Dataset Preparation

**Files:**
- Create: `LLM/tests/test_prepare_dataset.py`
- Create: `LLM/src/prepare_dataset.py`

- [x] **Step 1: Write failing tests** for JSONL validation and conversion to chat `messages`.
- [x] **Step 2: Run tests and verify failure** because `prepare_dataset` is missing.
- [x] **Step 3: Implement dataset preparation** with strict errors for missing fields and invalid JSON.
- [x] **Step 4: Run tests and verify pass.**

### Task 2: Training and Serving Scaffolding

**Files:**
- Create: `LLM/requirements.txt`
- Create: `LLM/configs/train_lora.yaml`
- Create: `LLM/configs/serve_vllm.env.example`
- Create: `LLM/scripts/setup_server.sh`
- Create: `LLM/scripts/train_lora.sh`
- Create: `LLM/scripts/merge_lora.sh`
- Create: `LLM/scripts/serve_vllm.sh`
- Create: `LLM/src/train_lora.py`
- Create: `LLM/src/merge_lora.py`

- [x] **Step 1: Add dependency list** for cloud setup.
- [x] **Step 2: Add editable config templates** for LoRA training and vLLM serving.
- [x] **Step 3: Add scripts** that run from a cloned cloud server checkout.
- [x] **Step 4: Add training and merge entrypoints** with clear defaults and explicit paths.

### Task 3: Documentation and Verification

**Files:**
- Modify: `LLM/README.md`
- Modify: `README.md`
- Modify: `.gitignore`

- [x] **Step 1: Document cloud workflow** from clone to train to serve.
- [x] **Step 2: Ensure model weights, datasets, adapters, and local env files are ignored.**
- [x] **Step 3: Run tests and inspect Git status.**
