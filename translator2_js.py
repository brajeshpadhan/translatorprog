import os
import re
import csv
import shutil
import deepl

# =============================
# CONFIGURATION
# =============================
API_KEY = "REPLACE_WITH_YOUR_DEEPL_API_KEY"
PROJECT_PATH = r"E:\multi-project"
BACKUP_FOLDER = "backup_project"
REPORT_CSV = "japanese_report.csv"
FILE_EXTENSIONS = (".dart", ".html", ".ts", ".groovy", ".java",
                   ".properties", ".json", ".arb", ".yml", ".yaml")
IGNORE_DIRS = {".git", "build", "dist", "node_modules", "target", ".dart_tool", ".angular"}
TARGET_LANG = "EN-US"

# =============================
# INITIALIZE DEEPL
# =============================
translator = deepl.Translator(API_KEY)

# =============================
# REGEX
# =============================
JAPANESE_REGEX = re.compile(r'[\u3040-\u30ff\u4e00-\u9faf]+')
STRING_REGEX = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"')
YML_VALUE_REGEX = re.compile(r'(:\s*)(["\']?)(.+?)(["\']?)$')
SKIP_PATTERNS = ("/", ":", "{", "}", "%", "$", "@", "\\n")

# =============================
# BACKUP
# =============================
if not os.path.exists(BACKUP_FOLDER):
    shutil.copytree(PROJECT_PATH, BACKUP_FOLDER)
    print(f"Backup created: {BACKUP_FOLDER}")

# =============================
# HELPER FUNCTIONS
# =============================
def contains_japanese(text):
    return bool(JAPANESE_REGEX.search(text))

def safe_text(text):
    return contains_japanese(text) and not any(p in text for p in SKIP_PATTERNS)

# =============================
# STEP 1: GENERATE REPORT (NO TRANSLATION YET)
# =============================
report_rows = []

for root, dirs, files in os.walk(PROJECT_PATH):
    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

    for file in files:
        if not file.endswith(FILE_EXTENSIONS):
            continue

        path = os.path.join(root, file)

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines, start=1):
            japanese_texts = set()

            # ---------- .properties ----------
            if file.endswith(".properties"):
                if "=" in line and not line.strip().startswith("#"):
                    _, value = line.split("=", 1)
                    if contains_japanese(value.strip()):
                        japanese_texts.add(value.strip())

            # ---------- YAML ----------
            elif file.endswith((".yml", ".yaml")):
                match = YML_VALUE_REGEX.search(line)
                if match:
                    _, _, val, _ = match.groups()
                    val = val.strip()
                    if safe_text(val):
                        japanese_texts.add(val)

            # ---------- Java / Dart / TS / Groovy ----------
            else:
                for match in STRING_REGEX.findall(line):
                    if safe_text(match):
                        japanese_texts.add(match)

            for text in japanese_texts:
                report_rows.append({
                    "file": path,
                    "line_number": i,
                    "japanese_text": text,
                    "english_text": ""  # Will fill in step 2
                })

# Save initial report
with open(REPORT_CSV, "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["file", "line_number", "japanese_text", "english_text"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(report_rows)

print(f"Step 1 complete: Report generated ({REPORT_CSV})")
print(f"Total Japanese snippets found: {len(report_rows)}")

# =============================
# STEP 2: TRANSLATE AND UPDATE REPORT
# =============================
proceed = input("Proceed to translate Japanese text in the report? (y/n): ").strip().lower()
if proceed != "y":
    print("Translation skipped. You can review the report first.")
    exit()

translation_cache = {}

def translate(text):
    if text in translation_cache:
        return translation_cache[text]
    try:
        translated = translator.translate_text(text, source_lang="JA", target_lang=TARGET_LANG).text
        translation_cache[text] = translated
        return translated
    except Exception as e:
        print(f"Translation error for '{text}': {e}")
        return text

# Translate all Japanese text in the report
for row in report_rows:
    japanese = row["japanese_text"]
    row["english_text"] = translate(japanese)

# Save updated report with English
with open(REPORT_CSV, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=["file", "line_number", "japanese_text", "english_text"])
    writer.writeheader()
    writer.writerows(report_rows)

print(f"Step 2 complete: Report updated with English translations ({REPORT_CSV})")
print(f"Unique translations: {len(translation_cache)}")

# =============================
# OPTIONAL: APPLY TRANSLATION TO FILES
# =============================
apply_changes = input("Do you want to apply translations to files? (y/n): ").strip().lower()
if apply_changes != "y":
    print("Done. No files modified.")
else:
    for row in report_rows:
        file_path = row["file"]
        japanese = row["japanese_text"]
        english = row["english_text"]

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        content = content.replace(japanese, english)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    #=================================
    # logic with line number either above or below need to use
    #=================================
  for row in report_rows:
    file_path = row["file"]
    line_number = row["line_number"]  # 1-based
    japanese_text = row["japanese_text"]
    english_text = row["english_text"]

    # Read file lines
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Replace Japanese text ONLY in the specific line
    idx = line_number - 1  # Convert to 0-based index
    if idx < len(lines) and japanese_text in lines[idx]:
        lines[idx] = lines[idx].replace(japanese_text, english_text)
        # Optional: log what changed
        print(f"Line {line_number} in {file_path} translated.")

    # Write lines back to file
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("All files updated with English translations.")
