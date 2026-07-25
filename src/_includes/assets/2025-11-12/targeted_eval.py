import argparse
import json
import os
import base64
import requests
import re
from Levenshtein import distance as levenshtein_distance

# --- Configuration ---
LLAMA_SERVER_URL = "https://tellme-gemma.dev.easybits.tech/v1/chat/completions"
IMAGE_DIR = "test_docs" # Directory where your PNG screenshots are saved

# --- THE GOLDEN SET: Specific tests for your files ---
SPECIFIC_FILE_QUESTIONS = [
    # 1. Structured Form Test (Tax Plate)
    {
        "id": "tax_plate_kv",
        "filename": "9054f2bd-e80a-4fd6-b222-835dd7c152a6.pdf",
        "page": 1,
        "type": "key_value_extraction",
        "prompt": "Extract the Tax Identity Number (VERGİ KİMLİK NO) from the document. Return only the number.",
        "ground_truth": "3290637431",
        "output_format": "text"
    },
    # 2. Table Logic Test (UK Gov Doc)
    {
        "id": "uk_gov_table",
        "filename": "uk-gov-doc.pdf",
        "page": 1,
        "type": "table_row_retrieval",
        "prompt": "Look at the table. If the test was originally due in 'August 2020', what is the 'New test due date (12-month extension)'? Return just the date.",
        "ground_truth": "August 2021",
        "output_format": "text"
    },
    # 3. Spatial Reasoning Test (Layout Test)
    {
        "id": "layout_spatial",
        "filename": "layout_test_001.pdf",
        "page": 1,
        "type": "spatial_reasoning",
        "prompt": "Look at the shapes. Is the blue square located above or below the text 'Figure A'?",
        "ground_truth": "below",
        "output_format": "text"
    },
    # 4. Code Extraction Test (Zero Shot Paper)
    {
        "id": "code_extract",
        "filename": "Zero-Shot-Classification.pdf",
        "page": 2, # Page with the first code block
        "type": "entity_list_extraction",
        "prompt": "Extract the Python import statements from the code block. Return them as a JSON list of strings.",
        "ground_truth": '["torch", "copy", "random", "transformers", "torch.utils.data", "datasets", "torch.nn"]',
        "output_format": "json"
    },
    # 5. Tiny Text Test (Invoice)
    {
        "id": "invoice_tiny_text",
        "filename": "invoice_001.pdf",
        "page": 1,
        "type": "small_text_extraction",
        "prompt": "Read the Reference Code at the very bottom of the invoice. Be precise.",
        "ground_truth": "X19-TINY-TEXT-TEST-STRING-98",
        "output_format": "text"
    }
]

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
            base64_image = self.encode_image(image_path)
            messages = []
            
            if system_context:
                messages.append({"role": "system", "content": system_context})

            user_content = [
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
            messages.append({"role": "user", "content": user_content})

            payload = {
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 500,
                "stream": False,
                "seed": 420
            }
            
            if json_mode:
                payload["response_format"] = {"type": "json_object"}

            response = requests.post(self.base_url, json=payload)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']

        except Exception as e:
            print(f"Error calling LLM: {e}")
            return ""

# --- Helper Functions ---
def extract_json_from_text(text):
    try:
        match = re.search(r'(\{|\[).*(\}|\])', text, re.DOTALL)
        if match: return json.loads(match.group(0))
        return json.loads(text)
    except: return None

def calculate_score(ground_truth, response, mode="text"):
    if mode == "json":
        gt_json = extract_json_from_text(str(ground_truth))
        resp_json = extract_json_from_text(response)
        if resp_json is None: return 0.0
        
        # Set comparison for lists
        if isinstance(gt_json, list) and isinstance(resp_json, list):
            gt_set = set(map(str, gt_json))
            resp_set = set(map(str, resp_json))
            if not gt_set: return 0.0
            return len(gt_set.intersection(resp_set)) / len(gt_set.union(resp_set))
        return 1.0 if str(gt_json) == str(resp_json) else 0.0
    else:
        # Text comparison
        clean_gt = re.sub(r'\s+', ' ', str(ground_truth)).strip().lower()
        clean_resp = re.sub(r'\s+', ' ', str(response)).strip().lower()
        dist = levenshtein_distance(clean_gt, clean_resp)
        return 1 - (dist / max(len(clean_gt), len(clean_resp), 1))

def find_document_context(contexts, filename):
    """Finds the doc in grounded_context.json, handling path variations."""
    for doc in contexts:
        # Match if filename is contained in path or vice versa (e.g., "./test_docs/file.pdf" vs "file.pdf")
        doc_path = doc.get('path', '') or doc.get('filename', '')
        if filename in doc_path or doc_path in filename:
            return doc
    return None

# --- Main Loop ---
def run_targeted_evaluation(context_file, output_file):
    print(f"Connecting to Llama Server at: {LLAMA_SERVER_URL}")
    client = LlamaCppClient(LLAMA_SERVER_URL)
    
    # Load grounded context
    try:
        raw_context = json.load(open(context_file, 'r'))
        contexts = [raw_context] if isinstance(raw_context, dict) else raw_context
    except Exception as e:
        print(f"Failed to load context file: {e}")
        return

    results = []
    
    print(f"\nStarting evaluation of {len(SPECIFIC_FILE_QUESTIONS)} specific test cases...\n")

    for i, q in enumerate(SPECIFIC_FILE_QUESTIONS):
        print(f"Test {i+1}: {q['id']} ({q['type']})")
        print(f"Question: {q['prompt']}")
        
        # 1. Resolve Image Path
        # Tries to find: IMAGE_DIR/filename.png (replacing .pdf with .png)
        base_name = os.path.splitext(os.path.basename(q['filename']))[0]
        image_filename = f"{base_name}.png" # Assuming simple mapping
        image_path = os.path.join(IMAGE_DIR, image_filename)
        
        if not os.path.exists(image_path):
            # Fallback: try mapping page number explicitly if using pdf2image output style
            image_path = os.path.join(IMAGE_DIR, f"{base_name}_page_{q['page']}.png")
            if not os.path.exists(image_path):
                print(f"  [SKIP] Image not found: {image_path}")
                continue

        # 2. Resolve Context
        doc_context = find_document_context(contexts, q['filename'])
        if not doc_context:
            print(f"  [SKIP] No JSON context found for {q['filename']}")
            continue
            
        # Get content for specific page
        page_content = next((p['content'] for p in doc_context.get('pages', []) if p['page_number'] == q['page']), [])
        
        # --- RUN METHOD A (Image Only) ---
        print("  -> Running Method A...")
        resp_a = client.generate_response(
            q['prompt'] + (" Respond in JSON." if q['output_format'] == 'json' else ""), 
            image_path, 
            json_mode=(q['output_format'] == 'json')
        )

        # --- RUN METHOD B (Image + JSON) ---
        print("  -> Running Method B...")
        # Context window optimization: Only give relevant tokens
        json_context_str = json.dumps(page_content, indent=2)
        
        # If context is too huge, truncate (naive approach)
        if len(json_context_str) > 15000: 
            json_context_str = json_context_str[:15000] + "\n...[truncated]"

        sys_msg = f"Use this JSON structure to verify your answer:\n{json_context_str}"
        
        resp_b = client.generate_response(
            q['prompt'], 
            image_path, 
            system_context=sys_msg,
            json_mode=(q['output_format'] == 'json')
        )

        # --- SCORING ---
        score_a = calculate_score(q['ground_truth'], resp_a, mode=q['output_format'])
        score_b = calculate_score(q['ground_truth'], resp_b, mode=q['output_format'])
        
        print(f"  -> Result: A={score_a:.2f} | B={score_b:.2f}")
        if score_b > score_a: print("     (Method B Wins)")
        
        results.append({
            "id": q['id'],
            "type": q['type'],
            "prompt": q['prompt'],
            "method_a": {"response": resp_a, "score": score_a},
            "method_b": {"response": resp_b, "score": score_b}
        })

    # Save
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved results to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('context_file', help="Path to grounded_context.json")
    parser.add_argument('--output_file', default='targeted_results.json')
    args = parser.parse_args()
    
    run_targeted_evaluation(args.context_file, args.output_file)
