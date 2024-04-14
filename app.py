from flask import Flask, render_template, redirect, request, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt

DATABASE = "C:/Users/Admin/OneDrive - Wellington College/Dictionary-Maori"
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "qwertyuiop"

def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


@app.route('/')
def hello_world():  # put application's code here
    return render_template('home.html')

def is_logged_in():
    if session.get('email') is None:
        return False
    else:
        return True

def is_teacher():
    if session.get('is_teacher') != 1:
        return False
    else:
        return True

def put_data(query, params):
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, params)
    con.commit()
    con.close()

@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    if is_logged_in():
        return redirect('/')
    if request.method == 'POST':
        fname = request.form.get('fname').title().strip()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        year_group = request.form.get('year_group').title().strip()
        class_name = request.form.get('class_name').title().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        teacher = 0
        if request.form.get('is_teacher') == 'on':
            teacher = 1

        if password != password2:
            return redirect('\signup?error=Passwords+do+not+match')

        if len(password) < 8:
            return redirect('/signup?error=Passwords+must+be+at+least+8+characters')

        hashed_password = bcrypt.generate_password_hash(password)

        try:
            put_data('INSERT INTO user (fname, lname, email, password, is_teacher, year_group, class ) VALUES (?, ?, ?, ?, ?, ?, ?, )', (fname, lname, email, hashed_password, is_teacher, year_group, class_name ))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')

        return redirect('/login')

    return render_template('signup.html', logged_in=is_logged_in(), is_teacher=is_teacher())

@app.route('/login', methods=['POST', 'GET'])
def render_login():
    if is_logged_in():
        return redirect('/menu/1')
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()
        query = """SELECT id, fname, password, is_teacher FROM user WHERE email= ?"""
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchone()
        con.close()
        try:
            user_id = user_data[0]
            first_name = user_data[1]
            db_password = user_data[2]
            is_teacher = user_data[3]
        except IndexError:
            return redirect('/login?error=Invalid+username+or+password')

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")

        session['email'] = email
        session['user_id'] = user_id
        session['firstname'] = first_name
        session['is_admin'] = is_teacher
        return redirect('/')

    return render_template('login.html')

@app.route('/logout')
def logout():
    [session.pop(key) for key in list(session.keys())]
    return redirect('/?message=See+you+next+time!')



if __name__ == '__main__':
    app.run()
