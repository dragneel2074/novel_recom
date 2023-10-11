from main import app, sitemapper
from flask import render_template, request, jsonify, flash, redirect, url_for, send_from_directory
import random
import pickle
from werkzeug.middleware.proxy_fix import ProxyFix
from sentiment import get_sentiment


# app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# load the data
novel_list = pickle.load(
    open('D:/projects/recomapp/data/novel_list.pkl', 'rb'))
novel_list['english_publisher'] = novel_list['english_publisher'].fillna(
    'unknown')
name_list = novel_list['name'].values
similarity = pickle.load(
    open('D:/projects/recomapp/data/similarity.pkl', 'rb'))


@sitemapper.include(lastmod="2023-06-21")
@app.route('/', methods=['GET', 'POST'])
def home():
    # Initialize selected_novel_name without any default value
    selected_novel_name = None

    if request.method == 'POST':
        action = request.form.get('action1') or request.form.get('action2') or request.form.get('action3')
        selected_novel_name = request.form.get('selected_novel_name')
        slider_value = request.form.get('slider')
        if slider_value is not None:
            slider_value = int(slider_value)
        else:
            slider_value = 1  # Assign a default value of 1

        recommendations = None

        if action == '💡 Recommend':
            recommendations = recommend(selected_novel_name, slider_value)
            if recommendations is None:
                flash("Novel not found in our database. Please try another one.")
                return redirect(url_for('home'))
        elif action == '🎲 Random':
            recommendations = [{'name': novel, 'image_url': novel_list[novel_list['name'] == novel]['image_url'].values[0],
                                'english_publisher': novel_list[novel_list['name'] == novel]['english_publisher'].values[0]} for novel in random.sample(list(name_list), 9)]
    elif request.method == 'GET':
        selected_novel_name = request.args.get('selected_novel_name')  # This will be None if there's no parameter
        slider_value = request.form.get('slider')
        if slider_value is not None:
            slider_value = int(slider_value)
        else:
            slider_value = 1

        recommendations = None
        if selected_novel_name:  # Only recommend if a novel name is provided
            recommendations = recommend(selected_novel_name, slider_value)

    # If no novel name is provided, default to 'Mother of Learning'
    if not selected_novel_name:
        selected_novel_name = 'Mother of Learning'

    return render_template('index.html', name_list=sorted(name_list), recommendations=recommendations, selected_novel_name=selected_novel_name,)



def recommend(novel, slider_start):
    try:
        novel_index = novel_list[novel_list['name'] == novel].index[0]
        distances = similarity[novel_index]
        new_novel_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[
            slider_start:slider_start+9]
    except IndexError:
        return None

    recommend_novel = [{'name': novel_list.iloc[i[0]]['name'], 'image_url': novel_list.iloc[i[0]]
                        ['image_url'], 'english_publisher': novel_list.iloc[i[0]]['english_publisher']} for i in new_novel_list]
    return recommend_novel


@sitemapper.include(lastmod="2023-06-10")
@app.route('/random', methods=['POST'])
def random_selection():
    if request.method == 'POST':
        random_novels = random.sample(list(name_list), 9)
        return jsonify({'recommendations': [{'name': novel, 'image_url': novel_list[novel_list['name'] == novel]['image_url'].values[0], 'english_publisher': novel_list[novel_list['name'] == novel]['english_publisher'].values[0]} for novel in random_novels]})


@app.route('/sentiment-analysis', methods=['POST'])
def analyze_sentiment():
    novel_name = request.form.get('novel_name')
    try:
        positive, negative, wordcloud = get_sentiment(novel_name)
    except Exception as e:
        print(e)
        return jsonify({'error': 'An error occurred during sentiment analysis.'})

    # Return analysis results
    return jsonify({
        'positive': positive,
        'negative': negative,
        'wordcloud': wordcloud
    })


@sitemapper.include(lastmod="2023-06-10")
@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    search = request.args.get('term')
    results = [novel for novel in name_list if search.lower() in novel.lower()]
    return jsonify(results)


@sitemapper.include(lastmod="2023-06-10")
@app.route('/top-picks')
def top_picks():
    return render_template("top-picks.html")


@sitemapper.include(lastmod="2023-07-09")
@app.route('/robots.txt')
def static_from_root_robots():
    return send_from_directory(app.static_folder, request.path[1:])


@sitemapper.include(lastmod="2023-07-15")
@app.route('/ads.txt')
def static_from_root_ads():
    return send_from_directory(app.static_folder, request.path[1:])


if __name__ == '__main__':
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run(debug=True)
