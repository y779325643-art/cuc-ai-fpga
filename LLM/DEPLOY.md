# Windows Cloud Deployment Guide for Qwen/Gemma on WSL

This guide describes how to deploy and smoke-train local LLMs on a Windows
cloud server with an RTX 4090 24GB GPU. The deployment uses
**Windows + WSL2/Ubuntu + vLLM + Transformers/QLoRA**.

Current policy:

- WSL/Ubuntu stays in its normal Windows-managed location. On this cloud
  machine, WSL cannot be installed or imported directly onto `E:`.
- Treat WSL itself as rebuildable.
- Store the project checkout on `E:` at
  `/mnt/e/Aowen/repos/cuc-ai-fpga`.
- Store the Python virtual environment on `E:` at
  `/mnt/e/Aowen/venvs/cuc-ai-fpga`.
- Keep durable assets on `E:\Aowen`: project code, model files, datasets,
  LoRA outputs, merged models, caches, logs, and optional WSL export backups.
- Do not use 4-bit quantization for inference; the Qwen vLLM service uses
  float16.
- The smoke fine-tuning flow uses QLoRA to reduce training memory.
- Hugging Face access from WSL may fail; the current working download route is ModelScope.
- The verified serving model is `Qwen/Qwen2.5-Coder-7B-Instruct`.
- Gemma 4 12B currently has a Gemma4 Unified compatibility failure in vLLM EngineCore; use Transformers for Gemma testing and Qwen2.5-Coder for the stable vLLM service.

## 1. Target Layout

Create durable folders on the `E:` drive from Windows PowerShell:

```powershell
mkdir E:\Aowen
mkdir E:\Aowen\repos
mkdir E:\Aowen\models
mkdir E:\Aowen\datasets
mkdir E:\Aowen\runs
mkdir E:\Aowen\merged
mkdir E:\Aowen\venvs
mkdir E:\Aowen\hf-cache
mkdir E:\Aowen\modelscope-cache
mkdir E:\Aowen\backups
mkdir E:\Aowen\logs
```

Inside Ubuntu/WSL, these paths appear as:

```text
/mnt/e/Aowen/repos
/mnt/e/Aowen/models
/mnt/e/Aowen/datasets
/mnt/e/Aowen/runs
/mnt/e/Aowen/merged
/mnt/e/Aowen/venvs
/mnt/e/Aowen/hf-cache
/mnt/e/Aowen/modelscope-cache
/mnt/e/Aowen/backups
/mnt/e/Aowen/logs
```

Use `E:\Aowen` for files that must survive cleanup. Do not rely on `C:` or
`D:` for model weights, real datasets, long training runs, or final adapters.

The project checkout should live on `E:`:

```text
/mnt/e/Aowen/repos/cuc-ai-fpga
```

This keeps code, configs, and scripts alongside the persistent venv, models,
datasets, and outputs. If `C:` is cleaned, reinstall or enter WSL, then
continue from this E-drive checkout.

Because WSL itself cannot be placed on `E:` in the current environment, protect
it by keeping a WSL export backup on `E:` and keeping all experiment outputs on
`E:`.

## 2. Windows and WSL2 Setup

Open **Administrator PowerShell**:

```powershell
wsl --install -d Ubuntu-22.04
wsl --set-default-version 2
wsl --update
wsl --shutdown
```

If `wsl --install` cannot download the distribution list, use manual installation:

```powershell
mkdir C:\WSL
cd C:\WSL
curl.exe -L -o Ubuntu-22.04.appx https://aka.ms/wslubuntu2204
Add-AppxPackage .\Ubuntu-22.04.appx
```

Then start Ubuntu from the Start menu, or from PowerShell:

```powershell
wsl -d Ubuntu-22.04
```

Do not install a Linux NVIDIA driver inside WSL2. CUDA is provided by the Windows NVIDIA driver.

## 3. Back Up WSL to E Drive

Do this periodically if `C:` can be cleaned. This does not move WSL to `E:`;
it creates a recoverable snapshot.

First, check the distribution name in **PowerShell**:

```powershell
wsl -l -v
```

Assume the name is `Ubuntu-22.04`. If your output shows a different name, replace `Ubuntu-22.04` in the commands below.

Create a backup folder:

```powershell
mkdir E:\Aowen\backups
```

Shut down WSL:

```powershell
wsl --shutdown
```

Export the current Ubuntu distribution:

```powershell
wsl --export Ubuntu-22.04 E:\Aowen\backups\ubuntu-22.04-latest.tar
```

Confirm the backup exists:

```powershell
dir E:\Aowen\backups\ubuntu-22.04-latest.tar
```

Start Ubuntu again:

```powershell
wsl -d Ubuntu-22.04
```

Important notes:

- Do not run `wsl --unregister` unless you intentionally want to delete the
  current Ubuntu distribution.
- The export file can be large. Keep at least one known-good backup on `E:`.
- Even with WSL backups, put model files, datasets, and adapter outputs under
  `E:\Aowen` because they are the most expensive files to recreate.

## 4. Verify GPU in Ubuntu

In Ubuntu:

```bash
nvidia-smi
```

If this fails:

- Install or update the NVIDIA Windows driver.
- Restart Windows.
- Run `wsl --shutdown` in PowerShell.
- Enter Ubuntu again.

Then install base tools:

```bash
sudo apt update
sudo apt install -y git python3-venv python3-pip curl
```

## 5. Clone or Update the Project on E Drive

Use the persistent E-drive path:

```bash
mkdir -p /mnt/e/Aowen/repos
cd /mnt/e/Aowen/repos
git clone https://github.com/y779325643-art/cuc-ai-fpga.git
cd cuc-ai-fpga
```

If the repository already exists, update it instead:

```bash
cd /mnt/e/Aowen/repos/cuc-ai-fpga
git pull origin main
```

If Git asks for GitHub credentials:

- Username: `y779325643-art`
- Password: a GitHub Personal Access Token, not the GitHub account password.

For public read-only clone, credentials should not normally be needed.

## 6. Install Python Environment

From the project root:

```bash
bash LLM/scripts/setup_server.sh
source /mnt/e/Aowen/venvs/cuc-ai-fpga/bin/activate
```

This creates:

```text
/mnt/e/Aowen/venvs/cuc-ai-fpga
```

The setup script creates the venv on `E:` by default. Override the location
only if needed:

```bash
LLM_VENV_PATH=/custom/path bash LLM/scripts/setup_server.sh
source /custom/path/bin/activate
```

## 7. Persist Model and Package Caches on E Drive

Use this before downloading models or training. In Ubuntu:

```bash
mkdir -p /mnt/e/Aowen/hf-cache

cat >> ~/.bashrc <<'EOF'
export HF_HOME=/mnt/e/Aowen/hf-cache
export HF_HUB_CACHE=/mnt/e/Aowen/hf-cache/hub
export TRANSFORMERS_CACHE=/mnt/e/Aowen/hf-cache
EOF

source ~/.bashrc
```

This keeps Hugging Face cache files on the persistent E drive.

For ModelScope, also add:

```bash
cat >> ~/.bashrc <<'EOF'
export MODELSCOPE_CACHE=/mnt/e/Aowen/modelscope-cache
EOF

mkdir -p /mnt/e/Aowen/modelscope-cache
source ~/.bashrc
```

## 8. Hugging Face Login

This section is optional for the current deployment, because the model has been downloaded through ModelScope. Keep it only for future Hugging Face downloads.

Open this page in a browser:

```text
https://huggingface.co/settings/tokens
```

Create a **Read** token. Do not use a Write token.

In Ubuntu:

```bash
hf auth login
```

Paste the `hf_...` token. If it asks:

```text
Add token as git credential? (Y/n)
```

Answer:

```text
Y
```

Verify:

```bash
hf auth whoami
```

If PowerShell or the terminal cannot paste, create a temporary file on Windows:

```text
E:\Aowen\hf_token.txt
```

Put the token in that file, then run in Ubuntu:

```bash
TOKEN=$(cat /mnt/e/Aowen/hf_token.txt)
hf auth login --token "$TOKEN"
hf auth whoami
rm /mnt/e/Aowen/hf_token.txt
```

Never put the token inside the Git repository.

## 9. If WSL Cannot Access Hugging Face

If Windows browser can open Hugging Face but Ubuntu reports errors such as:

```text
Temporary failure in name resolution
Could not resolve host: huggingface.co
Network is unreachable
```

Check Ubuntu networking:

```bash
cat /etc/resolv.conf
ip route
ping -c 3 1.1.1.1
curl -I https://huggingface.co
```

If `/etc/resolv.conf` is missing or DNS fails, recreate it:

```bash
sudo tee /etc/wsl.conf > /dev/null <<'EOF'
[network]
generateResolvConf = false
EOF

sudo tee /etc/resolv.conf > /dev/null <<'EOF'
nameserver 8.8.8.8
nameserver 1.1.1.1
EOF
```

Then in Windows PowerShell:

```powershell
wsl --shutdown
wsl -d Ubuntu-22.04
```

