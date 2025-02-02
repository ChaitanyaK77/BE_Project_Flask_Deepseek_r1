import json

def extract_high_rated_conversations(file_path="conversation_history1.json", min_rating=4):
    try:
        with open(file_path, 'r') as file:
            history = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("No valid conversation history found.")
        return []

    processed_ids = set()
    high_rated = []
    for entry in history:
        if isinstance(entry.get("rating"), int) and entry["rating"] >= min_rating and entry["id"] not in processed_ids:
            high_rated.append({"prompt": entry["question"], "response": entry["response"]})
            processed_ids.add(entry["id"])

    with open("high_rated_dataset.json", "w") as file:
        json.dump(high_rated, file, indent=4)

    print(f"Extracted {len(high_rated)} high-rated conversations.")
    return high_rated

extract_high_rated_conversations()
import json

def convert_to_alpaca_format(input_file="high_rated_dataset.json", output_file="alpaca_format_dataset.json"):
    try:
        with open(input_file, 'r') as file:
            high_rated = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("No valid high-rated conversation history found.")
        return []

    alpaca_format = []
    for entry in high_rated:
        alpaca_format.append({
            "instruction": entry["prompt"],  # Use the prompt as the instruction
            "input": "",  # You can leave this empty or add additional context if available
            "output": entry["response"]  # Use the response as the output
        })

    with open(output_file, "w") as file:
        json.dump(alpaca_format, file, indent=4)

    print(f"Converted {len(alpaca_format)} conversations to Alpaca Instruct format.")
    return alpaca_format

convert_to_alpaca_format()