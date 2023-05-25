import os
from flask import Flask, render_template, request, jsonify, flash, redirect,url_for
import random
import pandas as pd
import numpy as np
import pickle
from aws_request_signer import AwsRequestSigner
import requests
import json
import hashlib

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# load the data
novel_list = pickle.load(open('D:/projects/flask - Copy/data/novel_list.pkl', 'rb'))
novel_list['english_publisher'] = novel_list['english_publisher'].fillna('unknown')
print(novel_list.columns)
name_list = novel_list['name'].values
similarity = pickle.load(open('D:/projects/flask - Copy/data/similarity.pkl', 'rb'))

# AWS Configuration
HOST = "webservices.amazon.com"
URI_PATH = "/paapi5/searchitems"
ACCESS_KEY = 'AKIAI2ZWF7R5J7D6P4LQ'
SECRET_KEY = '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'
REGION = "us-east-1"
request_signer = AwsRequestSigner(REGION, ACCESS_KEY, SECRET_KEY, "ProductAdvertisingAPI")

def sign_aws_request(payload):
    payload_hash = hashlib.sha256(json.dumps(payload).encode()).hexdigest()
    headers = {
        "host": HOST,
        "content-type": "application/json; charset=UTF-8",
        "x-amz-target": "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems",
        "content-encoding": "amz-1.0"
    }
    headers.update(request_signer.sign_with_headers("POST", f"https://{HOST}{URI_PATH}", headers, payload_hash))
    return headers

def recommend(novel, start=1, end=10):
    try:
        novel_index = novel_list[novel_list['name'] == novel].index[0]
        distances = similarity[novel_index]
        new_novel_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[start:end]
    except IndexError:
        return None

    recommend_novel = [{'name': novel_list.iloc[i[0]]['name'], 'image_url': novel_list.iloc[i[0]]['image_url'],'english_publisher': novel_list.iloc[i[0]]['english_publisher']} for i in new_novel_list]
    return recommend_novel

def get_amazon_products(keyword):
    payload = {
        "Keywords": keyword,
        "Resources": ["Images.Primary.Large", "ItemInfo.Title"],
        "PartnerTag": "dragneelclub-20",
        "PartnerType": "Associates",
        "Marketplace": "www.amazon.com"
    }
    
    headers = sign_aws_request(payload)
    response = requests.post(f"https://{HOST}{URI_PATH}", headers=headers, json=payload)
    if response.status_code == 200:
        return response.json().get("SearchResult", {}).get("Items", None)
    else:
        return None

@app.route('/', methods=['GET', 'POST'])
def home():
    recommendations = None
    amazon_products = get_amazon_products('harem lit novels')
    selected_novel_name = request.form.get('selected_novel_name') or request.args.get('selected_novel_name') or None

    if request.method == 'POST':
        action = request.form.get('action1') or request.form.get('action2')
        selected_novel_name = request.form.get('selected_novel_name') if request.form.get('selected_novel_name') else 'Mother of Learning'
        if action == '💡 Recommend':
            recommendations = recommend(selected_novel_name)
            if recommendations is None:
        # Option 1: Show an error message to the user where novel is not found in database
                flash("Novel not found in our database. Please try another one.")
                return redirect(url_for('home'))
            recommendation_names = [rec['name'] for rec in recommendations]
            recommendation_images = [rec['image_url'] for rec in recommendations]   
            recommendation_pub = [rec['english_publisher'] for rec in recommendations]

            amazon_products = get_amazon_products(selected_novel_name)
        elif action == '🎲 Random':
            recommendations = [{'name': novel, 'image_url': novel_list[novel_list['name'] == novel]['image_url'].values[0],'english_publisher': novel_list[novel_list['name'] == novel]['english_publisher'].values[0]} for novel in random.sample(list(name_list), 9)]
            # recommendation_names = [rec['name'] for rec in recommendations]
            # recommendation_images = [rec['image_url'] for rec in recommendations]  
            # recommendation_pub = [rec['english_publisher'] for rec in recommendations]
            amazon_products = get_amazon_products('new light novels')
    elif request.method == 'GET':
            # selected_novel_name = request.args.get('selected_novel_name')
            if selected_novel_name:
                selected_novel_name = request.args.get('selected_novel_name') if request.args.get('selected_novel_name') else 'Mother of Learning'
                recommendations = recommend(selected_novel_name)
                if recommendations:
                    recommendation_names = [rec['name'] for rec in recommendations]
                    recommendation_images = [rec['image_url'] for rec in recommendations]
                    recommendation_pub = [rec['english_publisher'] for rec in recommendations]
  
                amazon_products = get_amazon_products(selected_novel_name)
  
    return render_template('index.html', name_list=sorted(name_list), recommendations=recommendations, selected_novel_name=selected_novel_name, amazon_products=amazon_products)


@app.route('/random', methods=['POST'])
def random_selection():
   if request.method == 'POST':
        random_novels = random.sample(list(name_list), 9)
        return jsonify({'recommendations': [{'name': novel, 'image_url': novel_list[novel_list['name'] == novel]['image_url'].values[0],'english_publisher': novel_list[novel_list['name'] == novel]['english_publisher'].values[0]} for novel in random_novels]})
   

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    search = request.args.get('term')
    results = [novel for novel in name_list if search.lower() in novel.lower()]
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)