In the current setup, Hugging Face access from WSL failed, so use ModelScope download or an already-downloaded local model path.

## 10. Model Download Options

### Option A: Download with ModelScope

This is the current working route. Install ModelScope in the active environment:

```bash
cd /mnt/e/Aowen/repos/cuc-ai-fpga
source /mnt/e/Aowen/venvs/cuc-ai-fpga/bin/activate
python -m pip install -U modelscope
```

Download to the persistent E drive:

```bash
mkdir -p /mnt/e/Aowen/models
modelscope download --model google/gemma-4-12B-it --local_dir /mnt/e/Aowen/models/gemma-4-12B-it
```

Expected model path for vLLM:

```text
/mnt/e/Aowen/models/gemma-4-12B-it
```

The folder should include files such as:

```text
config.json
tokenizer.json
model.safetensors
```

or sharded `.safetensors` files.

ModelScope's official download command supports `--model` and `--local_dir`, and its default cache is under `~/.cache/modelscope/hub`. We explicitly use `--local_dir` so the final model folder is easy for vLLM to load.

### Option B: Download from Hugging Face

Use this only if WSL can access Hugging Face reliably:

```bash
cd /mnt/e/Aowen
hf download google/gemma-4-12B-it --local-dir models/gemma-4-12B-it
```

### Option C: Download Elsewhere and Copy to E Drive

Use this if neither WSL Hugging Face access nor ModelScope download works.

On a machine that can access Hugging Face:

```bash
pip install -U huggingface_hub
hf auth login
hf download google/gemma-4-12B-it --local-dir gemma-4-12B-it
```

Copy the full folder to the Windows cloud server:

```text
E:\Aowen\models\gemma-4-12B-it
```

Then verify in Ubuntu:

```bash
ls /mnt/e/Aowen/models/gemma-4-12B-it
```

Do not place model files inside the Git repository.

## 11. Configure vLLM

From the project root:

```bash
cd /mnt/e/Aowen/repos/cuc-ai-fpga
cp LLM/configs/serve_vllm.env.example LLM/configs/serve_vllm.env
```

Edit:

```bash
nano LLM/configs/serve_vllm.env
```

Set `MODEL_PATH` to the local ModelScope-downloaded folder:

```bash
MODEL_PATH=/mnt/c/Users/Administrator/models/gemma-4-12B-it
HOST=127.0.0.1
PORT=8000
SERVED_MODEL_NAME=cuc-ai-fpga
GPU_MEMORY_UTILIZATION=0.85
MAX_MODEL_LEN=1024
MAX_NUM_SEQS=1
DTYPE=float16
```

The Gemma script adds `--trust-remote-code`, `--enforce-eager`, and
`--language-model-only` directly. It intentionally does not pass a
multimodal-limit JSON argument.

## 12. Start the API Server

From the project root:

### Gemma 4 vLLM Compatibility Test

```bash
source /mnt/e/Aowen/venvs/cuc-ai-fpga/bin/activate
bash LLM/scripts/serve_vllm.sh
```

The script uses:

```text
/mnt/c/Users/Administrator/models/gemma-4-12B-it
```

It also uses `--language-model-only`, `--trust-remote-code`, and
`--enforce-eager`. It does not pass `--limit-mm-per-prompt`, avoiding the
previous malformed JSON argument.

The known vLLM failure is:

```text
RuntimeError: mat1 and mat2 shapes cannot be multiplied
(1024x4096 and 8192x3840)
```

This occurs in Gemma4 Unified attention `o_proj`. Loading 22.56 GiB of model
weights succeeds before this failure, so the model path and weight files are
probably valid.

### Gemma 4 Transformers Test

```bash
source /mnt/e/Aowen/venvs/cuc-ai-fpga/bin/activate
python test_gemma_transformers.py
```

This route uses the tokenizer chat template instead of a raw prompt.

### Recommended Qwen vLLM Service

This deployment has been verified successfully on an RTX 4090 24GB. The
recommended persistent Windows model directory is:

```text
E:\Aowen\models\Qwen2.5-Coder-7B-Instruct
```

The corresponding WSL path is:

```text
/mnt/e/Aowen/models/Qwen2.5-Coder-7B-Instruct
```

If the model must be downloaded again, use ModelScope:

```bash
mkdir -p /mnt/e/Aowen/models
modelscope download \
  --model Qwen/Qwen2.5-Coder-7B-Instruct \
  --local_dir /mnt/e/Aowen/models/Qwen2.5-Coder-7B-Instruct
```

