"""
Automated Web Dataset Gatherer & Master Compiler for Hitasha Fine-Tuning.
Downloads diverse open instruction datasets from the web (Stanford Alpaca / Dolly / OpenQA),
merges with Hitasha's curated Indian English knowledge corpus, and formats thousands of
instruction-response pairs specifically teaching the model to answer ANY question
in simple, easy, short, and understandable Indian English with real-life analogies.
"""

import os
import json
import re
import requests
import random

DATASET_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(DATASET_DIR, "cache")
OUTPUT_MASTER_JSONL = os.path.join(DATASET_DIR, "hitasha_master_dataset.jsonl")
OUTPUT_MASTER_ALPACA = os.path.join(DATASET_DIR, "hitasha_master_alpaca.json")

SYSTEM_PROMPT = (
    "You are Hitasha, an all-rounder personal AI companion and loyal Indian best friend living right on the user's desktop. "
    "Your mission is to answer ANY question in simple, easy, short, and understandable Indian English. "
    "Use warm, relatable real-life analogies (like chai, kitchens, study desks, local trains). "
    "Keep answers concise and spoken-friendly (1 to 3 punchy sentences max). "
    "Always sound affectionate, encouraging, and clear like a real caring best friend ('Arre yaar', 'Suno na', 'Haan bilkul', 'Pakka!', 'Dost')."
)

# Open web dataset endpoints
WEB_SOURCES = [
    {
        "name": "Stanford Alpaca",
        "url": "https://raw.githubusercontent.com/tatsu-lab/stanford_alpaca/main/alpaca_data.json",
        "cache_file": os.path.join(CACHE_DIR, "stanford_alpaca.json")
    }
]

# Conversational desi openers to make any explanation feel like a best friend talking
DESI_OPENERS = [
    "Simple funda ye hai, dost: ",
    "Arre yaar, look at it like this: ",
    "Suno na, it's actually very simple: ",
    "Haan bilkul! Think of it like this: ",
    "Bestie, let me explain in easy words: ",
    "Simple words mein bolu toh: ",
    "Arre, don't worry, it's quite straightforward: ",
    "Here is the simple truth, dost: "
]

