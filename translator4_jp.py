import os
import re
import csv
import shutil
import deepl

# =============================
# CONFIGURATION
# =============================
API_KEY = "apikeyhere"  #
PROJECT_PATH = r"E:\spring-boot-project\demo"
BACKUP_FOLDER = "backup_project"
REPORT_CSV = "japanese_report4.csv"

FILE_EXTENSIONS = (".java", ".groovy", ".ts", ".dart", ".properties", ".yml", ".yaml")
IGNORE_DIRS = {".git", "build", "dist", "target", "node_modules", ".dart_tool", ".angular"}

TARGET_LANG = "EN-US"

# =============================
# INITIALIZE DEEPL
# =============================
translator = deepl.Translator(API_KEY)

# =============================
# REGEX DEFINITIONS
# =============================
JAPANESE_REGEX = re.compile(r'[\u3040-\u30ff\u4e00-\u9faf]')
STRING_REGEX = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"')
LINE_COMMENT_REGEX = re.compile(r'//(.*)')
BLOCK_COMMENT_REGEX = re.compile(r'/\*(?!\*)([\s\S]*?)\*/')
JAVADOC_REGEX = re.compile(r'/\*\*([\s\S]*?)\*/')
YML_VALUE_REGEX = re.compile(r'(:\s*)(["\']?)(.+?)(["\']?)$')

# =============================
# CREATE BACKUP
# =============================
if not os.path.exists(BACKUP_FOLDER):
    shutil.copytree(PROJECT_PATH, BACKUP_FOLDER)
    print(f"Backup created at: {BACKUP_FOLDER}")

# =============================
# TRANSLATION FUNCTION
# =============================
def translate_text(text: str) -> str:
    try:
        translated = translator.translate_text(text, source_lang="JA", target_lang=TARGET_LANG).text
        return translated.replace("。", ".")
    except Exception as e:
        print(f"Translation failed for '{text}': {e}")
        return text

# =============================
# STEP 1: SCAN FILES AND GENERATE REPORT
# =============================
report_rows = []
translation_cache = {}

for root, dirs, files in os.walk(PROJECT_PATH):
    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

    for file in files:
        if not file.endswith(FILE_EXTENSIONS):
            continue

        path = os.path.join(root, file)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.splitlines()

        # --- JavaDoc ---
        for match in JAVADOC_REGEX.finditer(content):
            start_line = content[:match.start()].count("\n") + 1
            block = match.group(1)
            for offset, line in enumerate(block.splitlines()):
                text = line.strip(" *")
                if JAPANESE_REGEX.search(text):
                    if text not in translation_cache:
                        translation_cache[text] = translate_text(text)
                    report_rows.append({
                        "file": path,
                        "line_number": start_line + offset,
                        "japanese_text": text,
                        "english_text": translation_cache[text]
                    })

        # --- Block comments ---
        for match in BLOCK_COMMENT_REGEX.finditer(content):
            start_line = content[:match.start()].count("\n") + 1
            block = match.group(1)
            for offset, line in enumerate(block.splitlines()):
                text = line.strip(" *")
                if JAPANESE_REGEX.search(text):
                    if text not in translation_cache:
                        translation_cache[text] = translate_text(text)
                    report_rows.append({
                        "file": path,
                        "line_number": start_line + offset,
                        "japanese_text": text,
                        "english_text": translation_cache[text]
                    })

        # --- Line by line scan ---
        for line_no, line in enumerate(lines, start=1):
            # Line comments
            m = LINE_COMMENT_REGEX.search(line)
            if m:
                text = m.group(1).strip()
                if JAPANESE_REGEX.search(text):
                    if text not in translation_cache:
                        translation_cache[text] = translate_text(text)
                    report_rows.append({
                        "file": path,
                        "line_number": line_no,
                        "japanese_text": text,
                        "english_text": translation_cache[text]
                    })

            # String literals (includes annotations, DTOs, Controller strings)
            for match in STRING_REGEX.findall(line):
                if JAPANESE_REGEX.search(match):
                    if match not in translation_cache:
                        translation_cache[match] = translate_text(match)
                    report_rows.append({
                        "file": path,
                        "line_number": line_no,
                        "japanese_text": match,
                        "english_text": translation_cache[match]
                    })

            # YAML / properties
            if file.endswith((".yml", ".yaml")):
                m = YML_VALUE_REGEX.search(line)
                if m:
                    val = m.group(3).strip()
                    if JAPANESE_REGEX.search(val):
                        if val not in translation_cache:
                            translation_cache[val] = translate_text(val)
                        report_rows.append({
                            "file": path,
                            "line_number": line_no,
                            "japanese_text": val,
                            "english_text": translation_cache[val]
                        })

            if file.endswith(".properties") and "=" in line and not line.strip().startswith("#"):
                val = line.split("=",1)[1].strip()
                if JAPANESE_REGEX.search(val):
                    if val not in translation_cache:
                        translation_cache[val] = translate_text(val)
                    report_rows.append({
                        "file": path,
                        "line_number": line_no,
                        "japanese_text": val,
                        "english_text": translation_cache[val]
                    })

# Deduplicate
unique = {(r["file"], r["line_number"], r["japanese_text"]): r for r in report_rows}
report_rows = list(unique.values())

# Save CSV report
with open(REPORT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["file","line_number","japanese_text","english_text"])
    writer.writeheader()
    writer.writerows(report_rows)

print(f"✅ Report generated: {REPORT_CSV}")
print(f"Total Japanese entries found: {len(report_rows)}")
input("Review the CSV if needed, then press Enter to apply translations...")

# =============================
# STEP 2: APPLY TRANSLATIONS
# =============================
for row in report_rows:
    with open(row["file"], "r", encoding="utf-8") as f:
        content = f.read()

    # Replace Japanese only
    content = content.replace(row["japanese_text"], row["english_text"])

    with open(row["file"], "w", encoding="utf-8") as f:
        f.write(content)

print("✅ Japanese → English translation applied successfully.")
