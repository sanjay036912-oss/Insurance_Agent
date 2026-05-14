import json
import sys
import os

from extractor.text_extractor import extract_text
from extractor.regex_extractor import extract_with_regex
from extractor.local_llm import extract_with_local_llm
from validator.validator import validate_fields
from router.router import route_claim


def process_claim(file_path):
    text = extract_text(file_path)
    regex_data = extract_with_regex(text)
    llm_data = extract_with_local_llm(text, regex_data)
    final_data = {**regex_data, **llm_data}
    validation = validate_fields(final_data)
    decision = route_claim(validation)

    return {
        "extractedFields": final_data,
        "missingFields": validation["missing_fields"],
        "recommendedRoute": decision["route"],
        "reasoning": decision["reason"]
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python app.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    result = process_claim(file_path)

    # Print to console
    print("\n=== CLAIM PROCESSING RESULT ===\n")
    print(json.dumps(result, indent=2))

    # Save to JSON file (same name as input, .json extension)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_path = f"outputs/{base_name}_result.json"
    os.makedirs("outputs", exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"\nSaved to: {output_path}")