Confirm that the snapshot is complete:

```bash
test -f /mnt/e/Aowen/models/Qwen2.5-Coder-7B-Instruct/config.json
```

Start vLLM:

```bash
cd /mnt/e/Aowen/repos/cuc-ai-fpga
source /mnt/e/Aowen/venvs/cuc-ai-fpga/bin/activate
sed -i 's/\r$//' LLM/scripts/*.sh
chmod +x LLM/scripts/*.sh
bash LLM/scripts/serve_qwen_vllm.sh
```

The Qwen service defaults to this local path:

```text
/mnt/e/Aowen/models/Qwen2.5-Coder-7B-Instruct
```

It is the recommended path for completing the RTL/Verilog API workflow on an
RTX 4090 24GB.

If the model is stored elsewhere, pass its complete local snapshot path:

```bash
QWEN_MODEL_PATH=/path/to/Qwen2.5-Coder-7B-Instruct \
  bash LLM/scripts/serve_qwen_vllm.sh
```

The script sets `VLLM_USE_FLASHINFER_SAMPLER=0` by default. This avoids
FlashInfer sampler JIT compilation on WSL installations that have GPU runtime
support but do not have the CUDA Toolkit, `/usr/local/cuda`, or `nvcc`.
Attention and model execution still use the NVIDIA GPU; only the sampling
implementation falls back to PyTorch.

If the model is still in the old C-drive location, use this temporarily:

```bash
QWEN_MODEL_PATH=/mnt/c/Users/Administrator/models/Qwen2.5-Coder-7B-Instruct \
  bash LLM/scripts/serve_qwen_vllm.sh
```

The API listens on:

```text
http://127.0.0.1:8000/v1
```

`HOST=127.0.0.1` is intentional. It avoids exposing an unauthenticated model API to the public internet.

## 13. Test the API

Open a second Ubuntu terminal:

```bash
cd /mnt/e/Aowen/repos/cuc-ai-fpga
source /mnt/e/Aowen/venvs/cuc-ai-fpga/bin/activate
BASE_URL=http://127.0.0.1:8000/v1 bash LLM/scripts/test_api.sh
```

You can also test with curl:

```bash
curl http://127.0.0.1:8000/v1/models
```

From Windows PowerShell, prefer `Invoke-RestMethod`. It avoids the JSON quoting
error that can occur when passing escaped JSON to `curl.exe`:

```powershell
$body = @{
    model = "cuc-ai-fpga"
    messages = @(
        @{
            role = "user"
            content = "请写一个可综合的 Verilog 8位同步计数器，包含 clk、rst_n、en、count 端口，只输出代码。"
        }
    )
    temperature = 0.2
    max_tokens = 512
} | ConvertTo-Json -Depth 5

$response = Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/v1/chat/completions" `
  -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body ([Text.Encoding]::UTF8.GetBytes($body))

$response.choices[0].message.content
```

## 14. Access from Your Local Computer

Prefer SSH port forwarding:

```bash
ssh -L 8000:127.0.0.1:8000 <windows-user>@<server-ip>
```

Then access locally:

```text
http://127.0.0.1:8000/v1
```

Avoid opening port `8000` directly to the public internet unless you add authentication and firewall rules.

## 15. Troubleshooting

### CUDA Out of Memory

Edit `LLM/configs/serve_vllm.env`:

```bash
MAX_MODEL_LEN=1024
GPU_MEMORY_UTILIZATION=0.80
```

Restart:

```bash
bash LLM/scripts/serve_vllm.sh
```

If the same matrix-shape error appears, it is the known Gemma4 Unified
compatibility issue rather than CUDA OOM. Use the Transformers test or switch
the vLLM service to Qwen2.5-Coder.

### WSL DNS Failure

Symptoms:

```text
Temporary failure in name resolution
Could not resolve host
```

Use the DNS repair steps in Section 9.

### Hugging Face Permission Error

Symptoms:

```text
401 Unauthorized
403 Forbidden
Repository access denied
```

Fix:

- Accept the `google/gemma-4-12B-it` terms on Hugging Face.
- Create a Read token.
- Run `hf auth login` again.

### Model Path Error

If vLLM still tries to download from Hugging Face when you intended offline mode, check:

```bash
ls /mnt/e/Aowen/models/Qwen2.5-Coder-7B-Instruct
```

Start Qwen with a complete local path:

```bash
QWEN_MODEL_PATH=/mnt/e/Aowen/models/Qwen2.5-Coder-7B-Instruct \
  bash LLM/scripts/serve_qwen_vllm.sh
