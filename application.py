import json

import boto3
import logging
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename

import tools.tools
from tools import tools as t
import flask
from flask import Flask, render_template, flash, request, session

boto3 = boto3.Session()
application = Flask(__name__)
application.secret_key = "superSecretKey"
# s3 = boto3.resource('s3')
s3 = boto3.resource('s3')
db = boto3.resource('dynamodb')
application.config['SESSION_TYPE'] = 'testing'
errors = []
messages = []
usersDB = db.Table('login')
recordsDB = db.Table('max_hangs')
subDB = db.Table('subscriptions')


# testfile = open("test.jpg", "rb")
# tools.uploadToBucket(testfile.name, testfile, "s3917984bucket")

# # Upload a new file
# data = open('test.jpg', 'rb')
# s3.Bucket('s3917984bucket').put_object(Key='test.jpg', Body=data)
# # Print out bucket names
# for bucket in s3.buckets.all():
#     print(bucket.name)

def session_active_user(user_record):
    session['email'] = (user_record['email'])
    session['user_name'] = (user_record['user_name'])
    session['profile_img_url'] = tools.tools.get_img_url(user_record['profile_img'])


def get_subs(email):
    results = subDB.query(
        KeyConditionExpression=Key('email').eq(session.get("email"))
    )
    subs = results['Items']
    return subs


@application.route('/')
def hello_world():  # put application's code here
    return render_template('index.html')


@application.route('/main_page')
def main_page():
    url = 'main_page.html'
    subs = get_subs(session.get("email"))
    records_array = generate_array_for_chart()
    return render_template(url, errors=errors, messages=messages, subs=subs, records_array=records_array)


def generate_array_for_chart():
    request = recordsDB.scan()
    records = request['Items']
    records_array = []
    i = 0
    highlight = 'null'
    for record in records:
        if record['username'] == session['user_name']:
            highlight = "point { size: 18; shape-type: star; fill-color: #f70000; }"
        formatted_record = [int(record['grade']), int(record['weight']), highlight]
        records_array.append(formatted_record)
        i += 1
        highlight = 'null'
    print(records_array)
    return records_array


@application.route('/remove_sub', methods=['GET', 'POST'])
def remove_sub():
    email = session.get("email")
    url = 'main_page.html'
    if request.method == 'POST':
        form_data = request.form
        title = ''
        artist = ''
        title = form_data.get('rem-title')
        artist = form_data.get('rem-artist')
        t.rem_subscription(email, artist, title)
        messages.append(session.get("user_name"))
        subs = get_subs(session.get("email"))
    messages.append(session.get("user_name"))
    subs = get_subs(session.get("email"))
    songs = []
    return render_template(url, errors=errors, messages=messages, subs=subs, songs=songs)


@application.route('/checkLogin', methods=['GET', 'POST'])
def check_login():
    errors = []
    messages = []
    email = ""
    subs = []
    url = 'index.html'
    if (request.method == 'POST'):
        post = request.form
        email = post.get('email')
        password = post.get('password')
        usersDB = db.Table('login')
        results = usersDB.query(
            KeyConditionExpression=Key('email').eq(email)
        )
        if results['Count'] > 0:
            user_info = results['Items'][0]
            if ((email == user_info['email']) and (password == user_info['password'])):
                session_active_user(user_info)
                session['logged_in'] = True
                messages.clear()
                messages.append('Successfuly logged in as ' + user_info['user_name'])
                url = 'main_page.html'
                subs = get_subs(email)
                main_page()
                records_array = generate_array_for_chart()
            else:
                errors.clear()
                errors.append('email or password is invalid')
        else:
            errors.clear()
            errors.append('email or password is invalid')
    else:
        errors.clear()
        errors.append('email or password is invalid')

    return render_template(url, messages=messages, errors=errors, subs=subs, records_array=records_array)


@application.route('/logout')
def logout():
    session.pop('logged_in', None)
    messages.clear()
    messages.append("You were logged out.")
    return render_template("index.html", errors=errors, messages=messages)


@application.route('/register', methods=['GET', 'POST'])
def register():
    errors = []
    messages = []
    url = 'register.html'
    account_created = False
    if request.method == 'POST':
        form_data = request.form
        candidate_email = form_data.get('email')
        candidate_user_name = form_data.get('user_name')
        candidate_password = form_data.get('password')
        file = request.files['profile_img']
        fileKey = t.upload_image(file, 's3917984')
        if candidate_email == '' or candidate_user_name == '' or candidate_password == '':
            errors = []
            errors.append("Please don't leave fields empty")
        else:
            errors = []
            results = usersDB.query(
                KeyConditionExpression=Key('email').eq(candidate_email)
            )
            if results['Count'] > 0:
                errors.append('Duplicate email, please login with existing account or use a different email address')
        if not errors:
            t.store_account_info(usersDB, candidate_email, candidate_user_name, candidate_password,
                                 fileKey)
            account_created = True
        if account_created:
            url = 'index.html'
            messages = ['Account Successfully created, please login with your new ID and Password']
    return render_template(url, errors=errors, messages=messages)


def save_new_user(email, username, password):
    pass


@application.route('/add_record', methods=['GET', 'POST'])
def add_record():
    url = 'main_page.html'
    songs = []
    subs = []
    messages.clear()
    messages.append(session.get("user_name"))
    records = get_subs(session.get("email"))
    if request.method == 'POST':
        form_data = request.form
        username = ''
        grade = ''
        bodyweight = ''
        username = form_data.get('username')
        grade = form_data.get('grade')
        bodyweight = form_data.get('bodyweight')
        t.add_data_to_max_hang(username, grade, bodyweight)
        records_array = generate_array_for_chart()
    return render_template(url, errors=errors, messages=messages, songs=songs, subs=subs, records_array=records_array)


@application.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    url = 'main_page.html'
    songs = []
    subs = []
    subs = get_subs(session.get("email"))
    if request.method == 'POST':
        form_data = request.form
        title = ''
        artist = ''
        email = session.get("email")
        img_url = ''
        web_url = ''
        year = ''
        title = form_data.get('sub-title')
        artist = form_data.get('sub-artist')
        img_url = form_data.get('sub-img_url')
        web_url = form_data.get('sub-web_url')
        year = form_data.get('sub-year')
        print(title + " before store function")
        t.store_subscription(subDB, email, artist, title, img_url, web_url, year)
        messages.append(session.get("user_name"))
        subs = get_subs(session.get("email"))
    return render_template(url, errors=errors, messages=messages, songs=songs, subs=subs)


def register_page():
    url = 'register.html'
    return render_template(url, errors=errors, messages=messages)


def validate_email(email):
    valid = False
    if (valid == True):
        valid = True
    return valid


# probably move these to tools
def login(email, password):
    # send to main page
    pass


def invalid_login():
    # send back to login page and display "password or email invalid"
    pass
