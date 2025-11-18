# PDF extraction with column, paragraph and table detection
# Integrated script: - robust extraction via PyMuPDF (fitz)
# - column detection (1D clustering / histogram gaps)
# - paragraph grouping heuristics
# - simple table detection using grid alignment
# - visualization with corrected bbox rendering (PDF -> Matplotlib coordinate flip)

import os
import json
import math
from typing import List, Dict, Any, Tuple

import fitz  # PyMuPDF
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
    # sanitize minimal
    return "".join(c for c in name if c.isalnum() or c in ("_", ".", "-"))


# -------------------------
# Core extraction
# -------------------------

def extract_pdf_structure(pdf_path: str, output_dir: str = "extracted_pdf_assets") -> Dict[str, Any]:
    """Extract a structured representation of the PDF using PyMuPDF.

    Returns a dictionary with page-level blocks: text spans, images, vectors.
    """
    safe_mkdir(output_dir)
    structure: Dict[str, Any] = {"path": pdf_path, "pages": []}

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise RuntimeError(f"Failed to open PDF '{pdf_path}': {e}")

    structure["page_count"] = len(doc)

    for pno in range(len(doc)):
        page = doc[pno]
        page_w, page_h = page.rect.width, page.rect.height
        page_dict = {"page_number": pno + 1, "width": page_w, "height": page_h, "text": [], "images": [], "vectors": []}

        # TEXT: spans with bbox, font, size
        try:
            tdict = page.get_text("dict")
            for block in tdict.get("blocks", []):
                if block.get("type") == 0:  # text
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            txt = span.get("text", "")
                            if not txt.strip():
                                continue
                            bbox = [round(v, 2) for v in span.get("bbox", [])]  # [x0,y0,x1,y1]
                            page_dict["text"].append({
                                "text": txt,
                                "bbox": bbox,
                                "font": span.get("font"),
                                "size": span.get("size"),
                                "flags": span.get("flags"),
                                # helpful derived fields
                                "x0": bbox[0], "y0": bbox[1], "x1": bbox[2], "y1": bbox[3],
                                "cx": (bbox[0] + bbox[2]) / 2.0,
                                "cy": (bbox[1] + bbox[3]) / 2.0,
                            })
        except Exception as e:
            print(f"[warn] text extraction failed on page {pno+1}: {e}")

        # IMAGES: use blocks when available (gives bbox) and doc.extract_image(xref)
        try:
            tdict = page.get_text("dict")
            img_idx = 0
            for block in tdict.get("blocks", []):
                if block.get("type") == 1:  # image block
                    bbox = [round(v, 2) for v in block.get("bbox", [])]
                    xref = block.get("xref")
                    if xref:
                        try:
                            base = doc.extract_image(xref)
                            img_bytes = base["image"]
                            img_ext = base.get("ext", "png")
                            fname = _safe_filename(f"page{pno+1}_img{img_idx+1}", img_ext)
                            outpath = os.path.join(output_dir, fname)
                            with open(outpath, "wb") as fh:
                                fh.write(img_bytes)
                            page_dict["images"].append({"bbox": bbox, "xref": xref, "filename": outpath, "ext": img_ext, "width": base.get("width"), "height": base.get("height")})
                        except Exception as e:
                            print(f"[warn] could not extract image xref {xref} on page {pno+1}: {e}")
                    else:
                        page_dict["images"].append({"bbox": bbox, "xref": None, "filename": None, "ext": None})
                    img_idx += 1
        except Exception as e:
            print(f"[warn] image extraction failed on page {pno+1}: {e}")

        # VECTORS: page.get_drawings() if supported
        try:
            drawings = page.get_drawings()
            for d in drawings:
                # d typically contains: type, rect, items, width, fill
                if d.get("rect"):
                    r = d.get("rect")
                    bbox = [round(r.x0, 2), round(r.y0, 2), round(r.x1, 2), round(r.y1, 2)]
                    page_dict["vectors"].append({"type": "rect", "bbox": bbox, "width": d.get("width")})
                elif d.get("items"):
                    for item in d.get("items", []):
                        if item[0] == "l":
                            _, x1, y1, x2, y2 = item
                            page_dict["vectors"].append({"type": "line", "p1": [round(x1, 2), round(y1, 2)], "p2": [round(x2, 2), round(y2, 2)], "width": d.get("width")})
                        elif item[0] == "re":
                            _, x, y, w, h = item
                            page_dict["vectors"].append({"type": "rect", "bbox": [round(x, 2), round(y, 2), round(x + w, 2), round(y + h, 2)], "width": d.get("width")})
                        else:
                            page_dict["vectors"].append({"type": "path", "cmd": item})
                else:
                    page_dict["vectors"].append({"type": "drawing", "raw": d})
        except Exception:
            pass

        structure["pages"].append(page_dict)

    doc.close()
    return structure


