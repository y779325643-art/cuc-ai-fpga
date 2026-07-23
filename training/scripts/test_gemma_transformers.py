"""Smoke-test Gemma 4 12B through Transformers chat generation."""

import os

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


model_path = os.environ.get("MODEL_PATH", "google/gemma-4-12B-it")

tokenizer = AutoTokenizer.from_pretrained(
    model_path,
    trust_remote_code=True,
)

model = AutoModelForCausalLM.from_pretrained(
    model_path,
    dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
    attn_implementation="eager",
)
model.eval()

messages = [
    {
        "role": "user",
        "content": "请写一个可综合的 Verilog 8位同步计数器，要求包含 clk、rst_n、en、count 端口。只输出代码。",
    }
]

prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
)

inputs = tokenizer(
    prompt,
    return_tensors="pt",
).to(model.device)

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=512,
        do_sample=False,
        repetition_penalty=1.1,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
    )

generated = outputs[0][inputs["input_ids"].shape[-1] :]
print(tokenizer.decode(generated, skip_special_tokens=True))
