"""Merge a LoRA adapter into its base model for serving."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge a LoRA adapter into a base model.")
    parser.add_argument("--base-model", required=True, help="Base model name or local path.")
    parser.add_argument("--adapter", required=True, help="LoRA adapter directory.")
    parser.add_argument("--output", required=True, type=Path, help="Merged model output directory.")
    args = parser.parse_args()

    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        device_map="auto",
        torch_dtype="auto",
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(model, args.adapter)
    merged_model = model.merge_and_unload()

    args.output.mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(args.output, safe_serialization=True)

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    tokenizer.save_pretrained(args.output)
    print(f"Merged model saved to {args.output}")


if __name__ == "__main__":
    main()
