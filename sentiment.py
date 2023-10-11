from flask import Flask, request, render_template
import pickle
import os
import praw
import torch
from transformers import RobertaTokenizer, RobertaForSequenceClassification
import nltk
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords
import spacy
import string
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from main import app


def save_data(data, filename):
    with open(filename, 'wb') as file:
        pickle.dump(data, file)


def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'rb') as file:
            return pickle.load(file)
    else:
        return None


# PRAW configs
REDDIT_CLIENT_ID = "lI0C_W9_eESoiS2mtUMNDg"
REDDIT_CLIENT_SECRET = "IK1Vn7s0EZGiNt6vMZ54sfT6pYvbHA"
REDDIT_USERNAME = "Tiger_in_the_Snow"

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=f"script:sentiment-analysis:v0.0.1 (by {REDDIT_USERNAME})"
)

# NLP configs
stemmer = PorterStemmer()
nlp = spacy.load("en_core_web_sm")


# Model configs
tokenizer = RobertaTokenizer.from_pretrained('aychang/roberta-base-imdb')
model = RobertaForSequenceClassification.from_pretrained(
    'aychang/roberta-base-imdb', num_labels=2)
model.classifier = torch.nn.Linear(768, 2)


def get_sentiment(query):
    print(query)
    filename = f"D:/projects/recomapp/data/sa/{query}_results.pkl"
    saved_data = load_data(filename)
   
    if saved_data:
        positive, negative, _ = saved_data
        wordcloud = f'/static/images/cloud/{query}_cloud.png'
        return positive, negative, wordcloud
    else:
       
        results = get_reddit_results(query)
        if not results:
            error = "No results found for query"
            return error

        positive, negative, wordcloud = analyze_comments(
            results, query=query)
        print(f'positive:{positive}')
        save_data((positive, negative, wordcloud), filename)
        return positive, negative, f'/static/images/cloud/{query}_cloud.png'


def get_reddit_results(query):
    sub = reddit.subreddit('noveltranslations+progressionfantasy')
    results = sub.search(query, limit=1)
    return list(results)


def transform_text(text):
    text = text.lower()
    text = nltk.word_tokenize(text)
    text = [i for i in text if i.isalnum()]
    text = [i for i in text if i not in stopwords.words(
        'english') and i not in string.punctuation]
    text = [stemmer.stem(i) for i in text]
    return ' '.join(text)


def tokenize(text):
    doc = nlp(text)
    return [token.text for token in doc]


def analyze_comments(results, query):
    total_positive = 0
    total_negative = 0
    total_comments = 0
    comments_for_cloud = []

    for submission in results:
        submission.comments.replace_more(limit=None)
        all_comments = submission.comments.list()

        for comment in all_comments:
            comment_body = comment.body

            text = transform_text(comment_body)
            comments_for_cloud.append(comment_body)

            if text:
                tokens = tokenize(text)

                tokenized_input = tokenizer(
                    tokens, return_tensors='pt', truncation=True, padding=True)

                outputs = model(**tokenized_input)

                probabilities = torch.softmax(outputs.logits, dim=-1)
                mean_probabilities = probabilities.mean(dim=1)

                positive_pct = mean_probabilities[0][1].item() * 100
                negative_pct = mean_probabilities[0][0].item() * 100

                total_positive += positive_pct
                total_negative += negative_pct
                total_comments += 1

    if total_comments > 0:
        avg_positive = total_positive / total_comments
        avg_negative = total_negative / total_comments
    else:
        avg_positive = 0
        avg_negative = 0

    if total_comments > 0:
        all_comments_string = ' '.join(comments_for_cloud)

        wordcloud = WordCloud(width=400, height=400,
                              background_color='white',
                              max_words=30,
                              stopwords=stopwords.words('english'),
                              min_font_size=10).generate(all_comments_string)
     # Save the WordCloud image as a static file
        wordcloud.to_file(
            f'D:/projects/recomapp/static/images/cloud/{query}_cloud.png')
    else:
        wordcloud = None

    return round(avg_positive), round(avg_negative), wordcloud
