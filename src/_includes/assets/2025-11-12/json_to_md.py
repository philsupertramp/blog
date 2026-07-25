import json
import os
import argparse

def transform_for_vision_llm(input_data):
    """
    Transforms raw PDF JSON into a clean, grounded structure for Vision LLMs.
    """
    
    # If input is a string, parse it; otherwise assume it's a dict
    if isinstance(input_data, str):
        data = json.loads(input_data)
    else:
        data = input_data

    transformed_doc = {
        "filename": data.get("path", "unknown_file"),
        "total_pages": len(data.get("pages", [])),
        "pages": []
    }

    for page in data.get("pages", []):
        page_width = page.get("width")
        page_height = page.get("height")
        
        structured_page = {
            "page_number": page.get("page_number"),
            "dimensions": [int(page_width), int(page_height)],
            "content": []
        }

        # 1. Process Tables (High Priority for grounding)
        # We define tables first so we can potentially filter out text that exists inside tables
        # to avoid duplication (optional, but recommended).
        table_bboxes = []
        for table in page.get("tables", []):
            bbox = [int(n) for n in table.get("bbox", [0,0,0,0])]
            table_bboxes.append(bbox)
            
            # Convert table rows to Markdown format
            md_table = _json_rows_to_markdown(table.get("rows", []))
            
            structured_page["content"].append({
                "type": "table",
                "bbox": bbox,
                "format": "markdown",
                "data": md_table
            })

        # 2. Process Images
        for img in page.get("images", []):
            structured_page["content"].append({
                "type": "image",
                "bbox": [int(n) for n in img.get("bbox", [0,0,0,0])],
                "source_filename": img.get("filename", "embedded")
            })

        # 3. Process Text Lines
        # We prefer 'lines' over 'text' spans because they are pre-assembled.
        for line in page.get("lines", []):
            line_bbox = [int(n) for n in line.get("bbox", [0,0,0,0])]
            
            # Simple collision detection: If this text line is inside a table we already processed,
            # we might want to skip it to reduce noise. 
            # (Logic: Center point of line is inside a table bbox)
            cx = line.get("cx", line_bbox[0])
            cy = line.get("cy", line_bbox[1])
            
            is_inside_table = False
            for t_box in table_bboxes:
                if (t_box[0] <= cx <= t_box[2]) and (t_box[1] <= cy <= t_box[3]):
                    is_inside_table = True
                    break
            
            if not is_inside_table:
                structured_page["content"].append({
                    "type": "text",
                    "bbox": line_bbox,
                    "text": line.get("text", "").strip()
                })
        structured_page['content'] = sorted(
            structured_page['content'],
            key=lambda x: x['bbox'][1]
        )

        transformed_doc["pages"].append(structured_page)

    return transformed_doc

def _json_rows_to_markdown(rows):
    """Helper to convert list of lists into a Markdown table string."""
    if not rows:
        return ""
    
    try:
        # headers are usually the first row
        headers = rows[0]
        # Determine if headers are valid strings
        clean_headers = [str(h).replace("\n", " ") for h in headers]
        
        md_lines = []
        # Header row
        md_lines.append("| " + " | ".join(clean_headers) + " |")
        # Separator row
        md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # Body rows
        for row in rows[1:]:
            clean_row = [str(cell).replace("\n", " ") if cell is not None else "" for cell in row]
            md_lines.append("| " + " | ".join(clean_row) + " |")
            
        return "\n".join(md_lines)
    except Exception:
        return "Error generating table content"

# --- Usage Example ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_filename', default='pdf_structure.json')

    args = parser.parse_args()
    # Ensuring the script can be run if the json file is local
    input_filename = args.input_filename
    
    if os.path.exists(input_filename):
        with open(input_filename, 'r') as f:
            raw_json = json.load(f)
            
        clean_output = transform_for_vision_llm(raw_json)
        
        # Output to console or save to new file
        print(json.dumps(clean_output, indent=2))
        data = [clean_output]
       
        if os.path.exists('grounded_context.json'):
            with open("grounded_context.json", "r") as f:
                data = json.load(f)

            elem = [e for e in data if e['filename'] == clean_output['filename']]
            data = [e for e in data if e['filename'] != clean_output['filename']]
            data.append(clean_output)

        # Save for use
        with open("grounded_context.json", "w") as f:
            json.dump(data, f, indent=2)
        print(f"\nTransformation complete. Saved to grounded_context.json")
    else:
        print("File not found. Please ensure the JSON file is in the directory.")
