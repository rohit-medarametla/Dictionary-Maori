from idlelib import query
from flask import Flask, render_template, redirect, request, session, url_for, flash
import os
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

DATABASE = "Maori.db"
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "qwertyuiop"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# this is a function that creates connection with database and queries what we want and store it in a variable
def get_list(query, params):
    with create_connection(DATABASE) as con:
        cur = con.cursor()
        if params == "":
            cur.execute(query)
        else:
            cur.execute(query, params)
        query_list = cur.fetchall()
    return query_list


# this is a fuction that puts data in the database tables
def put_data(query, params):
    with create_connection(DATABASE) as con:
        cur = con.cursor()
        cur.execute(query, params)
        con.commit()


# Function to establish connection to the database and execute queries
def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        print("Connection to database successful.")
        return connection
    except Error as e:
        print("Error connecting to database:", e)
        return None


# Function to check if a user is logged in
def is_logged_in():
    if session.get('email') is None:
        return False
    else:
        return True


# Function to check if a user is a teacher or student
def is_teacher():
    return session.get('is_teacher') == 1


# Route for home page
@app.route('/')
def render_home():
    return render_template('home.html', logged_in=is_logged_in(), is_teacher=is_teacher())


# Route for user signup
@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    # A if condition to check if user is logged in
    if is_logged_in():
        return redirect('allwords.html')
    # if condition for loggin
    if request.method == 'POST':
        print(request.form)
        # getting the data from the form
        fname = request.form.get('fname').title() # gets the first name and converts to tittle class
        lname = request.form.get('lname').title().strip() # gets the last name and converts to tittle class and strip leading spaces
        email = request.form.get('email').lower().strip() # gets email and, converts to lower case and strip leading spaces
        password = request.form.get('password') # gets the password
        password2 = request.form.get('password2') # Gets the confirm password
        # Defult teacher set to 0 and will be considered as a student
        teacher = 0
        # if the 'is_teacher' checkbox is checked set teacher flag to 1
        if request.form.get('is_teacher') == 'on':
            teacher = 1
        # checks if the password matches
        if password != password2:
            # Redirects to signup page with error message if passwords do 
            return redirect("\signup?error=Passwords+do+not+match")
        # checks if password has minimum of 8 charecter
        if len(password) < 8:
            return redirect("\signup?error=Password+must+be+at+least+8+characters")
        # So this enters hashed password into database
        hashed_password = bcrypt.generate_password_hash(password)
        # this tries to run code
        try:
            put_data("INSERT INTO user (fname, lname, email, password, is_teacher ) ""VALUES (?, ?, ?, ?, ?)",
                     (fname, lname, email, hashed_password, teacher))
        # this checks for any integrity error like duplicate email
        except sqlite3.IntegrityError:
            return redirect('\signup?error=Email+is+already+used')

        return redirect("\login")
    return render_template('signup.html', logged_in=is_logged_in(), is_teacher=is_teacher())

# this routes codes the log in
@app.route('/login', methods=['POST', 'GET'])
def render_login():

    if request.method == 'POST': # Check if the request method is POST, indicating that the form has been submitted.
        # Retrieve the email and password from the form data, stripping any leading whitespace.
        # Convert the email to lowercase to ensure case-insensitive comparison.
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()
        # define the sql query to select user details from the user table based on the email given by the user
        query = "SELECT user_id, fname, password, is_teacher FROM user WHERE email= ?"
        # creates a connection to the database
        con = create_connection(DATABASE)
        # creates a cursor object
        cur = con.cursor()
        # Exucute the SQL query, passing the email as a parameter to prevent SQL injection
        cur.execute(query, (email,))
        # Fetch the first row of the result set, which contains the user data.
        user_data = cur.fetchone()
        print(user_data)
        # Close the database connection.
        con.close()
        # a if statement if user data is none then it redirect
        if user_data is None:
            # Redirect the user back to the previous page (referrer) with an error message indicating invalid username or password
            redirect(request.referrer + '?error=Invalid+username+or+password')

        else:
            try:
                # Extract user data from user_data
                user_id = user_data[0]
                first_name = user_data[1]
                db_password = user_data[2]
                is_teacher = user_data[3]
            except IndexError:
                return redirect('/login?error=Invalid+username+or+password')

            # Check if the password provided matches the hashed password stored in the database.
            if not bcrypt.check_password_hash(db_password, password):
                # If the passwords don't match, redirect back to the previous page with an error message.
                return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")
            # If the password matches, store user information in the session.
            session['email'] = email
            session['user_id'] = user_id
            session['firstname'] = first_name
            session['is_teacher'] = is_teacher
            # Redirect the user to the homepage.
            return redirect('/')

    return render_template('login.html',  logged_in=is_logged_in(),)



