import os
import re
import csv

# =============================
# CONFIGURATION
# =============================
PROJECT_PATH = r"E:\spring-boot-project\demo"  # Path to your project
OUTPUT_CSV = "japanese_report_only.csv"
FILE_EXTENSIONS = (".java", ".properties", ".xml", ".html", ".json")  # File types to scan

# =============================
# FUNCTION TO DETECT JAPANESE TEXT
# =============================
# Matches Hiragana, Katakana, Kanji
japanese_regex = re.compile(r'[\u3040-\u30ff\u4e00-\u9faf]+')

def find_japanese_text(text):
    return japanese_regex.findall(text)

# =============================
# SCAN FILES
# =============================
report_rows = []

for root, dirs, files in os.walk(PROJECT_PATH):
    for file in files:
        if file.endswith(FILE_EXTENSIONS):
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, start=1):
                    matches = find_japanese_text(line)
                    if matches:
                        report_rows.append({
                            "file_path": file_path,
                            "line_number": i,
                            "original_text": line.strip()
                        })

# =============================
# SAVE REPORT AS CSV
# =============================
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["file_path", "line_number", "original_text"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in report_rows:
        writer.writerow(row)

print(f"Report generated: {OUTPUT_CSV}")
print(f"Total lines with Japanese text found: {len(report_rows)}")