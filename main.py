import json

from flask import Flask, request, render_template, redirect, url_for, session, send_file
import mysql.connector
from flask_session import Session
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)

app.secret_key = '545vfdb5fv54eergojfwe921c'

serializer = URLSafeTimedSerializer(app.secret_key)


@app.route('/')
def index():
    return render_template('UserLogin.html')


from flask import render_template


@app.route('/download_file/<token>', methods=['GET'])
def download_file(token):
    try:
        user_data = serializer.loads(token, max_age=3600)
        user_email = user_data['email']
        assignmentID = user_data['assignmentID']
        if 'loggedInEmail' in session:
            if user_email != session.get('loggedInEmail'):
                return "UnAurthorized user trying to download file"

            db_connection = mysql.connector.connect(
                host="localhost",
                user="root",
                passwd="",
                database="ezdatabase"
            )
            db_cursor = db_connection.cursor(buffered=True)

            check_query = "SELECT filename FROM uploadsdb WHERE assignmentID = %s"
            db_cursor.execute(check_query, (assignmentID,))
            file_data = db_cursor.fetchone()
            if file_data:
                filename = file_data[0]
                file_path = f"opUploads/{filename}"
                return send_file(file_path, as_attachment=True)

            return "File not found"

        else:
            # Handle case when 'loggedInEmail' is not in the session
            return "No logged-in email found in session"
    except:
        return "Invalid or expired token."


@app.route('/download/<assignmentID>', methods=['GET'])
def download_fle(assignmentID):
    filetoken = {'email': session.get('loggedInEmail'), 'assignmentID': assignmentID}
    token = serializer.dumps(filetoken)
    data = {
        'message': 'success',
        'download-link': f'/download_file/{token}'
    }
    return json.dumps(data, indent=4)


@app.route('/UserDashboard', methods=['GET'])
def UserDashboard():
    db_connection = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="",
        database="ezdatabase"
    )
    db_cursor = db_connection.cursor(buffered=True)

    select_query = "SELECT filename, assignmentID FROM uploadsDB"
    db_cursor.execute(select_query)

    data = db_cursor.fetchall()

    return render_template('user_dashboard.html', files=data)


@app.route('/usersignup', methods=['POST'])
def signup():
    user_email = request.form['signup_email']
    user_password = request.form['signup_password']
    user_name = request.form['signup_name']
    user_data = {'email': user_email, 'password': user_password, 'name': user_name}
    token = serializer.dumps(user_data)
    verification_url = url_for('verify_email', token=token, _external=True)
    return f"Verification url is sent on your email.Valid for 1 Hour<br><br><br><br>As its demo. Your URL is as follows.<br>URL: {verification_url}"


@app.route('/userLogin', methods=['POST'])
def userLogin():
    user_email = request.form['login_email']
    user_password = request.form['login_password']
    db_connection = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="",
        database="ezdatabase"
    )
    db_cursor = db_connection.cursor(buffered=True)
    query = "Select name,password from userdb where email=(%s) Limit 1"
    db_cursor.execute(query, (user_email,))
    user = db_cursor.fetchone()
    if user and user_password == user[1]:
        session['loggedInName'] = user[0]
        session['loggedInEmail'] = user_email
        return redirect(url_for('UserDashboard'))
    else:
        return "Invalid username or password"


@app.route('/verify/<token>')
def verify_email(token):
    try:
        user_data = serializer.loads(token, max_age=3600)
        user_email = user_data['email']
        user_password = user_data['password']
        user_name = user_data['name']

        db_connection = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="",
            database="ezdatabase"
        )
        db_cursor = db_connection.cursor(buffered=True)

        check_query = "SELECT * FROM userDB WHERE email = %s"
        db_cursor.execute(check_query, (user_email,))
        existing_user = db_cursor.fetchone()

        if existing_user:
            return "Email already exists. Please use a different email or login."

        insert_query = "INSERT INTO userDB (name, email, password) VALUES (%s, %s, %s)"
        db_cursor.execute(insert_query, (user_name, user_email, user_password))
        db_connection.commit()

        return render_template('email_verified.html')
    except:
        return "Invalid or expired token."


@app.route('/OPs')
def OPs():
    return render_template('OpsLogin.html')


import random

import random


@app.route('/opsUploadFile', methods=['POST'])
def opsUploadFile():
    if 'fileUpload' in request.files:
        uploaded_file = request.files['fileUpload']
        if uploaded_file.filename != '':
            db_connection = mysql.connector.connect(
                host="localhost",
                user="root",
                passwd="",
                database="ezdatabase"
            )
            db_cursor = db_connection.cursor(buffered=True)
            while True:
                assignment_id = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                check_query = "SELECT assignmentID FROM uploadsDB WHERE assignmentID = %s"
                db_cursor.execute(check_query, (assignment_id,))
                existing_assignment = db_cursor.fetchone()
                if not existing_assignment:
                    break
            uploaded_file.save('opUploads/' + uploaded_file.filename)
            insert_query = "INSERT INTO uploadsDB (filename, assignmentID) VALUES (%s, %s)"
            db_cursor.execute(insert_query, (uploaded_file.filename, assignment_id))
            db_connection.commit()
            return "File uploaded successfully! Assignment ID: " + assignment_id
    return "No file selected."


@app.route('/OPsHome')
def OPsHome():
    name = session.get('loggedInName')
    if name:
        return render_template('OpsHome.html', name=name)
    else:
        return redirect(url_for('loginOp'))


@app.route('/loginOp', methods=['POST', 'GET'])
def loginOp():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db_connection = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="",
            database="ezdatabase"
        )
        db_cursor = db_connection.cursor(buffered=True)
        query = "Select Name,password from ops_database where email=(%s) Limit 1"
        db_cursor.execute(query, (email,))
        user = db_cursor.fetchone()
        if user and password == user[1]:
            session['loggedInName'] = user[0]
            session['loggedInEmail'] = email
            return redirect(url_for('OPsHome'))
        else:
            return "Invalid username or password"
    else:
        return redirect(url_for('OPs'))


if __name__ == '__main__':
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    Session(app)
    app.run(host='0.0.0.0', port=5000)
