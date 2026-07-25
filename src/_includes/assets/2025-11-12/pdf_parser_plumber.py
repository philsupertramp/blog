# PDF extraction with column, paragraph and ROBUST table detection (via pdfplumber)
# Integrated script: 
# - robust text/image extraction via PyMuPDF (fitz)
# - BEST-IN-CLASS table detection via pdfplumber (replaces native fitz)
# - column detection (1D clustering / histogram gaps)
# - paragraph grouping heuristics
# - visualization with corrected bbox rendering

import os
import json
from typing import List, Dict, Any, Tuple

import fitz  # PyMuPDF
import pdfplumber # logic: pip install pdfplumber
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from sklearn.cluster import AgglomerativeClustering

# -------------------------
# Utilities
# -------------------------

def safe_mkdir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path

def _safe_filename(base: str, ext: str, idx: int = 0) -> str:
    name = f"{base}_{idx}.{ext}" if idx else f"{base}.{ext}"
    return "".join(c for c in name if c.isalnum() or c in ("_", ".", "-"))

# -------------------------
# Core extraction
# -------------------------

def extract_pdf_structure(pdf_path: str, output_dir: str = "extracted_pdf_assets") -> Dict[str, Any]:
    safe_mkdir(output_dir)
    structure: Dict[str, Any] = {"path": pdf_path, "pages": []}
    
    # We open the doc with fitz for text/images AND pdfplumber for tables
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise RuntimeError(f"Failed to open PDF with fitz '{pdf_path}': {e}")

    try:
        plumber_doc = pdfplumber.open(pdf_path)
    except Exception as e:
        print(f"[warn] Failed to open PDF with pdfplumber: {e}. Table detection will be skipped.")
        plumber_doc = None
    
    structure["page_count"] = len(doc)
    
    for pno, page in enumerate(doc):
        page_w, page_h = page.rect.width, page.rect.height
        page_dict = {
            "page_number": pno + 1, 
            "width": page_w, 
            "height": page_h, 
            "text": [], 
            "images": [], 
            "vectors": [],
            "tables": [] 
        }

        # 1. Text Extraction (Fitz is faster and very accurate for plain text)
        try:
            tdict = page.get_text("dict")
            for block in tdict.get("blocks", []):
                if block.get("type") == 0:  # text
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            txt = span.get("text", "")
                            if not txt.strip(): continue
                            bbox = [round(v, 2) for v in span.get("bbox", [])]
                            page_dict["text"].append({
                                "text": txt, "bbox": bbox, "font": span.get("font"),
                                "size": span.get("size"), "flags": span.get("flags"),
                                "x0": bbox[0], "y0": bbox[1], "x1": bbox[2], "y1": bbox[3],
                                "cx": (bbox[0] + bbox[2]) / 2.0, "cy": (bbox[1] + bbox[3]) / 2.0,
                                "table_id": None, 
                            })
        except Exception as e:
            print(f"[warn] text extraction failed on page {pno+1}: {e}")

        # 2. Robust Table Detection (pdfplumber)
        # pdfplumber uses line detection and intersection heuristics which are superior 
        # to fitz's current implementation for complex layouts.
        if plumber_doc:
            try:
                # Access the corresponding page in pdfplumber
                # Note: pdfplumber pages are 0-indexed like fitz
                if pno < len(plumber_doc.pages):
                    p_page = plumber_doc.pages[pno]
                    
                    # find_tables() returns Table objects with .bbox and .extract()
                    # Default settings use 'lines' strategy which is good for bordered tables.
                    found_tables = p_page.find_tables()
                    
                    for tab in found_tables:
                        # tab.bbox is (x0, top, x1, bottom). 
                        # This coordinate system usually matches fitz (72dpi, top-left origin).
                        t_bbox = [round(v, 2) for v in tab.bbox]
                        
                        # Extract content (list of lists of strings)
                        t_content = tab.extract()
                        
                        page_dict["tables"].append({
                            "bbox": t_bbox,
                            "rows": t_content
                        })
            except Exception as e:
                print(f"[warn] pdfplumber table detection failed on page {pno+1}: {e}")

        # 3. Image Extraction
        try:
            img_idx = 0
            for img in page.get_images(full=True):
                xref = img[0]
                try:
                    base = doc.extract_image(xref)
                    img_bytes, img_ext = base["image"], base.get("ext", "png")
                    fname = _safe_filename(f"page{pno+1}_img{img_idx+1}", img_ext)
                    outpath = os.path.join(output_dir, fname)
                    with open(outpath, "wb") as fh: fh.write(img_bytes)
                    img_bbox = page.get_image_bbox(img).irect
                    page_dict["images"].append({
                        "bbox": [img_bbox.x0, img_bbox.y0, img_bbox.x1, img_bbox.y1],
                        "xref": xref, "filename": outpath, "ext": img_ext,
                        "width": base.get("width"), "height": base.get("height")
                    })
                    img_idx += 1
                except Exception as e:
                    print(f"[warn] could not extract image xref {xref} on page {pno+1}: {e}")
        except Exception as e:
            print(f"[warn] image extraction failed on page {pno+1}: {e}")

        # 4. Vector Extraction
        try:
            for d in page.get_drawings():
                r = d.get("rect")
                if r:
                    bbox = [round(r.x0, 2), round(r.y0, 2), round(r.x1, 2), round(r.y1, 2)]
                    page_dict["vectors"].append({"type": "rect", "bbox": bbox, "width": d.get("width")})
        except Exception:
            pass
            
        structure["pages"].append(page_dict)
    
    doc.close()
    if plumber_doc:
        plumber_doc.close()
        
    return structure

