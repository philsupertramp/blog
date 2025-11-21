# PDF extraction with column, paragraph and table detection
# Integrated script: - robust extraction via PyMuPDF (fitz)
# - column detection (1D clustering / histogram gaps)
# - paragraph grouping heuristics
# - simple table detection using grid alignment
# - visualization with corrected bbox rendering (PDF -> Matplotlib coordinate flip)

import os
import json
from typing import List, Dict, Any

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
    return "".join(c for c in name if c.isalnum() or c in ("_", ".", "-"))

# -------------------------
# Core extraction
# -------------------------

def extract_pdf_structure(pdf_path: str, output_dir: str = "extracted_pdf_assets") -> Dict[str, Any]:
    safe_mkdir(output_dir)
    structure: Dict[str, Any] = {"path": pdf_path, "pages": []}
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise RuntimeError(f"Failed to open PDF '{pdf_path}': {e}")
    structure["page_count"] = len(doc)
    for pno, page in enumerate(doc):
        page_w, page_h = page.rect.width, page.rect.height
        page_dict = {"page_number": pno + 1, "width": page_w, "height": page_h, "text": [], "images": [], "vectors": []}
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
                            })
        except Exception as e:
            print(f"[warn] text extraction failed on page {pno+1}: {e}")
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
# Enhanced Table Detection
# -------------------------

def get_line_segments(line: Dict[str, Any], space_scale: float = 2.0) -> List[Dict[str, Any]]:
    """
    Breaks a line into visual segments based on horizontal gaps.
    User Heuristic: Gap > space character.
    """
    spans = sorted(line["spans"], key=lambda s: s["x0"])
    if not spans:
        return []

    # Calculate an approximate space width for this specific line based on font size
    # Average char width is roughly height / 2. A wide gap is ~ 2 to 3 spaces.
    avg_font_size = np.mean([s["size"] for s in spans]) if spans else 10.0
    gap_threshold = avg_font_size * 0.6 * space_scale 

    segments = []
    current_segment = [spans[0]]
    
    for i in range(1, len(spans)):
        prev = spans[i-1]
        curr = spans[i]
        gap = curr["x0"] - prev["x1"]
        
        if gap > gap_threshold:
            # Gap detected: close current segment and start new
            segments.append(current_segment)
            current_segment = [curr]
        else:
            current_segment.append(curr)
    segments.append(current_segment)

    # Convert list of spans into simplified segment dicts
    segment_dicts = []
    for seg in segments:
        x0 = min(s["x0"] for s in seg)
        x1 = max(s["x1"] for s in seg)
        text = " ".join(s["text"] for s in seg)
        segment_dicts.append({"x0": x0, "x1": x1, "text": text, "spans": seg})
            
    return segment_dicts

def segments_overlap(seg1: Dict[str, Any], seg2: Dict[str, Any], tolerance: float = 5.0) -> bool:
    """Checks if two segments vertically align (share x-coordinates)."""
    return max(0, min(seg1["x1"], seg2["x1"]) - max(seg1["x0"], seg2["x0"])) > tolerance

