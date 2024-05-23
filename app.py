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
        fname = request.form.get('fname').title()  # gets the first name and converts to tittle class
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

        return redirect("/login")
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

# Route for displaying all words in the dictionary
@app.route('/allwords')
def table():
    # Retrieve a list of all categories from the database
    category_list = get_list("SELECT cat_id, category_name FROM category", "")

    # Retrieve a list of all words from the Dictionary table, including related category data
    words_list = get_list(
        "SELECT word_id, Maori, English, level, category_name FROM Dictionary m "
        "INNER JOIN category c ON m.cat_id_fk = c.cat_id", "")

    # Print the list of words to the console for debugging purposes
    print(words_list)

    # Render the allwords.html template with the list of words and other data
    return render_template("allwords.html", word=words_list, logged_in=is_logged_in(), categories=category_list, is_teacher=is_teacher())




# Define a route for accessing a specific category page based on its cat_id.
@app.route('/category/<cat_id>')
def render_category(cat_id):
    # Set the title of the category page to the cat_id.
    title = cat_id

    # uses get_list function to query and grab the data and stored it in category_list .
    category_list = get_list("SELECT cat_id, category_name FROM category", "")

    # Print the recived category list to check if the code above is working right .
    print(category_list)

    # uses get_list function to query and grab the data and stored it in words_list .
    words_list = get_list("SELECT word_id, Maori, English, level, category_name"
                                " FROM Dictionary m "
                                "INNER JOIN category c ON m.cat_id_fk = c.cat_id WHERE cat_id=?", (cat_id, ))

    # Print the recived words list to check if the code above is working right .
    print(words_list)

    # Render the category.html template with the received data and pass it to the template.
    return render_template("category.html", word=words_list, categories=category_list,
                           logged_in=is_logged_in(), title=title)


#  a route for accessing the detail page of a specific word based on its word_id.
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
    return render_template("word_detail.html", wordinfo=about_word,  logged_in=is_logged_in(), categories=category_list, is_teacher=is_teacher())



# a route for logging out the user.
@app.route('/logout')
def logout():
    # Print the keys in the session for testing purposes.
    print(list(session.keys()))

    # Remove all keys from the session.
    [session.pop(key) for key in list(session.keys())]

    # Print the keys in the session after removing them for testing purposes.
    print(list(session.keys()))

    # Redirect the user to the homepage with a message indicating successful logout.
    return redirect('/?message=See+you+next+time!')


#  a route for accessing the admin page.
@app.route('/admin')
def render_admin():
    # Check if the user is logged in and is a teacher.
    if is_logged_in and is_teacher():
        # grabs a list of all categories from the database and stores it in the category_list variable.
        category_list = get_list("SELECT cat_id, category_name FROM category", "")

        # Retrieve word details (word_id and English word) from the Dictionary table.
        word_detail = get_list("SELECT word_id, English FROM Dictionary", "")
    else:
        # If the user is not logged in or is not a teacher, redirect to the homepage with a message.
        return redirect('/?message=Need+to+be+logged+in.')

    # Render the admin.html template with the grabbed data and pass it to the template.
    return render_template("admin.html", logged_in=is_logged_in(), is_teacher=is_teacher(),
                           categories=category_list, word_detail=word_detail)


# Route for adding a new category
@app.route('/add_category', methods=['POST'])
def add_category():
    # Check if the user is logged in
    if not is_logged_in():
        # If not logged in, redirect to the homepage with a message
        return redirect('/?message=Need+to+be+logged+in.')

    # Check if the request method is POST
    if request.method == "POST":
        # grabs the category name from the form data, convert it to lowercase, and strip whitespace
        cat_name = request.form.get('name').lower().strip()

        # Insert the new category into the database
        put_data('INSERT INTO category (category_name) VALUES (?)', (cat_name,))

        # Redirect to the admin page after adding the category
        return redirect('/admin')


# Route for adding a new word
@app.route('/add_newword', methods=['POST'])
def add_word():
    # Check if the user is logged in
    if not is_logged_in():
        # If not logged in, redirect to the homepage with a message
        return redirect('/?message=Need+to+be+logged+in.')

    # Check if the request method is POST
    if request.method == "POST":
        # grab word details from the form data, convert them to lowercase, and strip whitespace
        maori_word = request.form.get('Maori').lower().strip()
        english_word = request.form.get('English').lower().strip()
        definition = request.form.get('Definition').lower().strip()
        level = request.form.get('level').lower().strip()

        # Grabs the user ID from the session
        user_id = session.get('user_id')

        # Get the current date and time
        date_time_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Grabs the category ID from the form data
        category = request.form.get('cat_id')
        image = "noimage"  # Default image
        category = category.split(", ")
        cat_id = category[0]

        # Insert the new word into the database
        put_data('INSERT INTO Dictionary (Maori, English, Definition, level, image,  cat_id_fk, entry_date,'
                 ' user_id_fk ) VALUES (?,?,?,?,?,?,?,?)',
                 (maori_word, english_word, definition, level, image, cat_id, date_time_added, user_id,))

    # Redirect to the admin page after adding the word
    return redirect('/admin')


