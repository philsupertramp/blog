import argparse
import json
import itertools
import random
import base64
import os
import requests
import re
import fitz
from tempfile import TemporaryDirectory
from Levenshtein import distance as levenshtein_distance


# --- Configuration ---
LLAMA_SERVER_URL = "https://tellme-gemma.dev.easybits.tech/v1/chat/completions" 

# --- NEW: Templates for Extraction Tasks ---
QUESTIONS = {
    'spatial_reasoning': [
        {
            "prompt": "Look at the layout. Is the image located above, below, left, or right of the table? Reply with a single word for the direction.",
            "verification_context": "Image bbox: {img}, Table bbox: {tbl}",
            "output_format": "text"
        }
    ],
    # NEW: Extracts a specific value based on a visual label
    'key_value_extraction': [
        {
            "prompt": "Extract the value associated with the label '{key}'. Return ONLY the value as a string.",
            "verification_context": "Visual link between label '{key}' and value '{value}'.",
            "output_format": "text"
        }
    ],
    'negative_constraint': [
        {
            "prompt": "What is the exact text written in the top-left corner margin at coordinates [0, 0, 50, 50]? If empty, reply 'EMPTY'.",
            "verification_context": "No content overlaps with bbox [0,0,50,50]",
            "ground_truth": "empty",
            "output_format": 'text',
        },
        {
            "prompt": "What is the exact text written in the top-left corner? If empty, reply 'EMPTY'.",
            "verification_context": "",
            "ground_truth": "PDF",
            "output_format": 'text',
        },

    ], 
    # NEW: Forces the model to find ALL instances of a type
    'entity_list_extraction': [
        {
            "prompt": "Identify all distinct {entity_type} mentioned in this section. Return them as a JSON list of strings: [\"item1\", \"item2\"].",
            "verification_context": "Recall test for {entity_type}.",
            "output_format": "json"
        }
    ],
    'table_row_retrieval': [
        {
            "prompt": "In the table, find the row where '{name}' is '{key}'. Return the row as a JSON object: {{\"col1\": \"val1\", ...}}.",
            "verification_context": "Row alignment check.",
            "output_format": "json"
        }
    ]
}

# Map your page numbers to actual image files
PAGE_TO_IMAGE_MAP = {
    1: "green-on-green-1.png", 
}

class LlamaCppClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def encode_image(self, image_path):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def generate_response(self, prompt_text, image_path, system_context=None, json_mode=False):
        try:
            base64_image = None
            if image_path is not None:
                base64_image = self.encode_image(image_path)
            messages = []
            
            if system_context:
                messages.append({"role": "system", "content": system_context})

            user_content = [
                {"type": "text", "text": prompt_text},
            ]
            if image_path is not None:
                user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}})
            messages.append({"role": "user", "content": user_content})

            payload = {
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 500,
                "stream": False,
                "seed": 420
            }
            
            # Enable JSON mode if the server supports it (common in llama-cpp)
            if json_mode:
                payload["response_format"] = {"type": "json_object"}

            response = requests.post(self.base_url, json=payload)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']

        except Exception as e:
            print(f"Error calling LLM: {e}")
            return ""