```

Do not pass only the online repository ID when Hugging Face traffic is
unavailable:

```text
Qwen/Qwen2.5-Coder-7B-Instruct
```

### Shell Script CRLF Error

Symptom:

```text
set: pipefail: invalid option name
```

Repair the current checkout and disable automatic CRLF conversion:

```bash
git config core.autocrlf false
sed -i 's/\r$//' LLM/scripts/*.sh
chmod +x LLM/scripts/*.sh
```

The repository's `.gitattributes` forces shell scripts to use LF.

### FlashInfer Cannot Find nvcc

Symptom:

```text
RuntimeError: Could not find nvcc and default cuda_home='/usr/local/cuda' doesn't exist
```

The Qwen startup script sets this automatically:

```bash
export VLLM_USE_FLASHINFER_SAMPLER=0
```

Installing the full CUDA Toolkit is not required for this deployment. The
model and attention kernels continue running on the GPU.

### Git Pull Blocked by Local Changes

Symptom:

```text
Your local changes would be overwritten by merge
```

Preserve the cloud changes before pulling:

```bash
git stash push -m "cloud-local-changes"
git pull origin main
```

Review the stash later with `git stash show -p`.

## 16. Verified Deployment Result

The completed deployment used:

- Windows cloud server with Ubuntu 22.04 under WSL2.
- NVIDIA RTX 4090 24GB.
- vLLM `0.22.1`.
- Qwen2.5-Coder-7B-Instruct in float16, without 4-bit quantization.
- ModelScope for model download.
- Local model path
  `/mnt/e/Aowen/models/Qwen2.5-Coder-7B-Instruct`.
- `VLLM_USE_FLASHINFER_SAMPLER=0` because the WSL image did not contain
  `nvcc`.
- OpenAI-compatible endpoint `http://127.0.0.1:8000/v1`.

The model loaded approximately 14.29 GiB of GPU memory and successfully
generated synthesizable Verilog through `/v1/chat/completions`.

## 17. First Smoke Fine-Tuning Run

Before building a real FPGA dataset, run the tiny tracked Verilog smoke
dataset once. This verifies the full path:

```text
raw JSONL -> chat JSONL -> QLoRA training -> LoRA adapter output
```

Use the existing cloud checkout:

```bash
cd /mnt/e/Aowen/repos/cuc-ai-fpga
source /mnt/e/Aowen/venvs/cuc-ai-fpga/bin/activate
```

Generate the training file. `LLM/data/train.jsonl` is intentionally ignored by
Git because real datasets can become large:

```bash
python -m LLM.src.prepare_dataset \
  --input LLM/data/examples/smoke_verilog_raw.jsonl \
  --output LLM/data/train.jsonl
```

Run the short Qwen QLoRA job:

```bash
mkdir -p /mnt/e/Aowen/runs
bash LLM/scripts/train_lora.sh LLM/configs/train_qwen_smoke.yaml
```

The smoke config uses:

- Base model:
  `/mnt/e/Aowen/models/Qwen2.5-Coder-7B-Instruct`
- `use_qlora: true`
- `max_seq_length: 512`
- `max_steps: 10`
- LoRA rank `8`
- Output directory:
  `/mnt/e/Aowen/runs/qwen2_5_coder_7b_smoke_lora`

Expected result:

```text
/mnt/e/Aowen/runs/qwen2_5_coder_7b_smoke_lora/
```

That folder should contain adapter files such as `adapter_config.json` and
adapter weights. This smoke run is not meant to improve the model; it only
proves the training stack works.

If CUDA runs out of memory during the smoke run, reduce these fields in
`LLM/configs/train_qwen_smoke.yaml`:

```yaml
max_seq_length: 256
lora_r: 4
```

## 18. Later Real Fine-Tuning Path

Fine-tuning is not part of the first deployment. When ready:

```bash
python -m LLM.src.prepare_dataset --input LLM/data/raw.jsonl --output LLM/data/train.jsonl
bash LLM/scripts/train_lora.sh
bash LLM/scripts/merge_lora.sh
```

Then update `MODEL_PATH` to the merged model directory.

## 19. References

- ModelScope model download documentation: https://modelscope.cn/docs/models/download
- ModelScope quick start: https://modelscope.cn/docs/intro/quickstart
- Microsoft WSL installation: https://learn.microsoft.com/windows/wsl/install
- NVIDIA CUDA on WSL: https://docs.nvidia.com/cuda/wsl-user-guide/
- vLLM Gemma 4 guide: https://docs.vllm.ai/projects/recipes/en/stable/Google/Gemma4.html