# -------------------------
# Layout heuristics
# -------------------------

def detect_columns_from_spans(spans: List[Dict[str, Any]], max_columns: int = 4, gap_threshold: float | None = None) -> List[int]:
    if not spans: return []
    centers = np.array([s["cx"] for s in spans]).reshape(-1, 1)
    if gap_threshold is None:
        widths = np.array([s["x1"] - s["x0"] for s in spans])
        median_w = np.median(widths) if widths.size else 50
        gap_threshold = max(30.0, median_w * 0.6)
    clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=gap_threshold, linkage="ward")
    labels = clustering.fit_predict(centers)
    unique_labels, means = np.unique(labels, return_counts=False), [np.mean(centers[labels == l]) for l in np.unique(labels)]
    sorted_labels = [label for _, label in sorted(zip(means, unique_labels))]
    label_to_col = {label: idx for idx, label in enumerate(sorted_labels)}
    cols = [min(label_to_col[l], max_columns - 1) for l in labels]
    return cols

def group_spans_to_lines(spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not spans: return []
    sorted_spans = sorted(spans, key=lambda s: (s["y0"], s["x0"]))
    lines: List[Dict[str, Any]] = []
    heights = [s["y1"] - s["y0"] for s in spans if s["y1"] - s["y0"] > 0]
    median_height = float(np.median(heights)) if heights else 10.0
    line_threshold = max(2.0, median_height * 0.4)
    current_line_spans = [sorted_spans[0]]
    for i in range(1, len(sorted_spans)):
        prev_s, curr_s = current_line_spans[-1], sorted_spans[i]
        if abs(curr_s["cy"] - prev_s["cy"]) <= line_threshold:
            current_line_spans.append(curr_s)
        else:
            all_x0, all_y0 = [s['x0'] for s in current_line_spans], [s['y0'] for s in current_line_spans]
            all_x1, all_y1 = [s['x1'] for s in current_line_spans], [s['y1'] for s in current_line_spans]
            bbox = [min(all_x0), min(all_y0), max(all_x1), max(all_y1)]
            lines.append({
                "spans": current_line_spans,
                "text": " ".join(s['text'] for s in sorted(current_line_spans, key=lambda s: s['x0'])),
                "bbox": bbox, "x0": bbox[0], "y0": bbox[1], "x1": bbox[2], "y1": bbox[3],
                "cx": (bbox[0] + bbox[2]) / 2, "cy": (bbox[1] + bbox[3]) / 2,
            })
            current_line_spans = [curr_s]
    if current_line_spans:
        all_x0, all_y0 = [s['x0'] for s in current_line_spans], [s['y0'] for s in current_line_spans]
        all_x1, all_y1 = [s['x1'] for s in current_line_spans], [s['y1'] for s in current_line_spans]
        bbox = [min(all_x0), min(all_y0), max(all_x1), max(all_y1)]
        lines.append({
            "spans": current_line_spans,
            "text": " ".join(s['text'] for s in sorted(current_line_spans, key=lambda s: s['x0'])),
            "bbox": bbox, "x0": bbox[0], "y0": bbox[1], "x1": bbox[2], "y1": bbox[3],
            "cx": (bbox[0] + bbox[2]) / 2, "cy": (bbox[1] + bbox[3]) / 2,
        })
    return lines

def group_lines_to_paragraphs(lines: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    if not lines: return []
    sorted_lines = sorted(lines, key=lambda l: l["y0"])
    heights = [l["y1"] - l["y0"] for l in sorted_lines if l["y1"] - l["y0"] > 0]
    if not heights: return []
    median_height = float(np.median(heights))
    gap_threshold = median_height * 0.6
    paragraphs: List[List[Dict[str, Any]]] = []
    current_para: List[Dict[str, Any]] = [sorted_lines[0]]
    for i in range(1, len(sorted_lines)):
        prev_ln, curr_ln = sorted_lines[i-1], sorted_lines[i]
        gap = curr_ln["y0"] - prev_ln["y1"]
        prev_end_char = prev_ln["text"].strip()[-1] if prev_ln["text"].strip() else ""
        is_punct_break = prev_end_char in {".", "!", "?", ":"} and gap > (median_height * 0.2)
        if gap > gap_threshold or is_punct_break:
            paragraphs.append(current_para)
            current_para = [curr_ln]
        else:
            current_para.append(curr_ln)
    if current_para: paragraphs.append(current_para)
    return paragraphs

# -------------------------
# High-level pipeline
# -------------------------

def analyze_pdf(pdf_path: str, output_dir: str = "extracted_pdf_assets") -> Dict[str, Any]:
    struct = extract_pdf_structure(pdf_path, output_dir=output_dir)
    for page in struct.get("pages", []):
        spans = page.get("text", [])
        if not spans: continue
        
        # Step 1: Group spans into lines
        lines = group_spans_to_lines(spans)
        
        # Step 2: Detect columns on all spans
        col_labels = detect_columns_from_spans(spans)
        for s, c in zip(spans, col_labels): s["col"] = int(c)
        for ln in lines:
            span_cols = [sp.get("col", 0) for sp in ln.get("spans", [])]
            ln["col"] = int(max(set(span_cols), key=span_cols.count)) if span_cols else 0
        
        # Step 3: Tag spans that belong to tables
        # This relies on the 'tables' detected via pdfplumber in extract_pdf_structure
        tables = page.get("tables", [])
        for i, tbl in enumerate(tables):
            tx0, ty0, tx1, ty1 = tbl["bbox"]
            for span in spans:
                # Check if span center is within the table bbox
                sx, sy = span["cx"], span["cy"]
                if tx0 <= sx <= tx1 and ty0 <= sy <= ty1:
                    span["table_id"] = i + 1 

        # Step 4: Exclude table lines from paragraph analysis 
        # A line is considered a table line if ANY of its spans are tagged
        non_table_lines = []
        for ln in lines:
            is_table_line = False
            for s in ln.get("spans", []):
                if s.get("table_id") is not None:
                    is_table_line = True
                    break
            if not is_table_line:
                non_table_lines.append(ln)

        # Step 5: Group remaining non-table lines into paragraphs per column
        paragraphs_by_col: Dict[int, List[List[Dict[str, Any]]]] = {}
        cols = sorted(list(set(ln.get("col", 0) for ln in non_table_lines)))
        for col_id in cols:
            col_lines = [ln for ln in non_table_lines if ln.get("col", 0) == col_id]
            if col_lines:
                paras = group_lines_to_paragraphs(col_lines)
                paragraphs_by_col[col_id] = paras

        page["lines"] = lines
        page["paragraphs_by_col"] = paragraphs_by_col
    return struct

# -------------------------
# Visualization and Save helpers
# -------------------------

def visualize_page(struct: Dict[str, Any], page_number: int = 1, save_path: str | None = None, show: bool = False):
    pages = struct.get("pages", [])
    if not (1 <= page_number <= len(pages)): raise ValueError("page_number out of range")
    page = pages[page_number - 1]
    w, h = page["width"], page["height"]
    fig, ax = plt.subplots(figsize=(w/72, h/72), dpi=150)
    margin = max(20, min(w, h) * 0.03)
    ax.set_xlim(-margin, w + margin); ax.set_ylim(-margin, h + margin)
    
    # Draw Images
    for img in page.get("images", []):
        x0, y0, x1, y1 = img.get("bbox", [0,0,0,0])
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=True, alpha=0.18, color='gray'))
        ax.text((x0 + x1) / 2, (y0 + y1) / 2, "[IMG]", ha='center', va='center', fontsize=6)

    # Draw Text Spans (Cyan) - Highlight table spans in magenta
    for t in page.get("text", []):
        x0, y0, x1, y1 = t["bbox"]
        color = 'cyan' if t.get("table_id") is None else 'magenta' 
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, linewidth=0.25, edgecolor=color, alpha=0.5))

    # Draw Paragraphs (Green)
    for col, paras in page.get("paragraphs_by_col", {}).items():
        for para in paras:
            if not para: continue
            for ln in para:
                l_x0, l_y0, _, _ = ln['bbox']
                ax.text(l_x0, l_y0, s=ln['text'], ha='left', va='top', fontsize=6)

    # Draw Tables (Red)
    for tbl in page.get("tables", []):
        bx0, by0, bx1, by1 = tbl.get("bbox", [0, 0, 0, 0])
        ax.add_patch(Rectangle((bx0, by0), bx1 - bx0, by1 - by0, fill=False, edgecolor='red', linewidth=1.2, alpha=0.7))
        ax.text(bx0 + 5, by0 + 5, "TABLE", color='red', fontsize=8, va='top', ha='left')
        
    ax.set_aspect('equal'); ax.invert_yaxis(); ax.axis('off')
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight')
        print(f"Saved visualization to {save_path}")
    if show: plt.show()
    plt.close(fig)

def save_structure_json(struct: Dict[str, Any], out_json_path: str):
    with open(out_json_path, "w", encoding="utf-8") as fh:
        json.dump(struct, fh, indent=2, ensure_ascii=False)
    print(f"Saved structure JSON to {out_json_path}")

# -------------------------
# CLI-like main (demo)
# -------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="PDF extractor with layout analysis")
    parser.add_argument("pdf", help="input PDF file")
    parser.add_argument("--outdir", default="extracted_pdf_assets", help="output dir for assets")
    parser.add_argument("--json", default="pdf_structure.json", help="output JSON file")
    parser.add_argument("--visualize", action="store_true", help="save visualizations for all pages")
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf):
        print(f"[error] {args.pdf} not found"); raise SystemExit(2)
        
    result = analyze_pdf(args.pdf, output_dir=args.outdir)
    save_structure_json(result, args.json)
    
    if args.visualize and result.get("pages"):
        page_count = result.get("page_count", 0)
        print(f"Visualizing {page_count} page(s)...")
        for i in range(page_count):
            visualize_page(result, page_number=i + 1, save_path=f"layout_page{i+1}.png")
    print("Done.")
