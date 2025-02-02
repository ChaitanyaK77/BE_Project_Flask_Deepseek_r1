import json
import re
from flask import Flask, request, jsonify
import ollama
from flask_cors import CORS
from transformers import pipeline
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer


app = Flask(__name__)
CORS(app)

'''
model_name = "roberta-large-mnli" 
tokenizer = AutoTokenizer.from_pretrained(model_name)

model = AutoModelForSequenceClassification.from_pretrained(model_name)
'''

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")


greeting_keywords = ["hi", "hello", "hey", "how are you", "good morning", "good evening", "who are you", "what's up", "greetings","hey there"]
thank_you_goodbye_keywords = ["thanks", "thank you", "goodbye", "bye", "see you", "take care", "later"]
def is_greeting(question):
    
    question = question.lower()


    if any(greeting in question for greeting in greeting_keywords):
        
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
    candidate_labels = ['border surveillance', 'military', 'security', 'border','army','patrolling']
    result = classifier(question, candidate_labels)
    
    print(f"Classification result: {result}")  
    
    
    for score in result['scores']:
        if score > 0.5:
            return True
   # seekdeep
   
    return False

import re

def format_report(text):
    
    formatted_text = re.sub(r'\*\*(.*?)\*\*', r'\n\n\1\n\n', text)
    
    
    formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)
    
    return formatted_text.strip()






def save_conversation_history(question, response):
    try:
       
        with open('conversation_history.json', 'r') as file:
            try:
                history = json.load(file)
            except json.JSONDecodeError:
               
                history = []
    except FileNotFoundError:
        
        history = []

   
    history.append({"question": question, "response": response})

   
    with open('conversation_history.json', 'w') as file:
        json.dump(history, file, indent=4)

    print("Conversation history saved.") 


def remove_think_content(response):
   
    clean_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    return clean_response

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get("question", "")
    if is_greeting(question):
        response = "Hi, I am SeekDeep, a large language model fine-tuned by a bunch of enthusiasts to streamline automatic surveillance and assist with various tasks related to security and monitoring."
        save_conversation_history(question, response)
        return jsonify({"answer": response})
    if is_thank_you_or_goodbye(question):
        response = "Thank you for using SeekDeep... Stay Safe."
        save_conversation_history(question, response)
        return jsonify({"answer": response})
    if not is_border_related(question):
        response = "Sorry, please ask border-related questions. Thank you."
        save_conversation_history(question, response)
        return jsonify({"answer": response})
    

   
    llm = ollama.chat(model='deepseek-r1:8b', messages=[{"role": "user", "content": question+"Answer in short the previous question and if it is related giving a report then only consider answering the following prompt:Generate a fake border surveillance activity report with random details like drone temperature, time of detection, risk level, location, and previous activity. Location must be from India borders only. It should sound realistic and include random values for temperature, time, weather, and activity."}])
    response = llm["message"]["content"]
    
   
    cleaned_response = remove_think_content(response)
    cleaned_response = format_report(cleaned_response)
    save_conversation_history(question, cleaned_response)
    
    return jsonify({"answer": cleaned_response})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
