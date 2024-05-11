from idlelib import query
from flask import Flask, render_template, redirect, request, session, url_for
import os
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

DATABASE = "C:/Users/Admin/OneDrive - Wellington College/Dictionary-Maori/Maori.db"
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "qwertyuiop"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



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

        hashed_password = bcrypt.generate_password_hash(password)
        try:
            put_data("INSERT INTO user (fname, lname, email, password, is_teacher, year_group, class_name) ""VALUES (?, ?, ?, ?, ?, ?, ?)",
            (fname, lname, email, hashed_password, teacher, year_group, class_name))
        except sqlite3.IntegrityError:
            return redirect('\signup?error=Email+is+already+used')
        return redirect("\login")
    return render_template('signup.html', logged_in=is_logged_in(), is_teacher=is_teacher())

@app.route('/login', methods=['POST', 'GET'])
def render_login():

    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()
        query = "SELECT user_id, fname, password, is_teacher FROM user WHERE email= ?"
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchone()
        print(user_data)
        con.close()

        if user_data == None:
             redirect(request.referrer + '?error=Invalid+username+or+password')
        else:
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

@app.route('/allwords')
def render_all_words():
    category_list = get_list("SELECT * FROM category", "")
    words_list = get_list("SELECT Maori, English, Definition, level, image, category_name, fname FROM maori_words m "
             "INNER JOIN user u on m.user_id_fk = u.user_id "
             "INNER JOIN category c ON m.cat_id_fk = c.cat_id ", "")

    return render_template("allwords.html", word=words_list,  logged_in=is_logged_in(), categories=category_list)
@app.route('/category/<cat_id>')
def render_category(cat_id):
    title = cat_id
    category_list = get_list("SELECT * FROM category", "")
    print(category_list)
    words_list = get_list("SELECT word_id, Maori, English, Definition, level, image, category_name, fname FROM maori_words m "
                          "INNER JOIN user u on m.user_id_fk = u.user_id "
                          "INNER JOIN category c ON m.cat_id_fk = c.cat_id WHERE cat_id=?", (cat_id, ))
    print(words_list)
    return render_template("category.html", word=words_list, categories=category_list, logged_in=is_logged_in(), title=title)

@app.route('/word_detail/<word_id>')
def render_word_detail(word_id):
    query = ("SELECT word_id, Maori, English, Definition, level, image, category_name, fname, entry_date FROM maori_words m "
             "INNER JOIN user u on m.user_id_fk = u.user_id "
             "INNER JOIN category c ON m.cat_id_fk = c.cat_id WHERE word_id=?")
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, (word_id,))
    about_word = cur.fetchall()
    con.close()
    return render_template("word_detail.html", wordinfo=about_word,  logged_in=is_logged_in())



@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=See+you+next+time!')
@app.route('/admin')
def render_admin():
    if is_logged_in():
        category_list = get_list("SELECT * FROM category", "")
        word_d = get_list("SELECT word_id, English FROM maori_words", "")
    else:
        return redirect('/?message=Need+to+be+logged+in.')
    return render_template("admin.html", logged_in=is_logged_in(), is_teacher=is_teacher(), categories=category_list, word_de=word_d)

@app.route('/add_category', methods=['POST'])
def add_category():
    if not is_logged_in():
        return redirect('/?message=Need+to+be+logged+in.')
    if request.method == "POST":
        cat_name = request.form.get('name').lower().strip()
        put_data('INSERT INTO category (category_name) VALUES (?)', (cat_name,))
        return redirect('/admin')

@app.route('/add_newword', methods=['POST'])
def add_word():
    if not is_logged_in():
        return redirect('/?message=Need+to+be+logged+in.')
    if request.method == "POST":
        mao_word = request.form.get('Maori').lower().strip()
        eng_word = request.form.get('English').lower().strip()
        deff = request.form.get('Definition').lower().strip()
        level = request.form.get('level').lower().strip()
        user_id = session.get('user_id')
        date_added = datetime.today().strftime('%Y-%m-%d')
        category = request.form.get('cat_id')
        image = "noimage"
        category = category.split(", ")
        cat_id = category[0]
        put_data('INSERT INTO maori_words (Maori, English, Definition, level, image,  cat_id_fk, entry_date, user_id_fk ) VALUES (?,?,?,?,?,?,?,?)', (mao_word, eng_word, deff, level, image, cat_id, date_added, user_id,))


    return redirect('/admin')



@app.route('/delete_category', methods=['POST'])
def render_delete_category():
    if not is_logged_in():
        return redirect('/?message=Need+to+be+logged+in.')
    if request.method == "POST":
        category = request.form.get('cat_id')
        category = category.split(", ")
        cat_id = category[0]
        cat_name = category[1]
        return render_template("delete_confirm.html", id=cat_id, category_name=cat_name, type="category", logged_in=is_logged_in(), is_teacher=is_teacher())
    return redirect('/admin')

@app.route('/delete_category_confirm/<category_id>')
def delete_category_confirm(category_id):
    if not is_logged_in():
        return redirect('/?message=Need+tobe+logged+in.')
    con = create_connection(DATABASE)
    query = 'DELETE FROM category WHERE cat_id = ?'
    cur = con.cursor()
    cur.execute(query, (category_id,))
    con.commit()
    con.close()
    return redirect('/admin')

@app.route('/delete_word', methods=['POST'])
def render_delete_word():
    if not is_logged_in():
        return redirect('/?message=Need+to+be+logged+in.')
    if request.method == "POST":
        word = request.form.get('word')
        word = word.split(", ")
        id1 = word[0]
        name_s = word[1]
        return render_template("delete_confirm1.html", id=id1, name=name_s, type="word", logged_in=is_logged_in(), is_teacher=is_teacher())
    return redirect('/admin')

@app.route('/delete_word_confirm/<word_id>')
def delete_word_confirm(word_id):
    if not is_logged_in():
        return redirect('/?message=Need+to+be+logged+in.')
    con = create_connection(DATABASE)
    query = 'DELETE FROM maori_words WHERE word_id = ?'
    cur = con.cursor()
    cur.execute(query, (word_id,))
    con.commit()
    con.close()
    return redirect('/admin')

@app.route('/search', methods=['GET', 'POST'])
def render_search():
    search = request.form['search']
    title = "Search for " + search
    query = "SELECT id, Maori, English, definition, level  FROM maori_words WHERE " \
            "id like ? or Maori like ? OR English like ? OR definition like ? OR level like ? "
    search = "%" + search + "%"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, (search, search, search, search, search))
    search_list = cur.fetchall()
    con.close()
    return render_template("allwords.html", find=search_list, title=title)

@app.route('/allwords_table')
def table():
    query = "SELECT cat_id, category_name FROM category"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query)
    category_list = cur.fetchall()
    con.close()
    query = ("SELECT word_id, Maori, English, Definition, level, image, category_name FROM maori_words m "
             "INNER JOIN category c ON m.cat_id_fk = c.cat_id")
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, )
    words_list = cur.fetchall()
    con.close()
    print(words_list)

    return render_template("allwords_table.html", word=words_list, logged_in=is_logged_in(), categories=category_list)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        add_image_to_database(filename)
        return redirect(url_for('index'))


def add_image_to_database(filename):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO maori_words (image) VALUES (?)", (filename,))
    conn.commit()
    conn.close()
    return render_template('upload.html')



if __name__ == '__main__':
    app.run()
