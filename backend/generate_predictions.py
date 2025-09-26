import argparse
import os
import json
import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import logging

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate(args):
    """
    Generates predictions from a fine-tuned model on a given dataset.
    """
    logger.info("Starting prediction generation with arguments: %s", args)

    # --- 1. Load Tokenizer and Model ---
    logger.info(f"Loading tokenizer for model: {args.base_model_id}")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    logger.info(f"Loading base model: {args.base_model_id}")
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model_id,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )

    # --- 2. Load PEFT Adapters if specified ---
    if args.adapter_path:
        logger.info(f"Loading PEFT adapters from: {args.adapter_path}")
        try:
            model = PeftModel.from_pretrained(model, args.adapter_path)
            model = model.merge_and_unload() # Merge for faster inference
            logger.info("Successfully merged PEFT adapters.")
        except Exception as e:
            logger.error(f"Failed to load PEFT adapters from {args.adapter_path}. Error: {e}")
            return

    # --- 3. Load and Preprocess Dataset ---
    logger.info(f"Loading dataset from: {args.dataset_path}")
    dataset = load_dataset('json', data_files=args.dataset_path, split='train')

    def create_prompt(example):
        # Using the same prompt structure as in training
        return f"Question: {example['question']}\nContext: {example['context']}\nAnswer:"

    # --- 4. Generate Predictions ---
    predictions = []
    output_file = os.path.join(args.output_dir, "qa_pred.jsonl")

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for i, example in enumerate(dataset):
            prompt = create_prompt(example)
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

            # Generate output
            generate_ids = model.generate(**inputs, max_new_tokens=50)

            # Decode the generated tokens, skipping the prompt
            full_output = tokenizer.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
            prediction_text = full_output[len(prompt):].strip()

            # Create the prediction record
            prediction_record = {
                "id": example.get("id", f"pred_{i}"),
                "question": example["question"],
                "context": example["context"],
                "prediction": prediction_text,
                "gold_answers": example.get("answers", []) # Keep gold answers for easy comparison
            }

            f.write(json.dumps(prediction_record) + "\n")
            if (i + 1) % 10 == 0:
                logger.info(f"Generated {i + 1}/{len(dataset)} predictions...")

    logger.info(f"Prediction generation complete. Results saved to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate predictions from a fine-tuned model.")

    # Model and Data Arguments
    parser.add_argument("--base_model_id", type=str, required=True, help="The base model ID from Hugging Face.")
    parser.add_argument("--adapter_path", type=str, default=None, help="Path to the trained PEFT adapters (optional).")
    parser.add_argument("--dataset_path", type=str, required=True, help="Path to the JSONL test dataset file.")
    parser.add_argument("--output_dir", type=str, default="./reports", help="Directory to save the prediction file.")

    args = parser.parse_args()
    generate(args)