# -------------------------
# Layout heuristics
# -------------------------

def detect_columns_from_spans(spans: List[Dict[str, Any]], max_columns: int = 4, gap_threshold: float | None = None) -> List[int]:
    """Detect columns by clustering span x-centers. Returns column index per span."""
    if not spans:
        return []

    centers = np.array([s["cx"] for s in spans]).reshape(-1, 1)

    if gap_threshold is None:
        widths = np.array([s["x1"] - s["x0"] for s in spans])
        median_w = np.median(widths) if widths.size else 50
        gap_threshold = max(30.0, median_w * 0.6)

    clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=gap_threshold, linkage="ward")
    labels = clustering.fit_predict(centers)

    unique_labels = np.unique(labels)
    means = [np.mean(centers[labels == l]) for l in unique_labels]
    
    # Sort labels by their X position (Left -> Right)
    sorted_means = sorted(zip(unique_labels, means), key=lambda x: x[1])
    label_to_col = {label: idx for idx, (label, _) in enumerate(sorted_means)}

    cols = [label_to_col[l] for l in labels]
    cols = [min(c, max_columns - 1) for c in cols]
    return cols


def group_spans_to_lines(spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group close spans on same y into synthetic 'lines'.
    
    FIXED: Sorted by cy ascending (Top -> Bottom in PyMuPDF coords).
    """
    if not spans:
        return []

    # Sort: Primary = Top-to-Bottom (y0), Secondary = Left-to-Right (x0)
    # PyMuPDF origin is Top-Left. Small y = Top.
    sorted_spans = sorted(spans, key=lambda s: (s["cy"], s["x0"]))
    lines: List[Dict[str, Any]] = []

    heights = [s["y1"] - s["y0"] for s in spans if s["y1"] - s["y0"] > 0]
    median_height = float(np.median(heights)) if heights else 10.0
    line_threshold = max(2.0, median_height * 0.6)

    for s in sorted_spans:
        if not lines:
            lines.append({"spans": [s], "bbox": s["bbox"], "text": s["text"], "x0": s["x0"], "x1": s["x1"], "y0": s["y0"], "y1": s["y1"], "cx": s["cx"], "cy": s["cy"]})
            continue
        last = lines[-1]
        
        # Vertical gap
        gap = abs(last["cy"] - s["cy"])
        
        if gap <= line_threshold:
            last["spans"].append(s)
            last["text"] = last["text"] + " " + s["text"]
            last["x0"] = min(last["x0"], s["x0"])
            last["x1"] = max(last["x1"], s["x1"])
            last["y0"] = min(last["y0"], s["y0"])
            last["y1"] = max(last["y1"], s["y1"])
            last["cx"] = (last["x0"] + last["x1"]) / 2.0
            last["cy"] = (last["y0"] + last["y1"]) / 2.0
        else:
            lines.append({"spans": [s], "bbox": s["bbox"], "text": s["text"], "x0": s["x0"], "x1": s["x1"], "y0": s["y0"], "y1": s["y1"], "cx": s["cx"], "cy": s["cy"]})
    return lines


def group_lines_to_paragraphs(lines: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Group line-like objects into paragraphs.
    
    FIXED: Logic now respects Top -> Bottom sorting.
    """
    if not lines:
        return []

    # Sort Top -> Bottom
    sorted_lines = sorted(lines, key=lambda l: l["cy"])

    heights = [l["y1"] - l["y0"] for l in sorted_lines if l["y1"] - l["y0"] > 0]
    median_height = float(np.median(heights)) if heights else 10.0
    gap_threshold = median_height * 1.35

    paragraphs: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] = []
    prev = None
    
    for ln in sorted_lines:
        if prev is None:
            current.append(ln)
            prev = ln
            continue

        # Gap: Top of current (y0) - Bottom of previous (y1)
        # Because Y increases downwards
        gap = ln["y0"] - prev["y1"] 
        
        # Indent detection
        indent = ln["x0"] - prev["x0"]

        prev_end = prev["text"].strip()[-1] if prev["text"].strip() else ""
        punct_break = prev_end in {".", "!", "?"}

        # Heuristics: Big gap, indent, or previous line ended with sentence stop
        if gap > gap_threshold or indent > max(8.0, median_height * 0.25) or punct_break:
            paragraphs.append(current)
            current = [ln]
        else:
            current.append(ln)

        prev = ln

    if current:
        paragraphs.append(current)

    return paragraphs