# Route for editing a word
@app.route('/edit/<word_id>', methods=['GET', 'POST'])
def edit_word(word_id):
    # Check if the user is logged in and is a teacher
    if is_logged_in() and is_teacher():
        # Grabs information about the word with the specified word_id
        about_word = get_list(
            "SELECT Maori, English, Definition, level, cat_id_fk"
            " FROM Dictionary m "
            "INNER JOIN category c ON m.cat_id_fk = c.cat_id WHERE word_id=?", (word_id,))

        # Extract the first row from the result
        about_word = about_word[0]

        # Grabs a list of all categories from the database
        category_list = get_list("SELECT cat_id, category_name FROM category", "")

        # Check if the request method is POST
        if request.method == "POST":
            # Grabs updated word details from the form data
            maori_word = request.form.get('Maori').lower().strip()
            english_word = request.form.get('English').lower().strip()
            definition = request.form.get('Definition').lower().strip()
            level = request.form.get('level').lower().strip()
            user_id = session.get('user_id')
            date_time_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cat_id = request.form.get('cat_id')

            # Update the word in the database
            put_data("UPDATE Dictionary SET"
                     " Maori=?, English=?, Definition=?, level=?, user_id_fk=?, entry_date=?, cat_id_fk=? "
                     "WHERE word_id=?", (maori_word, english_word, definition, level, user_id, date_time_added, cat_id, word_id))

            # Flash a message indicating that the word has been updated
            flash("The word has been updated!", "info")

            # Redirect to the page displaying all words
            return redirect('/allwords')

    else:
        # If the user is not logged in or is not a teacher, redirect to the homepage with a message
        return redirect('/?message=Need+to+be+teacher.')

    # Render the edit.html template with the retrieved data and pass it to the template
    return render_template('edit.html', logged_in=is_logged_in(), word_detail=about_word, word_id=word_id,
                           categories=category_list, is_teacher=is_teacher())


# Route for rendering the delete page for category
@app.route('/delete_category', methods=['POST'])
def render_delete_category():
    # Check if the user is logged in
    if not is_logged_in():
        # If not logged in, redirect to the homepage with a message
        return redirect('/?message=Need+to+be+logged+in.')

    # Check if the request method is POST
    if request.method == "POST":
        # Retrieve the category ID and name from the form data
        category = request.form.get('cat_id')
        category = category.split(", ")
        cat_id = category[0]
        cat_name = category[1]

        # Render the delete_confirm.html template with the category ID, name, and type of deletion
        return render_template("delete_confirm.html", id=cat_id, category_name=cat_name,
                               type="category", logged_in=is_logged_in(), is_teacher=is_teacher())

    # Redirect to the admin page if the request method is not POST
    return redirect('/admin')


# Route for confirming and deleting a category
@app.route('/delete_category_confirm/<category_id>')
def delete_category_confirm(category_id):
    # Check if the user is logged in
    if not is_logged_in():
        # If not logged in, redirect to the homepage with a message
        return redirect('/?message=Need+to+be+logged+in.')

    # Delete the category from the database using the provided category_id
    put_data('DELETE FROM category WHERE cat_id = ?', (category_id,))

    # Redirect to the admin page after deletion
    return redirect('/admin')


# Route for rendering the confirmation page for deleting a word
@app.route('/delete_word/<word_id>')
def render_delete_word(word_id):
    # Check if the user is logged in
    if not is_logged_in():
        # If not logged in, redirect to the homepage with a message
        return redirect('/?message=Need+to+be+logged+in.')

    # Check if the user is a teacher
    if not is_teacher():
        # If not a teacher, redirect to the homepage
        return redirect('/')

    # Grabs the Maori word associated with the specified word_id from the database
    word_info = get_list("SELECT Maori FROM Dictionary WHERE word_id = ?", (word_id,))

    # Render the delete_confirm1.html template with the word information and deletion details
    return render_template("delete_confirm1.html", id=word_id, name=word_info[0][0], type="word",
                           logged_in=is_logged_in(), is_teacher=is_teacher())


# Route for confirming the deletion of a word
@app.route('/delete_word_confirm/<word_id>', methods=['POST'])
def delete_word_confirm(word_id):
    # Check if the user is logged in
    if not is_logged_in():
        # If not logged in, redirect to the homepage with a message
        return redirect('/?message=Need+to+be+logged+in.')

    # Delete the word with the specified word_id from the database
    put_data('DELETE FROM Dictionary WHERE word_id = ?', (word_id,))

    # Redirect to the page displaying all words after deletion
    return redirect('/allwords')


# Route for rendering search results
@app.route('/search', methods=['GET', 'POST'])
def render_search():
    # Retrieve a list of all categories from the database
    category_list = get_list("SELECT cat_id, category_name FROM category", "")

    # Get the search term from the form data
    search = request.form['search']

    # Create a title for the search results page
    title = "Search results for: " + search

    # SQL query to search for the term in various columns of the Dictionary table
    query = ("SELECT word_id, Maori, English, definition, level, category_name FROM Dictionary m "
             "INNER JOIN category c ON m.cat_id_fk = c.cat_id "
             "WHERE "
             "word_id LIKE ? OR Maori LIKE ? OR English LIKE ? OR definition LIKE ? OR level LIKE ? "
             "OR category_name LIKE ?")

    # Modify the search term for partial matching
    search = "%" + search + "%"

    # Establish a connection to the database
    con = create_connection(DATABASE)
    cur = con.cursor()

    # Execute the search query with the search term applied to all columns
    cur.execute(query, (search, search, search, search, search, search))

    # Fetch all matching rows
    search_list = cur.fetchall()

    # Close the database connection
    con.close()

    # Render the allwords.html template with the search results and other data
    return render_template("allwords.html", word=search_list, title=title, logged_in=is_logged_in(),
                           categories=category_list)


if __name__ == '__main__':
    app.run()
