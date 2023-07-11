from flask import Flask, request, jsonify, render_template, json
from main import app
import openai
import requests
import os

API_URL = os.getenv('API_URL', 'https://api.openai.com/v1')
MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-3.5-turbo-16k')

def validate_api_key(api_key):
    url = f'{API_URL}/models'
    headers = {
        'Authorization': f'Bearer {api_key}',
    }
    response = requests.get(url, headers=headers)
    return response.status_code == 200

@app.route('/validate-api-key', methods=['POST'])
def validate_api_key_route():
    api_key = request.form.get('apiKey')
    if not validate_api_key(api_key):
        return jsonify(error='Invalid API key. Please check your key and try again.'), 401
    return jsonify(success=True)

@app.route('/web-novel-translate')
def translate_page():
    return render_template('translate.html')

def translate_text(user_input, api_key):
    url = f'{API_URL}/chat/completions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Follow the commands: 1. Act as a Professional Web Novel Translator. 2. Translate the chapter to English."},
            {"role": "user", "content": user_input}
        ]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content'].strip()

@app.route('/translate-api', methods=['POST'])
def translate_route():
    try:
        text = request.form.get('text')
        api_key = request.form.get('apiKey')

        if not text:
            return jsonify(error='No text provided. Please provide some text to translate.'), 400

        if not validate_api_key(api_key):
            return jsonify(error='Invalid API key. Please check your key and try again.'), 401

        translated_text = translate_text(text, api_key)
        return jsonify(translated_text=translated_text)
    except requests.HTTPError as http_err:
        return jsonify(error=f'HTTP error occurred: {http_err}'), 500
    except Exception as err:
        return jsonify(error=f'An error occurred: {err}'), 500
