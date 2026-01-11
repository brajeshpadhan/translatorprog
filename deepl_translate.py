import os
import re
import csv
import shutil
import deepl

# =============================
# CONFIGURATION
# =============================
API_KEY = "Replace with your DeepL API"  # Replace with your DeepL API key
PROJECT_PATH = r"E:\spring-boot-project\demo"  # Path to your project
REPORT_CSV = "japanese_report.csv"  # CSV report of all Japanese text
BACKUP_FOLDER = "backup_project"  # Backup folder before translation
FILE_EXTENSIONS = (".java", ".properties", ".xml", ".html", ".json")  # Files to scan
TARGET_LANG = "EN-US"  # Translate to English

# =============================
# INITIALIZE DEEPL TRANSLATOR
# =============================
translator = deepl.Translator(API_KEY)

# =============================
# FUNCTION TO DETECT JAPANESE
# =============================
# Matches Hiragana, Katakana, Kanji
japanese_regex = re.compile(r'[\u3040-\u30ff\u4e00-\u9faf]+')

def find_japanese_text(text):
    return japanese_regex.findall(text)

# =============================
# CREATE BACKUP
# =============================
if not os.path.exists(BACKUP_FOLDER):
    shutil.copytree(PROJECT_PATH, BACKUP_FOLDER)
    print(f"Backup created at '{BACKUP_FOLDER}'")

# =============================
# SCAN FILES AND CREATE REPORT
# =============================
report_rows = []

for root, dirs, files in os.walk(PROJECT_PATH):
    for file in files:
        if file.endswith(FILE_EXTENSIONS):
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, start=1):
                    matches = find_japanese_text(line)
                    for match in matches:
                        report_rows.append({
                            "file_path": file_path,
                            "line_number": i,
                            "japanese_text": match
                        })

# Save report
with open(REPORT_CSV, "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["file_path", "line_number", "japanese_text"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in report_rows:
        writer.writerow(row)

print(f"Report generated: {REPORT_CSV}")
print(f"Total Japanese snippets found: {len(report_rows)}")

# =============================
# TRANSLATE FILES USING DEEPL
# =============================
def translate_text(text):
    try:
        return translator.translate_text(text, target_lang=TARGET_LANG).text
    except Exception as e:
        print(f"Error translating '{text}': {e}")
        return text

for row in report_rows:
    file_path = row["file_path"]
    original_text = row["japanese_text"]

    # Read file content
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace all occurrences of the Japanese snippet
    translated_text = translate_text(original_text)
    content = content.replace(original_text, translated_text)

    # Save back to file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Translated '{original_text}' in {file_path}")

print("All Japanese text translated successfully!")
