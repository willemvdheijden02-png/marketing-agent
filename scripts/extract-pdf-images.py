#!/usr/bin/env python3
"""
Extract images from a PDF, labelling each image with the nearest section heading above it.
Heading font is auto-detected: the (font-name, rounded-size) pair that appears most frequently
in short text spans (1-6 words) across all pages.

Usage:
    python3 extract-pdf-images.py <pdf_path> <output_dir>

Outputs JSON to stdout:
    {"images": [...], "frameworks": [...], "total": N, "heading_font": "...", "heading_size": N}
"""
import sys
import os
import json
from collections import Counter
import fitz  # PyMuPDF


def detect_heading_font(doc):
    font_counter = Counter()
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    word_count = len(text.split())
                    if 1 <= word_count <= 8 and len(text) >= 2:
                        font_counter[(span["font"], round(span["size"]))] += 1

    if not font_counter:
        return None, None
    font_name, font_size = font_counter.most_common(1)[0][0]
    return font_name, font_size


def find_heading_above(headings_on_page, img_y):
    above = [h for h in headings_on_page if h["y"] <= img_y + 5]
    if above:
        return max(above, key=lambda h: h["y"])["text"]
    return "UNKNOWN"


def extract(pdf_path, output_dir):
    doc = fitz.open(pdf_path)
    heading_font, heading_size = detect_heading_font(doc)

    os.makedirs(output_dir, exist_ok=True)

    results = []
    img_count = 0
    seen_xrefs = set()

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]

        headings = []
        for block in blocks:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    is_heading = False
                    if heading_font and span["font"] == heading_font and abs(span["size"] - heading_size) < 2:
                        is_heading = True
                    # Fallback: all-caps short text often marks a framework name
                    elif text.isupper() and 1 <= len(text.split()) <= 6:
                        is_heading = True
                    if is_heading:
                        headings.append({"text": text, "y": block["bbox"][1]})

        img_info_map = {item["xref"]: item for item in page.get_image_info() if "xref" in item}

        for img_ref in page.get_images(full=True):
            xref = img_ref[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)

            img_info = img_info_map.get(xref)
            img_y = img_info["bbox"][1] if img_info else 9999

            label = find_heading_above(headings, img_y)

            try:
                base_image = doc.extract_image(xref)
            except Exception:
                continue

            img_data = base_image["image"]
            img_ext = base_image.get("ext", "png")

            if len(img_data) < 1000:  # skip tiny icons / decorations
                continue

            img_count += 1
            safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label.upper())
            filename = f"page{page_num+1:03d}_img{img_count:03d}_{safe_label}.{img_ext}"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "wb") as f:
                f.write(img_data)

            results.append({
                "page": page_num + 1,
                "index": img_count,
                "label": label,
                "file": filename,
                "path": filepath,
            })

    frameworks = sorted(set(r["label"] for r in results if r["label"] != "UNKNOWN"))
    if any(r["label"] == "UNKNOWN" for r in results):
        frameworks.append("UNKNOWN")

    print(json.dumps({
        "images": results,
        "frameworks": frameworks,
        "total": img_count,
        "heading_font": heading_font,
        "heading_size": heading_size,
    }))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: extract-pdf-images.py <pdf_path> <output_dir>", file=sys.stderr)
        sys.exit(1)
    extract(sys.argv[1], sys.argv[2])
