from main import app
from flask import render_template, request, redirect, url_for, flash
from flask_mail import Message

@app.route('/contact', methods=['GET', 'POST'])
def contact():

    return render_template('contact.html')
