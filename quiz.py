import os
from main import app, User, db, QuizResult, sitemapper
from flask import Flask, abort, render_template, request, redirect, session, url_for, flash
import csv
import random
from sqlalchemy.exc import IntegrityError
from urllib.parse import unquote
from werkzeug.exceptions import BadRequest, NotFound


def load_questions(directory):
    question_sets = {}
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            questions = []
            with open(os.path.join(directory, filename), 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                rows = list(reader)

                random.shuffle(rows)
                for i, row in enumerate(rows):
                    if len(row) != 6:
                        raise ValueError(
                            f"Each row in the CSV file should have exactly 6 columns, but got {len(row)} columns.")

                    question = {
                        'id': i, 'question': row[0], 'options': row[1:5], 'answer': row[5]}
                    questions.append(question)
            question_sets[filename[:-4]] = questions
    return question_sets


questions = load_questions('data/quiz')

@sitemapper.include(lastmod="2023-06-20")
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


@app.route('/submit-quiz/<quiz_name>', methods=['POST'])
def submit_quiz_name(quiz_name):
    quiz_name = unquote(quiz_name)
    if quiz_name not in questions or 'questions' not in session:
        flash("No questions found in session.")
        return redirect(url_for('quiz', quiz_name=quiz_name))
    score = 0
    answers = {}
    for question in session['questions']:
        submitted_answer = request.form.get(question['question'])
        answers[question['question']] = submitted_answer
        if submitted_answer is None:
            flash("Not all questions were answered.")
            return render_template('quiz.html', questions=session['questions'], quiz_name=quiz_name, answers=answers)
        if submitted_answer == question['answer']:
            score += 1
    name = request.form.get('name')
    email = request.form.get('email')
    if not name or not email:
        flash("Name and email are required.")
        return render_template('quiz.html', questions=session['questions'], quiz_name=quiz_name, answers=answers)
    try:
        user = User.query.filter_by(email=email).first()
    except Exception as e:
        flash(f"Error querying for user: {str(e)}")
        return render_template('quiz.html', questions=session['questions'], quiz_name=quiz_name, answers=answers)
    if user is None:
        user = User(name=name, email=email)
        try:

            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Username or Email already Exists.")
            return render_template('quiz.html', questions=session['questions'], quiz_name=quiz_name, answers=answers)
    else:
        if user.name != name:
            user.name = name
            try:
                db.session.commit()

            except IntegrityError:
                db.session.rollback()
                flash("Error updating user name.")
                return render_template('quiz.html', questions=session['questions'], quiz_name=quiz_name, answers=answers)
    result = QuizResult(quiz_name=quiz_name,
                        quiz_topic=quiz_name, score=score, user_id=user.id)
    try:
        db.session.add(result)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Error saving quiz result.")
        return render_template('quiz.html', questions=session['questions'], quiz_name=quiz_name, answers=answers)
    session.pop('questions', None)
    return redirect(url_for('result', user_id=result.user_id, quiz_name=quiz_name))


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
        .order_by(QuizResult.quiz_topic, QuizResult.score.desc())\
        .limit(5)\
        .all()