# --- Helper: Parse & Score JSON ---
def extract_json_from_text(text):
    """Attempts to find and parse a JSON object/list inside a text response."""
    try:
        # Find the first '[' or '{' and the last ']' or '}'
        match = re.search(r'(\{|\[).*(\}|\])', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(text) # Try raw text
    except:
        return None

def calculate_score(ground_truth, response, mode="text"):
    """Scores based on mode: 'text' (Levenshtein) or 'json' (Key/Value match)"""
    if mode == "json":
        gt_json = extract_json_from_text(str(ground_truth))
        resp_json = extract_json_from_text(response)
        
        if resp_json is None:
            return 0.0 # Failed to produce JSON
        
        # Simple Intersection over Union for lists/keys
        if isinstance(gt_json, list) and isinstance(resp_json, list):
            gt_set = set(map(str, gt_json))
            resp_set = set(map(str, resp_json))
            if not gt_set: return 0.0
            return len(gt_set.intersection(resp_set)) / len(gt_set.union(resp_set))
            
        # For Objects, compare stringified values
        return 1.0 if str(gt_json) == str(resp_json) else 0.0

    else:
        # Text Mode
        clean_gt = re.sub(r'\s+', ' ', str(ground_truth)).strip().lower()
        clean_resp = re.sub(r'\s+', ' ', str(response)).strip().lower()
        return 1 - (levenshtein_distance(clean_gt, clean_resp) / max(len(clean_gt), len(clean_resp), 1))


def get_relative_position(bbox1, bbox2):
    """Determines if box1 is above/below/left/right of box2"""
    # bbox format: [x1, y1, x2, y2]
    # y-axis usually grows downwards in PDF coordinates, but let's assume standard graphics (0,0 top-left)
    
    # Center points
    c1_x, c1_y = (bbox1[0]+bbox1[2])/2, (bbox1[1]+bbox1[3])/2
    c2_x, c2_y = (bbox2[0]+bbox2[2])/2, (bbox2[1]+bbox2[3])/2
    
    dx = c1_x - c2_x
    dy = c1_y - c2_y
    
    if abs(dy) > abs(dx): # Vertical relationship is stronger
        return "below" if dy > 0 else "above"
    else: # Horizontal relationship is stronger
        return "to the right of" if dx > 0 else "to the left of"


def generate_questions(data):
    questions = []
    filename = data.get("filename", "doc")
    filename_id = filename.split('/')[-1].split('.')[0]
    
    for page in data.get("pages", []):
        p_num = page["page_number"]
        content = page["content"]
        
        tables = [c for c in content if c["type"] == "table"]
        images = [c for c in content if c["type"] == "image"]
        texts = [c for c in content if c["type"] == "text"]
        
        # --- 1. Key-Value Extraction (Visual Linking) ---
        # We look for text lines that might act as labels (short, ending in colon?)
        # For this demo, we simply pick a random short text and ask for it, 
        # but in a real "Form", you'd pick "Total" and expect "$500".
        # We will simulate this by picking a table header and asking for a value.
        for tbl in tables:
            rows = tbl['data'].split('\n')
            if len(rows) > 3:
                header = [h.strip() for h in rows[0].split('|')[1:-1]]
                data_row = [c.strip() for c in rows[3].split('|')[1:-1]]
                
                if len(header) == len(data_row):
                    idx = random.randint(0, len(header)-1)
                    e = random.choice(QUESTIONS['key_value_extraction'])
                    questions.append({
                        "id": f"{filename_id}_p{p_num}_kv",
                        "type": "key_value_extraction",
                        "page": p_num,
                        "prompt": e['prompt'].format(key=header[idx]),
                        "ground_truth": data_row[idx],
                        "output_format": e['output_format'],
                        "content": content,
                    })

        # --- 2. Entity List Extraction ---
        # Example: "Extract all words that start with Capital letters in this bbox"
        # (Simplified for the demo to just return the raw text of a line as a list)
        if texts:
            target_text = random.choice(texts)
            words = target_text['text'].split()
            if len(words) > 3:
                e = random.choice(QUESTIONS['entity_list_extraction'])
                questions.append({
                    "id": f"{filename_id}_p{p_num}_list",
                    "type": "entity_list_extraction",
                    "page": p_num,
                    "prompt": e['prompt'].format(entity_type="words in the specific sentence"),
                    "ground_truth": json.dumps(words),
                    "verification_context": f"Text at {target_text['bbox']}",
                    "output_format": e['output_format'],
                    "content": target_text,
                })
        if images and tables:
            # Limit to avoid exploding question counts
            imgs = random.choices(images, k=min(len(images), 2))
            tbls = random.choices(tables, k=min(len(tables), 2))

            for img, tbl in itertools.product(imgs, tbls):
                rel_pos = get_relative_position(img['bbox'], tbl['bbox'])
                
                # DYNAMICALLY select the correct template based on calculated position
                # If rel_pos is "below", we want a prompt that asks "where is it?" or specifically checks that.
                
                questions.append({
                    "id": f"{filename_id}_p{p_num}_spatial",
                    "type": "spatial_reasoning",
                    "page": p_num,
                    "filename": filename, # Pass filename to help find the image later
                    "prompt": f"Look at the layout. Is the image located above, below, left, or right of the table?",
                    "ground_truth": rel_pos,
                    "verification_context": f"Image bbox: {img['bbox']}, Table bbox: {tbl['bbox']}",
                    "output_format": 'text',
                    "content": content,
                })

        # --- 2. HALLUCINATION TRAP ---
        e = random.choice(QUESTIONS.get('negative_constraint'))
        questions.append({
            "id": f"{filename_id}_p{p_num}_hallucination",
            "type": "negative_constraint",
            "page": p_num,
            "filename": filename,
            "content": content,
            **e
        })

        # --- 3. SMALL TEXT ---
        if texts:
            sorted_text = sorted(texts, key=lambda x: (x['bbox'][3] - x['bbox'][1]))
            # Filter extremely small text only
            valid_small_texts = [t for t in sorted_text if (t['bbox'][3] - t['bbox'][1]) < 15]
            
            if valid_small_texts:
                # Pick one random small text item
                item = random.choice(valid_small_texts)
                height = item['bbox'][3] - item['bbox'][1]
                
                questions.append({
                    "id": f"{filename_id}_p{p_num}_resolution",
                    "type": "small_text_extraction",
                    "page": p_num,
                    "filename": filename,
                    "prompt": f"Read the small text located at {item['bbox']}. Be precise.",
                    "ground_truth": item['text'],
                    "verification_context": f"Smallest text height found: {height}",
                    "content": content,
                    "output_format": 'text'
                })

        # --- 4. TABLE LOGIC ---
        for tbl in tables:
            rows = tbl['data'].split('\n')
            if len(rows) > 3: 
                # Clean rows
                header = [h.strip() for h in rows[0].split('|')[1:-1]]
                # Filter valid data rows (skip header/separator)
                data_rows = [r for r in rows[2:] if '|' in r]
                
                if data_rows:
                    target_row_raw = random.choice(data_rows)
                    target_row = [c.strip() for c in target_row_raw.split('|')[1:-1]]
                    
                    if len(target_row) == len(header):
                        key_col_idx = 0 
                        target_key = target_row[key_col_idx]

                        # Use specific template
                        questions.append({
                            "id": f"{filename_id}_p{p_num}_table_logic",
                            "type": "table_row_retrieval",
                            "page": p_num,
                            "filename": filename,
                            "prompt": f"In the table, find the row where '{header[key_col_idx]}' is '{target_key}'. Return the values for the whole row.",
                            "ground_truth": target_row_raw,
                            "verification_context": "Row alignment check",
                            "content": content,
                            "output_format": 'text'
                        })
    return questions


def convert_from_path(pdf_file):
    # Open the document
    doc = fitz.open(pdf_file)

    files = []
    # Iterate over the pages
    for page_num, page in enumerate(doc):
        # Define the zoom level (Matrix)
        # 2.0 = 2x zoom (roughly 144 dpi). Default is 72 dpi.
        mat = fitz.Matrix(2.0, 2.0) 
    
        # Render the page to an image (pixmap)
        pix = page.get_pixmap(matrix=mat)
    
        # Save the image
        pix.save(f"page-{page_num + 1}.png")
        files.append(f"page-{page_num + 1}.png")

    return files

def run_evaluation(context_file, output_file):
    print(f"Connecting to Llama Server at: {LLAMA_SERVER_URL}")
    client = LlamaCppClient(LLAMA_SERVER_URL)
    
    # Load data (handle list or dict)
    raw = json.load(open(context_file, 'r'))
    contexts = [raw] if isinstance(raw, dict) else raw
    
    results = []

    
    for data in contexts:
        pdf_file = data['filename']
        image_paths = convert_from_path(pdf_file)

        if len(image_paths) != len(data['pages']):
            breakpoint()
        questions = generate_questions(data)
        for i, q in enumerate(questions):
            print(f"\nProcessing Q{i+1} [{q['type']}]: {q['prompt']}")
            
            # Dynamic Image Path
            image_path = image_paths[q['page'] - 1]
            if not image_path or not os.path.exists(image_path):
                print(f"Skipping - Image not found: {image_path}")
                continue
            
            # Method A (Image Only)
            print(" -> Method A...")
            in_a = q['prompt'] + (" Respond in JSON." if q['output_format'] == 'json' else "")
            resp_a = client.generate_response(
                in_a,
                image_path, 
                json_mode=(q['output_format'] == 'json')
            )
            if q['output_format'] == 'json':
                try:
                    resp_a = json.loads(resp_a)
                except:
                    pass
            
            # Method B (Image + JSON)
            print(" -> Method B...")
            # Context snippet
            page_content = q['content']
            json_context = json.dumps(page_content, indent=2) # Limit context size
            sys_msg = f"Use this JSON layout to verify observations:\n{json_context}\n\nRespond to user requests with short precise answers. Do not add additional text to your response."
            
            in_b = f"<system>{sys_msg}</system>\n<user>{q['prompt']}</user>"
            resp_b = client.generate_response(
                q['prompt'], 
                image_path, 
                system_context=sys_msg,
                json_mode=(q['output_format'] == 'json')
            )
            if q['output_format'] == 'json':
                try:
                    resp_b = json.loads(resp_b)
                except:
                    pass
            print(" -> Method C...")
            resp_c = client.generate_response(
                q['prompt'], 
                None, 
                system_context=sys_msg,
                json_mode=(q['output_format'] == 'json')
            )
            if q['output_format'] == 'json':
                try:
                    resp_c = json.loads(resp_c)
                except:
                    pass
            
            # Scoring
            score_a = calculate_score(q['ground_truth'], resp_a, mode=q['output_format'])
            score_b = calculate_score(q['ground_truth'], resp_b, mode=q['output_format'])
            score_c = calculate_score(q['ground_truth'], resp_c, mode=q['output_format'])
            
            print(f" -> Scores: A={score_a:.2f}, B={score_b:.2f}, C={score_c:.2f}")
            
            results.append({
                "id": q['id'],
                "type": q['type'],
                "method_a": {"response": resp_a, "score": score_a, "input": in_a},
                "method_b": {"response": resp_b, "score": score_b, "input": in_b},
                "method_c": {"response": resp_c, "score": score_c, "input": in_b},
                "expected": q['ground_truth']
            })

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('context_file')
    parser.add_argument('--output_file', default='extraction_results.json')
    args = parser.parse_args()
    run_evaluation(args.context_file, args.output_file)