# Define a route for accessing a specific category page based on its cat_id.
@app.route('/category/<cat_id>')
def render_category(cat_id):
    # Set the title of the category page to the cat_id.
    title = cat_id

    # receives a list of all categories from the database.
    category_list = get_list("SELECT cat_id, category_name FROM category", "")

    # Print the recieved category list for debugging purposes.
    print(category_list)

    # receive a list of words belonging to the specified category from the database.
    words_list = get_list("SELECT word_id, Maori, English, Definition, level, image, category_name, fname"
                          " FROM Dictionary m "
                          "INNER JOIN user u on m.user_id_fk = u.user_id "
                          "INNER JOIN category c ON m.cat_id_fk = c.cat_id WHERE cat_id=?", (cat_id, ))

    # Print the recived words list for debugging purposes.
    print(words_list)

    # Render the category.html template with the retrieved data and pass it to the template.
    return render_template("category.html", word=words_list, categories=category_list,
                           logged_in=is_logged_in(), title=title)




# Define a route for accessing the detail page of a specific word based on its word_id.
@app.route('/word_detail/<word_id>')
def render_word_detail(word_id):
    # Retrieve a list of all categories from the database.
    category_list = get_list("SELECT cat_id, category_name FROM category", "")

    # Retrieve detailed information about the specified word from the database.
    about_word = get_list("SELECT word_id, Maori, English, Definition, level, image, category_name, fname, "
                          "time_added , entry_date FROM Dictionary m "
                          "INNER JOIN user u on m.user_id_fk = u.user_id "
                          "INNER JOIN category c ON m.cat_id_fk = c.cat_id WHERE word_id=?", (word_id,))

    # Render the word_detail.html template with the retrieved word information and pass it to the template.
    return render_template("word_detail.html", wordinfo=about_word,  logged_in=is_logged_in(), categories=category_list)



# Define a route for logging out the user.
@app.route('/logout')
def logout():
    # Print the keys in the session for debugging purposes.
    print(list(session.keys()))

    # Remove all keys from the session.
    [session.pop(key) for key in list(session.keys())]

    # Print the keys in the session after removing them for debugging purposes.
    print(list(session.keys()))

    # Redirect the user to the homepage with a message indicating successful logout.
    return redirect('/?message=See+you+next+time!')


# Define a route for accessing the admin page.
@app.route('/admin')
def render_admin():
    # Check if the user is logged in and is a teacher.
    if is_logged_in and is_teacher():
        # Retrieve a list of all categories from the database.
        category_list = get_list("SELECT * FROM category", "")

        # Retrieve word details (word_id and English word) from the Dictionary table.
        word_detail = get_list("SELECT word_id, English FROM Dictionary", "")
    else:
        # If the user is not logged in or is not a teacher, redirect to the homepage with a message.
        return redirect('/?message=Need+to+be+logged+in.')

    # Render the admin.html template with the retrieved data and pass it to the template.
    return render_template("admin.html", logged_in=is_logged_in(), is_teacher=is_teacher(),
                           categories=category_list, word_detail=word_detail)


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
        time_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        category = request.form.get('cat_id')
        image = "noimage"
        category = category.split(", ")
        cat_id = category[0]
        put_data('INSERT INTO Dictionary (Maori, English, Definition, level, image,  cat_id_fk, entry_date,'
                 ' user_id_fk, time_added ) VALUES (?,?,?,?,?,?,?,?,?)',
                 (mao_word, eng_word, deff, level, image, cat_id, date_added, user_id, time_added,))

    return redirect('/admin')


