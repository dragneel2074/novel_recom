from flask import Flask, request, jsonify, render_template, json
from main import app
import openai
import requests


def validate_api_key(api_key):
    url = 'https://api.openai.com/v1/models'
    headers = {
        'Authorization': 'Bearer ' + api_key,
    }
    response = requests.get(url, headers=headers)
    print(response)
    return response.status_code == 200


@app.route('/validate-api-key', methods=['POST'])
def validate_api_key_route():
    api_key = request.form.get('apiKey')
    if not validate_api_key(api_key):
        return jsonify(error='Invalid API key'), 401
    return jsonify(success=True)


@app.route('/api-translate')
def translate_page():
    return render_template('translate.html')


def translate_text(user_input, api_key):
    translated_text = None
    print(api_key)
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': 'Bearer ' + api_key,
        'Content-Type': 'application/json'
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful web novel translator that translates web novel chapters to English."},
            {"role": "user", "content": user_input}
        ]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        raise Exception('Failed to translate text')
    translated_text = response.json(
    )['choices'][0]['message']['content'].strip()
    return translated_text


@app.route('/translate', methods=['POST'])
def translate_route():
    try:
        text = request.form.get('text')
        api_key = request.form.get('apiKey')

        if not text:
            return jsonify(error='No text provided'), 400

        if not validate_api_key(api_key):
            return jsonify(error='Invalid API key'), 401

        translated_text = translate_text(text, api_key)
        return jsonify(translated_text=translated_text)
    except Exception as e:
        return jsonify(error=str(e)), 500