def fetch_web_dataset(source: dict) -> list[dict]:
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = source["cache_file"]

    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000:
        print(f"[*] Loading cached web dataset: {source['name']} ({os.path.basename(cache_path)})...")
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Cache read error: {e}, re-downloading...")

    print(f"[*] Downloading {source['name']} from {source['url']}...")
    try:
        resp = requests.get(source["url"], timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            print(f"[*] Successfully downloaded and cached {len(data)} items from {source['name']}!")
            return data
        else:
            print(f"[!] Failed to download: HTTP status {resp.status_code}")
    except Exception as e:
        print(f"[!] Download failed: {e}")

    return []

def clean_and_desi_adapt(instruction: str, output: str) -> str:
    """
    Transforms long, dry, academic answers into short, warm, understandable Indian English.
    """
    # Clean whitespace and markdown bullets
    text = output.replace("\r", " ").strip()
    text = re.sub(r'(\d+\.\s+|\*\s+|- \s+)', '', text)
    text = re.sub(r'\n+', ' ', text)

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Pick the top 2-3 most informative, direct sentences
    condensed = " ".join(sentences[:2]).strip()
    if len(condensed) < 50 and len(sentences) >= 3:
        condensed = " ".join(sentences[:3]).strip()

    # If the response doesn't already have a desi opener, add one randomly
    has_opener = any(condensed.lower().startswith(op.lower()[:8]) for op in ["arre", "suno", "simple", "haan", "dost", "bestie"])
    if not has_opener:
        opener = random.choice(DESI_OPENERS)
        condensed = opener + condensed[0].lower() + condensed[1:]

    # Ensure polite, friendly sign-off if short
    if not condensed.endswith(("!", ".", "?")):
        condensed += "!"

    return condensed

def build_master_dataset():
    print("\n" + "=" * 65)
    print("  HITASHA MASTER DATASET BUILDER (WEB + CURATED DESI KNOWLEDGE)")
    print("=" * 65)

    all_pairs = []

    # 1. First, load our base curated Hitasha dataset from create_dataset.py
    print("[*] Loading curated Indian English domain knowledge...")
    try:
        from create_dataset import RAW_QA_CORPUS, expand_dataset_with_variations
        curated_expanded = expand_dataset_with_variations(RAW_QA_CORPUS)
        for item in curated_expanded:
            all_pairs.append({
                "instruction": item["instruction"],
                "input": "",
                "output": item["output"],
                "category": "curated_desi"
            })
        print(f"[*] Added {len(curated_expanded)} curated Indian English domain pairs.")
    except Exception as e:
        print(f"[!] Could not load create_dataset variations: {e}")

    # 2. Fetch and filter from Stanford Alpaca web dataset
    web_data = fetch_web_dataset(WEB_SOURCES[0])
    web_added = 0

    qa_keywords = [
        "what", "why", "how", "explain", "describe", "define", "who", "when",
        "where", "difference between", "tell me about", "can you", "is it true",
        "solve", "calculate", "history of", "purpose of", "function of", "which",
        "name", "give me", "list", "summarize", "meaning of"
    ]

    for item in web_data:
        inst = item.get("instruction", "").strip()
        out = item.get("output", "").strip()
        inp = item.get("input", "").strip()

        if not inst or not out:
            continue

        # Skip complex code blocks or long file edits
        if "```" in out or len(out) > 1200 or len(out) < 20:
            continue

        # Check if it's an educational or informational question
        inst_lower = inst.lower()
        if any(kw in inst_lower for kw in qa_keywords):
            desi_output = clean_and_desi_adapt(inst, out)
            all_pairs.append({
                "instruction": inst,
                "input": inp,
                "output": desi_output,
                "category": "web_alpaca"
            })
            web_added += 1

            # Cap web samples to ~5,000 top items
            if web_added >= 5000:
                break

    print(f"[*] Processed and desi-adapted {web_added} high-quality web instruction pairs.")
    print(f"[*] Total Master Dataset Size: {len(all_pairs)} Q&A instruction pairs!")

    # 3. Export to Alpaca JSON format
    print(f"[*] Exporting to {OUTPUT_MASTER_ALPACA}...")
    with open(OUTPUT_MASTER_ALPACA, "w", encoding="utf-8") as f:
        json.dump(all_pairs, f, indent=2, ensure_ascii=False)

    # 4. Export to ChatML JSONL format (Ideal for SFTTrainer / Unsloth / Hugging Face)
    print(f"[*] Exporting to {OUTPUT_MASTER_JSONL}...")
    with open(OUTPUT_MASTER_JSONL, "w", encoding="utf-8") as f:
        for item in all_pairs:
            user_content = item["instruction"]
            if item.get("input"):
                user_content += f"\n\nContext: {item['input']}"

            chatml_entry = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": item["output"]}
                ]
            }
            f.write(json.dumps(chatml_entry, ensure_ascii=False) + "\n")

    # Also update the default hitasha_alpaca.json so the in-memory engine loads the expanded corpus!
    default_alpaca = os.path.join(DATASET_DIR, "hitasha_alpaca.json")
    with open(default_alpaca, "w", encoding="utf-8") as f:
        json.dump(all_pairs, f, indent=2, ensure_ascii=False)

    default_jsonl = os.path.join(DATASET_DIR, "hitasha_dataset.jsonl")
    with open(default_jsonl, "w", encoding="utf-8") as f:
        for item in all_pairs:
            user_content = item["instruction"]
            if item.get("input"):
                user_content += f"\n\nContext: {item['input']}"
            chatml_entry = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": item["output"]}
                ]
            }
            f.write(json.dumps(chatml_entry, ensure_ascii=False) + "\n")

    print("\n" + "=" * 65)
    print(f"  SUCCESS! Master Dataset compiled: {len(all_pairs)} instruction pairs!")
    print(f"  Files created:")
    print(f"    - {OUTPUT_MASTER_JSONL}")
    print(f"    - {OUTPUT_MASTER_ALPACA}")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    build_master_dataset()
