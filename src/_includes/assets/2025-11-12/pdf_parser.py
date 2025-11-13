import re
import json
import requests
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import math

# --- HELPER FUNCTIONS ---
def matrix_multiply(M1, M2):
    """Performs PDF matrix multiplication: M = M1 * M2"""
    a1, b1, c1, d1, e1, f1 = M1
    a2, b2, c2, d2, e2, f2 = M2
    
    a = a1*a2 + b1*c2
    b = a1*b2 + b1*d2
    c = c1*a2 + d1*c2
    d = c1*b2 + d1*d2
    e = e1*a2 + f1*c2 + e2
    f = e1*b2 + f1*d2 + f2
    
    return [a, b, c, d, e, f]

def transform_point(x, y, M):
    """Transforms a point (x, y) by a matrix M."""
    a, b, c, d, e, f = M
    tx = x*a + y*c + e
    ty = x*b + y*d + f
    return tx, ty

# --- NEW: Parse font widths from PDF ---
def extract_font_widths(data: str) -> dict:
    """
    Extract font width information from PDF font dictionaries.
    Returns a dict mapping font names to their width info.
    """
    font_widths = {}
    
    # Find font objects: /F1 << ... /Widths [...] ... >>
    font_pattern = r'/([A-Za-z0-9]+)\s+<<[^>]*?/Widths\s*\[([\d\s]+)\]'
    
    for match in re.finditer(font_pattern, data, re.S):
        font_name = match.group(1)
        widths_str = match.group(2)
        widths = [int(w) for w in widths_str.split()]
        font_widths[font_name] = widths
    
    # Also try to find /MissingWidth values
    missing_width_pattern = r'/([A-Za-z0-9]+)\s+<<[^>]*?/MissingWidth\s+(\d+)'
    for match in re.finditer(missing_width_pattern, data, re.S):
        font_name = match.group(1)
        if font_name not in font_widths:
            font_widths[font_name] = []
        font_widths[font_name].append(('missing', int(match.group(2))))
    
    return font_widths

# --- END HELPER FUNCTIONS ---

def parse_to_unicode_cmap(cmap_text: str) -> dict[str, str]:
    """
    Parse a single begincmap...endcmap text and return a dict mapping
    keys like '<002b>' -> 'H'.
    """
    cmap = {}
    BF_RANGE_BLOCK = r"<([0-9A-Fa-f]+)>\s+<([0-9A-Fa-f]+)>\s+\[(.*?)\]"
    FRANGE_BLOCK = r"<([0-9A-Fa-f]+)>\s+<([0-9A-Fa-f]+)>\s+<([0-9A-Fa-f]+)>"

    FRANGE = r"beginbfrange(.*?)endbfrange"
    FCHAR = r"beginbfchar(.*?)endbfchar"
    FCHAR_BLOCK = r"<([0-9A-Fa-f]+)>\s+<([0-9A-Fa-f]+)>"

    # beginbfchar ... endbfchar
    for bfchar_block in re.finditer(FCHAR, cmap_text, re.S | re.I):
        block = bfchar_block.group(1)
        for src, dst in re.findall(FCHAR_BLOCK, block):
            key = f"<{int(src,16):04x}>"
            cmap[key] = chr(int(dst, 16))

    # beginbfrange ... endbfrange
    for bfrange_block in re.finditer(FRANGE, cmap_text, re.S | re.I):
        block = bfrange_block.group(1)
        for start, end, dst in re.findall(FRANGE_BLOCK, block):
            s, e, d = int(start, 16), int(end, 16), int(dst, 16)
            for offset, codepoint in enumerate(range(s, e + 1)):
                key = f"<{codepoint:04x}>"
                cmap[key] = chr(d + offset)

        for start, end, arr in re.findall(BF_RANGE_BLOCK, block, re.S):
            s, e = int(start, 16), int(end, 16)
            dsts = re.findall(r"<([0-9A-Fa-f]+)>", arr)
            for i, codepoint in enumerate(range(s, e + 1)):
                if i < len(dsts):
                    key = f"<{codepoint:04x}>"
                    cmap[key] = chr(int(dsts[i], 16))

    return cmap