def detect_tables(lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detects tables by finding consecutive lines that have multiple segments 
    which vertically align with each other.
    """
    if len(lines) < 2:
        return []

    # 1. Analyze every line to see if it has "columns" (segments)
    # We use a looser threshold (1.5 spaces) to catch tight tables
    line_structures = []
    for ln in lines:
        segs = get_line_segments(ln, space_scale=1.5)
        line_structures.append({
            "line_obj": ln,
            "segments": segs,
            "is_multi_col": len(segs) > 1
        })

    tables = []
    current_table_lines = []
    
    # 2. Group consecutive lines that look like they belong to the same grid
    for i in range(len(line_structures)):
        curr = line_structures[i]
        prev = line_structures[i-1] if i > 0 else None

        is_table_part = False
        
        if curr["is_multi_col"]:
            # If it has columns, check if it aligns with the previous table line
            if current_table_lines:
                prev_table_line = current_table_lines[-1]
                # Check alignment: Do at least 50% of segments align with the previous line?
                matches = 0
                for c_seg in curr["segments"]:
                    for p_seg in prev_table_line["segments"]:
                        if segments_overlap(c_seg, p_seg):
                            matches += 1
                            break
                if matches > 0:
                    is_table_part = True
            else:
                # Start of a potential table
                # Heuristic: Must be followed by another multi-col line to be a table
                if i + 1 < len(line_structures):
                    next_ln = line_structures[i+1]
                    if next_ln["is_multi_col"]:
                        # Check alignment with next
                        matches = 0
                        for c_seg in curr["segments"]:
                            for n_seg in next_ln["segments"]:
                                if segments_overlap(c_seg, n_seg):
                                    matches += 1
                                    break
                        if matches > 0:
                            is_table_part = True

        # 3. Handle Vertical Isolation (Whitespace heuristic)
        # If we have a table going, allows single-column lines if they are "sandwiched" closely
        if not is_table_part and current_table_lines:
            # Allow a single line break or a header line inside a table 
            # if the vertical gap is small
            gap = curr["line_obj"]["y0"] - current_table_lines[-1]["line_obj"]["y1"]
            if gap < 15.0: # Small vertical gap threshold
                # It might be a wrapped row. 
                # (Simplification: for now, strict visual alignment is safer)
                pass

        if is_table_part:
            current_table_lines.append(curr)
        else:
            if len(current_table_lines) >= 2:
                tables.append(process_table_block(current_table_lines))
            current_table_lines = []

    # Catch trailing table
    if len(current_table_lines) >= 2:
        tables.append(process_table_block(current_table_lines))

    return tables

def process_table_block(block_structs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Converts a list of raw line structures into a clean table dictionary.
    Recalculates columns based on the aggregate of all lines in the block.
    """
    # 1. Collect all x-intervals from all lines
    all_segments = []
    for item in block_structs:
        all_segments.extend(item["segments"])
    
    # 2. Determine global column boundaries for this block using X-clustering
    # (We reuse the logic from the old script here but restricted to this block)
    if not all_segments: return {}
    
    xs = np.array([(s["x0"] + s["x1"])/2 for s in all_segments]).reshape(-1, 1)
    # Cluster centers to find column buckets
    from sklearn.cluster import AgglomerativeClustering
    clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=20, linkage="ward")
    labels = clustering.fit_predict(xs)
    
    # Map unique labels to sorted x-positions
    unique_labels = np.unique(labels)
    col_centers = []
    for l in unique_labels:
        center = np.mean(xs[labels == l])
        col_centers.append((l, center))
    col_centers.sort(key=lambda x: x[1])
    label_map = {l: i for i, (l, c) in enumerate(col_centers)}
    num_cols = len(unique_labels)

    # 3. Build the grid
    rows = []
    for item in block_structs:
        row_cells = [""] * num_cols
        for seg in item["segments"]:
            # Find which column this segment belongs to
            seg_cx = (seg["x0"] + seg["x1"]) / 2
            # Find closest column center (naive but effective given the clustering)
            closest_lbl = min(unique_labels, key=lambda l: abs(np.mean(xs[labels==l]) - seg_cx))
            col_idx = label_map[closest_lbl]
            
            # Append text (handle overlaps)
            current_text = row_cells[col_idx]
            row_cells[col_idx] = (current_text + " " + seg["text"]).strip()
        rows.append(list(filter(bool, row_cells)))

    # 4. Calculate BBox
    all_x0 = [l["line_obj"]["x0"] for l in block_structs]
    all_y0 = [l["line_obj"]["y0"] for l in block_structs]
    all_x1 = [l["line_obj"]["x1"] for l in block_structs]
    all_y1 = [l["line_obj"]["y1"] for l in block_structs]
    
    bbox = [min(all_x0), min(all_y0), max(all_x1), max(all_y1)]

    return {"rows": rows, "bbox": [round(v, 2) for v in bbox]}

# -------------------------
# High-level pipeline
# -------------------------

def analyze_pdf(pdf_path: str, output_dir: str = "extracted_pdf_assets") -> Dict[str, Any]:
    struct = extract_pdf_structure(pdf_path, output_dir=output_dir)
    for page in struct.get("pages", []):
        spans = page.get("text", [])
        if not spans: continue
        lines = group_spans_to_lines(spans)
        col_labels = detect_columns_from_spans(spans)
        for s, c in zip(spans, col_labels): s["col"] = int(c)
        for ln in lines:
            span_cols = [sp.get("col", 0) for sp in ln.get("spans", [])]
            ln["col"] = int(max(set(span_cols), key=span_cols.count)) if span_cols else 0
        
        # Detect tables FIRST
        tables = detect_tables(lines)
        page["tables"] = tables

        # Exclude table lines from paragraph analysis
        table_line_indices = set()
        for tbl in tables:
            bx0, by0, bx1, by1 = tbl.get("bbox", [0, 0, 0, 0])
            for i, ln in enumerate(lines):
                if (by0 <= ln['cy'] <= by1) and (max(bx0, ln['x0']) < min(bx1, ln['x1'])):
                    table_line_indices.add(i)

        non_table_lines = [ln for i, ln in enumerate(lines) if i not in table_line_indices]
        
        # Group remaining lines into paragraphs per column
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

    # Draw Text Spans (Cyan)
    for t in page.get("text", []):
        x0, y0, x1, y1 = t["bbox"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, linewidth=0.25, edgecolor='cyan', alpha=0.5))

    # Draw Paragraphs (Green)
    for col, paras in page.get("paragraphs_by_col", {}).items():
        for para in paras:
            if not para: continue
            
            # Calculate paragraph bounding box
            all_x0 = [ln['x0'] for ln in para]; all_y0 = [ln['y0'] for ln in para]
            all_x1 = [ln['x1'] for ln in para]; all_y1 = [ln['y1'] for ln in para]
            if not all_x0: continue
            px0, py0, px1, py1 = min(all_x0), min(all_y0), max(all_x1), max(all_y1)
            
            # Draw the Paragraph Box
            ax.add_patch(Rectangle((px0, py0), px1 - px0, py1 - py0, fill=False, edgecolor='green', linewidth=0.8, alpha=0.7))
            
            # Draw the Text
            for ln in para:
                # FIX: removed stale 'x0' variable and corrected alignment
                l_x0, l_y0, _, _ = ln['bbox']
                ax.text(l_x0, l_y0, s=ln['text'], ha='left', va='top', fontsize=6)

    # Draw Tables (Red)
    for tbl in page.get("tables", []):
        bx0, by0, bx1, by1 = tbl.get("bbox", [0, 0, 0, 0])
        ax.add_patch(Rectangle((bx0, by0), bx1 - bx0, by1 - by0, fill=False, edgecolor='red', linewidth=1.2, alpha=0.7))
        
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