def detect_tables(lines: List[Dict[str, Any]], min_columns: int = 2, col_distance_thresh: float = 20.0, row_distance_thresh: float = 8.0) -> List[Dict[str, Any]]:
    """Detect simple tables by finding vertical alignments of many word centers across lines."""
    if not lines:
        return []

    all_centers = []
    for ln in lines:
        for s in ln.get("spans", []):
            all_centers.append((s["cx"], ln["cy"], s["text"]))

    if not all_centers:
        return []

    xs = np.array([c[0] for c in all_centers]).reshape(-1, 1)
    clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=col_distance_thresh, linkage="ward")
    try:
        x_labels = clustering.fit_predict(xs)
    except Exception:
        return []

    unique_x = np.unique(x_labels)
    col_centers = [np.mean(xs[x_labels == u]) for u in unique_x]
    
    if len(col_centers) < min_columns:
        return []

    ys = np.array([c[1] for c in all_centers]).reshape(-1, 1)
    row_clust = AgglomerativeClustering(n_clusters=None, distance_threshold=row_distance_thresh, linkage="ward")
    try:
        row_labels = row_clust.fit_predict(ys)
    except Exception:
        return []

    grid = {}
    for (cx, cy, text), xl, rl in zip(all_centers, x_labels, row_labels):
        grid.setdefault(rl, {}).setdefault(xl, []).append((cx, cy, text))

    rows_sorted = []
    for rl in sorted(grid.keys()):
        row = []
        for xl in sorted(grid[rl].keys()):
            cell_text = " ".join([t for _, _, t in sorted(grid[rl][xl], key=lambda x: x[0])])
            row.append(cell_text)
        rows_sorted.append(row)

    if len(rows_sorted) < 2 or (len(rows_sorted[0]) < 2 if rows_sorted else True):
        return []

    # Compute overall table BBox
    all_x0 = []
    all_y0 = []
    all_x1 = []
    all_y1 = []
    
    # Helper to find spans participating in table
    # (In a production system, you'd link specific line IDs to the table, here we use rough area)
    for ln in lines:
        # Approximate: if line falls into the row Y-clusters
        pass 
    
    # Re-calculating bbox based on the spans that actually formed the grid
    table_x_min, table_y_min = float('inf'), float('inf')
    table_x_max, table_y_max = float('-inf'), float('-inf')
    
    for (cx, cy, _), _, _ in zip(all_centers, x_labels, row_labels):
        # This is rough because we only have centers here. 
        # Real implementation would trace back to span bbox.
        # We will use the range of centers +/- padding
        table_x_min = min(table_x_min, cx - 20)
        table_y_min = min(table_y_min, cy - 10)
        table_x_max = max(table_x_max, cx + 20)
        table_y_max = max(table_y_max, cy + 10)

    return [{"rows": rows_sorted, "bbox": [round(table_x_min, 2), round(table_y_min, 2), round(table_x_max, 2), round(table_y_max, 2)]}]


# -------------------------
# High-level pipeline
# -------------------------

def analyze_pdf(pdf_path: str, output_dir: str = "extracted_pdf_assets") -> Dict[str, Any]:
    """Run extraction + layout analysis across pages."""
    struct = extract_pdf_structure(pdf_path, output_dir=output_dir)

    for page in struct.get("pages", []):
        spans = page.get("text", [])
        
        lines = group_spans_to_lines(spans)

        col_labels = detect_columns_from_spans(spans)
        for s, c in zip(spans, col_labels):
            s["col"] = int(c)
        
        for ln in lines:
            span_cols = [sp.get("col", 0) for sp in ln.get("spans", [])]
            ln["col"] = int(max(set(span_cols), key=span_cols.count)) if span_cols else 0

        paragraphs_by_col: Dict[int, List[List[Dict[str, Any]]]] = {}
        for col in sorted(set([ln.get("col", 0) for ln in lines])):
            col_lines = [ln for ln in lines if ln.get("col", 0) == col]
            paras = group_lines_to_paragraphs(col_lines)
            paragraphs_by_col[col] = paras

        tables = detect_tables(lines)

        page["lines"] = lines
        page["paragraphs_by_col"] = paragraphs_by_col
        page["tables"] = tables

    return struct


# -------------------------
# Visualization helpers
# -------------------------

