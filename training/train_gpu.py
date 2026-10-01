"""
GPU Fine-Tuning Script for Hitasha AI Assistant.
Optimized for NVIDIA GeForce RTX 5050 Laptop GPU (8GB VRAM) using 4-bit QLoRA.
Trains the model on training/hitasha_dataset.jsonl to speak fluent Indian English
and answer any question in simple, easy, short, and understandable format.
"""

import os
import sys
import argparse

def check_dependencies():
    missing = []
    try:
        import torch
    except ImportError:
        missing.append("torch")

    try:
        import transformers
    except ImportError:
        missing.append("transformers")

    try:
        import peft
    except ImportError:
        missing.append("peft")

    try:
        import datasets
    except ImportError:
        missing.append("datasets")

    try:
        import trl
    except ImportError:
        missing.append("trl")

    if missing:
        print("\n" + "=" * 60)
        print("[!] MISSING TRAINING DEPENDENCIES")
        print("=" * 60)
        print("To run GPU fine-tuning on your NVIDIA RTX 5050, install the training stack:")
        print("\n  pip install torch --index-url https://download.pytorch.org/whl/cu124")
        print("  pip install transformers datasets peft accelerate trl bitsandbytes\n")
        print("Or run the automated installer: training/install_gpu_deps.bat")
        print("=" * 60 + "\n")
        return False
    return True


def run_training(base_model_id: str = "Qwen/Qwen2.5-3B-Instruct", epochs: int = 3, batch_size: int = 2):
    if not check_dependencies():
        sys.exit(1)

    import torch
    from datasets import load_dataset
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer

    print("\n" + "=" * 65)
    print("  HITASHA GPU FINE-TUNING PIPELINE (RTX 5050 8GB VRAM)")
    print("=" * 65)

    if not torch.cuda.is_available():
        print("[!] ERROR: CUDA is not available. Please ensure NVIDIA GPU drivers are installed.")
        sys.exit(1)

    gpu_name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    print(f"[*] Detected GPU: {gpu_name} ({vram_gb:.1f} GB VRAM)")
    print(f"[*] Base Model:   {base_model_id}")
    print(f"[*] Optimization: 4-bit QLoRA (NF4 + Double Quant + Paged AdamW)")
    print("=" * 65 + "\n")

    dataset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hitasha_dataset.jsonl")
    if not os.path.exists(dataset_path):
        print(f"[!] Dataset not found at {dataset_path}. Compiling now...")
        from create_dataset import main as build_dataset
        build_dataset()

    print(f"[*] Loading dataset from {dataset_path}...")
    dataset = load_dataset("json", data_files=dataset_path, split="train")
    print(f"[*] Total training examples: {len(dataset)}")

    # 1. 4-bit Quantization Config (Fits 3B model in ~4.5GB VRAM!)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True
    )

    print("[*] Loading base model weights...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    model = prepare_model_for_kbit_training(model)

    # 2. LoRA Adapter Configuration
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # 3. Training Arguments tailored for 8GB VRAM RTX 5050
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hitasha_lora_adapter")
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=10,
        save_strategy="epoch",
        optim="paged_adamw_8bit",
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        report_to="none"
    )

    # 4. SFT Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=lora_config,
        dataset_text_field="messages",
        max_seq_length=512,
        tokenizer=tokenizer,
        args=training_args
    )

    print("\n[*] Starting GPU Fine-Tuning on RTX 5050...")
    trainer.train()

    print("\n[*] Saving fine-tuned LoRA adapter...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"\n[+] SUCCESS: Hitasha fine-tuned adapter saved to: {output_dir}")
    print("[+] Model is now fully fine-tuned on your GPU!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune Hitasha AI Model on RTX 5050 GPU")
    parser.add_argument("--base_model", type=str, default="Qwen/Qwen2.5-3B-Instruct", help="HuggingFace model ID")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=2, help="Batch size per device")
    args = parser.parse_args()

    run_training(base_model_id=args.base_model, epochs=args.epochs, batch_size=args.batch_size)