@app.route('/edit/<word_id>', methods=['GET', 'POST'])
def edit_word(word_id):
    if is_logged_in() and is_teacher():
        about_word = get_list(
            "SELECT word_id, Maori, English, Definition, level, image, category_name, fname, entry_date, cat_id_fk"
            " FROM Dictionary m "
            "INNER JOIN user u on m.user_id_fk = u.user_id "
            "INNER JOIN category c ON m.cat_id_fk = c.cat_id WHERE word_id=?", (word_id,))
        about_word = about_word[0]
        category_list = get_list("SELECT cat_id, category_name FROM category", "")

        if request.method == "POST":
            mao_word = request.form.get('Maori').lower().strip()
            eng_word = request.form.get('English').lower().strip()
            deff = request.form.get('Definition').lower().strip()
            level = request.form.get('level').lower().strip()
            user_id = session.get('user_id')
            date_added = datetime.today().strftime('%Y-%m-%d')
            cat_id = request.form.get('cat_id')

            put_data("UPDATE Dictionary SET"
                     " Maori=?, English=?, Definition=?, level=?, last_edit_by=?, entry_date=?, cat_id_fk=? "
                     "WHERE word_id=?", (mao_word, eng_word, deff, level, user_id, date_added, cat_id, word_id))
            flash("The word has been updated!", "info")
            return redirect('/allwords')

    else:
        return redirect('/?message=Need+to+be+teacher.')

    return render_template('edit.html', logged_in=is_logged_in(), word_de=about_word, word_id=word_id, categories=category_list)



@app.route('/delete_category', methods=['POST'])
def render_delete_category():
    if not is_logged_in():
        return redirect('/?message=Need+to+be+logged+in.')
    if request.method == "POST":
        category = request.form.get('cat_id')
        category = category.split(", ")
        cat_id = category[0]
        cat_name = category[1]
        return render_template("delete_confirm.html", id=cat_id, category_name=cat_name,
                               type="category", logged_in=is_logged_in(), is_teacher=is_teacher())
    return redirect('/admin')


@app.route('/delete_category_confirm/<category_id>')
def delete_category_confirm(category_id):
    if not is_logged_in():
        return redirect('/?message=Need+to+be+logged+in.')
    put_data('DELETE FROM category WHERE cat_id = ?',(category_id))
    return redirect('/admin')


@app.route('/delete_word/<word_id>')
def render_delete_word(word_id):
    if not is_logged_in():
        return redirect('/?message=Need+to+be+logged+in.')
    if not is_teacher():
        return redirect('/')
    word_info = get_list("SELECT Maori FROM Dictionary WHERE word_id = ?", (word_id, ))

    return render_template("delete_confirm1.html", id=word_id, name=word_info[0][0], type="word",
                           logged_in=is_logged_in(), is_teacher=is_teacher())


@app.route('/delete_word_confirm/<word_id>', methods=['POST'])
def delete_word_confirm(word_id):
    if not is_logged_in():
        return redirect('/?message=Need+to+be+logged+in.')
    put_data('DELETE FROM Dictionary WHERE word_id = ?', (word_id,))
    return redirect('/allwords')


@app.route('/search', methods=['GET', 'POST'])
def render_search():
    category_list = get_list("SELECT cat_id, category_name FROM category", "")
    search = request.form['search']
    title = "Search results for: " + search
    query = ("SELECT word_id, Maori, English, definition, level, category_name  FROM Dictionary m "
             "INNER JOIN category c ON m.cat_id_fk = c.cat_id "
             "WHERE " 
            "word_id like ? or Maori like ? OR English like ? OR definition like ? OR level like ? "
             "OR category_name like ? ")
    search = "%" + search + "%"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, (search, search, search, search, search, search))
    search_list = cur.fetchall()
    con.close()
    return render_template("allwords.html", word=search_list, title=title, logged_in=is_logged_in(), categories=category_list)


@app.route('/allwords')
def table():
    category_list = get_list("SELECT cat_id, category_name FROM category", "")
    words_list = get_list(
        "SELECT word_id, Maori, English, Definition, level, category_name, image  FROM Dictionary m "
               "INNER JOIN category c ON m.cat_id_fk = c.cat_id", "")
    print(words_list)

    return render_template("allwords.html", word=words_list, logged_in=is_logged_in(), categories=category_list)



if __name__ == '__main__':
    app.run()