def visualize_page(struct: Dict[str, Any], page_number: int = 1, save_path: str | None = None, show: bool = False):
    pages = struct.get("pages", [])
    if page_number < 1 or page_number > len(pages):
        raise ValueError("page_number out of range")
    page = pages[page_number - 1]
    w, h = page["width"], page["height"]

    # Matplotlib setup
    fig, ax = plt.subplots(figsize=(w/72, h/72), dpi=150)
    margin = max(20, min(w, h) * 0.03)
    ax.set_xlim(-margin, w + margin)
    ax.set_ylim(-margin, h + margin)

    # Draw images
    for img in page.get("images", []):
        bbox = img.get("bbox")
        if not bbox:
            continue
        x0, y0, x1, y1 = bbox
        # Matplotlib Rectangle: (x, y) is bottom-left of the rect usually,
        # but with inverted Y axis, (x,y) becomes top-left visually.
        rect = Rectangle((x0, y0), x1 - x0, y1 - y0, fill=True, alpha=0.18)
        ax.add_patch(rect)
        ax.text((x0 + x1) / 2, (y0 + y1) / 2, "[IMG]", ha='center', va='center', fontsize=6)

    # Draw vectors
    for v in page.get("vectors", []):
        if v["type"] == "rect":
            x0, y0, x1, y1 = v["bbox"]
            # FIX: Do not overwrite v['width'] (stroke width) with the height of the rect
            rect_h = y1 - y0
            rect_w = x1 - x0
            v['width'] = 0.5
            ax.add_patch(Rectangle((x0, y0), rect_w, rect_h, fill=False, edgecolor='blue', 
                                   linewidth=max(0.3, v.get("width", 0.5)), alpha=0.1))
        elif v["type"] == "line":
            x1, y1 = v["p1"]
            x2, y2 = v["p2"]
            ax.plot([x1, x2], [y1, y2], linewidth=max(0.3, v.get("width", 0.3)))

    # Draw text
    for t in page.get("text", []):
        x0, y0, x1, y1 = t["bbox"]
        rect = Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, linewidth=0.25)
        ax.add_patch(rect)
        # With inverted Y, y0 is the visual Top
        ax.text(x0, y0, t["text"], fontsize=max(4, (t.get("size") or 10) * 0.7), va='top')

    # Overlay paragraph boxes
    for col, paras in page.get("paragraphs_by_col", {}).items():
        for pid, para in enumerate(paras):
            all_x0 = [ln['x0'] for ln in para]
            all_y0 = [ln['y0'] for ln in para]
            all_x1 = [ln['x1'] for ln in para]
            all_y1 = [ln['y1'] for ln in para]
            px0, py0, px1, py1 = min(all_x0), min(all_y0), max(all_x1), max(all_y1)
            ax.add_patch(Rectangle((px0, py0), px1 - px0, py1 - py0, fill=False, edgecolor='green', linewidth=0.6, alpha=0.6))

    # Overlay detected tables
    for tbl in page.get("tables", []):
        bx0, by0, bx1, by1 = tbl.get("bbox", [0, 0, 0, 0])
        ax.add_patch(Rectangle((bx0, by0), bx1 - bx0, by1 - by0, fill=False, edgecolor='red', linewidth=1.0, alpha=0.6))

    ax.set_aspect('equal')
    ax.invert_yaxis()  # Invert Y to match PDF coords (0,0 at top-left)
    ax.axis('off')

    if save_path:
        plt.savefig(save_path, bbox_inches='tight')
        print(f"Saved visualization to {save_path}")
    if show:
        plt.show()
    plt.close(fig)
    return True


# -------------------------
# Save helpers
# -------------------------

def save_structure_json(struct: Dict[str, Any], out_json_path: str):
    with open(out_json_path, "w", encoding="utf-8") as fh:
        json.dump(struct, fh, indent=2, ensure_ascii=False)
    print(f"Saved structure JSON to {out_json_path}")


# -------------------------
# CLI-like main (demo)
# -------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PDF extractor with columns/paragraphs/tables detection")
    parser.add_argument("pdf", help="input PDF file")
    parser.add_argument("--outdir", default="extracted_pdf_assets", help="output dir for assets")
    parser.add_argument("--json", default="pdf_structure.json", help="output JSON file")
    parser.add_argument("--visualize", action="store_true", help="save page1 visualization layout")
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        print(f"[error] {args.pdf} not found")
        raise SystemExit(2)

    result = analyze_pdf(args.pdf, output_dir=args.outdir)
    save_structure_json(result, args.json)

    if args.visualize and result.get("pages"):
        visualize_page(result, page_number=1, save_path="layout_page1.png")

    print("Done.")
