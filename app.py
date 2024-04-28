from idlelib import query
from flask import Flask, render_template, redirect, request, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt

DATABASE = "C:/Users/Admin/OneDrive - Wellington College/Dictionary-Maori/Maori.db"
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "qwertyuiop"

def get_list(query, params):
    con = create_connection(DATABASE)
    cur = con.cursor()
    if params == "":
        cur.execute(query)
    else:
        cur.execute(query, params)
    query_list = cur.fetchall()
    con.close()
    return query_list

def put_data(query, params):
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, params)
    con.commit()
    con.close()


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        print("Connection to database successful.")
        return connection
    except Error as e:
        print("Error connecting to database:", e)
        return None

def is_logged_in():
    if session.get('email') is None:
        return False
    else:
        return True

def is_teacher():
    if session.get('is_teacher')  != 1:
        print("student")
        return False
    else:
        print("teacher")
        return True


@app.route('/')
def render_home():  # put application's code here
    con = create_connection(DATABASE)
    query = ("SELECT Maori, English, Definition, level, image FROM maori_words")
    cur = con.cursor()
    cur.execute(query)
    words_list = cur.fetchall()
    con.close()
    print(words_list)
    return render_template('home.html', logged_in = is_logged_in())


@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    if is_logged_in():
        return redirect('allwords.html')
    if request.method == 'POST':
        print(request.form)
        fname = request.form.get('fname').title()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        year_group = request.form.get('year_group').title().strip()
        class_name = request.form.get('class_name').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        teacher = 0
        if request.form.get('is_teacher') == 'on':
            teacher = 1

        if password != password2:
            return redirect("\signup?error=Passwords+do+not+match")

        if len(password) < 8:
            return redirect("\signup?error=Password+must+be+at+least+8+characters")
        if len(password2) < 8:
            return redirect("\signup?error=Password+must+be+at+least+8+characters")

        hashed_password = bcrypt.generate_password_hash(password)
        #con = create_connection(DATABASE)
        #query = ("INSERT INTO user (fname, lname, email, password, is_teacher, year_group, class_name) "
                 #"VALUES (?, ?, ?, ?, ?, ?, ?)")
        #cur = con.cursor()

        try:
            put_data("INSERT INTO user (fname, lname, email, password, is_teacher, year_group, class_name) ""VALUES (?, ?, ?, ?, ?, ?, ?)",
            (fname, lname, email, hashed_password, teacher, year_group, class_name))
            #con.commit()
            #con.close()
        except sqlite3.IntegrityError:
            return redirect('\signup?error=Email+is+already+used')
        #con.close()
        return redirect("\login")
    return render_template('signup.html', logged_in=is_logged_in(), is_teacher=is_teacher())

@app.route('/login', methods=['POST', 'GET'])
def render_login():

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
        session['is_teacher'] = is_teacher
        return redirect('/')

    return render_template('login.html',  logged_in=is_logged_in())

@app.route('/allwords/<cat_id>')
def render_all_words(cat_id):

    words_list = get_list("SELECT Maori, English, Definition, level, image FROM maori_words WHERE cat_id=?",(cat_id, ))
    category_list = get_list("SELECT * FROM category", "")


    print(words_list)
    return render_template("allwords.html", word=words_list, categories=category_list )





@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=See+you+next+time!')


if __name__ == '__main__':
    app.run()
