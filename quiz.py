import os
from main import app, User, db, QuizResult
from flask import Flask, abort, render_template, request, url_for, redirect, flash
import csv
import random
from sqlalchemy.exc import IntegrityError

# Load questions from all CSV files in a directory


def load_questions(directory):
    question_sets = {}
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            questions = []
            with open(os.path.join(directory, filename), 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) != 6:
                        raise ValueError(
                            f"Each row in the CSV file should have exactly 6 columns, but got {len(row)} columns.")
                    question = {
                        'question': row[0],
                        'options': row[1:5],
                        'answer': row[5]
                    }
                    questions.append(question)
            # Remove '.csv' from filename
            question_sets[filename[:-4]] = questions
    return question_sets


questions = load_questions('D:/projects/flask - Copy/data/quiz')


@app.route('/quiz_select')
def quiz_select():
    top_scores = get_top_scores()
    return render_template('quiz_select.html', quizzes=questions.keys(), top_scores=top_scores)


@app.route('/submit-quiz', methods=['POST'])
def submit_quiz():
    if not questions:
        abort(500, description="Error loading questions.")
    score = 0
    for question in questions[:2]:
        submitted_answer = request.form.get(question['question'])
        if submitted_answer is None:
            abort(400, description="Not all questions were answered.")
        if submitted_answer == question['answer']:
            score += 1
    user = User(name=request.form.get('name'), email=request.form.get('email'), score=score)
    db.session.add(user)
    db.session.commit()
    top_scores = get_top_scores()
    return redirect(url_for('result', user_id=user.id, top_scores =top_scores))


@app.route('/quiz/<quiz_name>')
def quiz(quiz_name):
    if quiz_name not in questions:
        abort(404, description="Quiz not found.")
    random.shuffle(questions[quiz_name])
    return render_template('quiz.html', questions=questions[quiz_name][:2], quiz_name=quiz_name)


@app.route('/submit-quiz/<quiz_name>', methods=['POST'])
def submit_quiz_name(quiz_name):
    if quiz_name not in questions:
        abort(404, description="Quiz not found.")
    score = 0
    for question in questions[quiz_name][:2]:
        submitted_answer = request.form.get(question['question'])
        if submitted_answer is None:
            abort(400, description="Not all questions were answered.")
        if submitted_answer == question['answer']:
            score += 1
    name = request.form.get('name')
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    if user is None:
        # Create a new user if one does not exist
        user = User(name=name, email=email)
        db.session.add(user)
        db.session.commit()
    # Create a new quiz result
    result = QuizResult(quiz_name=quiz_name, quiz_topic=quiz_name, score=score, user_id=user.id)
    db.session.add(result)
    db.session.commit()
    top_scores = get_top_scores()
    return redirect(url_for('result', user_id=result.user_id, top_scores = top_scores))

@app.route('/result/<int:user_id>')
@app.route('/result/<int:result_id>')
def result(result_id):
    result = QuizResult.query.get_or_404(result_id)
    user = User.query.get_or_404(result.user_id)
    return render_template('result.html', user=user, result=result)

def get_top_scores():
    top_scores = db.session.query(QuizResult.quiz_topic, User.name, QuizResult.score)\
        .join(User)\
        .order_by(QuizResult.quiz_topic, QuizResult.score.desc())\
        .limit(5)\
        .all()
    return top_scores