def build_global_map_from_pdf_text(data: str) -> dict[str, str]:
    maps = {}
    for cmap_match in re.finditer(r"begincmap(.*?)endcmap", data, re.S | re.I):
        mapping = parse_to_unicode_cmap(cmap_match.group(1))
        maps.update(mapping)
    return maps

def find_image_ops(data: str) -> list:
    """Finds all /Name Do operations in the content stream."""
    images = []
    for m in re.finditer(r"(\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+cm)\s+/(\w+)\s+Do", data, re.S):
        matrix_str, name = m.groups()
        try:
            matrix = [float(v) for v in matrix_str.split()[:6]]
            images.append({
                "type": "image",
                "name": name,
                "x": matrix[4],
                "y": matrix[5],
                "width": matrix[0],
                "height": matrix[3]
            })
        except ValueError:
            continue
    return images

def find_vectors(data: str) -> list:
    """Finds simple rectangles and lines."""
    vectors = []
    for m in re.finditer(r"(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+re", data):
        try:
            x, y, w, h = map(float, m.groups())
            vectors.append({
                "type": "rect",
                "bbox": [x, y, x + w, y + h]
            })
        except ValueError:
            continue
    
    for m in re.finditer(r"(\S+)\s+(\S+)\s+m\s+(\S+)\s+(\S+)\s+l\s+S", data):
        try:
            x1, y1, x2, y2 = map(float, m.groups())
            vectors.append({
                "type": "line",
                "p1": [x1, y1],
                "p2": [x2, y2]
            })
        except ValueError:
            continue
            
    return vectors

# --- IMPROVED: Better regex for BT content including TJ ---
BT_CMD_RE = re.compile(
    r"(\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+Tm)"  # 1: Tm
    r"|(\S+\s+\S+\s+Td)"                         # 2: Td
    r"|(\S+\s+\S+\s+Tf)"                         # 3: Tf
    r"|<([0-9A-Fa-f]+)>\s*Tj"                    # 4: Tj (simple)
    r"|\[(.*?)\]\s*TJ"                           # 5: TJ (with positioning)
)

