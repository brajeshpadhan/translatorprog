from PIL import Image, ImageDraw, ImageFont
import pytesseract
import deepl
import csv
import os

# ==============================
# CONFIGURATION
# ==============================

IMAGES_FOLDER = "images"            # Folder with Japanese text images
OUTPUT_FOLDER = "translated_images" # Folder to save translated images
REPORT_CSV = "japanese_text_report.csv"

DEEPL_API_KEY = "YOUR_DEEPL_API_KEY"
FONT_PATH = "arial.ttf"             # Path to TTF font
FONT_SIZE = 40

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ==============================
# INITIALIZE TRANSLATOR
# ==============================
translator = deepl.Translator(DEEPL_API_KEY)

# ==============================
# 1. GENERATE REPORT (OCR + TRANSLATION)
# ==============================
report_rows = []

for filename in os.listdir(IMAGES_FOLDER):
    if filename.lower().endswith((".png", ".jpg", ".jpeg")):
        image_path = os.path.join(IMAGES_FOLDER, filename)
        img = Image.open(image_path)

        # OCR with bounding boxes
        data = pytesseract.image_to_data(img, lang='jpn', output_type=pytesseract.Output.DICT)
        n_boxes = len(data['level'])

        for i in range(n_boxes):
            text = data['text'][i].strip()
            if text == "":
                continue

            # Bounding box coordinates
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]

            # Translate text using DeepL
            try:
                translation = translator.translate_text(text, source_lang="JA", target_lang="EN-US").text
            except Exception as e:
                translation = text
                print(f"Translation failed for '{text}': {e}")

            # Add to report
            report_rows.append([filename, x, y, w, h, text, translation])

# Save CSV report
with open(REPORT_CSV, mode="w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Image File", "X", "Y", "Width", "Height", "Japanese Text", "English Translation"])
    writer.writerows(report_rows)

print(f"Report generated: {REPORT_CSV}")
print("Please validate the report before replacing text in images.\n")

# ==============================
# 2. REPLACE TEXT IN IMAGES AFTER VALIDATION
# ==============================

# Prompt user to continue
proceed = input("Do you want to replace Japanese text with English in images? (y/n): ").lower()
if proceed != "y":
    print("Process terminated. You can edit the report and rerun.")
    exit()

# Process images
for row in report_rows:
    filename, x, y, w, h, japanese_text, english_text = row
    image_path = os.path.join(IMAGES_FOLDER, filename)
    output_path = os.path.join(OUTPUT_FOLDER, filename)

    # Open image
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)

    # Cover original Japanese text
    draw.rectangle([x, y, x + w, y + h], fill="white")

    # Draw English translation
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    draw.text((x, y), english_text, fill="black", font=font)

    # Save translated image
    img.save(output_path)
    print(f"Translated image saved: {output_path}")

print("\nAll images processed successfully!")
