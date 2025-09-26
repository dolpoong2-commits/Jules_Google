import argparse
import os
import json
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import logging

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Main Training Function ---
def train(args):
    """
    Main function to orchestrate the model training process.
    """
    logger.info("Starting model training process with arguments: %s", args)

    # --- 1. Load Dataset ---
    logger.info(f"Loading dataset from {args.dataset_path}")
    # Assuming a jsonl file with 'question', 'context', and 'answers' keys
    raw_dataset = load_dataset('json', data_files=args.dataset_path)

    # --- 2. Load Tokenizer ---
    logger.info(f"Loading tokenizer for model: {args.model_id}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    # Set a padding token if one isn't already set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # --- 3. Preprocess Dataset ---
    def preprocess_function(examples):
        # Simple prompt template
        inputs = [f"Question: {q}\nContext: {c}\nAnswer:" for q, c in zip(examples['question'], examples['context'])]
        # The 'answers' are expected to be a list, we take the first one.
        targets = [a[0] if isinstance(a, list) and a else "" for a in examples['answers']]

        # Tokenize inputs and targets
        model_inputs = tokenizer(inputs, max_length=args.max_seq_length, truncation=True, padding="max_length")
        labels = tokenizer(targets, max_length=args.max_seq_length, truncation=True, padding="max_length")

        # Set the labels for the trainer
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    tokenized_dataset = raw_dataset.map(preprocess_function, batched=True, remove_columns=raw_dataset['train'].column_names)
    logger.info("Dataset preprocessing complete.")

    # --- 4. Configure Model (LoRA, QLoRA, or Full) ---
    bnb_config = None
    if args.training_method in ['qlora']:
        logger.info("Setting up QLoRA with 4-bit quantization.")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

    logger.info(f"Loading base model: {args.model_id}")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        quantization_config=bnb_config,
        device_map="auto", # Automatically handle device placement
        trust_remote_code=True
    )

    # --- 5. Apply PEFT if applicable ---
    if args.training_method in ['lora', 'qlora']:
        logger.info(f"Applying {args.training_method.upper()} configuration.")
        if args.training_method == 'qlora':
            model = prepare_model_for_kbit_training(model)

        peft_config = LoraConfig(
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "v_proj"] # Common for many models, might need adjustment
        )
        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()

    # --- 6. Set up Training Arguments ---
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation,
        learning_rate=args.learning_rate,
        fp16=True, # Use mixed precision
        logging_dir=f"{args.output_dir}/logs",
        logging_steps=10,
        save_steps=50,
        evaluation_strategy="no", # No eval set in this basic script
        save_strategy="steps",
        do_train=True,
    )

    # --- 7. Initialize and run Trainer ---
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset['train'],
        tokenizer=tokenizer,
    )

    logger.info("Starting training...")
    trainer.train()
    logger.info("Training complete.")

    # --- 8. Save the final model ---
    final_save_path = os.path.join(args.output_dir, "final_model")
    trainer.save_model(final_save_path)
    logger.info(f"Model saved to {final_save_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune a language model.")

    # Model and Data Arguments
    parser.add_argument("--model_id", type=str, default="TinyLlama/Llama-2-1b-chat-hf", help="The model ID from Hugging Face.")
    parser.add_argument("--dataset_path", type=str, required=True, help="Path to the JSONL dataset file.")
    parser.add_argument("--output_dir", type=str, default="./models/finetuned_model", help="Directory to save the trained model.")
    parser.add_argument("--max_seq_length", type=int, default=512, help="Maximum sequence length.")

    # Training Method Arguments
    parser.add_argument("--training_method", type=str, default="qlora", choices=["full", "lora", "qlora"], help="Fine-tuning method.")

    # Hyperparameters
    parser.add_argument("--epochs", type=int, default=1, help="Number of training epochs.")
    parser.add_argument("--batch_size", type=int, default=1, help="Training batch size per device.")
    parser.add_argument("--gradient_accumulation", type=int, default=4, help="Gradient accumulation steps.")
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="Learning rate.")

    # LoRA/QLoRA Specific Arguments
    parser.add_argument("--lora_r", type=int, default=8, help="LoRA attention dimension (rank).")
    parser.add_argument("--lora_alpha", type=int, default=16, help="LoRA alpha parameter.")
    parser.add_argument("--lora_dropout", type=float, default=0.05, help="LoRA dropout probability.")

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    train(args)