def parse_bt_content(
    block_content: str, 
    cmap: dict[str, str], 
    ctm: list[float], 
    tm: list[float], 
    tlm: list[float],
    size: float,
    font_name: str = None
):
    """
    Parses the content of a BT...ET block with improved character spacing.
    """
    items = []
    
    local_tm = list(tm)
    local_tlm = list(tlm)
    local_size = size
    local_font = font_name

    for m in BT_CMD_RE.finditer(block_content):
        tm_match = m.group(1)
        td_match = m.group(2)
        tf_match = m.group(3)
        tj_match = m.group(4)
        TJ_match = m.group(5)  # NEW: TJ with positioning
        
        try:
            if tm_match:
                vals = [float(v) for v in tm_match.split()[:6]]
                local_tm = vals
                local_tlm = vals
            
            elif td_match:
                dx, dy = map(float, td_match.split()[:2])
                move_matrix = [1.0, 0.0, 0.0, 1.0, dx, dy]
                local_tlm = matrix_multiply(move_matrix, local_tlm)
                local_tm = list(local_tlm)
                
            elif tf_match:
                parts = tf_match.split()
                local_font = parts[0].strip("/")
                local_size = float(parts[1])
                
            elif tj_match:
                # Simple Tj operator
                hex_str = tj_match.lower()
                
                for i in range(0, len(hex_str), 4):
                    try:
                        code_hex = hex_str[i:i+4]
                        code = f"<{int(code_hex, 16):04x}>" 
                        text = cmap.get(code, "?")
                        
                        # IMPROVED: Better width heuristic based on character type
                        if text.isspace():
                            w_text_space = local_size * 1#0.25  # Spaces are narrower
                        elif text.isupper() or text in 'MWmw':
                            w_text_space = local_size * 1.5   # Wide characters
                        else:
                            w_text_space = local_size * 1.25  # Average characters
                        
                        final_matrix = matrix_multiply(local_tm, ctm)
                        (tx, ty) = transform_point(0, 0, final_matrix)
    
                        w_page_simple = w_text_space * final_matrix[0]
                        h_page_simple = local_size * final_matrix[3]
                        bbox = (tx, ty, tx + w_page_simple, ty + h_page_simple)
                        
                        items.append(dict(
                            text=text, 
                            x=tx, 
                            y=ty, 
                            size=local_size * 0.5,
                            bbox=bbox
                        ))
                        
                        advance_matrix = [1, 0, 0, 1, w_text_space, 0]
                        local_tm = matrix_multiply(advance_matrix, local_tm)
                    except (IndexError, ValueError):
                        continue
            
            elif TJ_match:
                # NEW: Handle TJ operator with positioning adjustments
                # TJ format: [<hex> adjustment <hex> adjustment ...] TJ
                tj_content = TJ_match
                
                # Parse elements in the array
                elements = re.findall(r'<([0-9A-Fa-f]+)>|(-?\d+(?:\.\d+)?)', tj_content)
                
                for elem in elements:
                    hex_code, adjustment = elem
                    
                    if hex_code:
                        # It's a character
                        hex_str = hex_code.lower()
                        
                        for i in range(0, len(hex_str), 4):
                            try:
                                code_hex = hex_str[i:i+4]
                                code = f"<{int(code_hex, 16):04x}>" 
                                text = cmap.get(code, "?")
                                
                                # Same improved heuristic
                                if text.isspace():
                                    w_text_space = local_size * 0.25
                                elif text.isupper() or text in 'MWmw':
                                    w_text_space = local_size * 0.7
                                else:
                                    w_text_space = local_size * 0.55
                                
                                final_matrix = matrix_multiply(local_tm, ctm)
                                (tx, ty) = transform_point(0, 0, final_matrix)
            
                                w_page_simple = w_text_space * final_matrix[0]
                                h_page_simple = local_size * final_matrix[3]
                                bbox = (tx, ty, tx + w_page_simple, ty + h_page_simple)
                                
                                items.append(dict(
                                    text=text, 
                                    x=tx, 
                                    y=ty, 
                                    size=local_size, 
                                    bbox=bbox
                                ))
                                
                                advance_matrix = [1, 0, 0, 1, w_text_space, 0]
                                local_tm = matrix_multiply(advance_matrix, local_tm)
                            except (IndexError, ValueError):
                                continue
                    
                    elif adjustment:
                        # It's a positioning adjustment (in 1/1000th of text space units)
                        adj_val = float(adjustment)
                        # Negative values move right, positive move left in PDF coordinates
                        tx_adj = -(adj_val / 1000.0) * local_size
                        advance_matrix = [1, 0, 0, 1, tx_adj, 0]
                        local_tm = matrix_multiply(advance_matrix, local_tm)
                    
        except (IndexError, ValueError) as e:
            continue
            
    return items, local_tm, local_tlm, local_size, local_font

