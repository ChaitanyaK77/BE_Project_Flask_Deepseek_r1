import json
import re
from flask import Flask, request, jsonify
import ollama
from flask_cors import CORS
from transformers import pipeline
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer

app = Flask(__name__)
CORS(app)

# Zero-shot classifier for border-related questions
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

greeting_keywords = ["hi", "hello", "hey", "how are you", "good morning", "good evening", "who are you", "what's up", "greetings", "hey there"]
thank_you_goodbye_keywords = ["thanks", "thank you", "goodbye", "bye", "see you", "take care", "later"]

# Function to check if the question is a greeting
def is_greeting(question):
    question = question.lower()
    if any(greeting in question for greeting in greeting_keywords):
        if not any(keyword in question for keyword in ['border', 'surveillance', 'military', 'patrolling', 'army']):
            return True
    return False

# Function to check if the question is a thank you or goodbye
def is_thank_you_or_goodbye(question):
    question = question.lower()
    if any(keyword in question for keyword in thank_you_goodbye_keywords):
        if not any(keyword in question for keyword in ['border', 'surveillance', 'military', 'patrolling', 'army']):
            return True
    return False

# Function to check if the question is border-related
def is_border_related(question):
    candidate_labels = ['border surveillance', 'military', 'security', 'border', 'army', 'patrolling']
    result = classifier(question, candidate_labels)
    print(f"Classification result: {result}")  
    for score in result['scores']:
        if score > 0.5:
            return True
    return False

# Function to format the response report
import re
def format_report(text):
    formatted_text = re.sub(r'\*\*(.*?)\*\*', r'\n\n\1\n\n', text)
    formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)
    return formatted_text.strip()

# Save conversation history and include rating and id
global conversation_id
def save_conversation_history(question, response, rating=None):
    try:
        with open('conversation_history1.json', 'r') as file:
            try:
                history = json.load(file)
            except json.JSONDecodeError:
                history = []
    except FileNotFoundError:
        history = []

    conversation_id = len(history) + 1  # Auto-incrementing ID

    # Append the conversation with or without a rating
    history.append({"id": conversation_id, "question": question, "response": response, "rating": rating})

    with open('conversation_history1.json', 'w') as file:
        json.dump(history, file, indent=4)

    print("Conversation history saved.")
# Function to remove content inside <think> tags from response
def remove_think_content(response):
    clean_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    return clean_response

# Function to check ratings and trigger fine-tuning if required
def check_and_finetune():
    try:
        with open('conversation_history1.json', 'r') as file:
            history = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return

    # Get high-rated conversations (rating >= 4)
    high_rated_conversations = [conv for conv in history if conv["rating"] >= 4]

    if len(high_rated_conversations) >= 40:
        print(f"✅ Enough high-rated conversations found! Time to fine-tune model with {len(high_rated_conversations)} high-rated responses.")
        # Add fine-tuning logic here (e.g., prepare data and train)
        # For example, you can filter only high-rated conversations to be used for fine-tuning.

        # Clear or reset history after fine-tuning if needed
        # If you want to reset or back-up history after fine-tuning, uncomment the below line:
        # with open('conversation_history1.json', 'w') as file: json.dump([], file, indent=4)
    else:
        print(f"⚠️ Only {len(high_rated_conversations)} high-rated conversations found. Need 40 for fine-tuning.")

# Flask route for chat
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get("question", "")
    
    # Check if the question is a greeting or a thank you/goodbye
    if is_greeting(question):
        response = "Hi, I am SeekDeep, a large language model fine-tuned by a bunch of enthusiasts to streamline automatic surveillance and assist with various tasks related to security and monitoring."
        save_conversation_history(question, response, None)  # No rating yet
        return jsonify({"answer": response})

    if not is_border_related(question):
        response = "Sorry, please ask border-related questions. Thank you."
        save_conversation_history(question, response, None)  # No rating yet
        return jsonify({"answer": response})

    if is_thank_you_or_goodbye(question):
        response = "Thank you for using SeekDeep... Stay Safe."
        save_conversation_history(question, response, None)  # No rating yet
        return jsonify({"answer": response})

    # Get the response from Ollama LLM
    llm = ollama.chat(model='deepseek-r1:8b', messages=[{"role": "user", "content": question+"Generate a fake border surveillance activity report..."}])
    response = llm["message"]["content"]

    # Clean and format the response
    cleaned_response = remove_think_content(response)
    cleaned_response = format_report(cleaned_response)

    # Save the conversation with no rating yet
    save_conversation_history(question, cleaned_response, None)
    conversation_id=1
    return jsonify({"id": conversation_id, "answer": response})
@app.route('/rate', methods=['POST'])
def rate():
    data = request.json
    conversation_id = data.get("conversation_id")
    rating = data.get("rating")

    # Load the conversation history
    try:
        with open('conversation_history1.json', 'r') as file:
            history = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"error": "No conversation history found"}), 400

    # Find the conversation by ID
    for conversation in history:
        if conversation["id"] == conversation_id:
            conversation["rating"] = rating
            break
    else:
        return jsonify({"error": "Conversation ID not found"}), 404

    # Save the updated conversation history
    with open('conversation_history1.json', 'w') as file:
        json.dump(history, file, indent=4)

    return jsonify({"message": "Rating saved successfully"})
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
