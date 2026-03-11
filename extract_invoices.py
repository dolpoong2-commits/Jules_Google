import os
import re
import pandas as pd
import pdfplumber
import sys

INPUT_DIR = "input_pdfs"
OUTPUT_DIR = "output_excel"
ERROR_LOG = "error_log.txt"

def extract_invoice_data(pdf_path, filename):
    extracted_data = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text()
                    if not text:
                        continue

                    # Initialize default values
                    data = {
                        "파일명": filename,
                        "페이지": page_idx + 1,
                        "작성일자": "",
                        "공급자 등록번호": "",
                        "공급자 상호": "",
                        "공급받는자 등록번호": "",
                        "공급가액": "",
                        "세액": "",
                        "합계금액": "",
                        "품목명": []
                    }

                    # 1. 작성일자 추출
                    # 예: 2023년 01월 01일 or 2023-01-01 or 2023.01.01
                    date_match = re.search(r'작성\s*일자.*?(\d{4}[-./년\s]*\d{2}[-./월\s]*\d{2}[일]?)', text)
                    if not date_match:
                        # 홈택스 양식은 표 안에 작성일자가 기재되기도 함. "2023-10-10" 형태 등.
                        date_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', text)
                    if date_match:
                        data["작성일자"] = date_match.group(1).strip()

                    # 2. 사업자 등록번호 추출
                    # \d{3}-\d{2}-\d{5} 형태가 2개 존재 (공급자, 공급받는자)
                    reg_no_matches = re.findall(r'\d{3}-\d{2}-\d{5}', text)
                    if len(reg_no_matches) >= 1:
                        data["공급자 등록번호"] = reg_no_matches[0]
                    if len(reg_no_matches) >= 2:
                        data["공급받는자 등록번호"] = reg_no_matches[1]

                    # 3. 상호 추출
                    # 홈택스 양식에서 공급자 상호는 대개 "상 호\n(법인명) ㈜테스트" 또는 "상 호 (법인명) ㈜테스트" 형태
                    # 간단히 등록번호 주변이나 상호 키워드로 찾습니다.
                    supplier_name_match = re.search(r'상\s*호.*?\)\s*([^\n]+)', text)
                    if supplier_name_match:
                        data["공급자 상호"] = supplier_name_match.group(1).strip()
                    else:
                        supplier_name_match = re.search(r'공\s*급\s*자.*?상\s*호.*?([^\n]+)', text, re.DOTALL)
                        if supplier_name_match:
                            data["공급자 상호"] = supplier_name_match.group(1).strip()
                        else:
                            # 다른 방식의 탐색
                            lines = text.split('\n')
                            for i, line in enumerate(lines):
                                if "상 호" in line and "성 명" in line: # 홈택스 양식 라인
                                    if i + 1 < len(lines):
                                        # 상호 아래 라인에 상호명이 적혀 있을 수 있음
                                        parts = lines[i+1].split()
                                        if parts:
                                            data["공급자 상호"] = parts[0]
                                    break

                    # 4. 금액 추출
                    # 합계금액, 공급가액, 세액
                    # 숫자 콤마 포함하여 매칭 (예: 1,000,000)
                    for kind in ["합계금액", "공급가액", "세액"]:
                        match = re.search(fr'{kind}\s*([0-9,]+)', text)
                        if match and not data[kind]:
                            data[kind] = match.group(1)

                    # 5. 품목명 추출
                    # 홈택스 세금계산서의 테이블에서 추출
                    # "월 일 품목 규격 수량 단가 공급가액 세액 비고" 등의 헤더를 찾고 그 아래의 항목들을 추출합니다.
                    tables = page.extract_tables()
                    items = []

                    if tables:
                        for table in tables:
                            for row in table:
                                # row 요소들을 텍스트로 결합
                                row_text = ' '.join([str(c) if c else '' for c in row])
                                # 월, 일로 시작하는 데이터 행(품목)인지 체크 (예: 01 01 품목명 ...)
                                item_match = re.match(r'^\s*\d{1,2}\s*\d{1,2}\s+([^\s]+)', row_text)
                                if item_match:
                                    items.append(item_match.group(1))

                    # 테이블에서 못 찾았다면 텍스트 기반 보조 추출
                    if not items:
                        # 홈택스 품목 텍스트 예: "10 12 테스트 품목 1 10,000 10,000 1,000"
                        item_lines = re.findall(r'(?m)^\s*\d{1,2}\s+\d{1,2}\s+([가-힣a-zA-Z0-9_]+)', text)
                        for item in item_lines:
                            items.append(item)

                    data["품목명"] = items if items else []
                    extracted_data.append(data)

                except Exception as e:
                    with open(ERROR_LOG, "a", encoding="utf-8") as f:
                        f.write(f"File: {filename}, Page: {page_idx + 1}, Error: {str(e)}\n")

    except Exception as e:
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(f"File: {filename}, Error opening PDF: {str(e)}\n")

    return extracted_data

def main():
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    all_data = []

    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print(f"'{INPUT_DIR}' 폴더에 PDF 파일이 없습니다.")
        return

    print(f"총 {len(pdf_files)}개의 PDF 파일을 처리합니다.")

    for filename in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, filename)
        print(f"처리 중: {filename}...")
        file_data = extract_invoice_data(pdf_path, filename)
        all_data.extend(file_data)

    if not all_data:
        print("추출된 데이터가 없습니다.")
        return

    # 데이터 프레임 변환
    df = pd.DataFrame(all_data)

    # 품목명 리스트를 개별 컬럼으로 분리 (품목명1, 품목명2, ...)
    # 먼저 최대 품목 개수를 구함
    max_items = df["품목명"].apply(len).max() if not df.empty else 0

    for i in range(max_items):
        df[f"품목명{i+1}"] = df["품목명"].apply(lambda x: x[i] if i < len(x) else "")

    # 원본 품목명 컬럼 삭제
    if "품목명" in df.columns:
        df.drop(columns=["품목명"], inplace=True)

    # 엑셀로 저장
    output_path = os.path.join(OUTPUT_DIR, "tax_invoices_result.xlsx")
    df.to_excel(output_path, index=False)
    print(f"작업 완료! 결과가 {output_path}에 저장되었습니다.")

if __name__ == "__main__":
    main()
