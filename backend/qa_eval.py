import argparse
import json
import re
from collections import Counter
import string
import logging

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_answer(s: str) -> str:
    """
    Lower text and remove punctuation, articles and extra whitespace.
    This is a standard normalization function used in many QA benchmarks.
    """
    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))

def f1_score(prediction, ground_truth):
    """Computes token-level F1 score between a prediction and a ground truth."""
    prediction_tokens = normalize_answer(prediction).split()
    ground_truth_tokens = normalize_answer(ground_truth).split()
    common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
    num_same = sum(common.values())

    if num_same == 0:
        return 0

    precision = 1.0 * num_same / len(prediction_tokens)
    recall = 1.0 * num_same / len(ground_truth_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return f1

def exact_match_score(prediction, ground_truth):
    """Computes exact match score after normalization."""
    return normalize_answer(prediction) == normalize_answer(ground_truth)

def evaluate_qa(gold_file: str, pred_file: str):
    """
    Evaluates predictions against ground truth answers and calculates EM and F1 scores.
    """
    gold_data = {}
    with open(gold_file, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            gold_data[item['id']] = item['answers']

    pred_data = {}
    with open(pred_file, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            pred_data[item['id']] = item['prediction']

    exact_match = 0
    f1 = 0
    total = 0

    logger.info(f"Evaluating {len(pred_data)} predictions against {len(gold_data)} ground truths.")

    for qid, prediction in pred_data.items():
        if qid not in gold_data:
            logger.warning(f"Question ID '{qid}' found in predictions but not in gold data. Skipping.")
            continue

        total += 1
        ground_truths = gold_data[qid]

        # Calculate scores against all possible ground truths and take the max
        em_scores = [exact_match_score(prediction, gt) for gt in ground_truths]
        f1_scores = [f1_score(prediction, gt) for gt in ground_truths]

        exact_match += max(em_scores)
        f1 += max(f1_scores)

    if total == 0:
        logger.error("No matching question IDs found between prediction and gold files.")
        return {"error": "No matching questions."}

    em_avg = 100.0 * exact_match / total
    f1_avg = 100.0 * f1 / total

    report = {
        'total_questions': total,
        'exact_match': em_avg,
        'f1_score': f1_avg
    }

    logger.info(f"Evaluation complete. Results: {report}")
    return report

def save_report(report: dict, output_dir: str):
    """Saves the evaluation report to JSON and Markdown files."""
    os.makedirs(output_dir, exist_ok=True)

    # Save JSON report
    json_path = os.path.join(output_dir, "qa_eval_report.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"JSON report saved to {json_path}")

    # Save Markdown report
    md_path = os.path.join(output_dir, "qa_eval_report.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# QA Evaluation Report\n\n")
        f.write(f"- **Total Questions:** {report.get('total_questions', 'N/A')}\n")
        f.write(f"- **Exact Match (EM):** {report.get('exact_match', 0.0):.2f}%\n")
        f.write(f"- **F1 Score:** {report.get('f1_score', 0.0):.2f}%\n")
    logger.info(f"Markdown report saved to {md_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate QA model predictions.")
    parser.add_argument("--gold_file", type=str, required=True, help="Path to the ground truth JSONL file (e.g., qa_gold.jsonl).")
    parser.add_argument("--pred_file", type=str, required=True, help="Path to the prediction JSONL file (e.g., qa_pred.jsonl).")
    parser.add_argument("--output_dir", type=str, default="./reports", help="Directory to save the evaluation report.")

    args = parser.parse_args()

    evaluation_results = evaluate_qa(args.gold_file, args.pred_file)
    if "error" not in evaluation_results:
        save_report(evaluation_results, args.output_dir)
    else:
        logger.error(f"Evaluation failed: {evaluation_results['error']}")