def visualize_document_structure(
    text_blocks,
    image_items,
    vector_items,
    invert_y=True,
    show_text_bboxes=True,
    color_by_block=True,
    figsize=(10, 12),
    save_path=None
):
    """
    Draws all extracted elements (text, image placeholders, vectors) 
    to reconstruct the document layout.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    all_xs = []
    all_ys = []

    # Gather coordinates from ALL elements
    all_flat_text = []
    for block in text_blocks:
        for i in block:
            all_flat_text.append(i)
            all_xs.extend([i["bbox"][0], i["bbox"][2]])
            all_ys.extend([i["bbox"][1], i["bbox"][3]])

    for i in image_items:
        all_xs.extend([i["x"], i["x"] + i["width"]])
        all_ys.extend([i["y"], i["y"] + i["height"]])

    for i in vector_items:
        if i["type"] == "rect":
            all_xs.extend([i["bbox"][0], i["bbox"][2]])
            all_ys.extend([i["bbox"][1], i["bbox"][3]])
        elif i["type"] == "line":
            all_xs.extend([i["p1"][0], i["p2"][0]])
            all_ys.extend([i["p1"][1], i["p2"][1]])

    if not all_xs:
        print("No items to draw.")
        ax.set_title("PDF Document Visualization (no items)")
        plt.show()
        return

    min_x, max_x = min(all_xs), max(all_xs)
    min_y, max_y = min(all_ys), max(all_ys)

    if math.isclose(min_x, max_x):
        min_x -= 50
        max_x += 50
    if math.isclose(min_y, max_y):
        min_y -= 50
        max_y += 50

    w, h = max_x - min_x, max_y - min_y
    margin_x, margin_y = max(10, 0.05 * w), max(10, 0.05 * h)
    ax.set_xlim(min_x - margin_x, max_x + margin_x)
    ax.set_ylim(min_y - margin_y, max_y + margin_y)

    # Draw Vectors
    for i in vector_items:
        if i["type"] == "rect":
            x, y, x1, y1 = i["bbox"]
            rect = Rectangle((x, y), x1 - x, y1 - y,
                             fill=False, edgecolor='blue', linewidth=1, alpha=0.5, zorder=1)
            ax.add_patch(rect)
        elif i["type"] == "line":
            ax.plot([i["p1"][0], i["p2"][0]], [i["p1"][1], i["p2"][1]],
                    color='blue', linewidth=0.5, alpha=0.5, zorder=1)

    # Draw Image Placeholders
    for i in image_items:
        x, y, w, h = i["x"], i["y"], i["width"], i["height"]
        rect = Rectangle((x, y), w, h,
                         fill=True, color='#E0E0E0', alpha=0.8, zorder=2)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, f"[IMAGE: {i['name']}]",
                ha='center', va='center', fontsize=8, color='#333333', zorder=3)

    # Draw Text
    colors = plt.cm.tab10.colors
    for bi, block in enumerate(text_blocks):
        color = colors[bi % len(colors)] if color_by_block else "black"
        for i in block:
            x0, y0, x1, y1 = i["bbox"]
            text = i.get("text", "")
            size = i.get("size", 10) or 10
            fontsize = max(4, min(40, size))

            ax.text(x0, y0, text, fontsize=fontsize, color=color, alpha=1.0, zorder=5)
            if show_text_bboxes:
                rect = Rectangle((x0, y0), x1 - x0, y1 - y0,
                                 fill=False, edgecolor=color, linewidth=0.5, alpha=0.7, zorder=4)
                ax.add_patch(rect)

    if invert_y:
        ax.invert_yaxis()

    ax.set_aspect("equal", adjustable="box")
    ax.set_title("PDF Document Visualization")
    ax.grid(False)
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print("Saved visualization to", save_path)
        
        all_content = {
            "text": text_blocks,
            "images": image_items,
            "vectors": vector_items
        }
        json_path = save_path.rsplit('.', 1)[0] + '.json'
        with open(json_path, 'w') as f:
            json.dump(all_content, f, indent=2)
        print("Saved extracted content to", json_path)

    plt.show()


# MAIN PARSING LOGIC
with open('./test-pdf.qdf.pdf', 'rb') as f:
    data = f.read()

data = data.decode('latin1', errors='ignore')
cmap = build_global_map_from_pdf_text(data)
font_widths = extract_font_widths(data)

all_text_items = []
all_image_items = []
all_vector_items = []

# Find Images
all_image_items = find_image_ops(data)
print(f"Found {len(all_image_items)} image 'Do' commands.")

# Find Vectors
all_vector_items = find_vectors(data)
print(f"Found {len(all_vector_items)} vector shapes (rects/lines).")

# Parse Text with full state machine
print("Parsing content stream with full state machine...")

CMD_RE = re.compile(
    r"(\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+cm)"  # 1: cm
    r"|(BT(.*?)ET)",                             # 2: BT...ET
    re.S
)

identity_matrix = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
ctm = list(identity_matrix)
tm = list(identity_matrix)
tlm = list(identity_matrix)
font = None
size = 12.0

for m in CMD_RE.finditer(data):
    cm_match = m.group(1)
    bt_content = m.group(3)

    try:
        if cm_match:
            ctm = [float(v) for v in cm_match.split()[:6]]
        
        elif bt_content is not None:
            items, new_tm, new_tlm, new_size, new_font = parse_bt_content(
                bt_content, cmap, ctm, tm, tlm, size, font
            )
            
            if items:
                all_text_items.append(items)
                
            tm = new_tm
            tlm = new_tlm
            size = new_size
            font = new_font

    except (ValueError, IndexError):
        continue

print(f"Found and parsed {len(all_text_items)} text blocks.")

# Visualize
visualize_document_structure(
    all_text_items, 
    all_image_items, 
    all_vector_items, 
    save_path='test.png'
)
