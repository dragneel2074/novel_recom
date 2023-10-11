import os
from main import app, User, db, QuizResult, sitemapper
from flask import Flask, abort, render_template, request, redirect, session, url_for, flash, jsonify
import csv
import random
from sqlalchemy.exc import IntegrityError
from urllib.parse import unquote
from werkzeug.exceptions import BadRequest, NotFound





def load_question_from_row(row, id):
    if len(row) != 6:
        raise ValueError(
            f"Each row in the CSV file should have exactly 6 columns, but got {len(row)} columns.")
    question = {'id': id, 'question': row[0], 'options': row[1:5], 'answer': row[5]}
    return question

def load_questions_from_file(filename):
    questions = []
    with open(filename, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for i, row in enumerate(reader):
            question = load_question_from_row(row, i)
            if question not in questions:
                questions.append(question)
    return questions

def load_questions(directory):
    question_sets = {}
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            new_filename = filename.replace('-', ' ')
            filepath = os.path.join(directory, filename)
            question_sets[filename[:-4]] = load_questions_from_file(filepath)
    return question_sets

questions = load_questions('data/quiz')

@sitemapper.include(lastmod="2023-06-21")
@app.route('/quiz_select')
def quiz_select():
    return render_template('quiz_select.html', quizzes=questions.keys(), top_scores=get_top_scores())

@app.route('/quiz/<quiz_name>')
def quiz(quiz_name):
    quiz_name = unquote(quiz_name)
    if quiz_name not in questions:
        raise NotFound(description="Quiz not found.")
    quiz_questions = questions[quiz_name][:]
    random.shuffle(quiz_questions)
    session['questions'] = quiz_questions[:15]
    return render_template('quiz.html', questions=session['questions'], quiz_name=quiz_name)

@app.route('/quiz/<quiz_name>/question')
def get_question(quiz_name):
    quiz_name = unquote(quiz_name)
    if quiz_name not in questions:
        raise NotFound(description="Quiz not found.")
    question = random.choice(questions[quiz_name])
    return jsonify(question)

@app.route('/submit-quiz/<quiz_name>', methods=['POST'])
def submit_quiz_name(quiz_name):
    quiz_name = unquote(quiz_name)
    if quiz_name not in questions or 'questions' not in session:
        flash("No questions found in session.")
        return redirect(url_for('quiz', quiz_name=quiz_name))
    answers = get_submitted_answers()
    if None in answers.values():
        flash("Not all questions were answered.")
        return render_template('quiz.html', questions=session['questions'], quiz_name=quiz_name, answers=answers)
    score = calculate_score(answers)
    name = request.form.get('name')
    email = request.form.get('email')
    if not name or not email:
        flash("Name and email are required.")
        return render_template('quiz.html', questions=session['questions'], quiz_name=quiz_name, answers=answers)
    user = get_or_create_user(name, email)
    if user is None:
        return render_template('quiz.html', questions=session['questions'], quiz_name=quiz_name, answers=answers)
    if not save_result(user, quiz_name, score):
        return render_template('quiz.html', questions=session['questions'], quiz_name=quiz_name, answers=answers)
    session.pop('questions', None)
    return redirect(url_for('result', user_id=user.id, quiz_name=quiz_name))

def get_submitted_answers():
    answers = {}
    for question in session['questions']:
        answers[question['question']] = request.form.get(question['question'])
    return answers

def calculate_score(answers):
    score = 0
    for question in session['questions']:
        if answers[question['question']] == question['answer']:
            score += 1
    return score

def get_or_create_user(name, email):
    try:
        user = User.query.filter_by(email=email).first()
        if user is None:
            user = User(name=name, email=email)
            db.session.add(user)
            db.session.commit()
        elif user.name != name:
            user.name = name
            db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Username or Email already Exists.")
        user = None
    except Exception as e:
        flash(f"Error querying for user: {str(e)}")
        user = None
    return user

def save_result(user, quiz_name, score):
    result = QuizResult(quiz_name=quiz_name, quiz_topic=quiz_name, score=score, user_id=user.id)
    try:
        db.session.add(result)
        db.session.commit()
        return True
    except IntegrityError:
        db.session.rollback()
        flash("Error saving quiz result.")
        return False

@app.route('/result/<int:user_id>/<quiz_name>')
def result(user_id, quiz_name):
    quiz_name = unquote(quiz_name)
    user = User.query.get_or_404(user_id)
    result = QuizResult.query.filter_by(user_id=user_id, quiz_name=quiz_name)\
        .order_by(QuizResult.id.desc()).first()
    if result is None:
        raise NotFound(description="Result not found.")
    return render_template('result.html', user=user, result=result, top_scores=get_top_scores())

def get_top_scores():
    return db.session.query(QuizResult.quiz_topic, User.name, QuizResult.score)\
        .join(User)\
        .order_by(QuizResult.id.desc())\
        .limit(30)\
        .all()
