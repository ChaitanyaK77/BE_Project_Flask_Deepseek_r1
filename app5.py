import json
import re
from flask import Flask, request, jsonify
import ollama
from flask_cors import CORS
from transformers import pipeline
from guardrail import greeting_keywords, thank_you_goodbye_keywords
app = Flask(__name__)
CORS(app)


classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
authors = ["chaitanya","rishab"]


def is_greeting(question):
    question = question.lower()
    if any(greeting in question for greeting in greeting_keywords):
        if not any(keyword in question for keyword in ['border', 'surveillance', 'military', 'patrolling', 'army']):
            return True
    return False
def is_chaitanya_rishab(question):
    question = question.lower()
    if any(keyword in question for keyword in authors):
        if not any(keyword in question for keyword in ['border', 'surveillance', 'military', 'patrolling', 'army']):
            return True
    return False


def is_thank_you_or_goodbye(question):
    question = question.lower()
    if any(keyword in question for keyword in thank_you_goodbye_keywords):
        if not any(keyword in question for keyword in ['border', 'surveillance', 'military', 'patrolling', 'army']):
            return True
    return False


def is_border_related(question):
    candidate_labels = ['border surveillance', 'military', 'security', 'border', 'army', 'patrolling']
    result = classifier(question, candidate_labels)
    print(f"Classification result: {result}")  
    for score in result['scores']:
        if score > 0.5:
            return True
    return False


def format_report(text):
    formatted_text = re.sub(r'\*\*(.*?)\*\*', r'\n\n\1\n\n', text)
    formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)
    return formatted_text.strip()


def save_conversation_history(question, response, rating=None):
    try:
        with open('conversation_history1.json', 'r') as file:
            try:
                history = json.load(file)
            except json.JSONDecodeError:
                history = []
    except FileNotFoundError:
        history = []

    conversation_id = len(history) + 1  

    history.append({"id": conversation_id, "question": question, "response": response, "rating": rating})

    with open('conversation_history1.json', 'w') as file:
        json.dump(history, file, indent=4)

    print("Conversation history saved.")
    return conversation_id  


def remove_think_content(response):
    clean_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    return clean_response


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get("question", "")
    guard_rail = data.get("guardrail")
    if guard_rail:
        if is_greeting(question):
            response = "Hi, I am SeekDeep, a large language model fine-tuned by a bunch of enthusiasts to streamline automatic surveillance and assist with various tasks related to security and monitoring."
            conversation_id = save_conversation_history(question, response, None)
            return jsonify({"id": conversation_id, "answer": response})
        if is_thank_you_or_goodbye(question):
            response = "Thank you for using SeekDeep... Stay Safe."
            conversation_id = save_conversation_history(question, response, None)
            return jsonify({"id": conversation_id, "answer": response})
        if is_chaitanya_rishab(question):
            response="Chaitanya Kakade and Rishab Mandal are the visionary and driving force behind my existence, much like a singular creator who brought me into being. Their leadership and direction at SeekDeep made it possible for me to evolve and function as I do."
            conversation_id = save_conversation_history(question, response, None)
            return jsonify({"id": conversation_id, "answer": response})
        if not is_border_related(question):
            response = "Sorry, please ask border-related questions only. Thank you."
            conversation_id = save_conversation_history(question, response, None)
            return jsonify({"id": conversation_id, "answer": response})
        
            
            
        

        

    
        llm = ollama.chat(model='deepseek-r1:8b', messages=[{"role": "user", "content":  question+"Answer in the previous question and if it is asking  a report then only consider answering the following prompt:Generate a fake border surveillance activity report with random details like drone temperature, time of detection, risk level, location, and previous activity. Location must be from India borders only. It should sound realistic and include random values for temperature, time, weather, and activity and do not use the word 'fake' in it."}])
        response = llm["message"]["content"]
        response = llm["message"]["content"]

    
        cleaned_response = remove_think_content(response)
        cleaned_response = format_report(cleaned_response)

        
        conversation_id = save_conversation_history(question, cleaned_response, None)
        
        return jsonify({"id": conversation_id, "answer": cleaned_response}) 
    else:
        llm = ollama.chat(model='deepseek-r1:8b', messages=[{"role": "user", "content":  question}])
        response = llm["message"]["content"]
        cleaned_response = remove_think_content(response)
        cleaned_response = format_report(cleaned_response)
        conversation_id = save_conversation_history(question, cleaned_response, None)
        return jsonify({"id": conversation_id, "answer": cleaned_response})

@app.route('/rate', methods=['POST'])
def rate():
    data = request.json
    conversation_id = data.get("conversation_id")
    rating = data.get("rating")

    
    try:
        with open('conversation_history1.json', 'r') as file:
            history = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"error": "No conversation history found"}), 400

    
    for conversation in history:
        if conversation["id"] == conversation_id:
            conversation["rating"] = rating
            break
    else:
        return jsonify({"error": "Conversation ID not found"}), 404

    
    with open('conversation_history1.json', 'w') as file:
        json.dump(history, file, indent=4)

    return jsonify({"message": "Rating saved successfully"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
