import os
import json
import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts raw text from all pages of a PDF."""
    full_text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                full_text += page.get_text("text")
    except Exception as e:
        logger.error(f"Could not extract text from {pdf_path}: {e}")
    return full_text

def ocr_images_from_pdf(pdf_path: str, work_dir: str) -> str:
    """Extracts images from a PDF, performs OCR, and returns the text."""
    ocr_text = ""
    try:
        doc = fitz.open(pdf_path)
        img_dir = Path(work_dir) / "images"
        img_dir.mkdir(exist_ok=True)

        for page_num, page in enumerate(doc):
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                image_path = img_dir / f"page{page_num+1}_img{img_index}.png"
                with open(image_path, "wb") as f:
                    f.write(image_bytes)

                try:
                    text = pytesseract.image_to_string(Image.open(image_path))
                    ocr_text += text + "\n"
                except Exception as ocr_error:
                    logger.warning(f"OCR failed for image {image_path}: {ocr_error}")
    except Exception as e:
        logger.error(f"Could not process images from {pdf_path}: {e}")
    return ocr_text

def generate_specs_from_text(text: str) -> dict:
    """
    A simple rule-based approach to extract key-value specs from text.
    This is a placeholder for a more sophisticated extraction logic.
    """
    specs = {"specifications": []}
    # Example regex: Find lines like "Operating Voltage: 3.3V" or "Temperature Range -40 to 85 C"
    patterns = [
        r"(?i)(operating\s+voltage.*?[:\s])\s*([\d\.]+\s*V)",
        r"(?i)(temperature\s+range.*?[:\s])\s*([-\d]+\s*to\s*\d+\s*°?C)",
        r"(?i)(frequency.*?[:\s])\s*([\d\.]+\s*MHz)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # match is a tuple, e.g., ('Operating Voltage: ', '3.3V')
            spec_name = match[0].replace(':', '').strip()
            spec_value = match[1].strip()
            specs["specifications"].append({"name": spec_name, "value": spec_value})

    logger.info(f"Extracted {len(specs['specifications'])} specifications.")
    return specs

def generate_qa_from_specs(specs: dict) -> list:
    """Generates question-answer pairs from extracted specifications."""
    qa_pairs = []
    for spec in specs.get("specifications", []):
        question = f"What is the {spec['name'].lower()}?"
        answer = spec['value']
        qa_pairs.append({
            "id": f"auto_{spec['name'].lower().replace(' ', '_')}",
            "question": question,
            "answers": [answer],
            "context": f"The specification for {spec['name']} is {answer}."
        })
    logger.info(f"Generated {len(qa_pairs)} QA pairs.")
    return qa_pairs

def process_datasheet(pdf_path: str, output_dir: str):
    """
    Full pipeline to process a single PDF datasheet.
    """
    logger.info(f"Processing datasheet: {pdf_path}")
    pdf_path_obj = Path(pdf_path)
    output_dir_obj = Path(output_dir)
    output_dir_obj.mkdir(exist_ok=True)

    # 1. Extract text using both direct and OCR methods
    raw_text = extract_text_from_pdf(pdf_path)
    ocr_text = ocr_images_from_pdf(pdf_path, str(output_dir_obj))
    full_text = raw_text + "\n" + ocr_text

    # 2. Generate specifications
    specs = generate_specs_from_text(full_text)
    specs_path = output_dir_obj / f"{pdf_path_obj.stem}_specs.json"
    with open(specs_path, 'w', encoding='utf-8') as f:
        json.dump(specs, f, indent=2)
    logger.info(f"Saved specs to {specs_path}")

    # 3. Generate QA pairs
    qa_pairs = generate_qa_from_specs(specs)
    qa_path = output_dir_obj / f"{pdf_path_obj.stem}_qa_gold.jsonl"
    with open(qa_path, 'w', encoding='utf-8') as f:
        for pair in qa_pairs:
            f.write(json.dumps(pair) + "\n")
    logger.info(f"Saved QA pairs to {qa_path}")

    return {
        "source_pdf": pdf_path_obj.name,
        "specs_file": str(specs_path),
        "qa_file": str(qa_path),
        "status": "Success"
    }

def process_datasheet_directory(directory_path: str):
    """Processes all PDFs in a given directory."""
    results = []
    path_obj = Path(directory_path)
    pdf_files = list(path_obj.rglob("*.pdf"))

    if not pdf_files:
        logger.warning(f"No PDF files found in {directory_path}")
        return {"message": "No PDF files found."}

    processed_dir = path_obj / "processed"
    processed_dir.mkdir(exist_ok=True)

    for pdf_file in pdf_files:
        try:
            result = process_datasheet(str(pdf_file), str(processed_dir))
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {pdf_file.name}: {e}")
            results.append({"source_pdf": pdf_file.name, "status": "Failed", "error": str(e)})

    return {"results": results}