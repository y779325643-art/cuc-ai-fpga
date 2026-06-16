"""Train a LoRA/QLoRA adapter for chat fine-tuning."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)
    if not isinstance(config, dict):
        raise ValueError(f"Training config must be a mapping: {path}")
    return config


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a LoRA/QLoRA adapter.")
    parser.add_argument("--config", default="LLM/configs/train_lora.yaml", type=Path)
    args = parser.parse_args()
    config = load_config(args.config)

    from datasets import load_dataset
    from peft import LoraConfig
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
    from trl import SFTTrainer

    model_name = config["model_name_or_path"]
    train_file = config["train_file"]
    output_dir = config["output_dir"]

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quantization_config = None
    if config.get("use_qlora", True):
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        quantization_config=quantization_config,
        trust_remote_code=True,
    )

    dataset = load_dataset("json", data_files=train_file, split="train")

    def format_example(example: dict[str, Any]) -> str:
        return tokenizer.apply_chat_template(example["messages"], tokenize=False, add_generation_prompt=False)

    peft_config = LoraConfig(
        r=int(config.get("lora_r", 16)),
        lora_alpha=int(config.get("lora_alpha", 32)),
        lora_dropout=float(config.get("lora_dropout", 0.05)),
        target_modules=list(config.get("lora_target_modules", [])),
        bias="none",
        task_type="CAUSAL_LM",
    )

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=float(config.get("num_train_epochs", 3)),
        max_steps=int(config.get("max_steps", -1)),
        per_device_train_batch_size=int(config.get("per_device_train_batch_size", 1)),
        gradient_accumulation_steps=int(config.get("gradient_accumulation_steps", 16)),
        learning_rate=float(config.get("learning_rate", 2e-4)),
        warmup_ratio=float(config.get("warmup_ratio", 0.03)),
        logging_steps=int(config.get("logging_steps", 10)),
        save_steps=int(config.get("save_steps", 200)),
        bf16=bool(config.get("bf16", True)),
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        peft_config=peft_config,
        formatting_func=format_example,
        max_seq_length=int(config.get("max_seq_length", 2048)),
        args=training_args,
    )
    trainer.train()
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)


if __name__ == "__main__":
    main()
