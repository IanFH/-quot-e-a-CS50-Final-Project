
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_file
from flask_session import Session
from sqlalchemy import false
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import os


# Set Folder
ALLOWED_EXTENSIONS = {'txt'}

# Configure application
app = Flask(__name__)

# Configure folder
#app.config['UPLOAD_FOLDER'] = IMAGE_FOLDER

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")

# debugging switches

# input txt or paste
debug1 = True

# display unjoined list
debug2 = True

# display joined list
debug3 = True

# displya unique SQL title query
debug4 = False

# different format button route
debug5 = False

# fixing txt input
debug6 = True


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


#what if file name is e.g. text.kindle.txt?
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def homepage():
    return render_template("index.html")


@app.route("/login", methods= ['GET', 'POST'])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Username Field Empty", 'flash_error')
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Password Field Empty", 'flash_error')
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid Username and/or Password", 'flash_error')
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash("Login Successful!", 'flash_success')
        return redirect("/clean")
    if request.method == "GET":
        return render_template("login.html")
    
    return render_template("error.html", message="Login Faied To Load")

@app.route("/register", methods = ['GET', 'POST'])
def register():
    if request.method == "POST":
        # validation
        username = request.form.get("username")

        # if emtpy
        if not username:
            return render_template("register.html", message="Input Username")

        # if username taken
        username_check_dict = db.execute("SELECT username from users")
        username_check = []
        for items in username_check_dict:
            username_check.append(items["username"])
        
        if username in username_check:
            return render_template("register.html", message="Username Taken")

        # if empty password
        password = request.form.get("password")
        if not password:
            return render_template("register.html", message="Input Password")

        # check if passwords are the same
        confirmation = request.form.get("confirmation")
        if password != confirmation:
            return render_template("register.html", message="Password Does Not Match")

        # if password match, hash password
        hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

        # store user in TABLE users
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)

        # obtain automatically assigned user id
        user_id = db.execute("SELECT id FROM users WHERE username = ?", username)
        user_id_id = user_id[0]['id']

        # create TABLE for users portfolio
        db.execute("CREATE TABLE user_highlights_? (highlight_id INTEGER PRIMARY KEY NOT NULL, highlight_counter INTEGER NOT NULL, title TEXT NOT NULL, author TEXT NOT NULL, details TEXT NOT NULL, highlights TEXT NOT NULL)", user_id_id)

        # alert user of successful registration
        flash("Registration Successful", 'flash_success')

        # redirect user to login page
        return redirect("/login")

    if request.method == "GET":
        return render_template("register.html")
    
    return render_template("error.html", message="Registration Failed")

@app.route("/logout")
def logout():
    session.clear()
    flash("You were logged out successfully!", 'flash_success')
    return redirect("/")


@app.route("/clean", methods = ['GET', 'POST'])
@login_required
def clean():
    if request.method == "POST":
        # check if post request has file part, if not then its paste box
        if 'textfile' not in request.files:
            text = request.form["hl-text"]
            if not text:
                flash("Text Field Empty", 'flash_error')
                return render_template("clean.html")
            if debug1:
                print("-----pasted text-----")
                print(text)
                print("-----end of pasted text-----")
            
            # Process text string

            # set counters
            highlight_counter = 0
            colon_counter = 0
            details_end_counter = 0
            equals_counter = 0
            
            # switch
            # 0 = detecting title
            # 1 = detecting author
            # 2 = detecting details
            # 3 = detecting highlights
            # 4 = compiling one highlight block
            switch = 0


            # empty arrays to store data
            title = []
            author = []
            details = []
            highlight = []

            if debug6:
                print("reached start of for loop")

            # iterate through text
            for letter in text:
                # detect title
                if switch == 0 and letter == '(':
                    if debug6:
                        print("reached end of 0")
                    title = title[: len(title)-1]
                    
                    #remove 'ufeff' from list
                    if '\ufeff' in title:
                        title.remove('\ufeff')

                    if '\n' in title:
                        title.remove('\n')

                    if '\r' in title:
                        title.remove('\r')

                    # continue to next step
                    switch = 1
                if switch == 0: 
                    title.append(letter)

                # detect author
                if switch == 1 and letter == ')':
                    if debug6:
                        print("reached end of 1")
                    author = author[1:]
                    switch = 2
                if switch == 1:
                    author.append(letter) 

                # detect details
                if details_end_counter == 2:
                    if debug6:
                        print("reached end of 2")
                    # reset counters
                    colon_counter = 0
                    details_end_counter = 0
                    details = details[5:]
                    switch = 3
                if switch == 2:
                    details.append(letter)                    
                if colon_counter == 2:
                    details_end_counter += 1
                if switch == 2 and letter == ':':
                    colon_counter += 1  

                # detect highlights
                if switch == 3 and letter == '=':
                    equals_counter += 1
                if equals_counter == 10:                
                    if debug6:
                        print("reached end of 3")
                    equals_counter = 0
                    highlight = highlight[4:(len(highlight)-2)]
                    switch = 4
                if switch == 3 and letter != '=':
                    highlight.append(letter)
                
                # compiling highlight block
                if switch == 4:
                    # add to highlight counter
                    highlight_counter += 1

                    # debug before list join
                    if debug2:
                        print("---start of UNjoined highlight---")
                        print("Highlight counter:", highlight_counter)
                        print(title)
                        print(author)
                        print(details)
                        print(highlight)
                        print("equals_counter:", equals_counter)
                        print("---end of UNjoined highlight---")

                    # joining list into strings
                    title_string = ''.join([str(item) for item in title])
                    author_string = ''.join([str(item) for item in author])
                    details_string = ''.join([str(item) for item in details])
                    highlight_string =''.join([str(item) for item in highlight])

                    # debug after list join
                    if debug3:
                        print("---start of joined highlight-----")
                        print("Highlight_counter:", highlight_counter)
                        print(title_string)
                        print(author_string)
                        print(details_string)
                        print(highlight_string)
                        print("---end of joined highlight-----")

                    # get user session id
                    user_id = session["user_id"]

                    # input into user database
                    db.execute("INSERT INTO user_highlights_? (highlight_counter, title, author, details, highlights) VALUES (?, ?, ?, ?, ?)",
                                user_id, highlight_counter, title_string, author_string, details_string, highlight_string)
                    
                    # clear temporary array data
                    title = []
                    author = []
                    details = []
                    highlight = []

                    # switch back and loop over new highlight
                    switch = 0

            flash("Cleaning Successful!", 'flash_success')
            return redirect("/format")

        # if have, then its file submit
        else:
            if debug1:
                print("request.files: ", request.files)

            file = request.files['textfile']

            if debug1:
                print("file: ", file)

            # validate empty file
            if file.filename=="":
                flash("No File Found", 'flash_error')
                if debug1:
                    print("No File Found")
                return render_template("clean.html")

            # validate file format
            if not allowed_file(file.filename):
                flash("Not Supported File Format", 'flash_error')
                if debug1:
                    print("Not Allowed File Format")
                return render_template("clean.html")

            # if cleared all validation
            text = file.read()
            text = str(text)
            if debug1:
                print("----- txt text -----")
                print(text)
                print("-----end of txt text-----")
            
            # Process txt specific text string

            # set counters
            highlight_counter = 0
            colon_counter = 0
            details_end_counter = 0
            equals_counter = 0
            
            # switch
            # 0 = detecting title
            # 1 = detecting author
            # 2 = detecting details
            # 3 = detecting highlights
            # 4 = compiling one highlight block
            switch = 0


            # empty arrays to store data
            title = []
            author = []
            details = []
            highlight = []

            if debug6:
                print("reached start of for loop")

            # iterate through text
            for letter in text:
                # detect title
                if switch == 0 and letter == '(':
                    if debug6:
                        print("reached end of 0")
                    title = title[: len(title)-1]
                    
                    if highlight_counter == 0:
                        title = title[2:]
                    
                    if highlight_counter > 0:
                        title = title[16:]

                    # continue to next step
                    switch = 1
                if switch == 0: 
                    title.append(letter)

                # detect author
                if switch == 1 and letter == ')':
                    if debug6:
                        print("reached end of 1")
                    author = author[1:]
                    switch = 2
                if switch == 1:
                    author.append(letter) 

                # detect details
                if details_end_counter == 2:
                    if debug6:
                        print("reached end of 2")
                    # reset counters
                    colon_counter = 0
                    details_end_counter = 0
                    details = details[5:]
                    switch = 3
                if switch == 2:
                    details.append(letter)                    
                if colon_counter == 2:
                    details_end_counter += 1
                if switch == 2 and letter == ':':
                    colon_counter += 1  

                # detect highlights
                if switch == 3 and letter == '=':
                    equals_counter += 1
                if equals_counter == 10:                
                    if debug6:
                        print("reached end of 3")
                    equals_counter = 0
                    highlight = highlight[8:(len(highlight)-4)]
                    switch = 4
                if switch == 3 and letter != '=':
                    highlight.append(letter)
                
                # compiling highlight block
                if switch == 4:
                    # add to highlight counter
                    highlight_counter += 1

                    # debug before list join
                    if debug2:
                        print("---start of UNjoined highlight---")
                        print("Highlight counter:", highlight_counter)
                        print(title)
                        print(author)
                        print(details)
                        print(highlight)
                        print("equals_counter:", equals_counter)
                        print("---end of UNjoined highlight---")

                    # joining list into strings
                    title_string = ''.join([str(item) for item in title])
                    author_string = ''.join([str(item) for item in author])
                    details_string = ''.join([str(item) for item in details])
                    highlight_string =''.join([str(item) for item in highlight])

                    # debug after list join
                    if debug3:
                        print("---start of joined highlight-----")
                        print("Highlight_counter:", highlight_counter)
                        print(title_string)
                        print(author_string)
                        print(details_string)
                        print(highlight_string)
                        print("---end of joined highlight-----")

                    # replace special character
                    # ' = \xe2\x80\x99

                    character1 = '\\xe2\\x80\\x99'

                    if character1 in highlight_string:
                        if debug6:
                            print("character1 found")
                        highlight_string = highlight_string.replace(character1, "'")


                    # debug after replacing special character
                    if debug3:
                        print("---start of replaced highlight-----")
                        print("Highlight_counter:", highlight_counter)
                        print(title_string)
                        print(author_string)
                        print(details_string)
                        print(highlight_string)
                        print("---end of replaced highlight-----")

                    # get user session id
                    user_id = session["user_id"]

                    # input into user database
                    db.execute("INSERT INTO user_highlights_? (highlight_counter, title, author, details, highlights) VALUES (?, ?, ?, ?, ?)",
                                user_id, highlight_counter, title_string, author_string, details_string, highlight_string)
                    
                    # clear temporary array data
                    title = []
                    author = []
                    details = []
                    highlight = []

                    # switch back and loop over new highlight
                    switch = 0

            flash("Cleaning Successful!", 'flash_success')
            return redirect("/format")     

    if request.method == "GET":
        return render_template("clean.html")

    return render_template("error.html", message="Clean Faied To Load")


@app.route("/format", methods = ['GET', 'POST'])
@login_required
def format():
    if request.method == "GET":
        # get user id
        user_id = session["user_id"]

        # query dictionary of table using db.execute
        highlights_table = db.execute("SELECT * FROM user_highlights_?", user_id)

        # query dictionary for unique books
        title_dictionary = db.execute("SELECT DISTINCT title FROM user_highlights_?", user_id)

        # for debugging same but considered distinct title
        if debug4:
            print("---SQL distinct titles---")
            for title in title_dictionary:
                print(title["title"])

        return render_template("format.html", table=highlights_table, titles=title_dictionary)
    
    if request.method == "POST":
        # get user id
        user_id = session["user_id"]

        # check selected path
        if request.form['format'] == 'delete-selected':
            # debug to check for route
            if debug5:
                print("---delete-selected route choosen---")
            
            # get checked boxes as a list
            checkboxes = request.form.getlist("checkboxes")

            if debug5:
                print("checkboxes getlist : ", checkboxes)

            # validate if checkboxes are empty
            if not checkboxes:
                flash("No Checkboxes Selected!", 'flash_error')
                
                # query dictionary of table using db.execute
                highlights_table = db.execute("SELECT * FROM user_highlights_?", user_id)

                # query dictionary for unique books
                title_dictionary = db.execute("SELECT DISTINCT title FROM user_highlights_?", user_id)
                
                return render_template("format.html", table=highlights_table, titles=title_dictionary)

            # delete highlights with that highlight_id
            for highlight_id in checkboxes:
                db.execute("DELETE FROM user_highlights_? WHERE highlight_id=?", user_id, highlight_id)

            # flash successful delete
            flash("Delete Successful!", 'flash_success')

            # query dictionary of table using db.execute
            highlights_table = db.execute("SELECT * FROM user_highlights_?", user_id)

            # query dictionary for unique books
            title_dictionary = db.execute("SELECT DISTINCT title FROM user_highlights_?", user_id)
            
            return render_template("format.html", table=highlights_table, titles=title_dictionary)


        if request.form['format'] == 'compile-selected':
            if debug5:
                print("---compile-selected route choosen---")

            # get checked boxes as a list
            checkboxes = request.form.getlist("checkboxes")

            # validate if checkboxes are empty
            if not checkboxes:
                flash("No Checkboxes Selected!", 'flash_error')

                # query dictionary of table using db.execute
                highlights_table = db.execute("SELECT * FROM user_highlights_?", user_id)

                # query dictionary for unique books
                title_dictionary = db.execute("SELECT DISTINCT title FROM user_highlights_?", user_id)
                
                return render_template("format.html", table=highlights_table, titles=title_dictionary)

            if debug5:
                print("checkboxes getlist : ", checkboxes)
            
            # declare empty list
            highlight_all_list = []

            # query dictionary with highlight_id selected
            for highlight_id in checkboxes:
                highlight_listofdict = db.execute("SELECT * FROM user_highlights_? WHERE highlight_id=?", user_id, highlight_id)
                highlight = highlight_listofdict[0]
                highlight_list = []
                highlight_list.append(highlight["title"])
                highlight_list.append("\n")
                highlight_list.append(highlight["highlights"])
                highlight_string = ''.join([str(item) for item in highlight_list])
                highlight_all_list.append(highlight_string)
            
            if debug5:
                print("highlight_all_list: ", highlight_all_list)

            # compile all different highlights in a single string
            compiled_highlights = '\n\n'.join(str(item) for item in highlight_all_list)

            if debug5:
                print("compiled_highlights: ", compiled_highlights)
            
            # concatonate path with user_id and create file
            path = "./static/temporarytxt/compiled_highlights_" + str(user_id) + ".txt"

            # remove previous path
            os.remove(path)

            # write string into text file
            text_file = open(path, 'w')
            text_file.write(compiled_highlights)
            text_file.close()

            # send file
            return send_file(path, as_attachment=True)

        if request.form['format'] == 'compile-by-title':
            if debug5:
                print("---compile-by-title route choosen---")
            
            # request for title
            title = request.form.get("titles")

            # validate title
            if not title:
                flash("No Title Selected!", 'flash_error')
                
                # query dictionary of table using db.execute
                highlights_table = db.execute("SELECT * FROM user_highlights_?", user_id)

                # query dictionary for unique books
                title_dictionary = db.execute("SELECT DISTINCT title FROM user_highlights_?", user_id)
                
                return render_template("format.html", table=highlights_table, titles=title_dictionary)

            if debug5:
                print("title: ", title)

            # declare empty list
            highlight_all_list = []

            # query for all highlights with selected title
            highlights_by_title_dict = db.execute("SELECT * FROM user_highlights_? WHERE title=?", user_id, title)

            for highlight in highlights_by_title_dict:
                highlight_list = []

                # declare switch for first check
                first_check_switch = 0
                
                # check for requests
                title_check = request.form.get("title_check")
                if title_check:
                    first_check_switch += 1
                    if first_check_switch != 1:
                        highlight_list.append("\n")
                    highlight_list.append(highlight["title"])

                author_check = request.form.get("author_check")
                if author_check:
                    first_check_switch += 1
                    if first_check_switch != 1:
                        highlight_list.append("\n")
                    highlight_list.append(highlight["author"])

                details_check = request.form.get("details_check")
                if details_check:
                    first_check_switch += 1
                    if first_check_switch != 1:
                        highlight_list.append("\n") 
                    highlight_list.append(highlight["details"])
                
                # append highlight
                first_check_switch += 1
                if first_check_switch != 1:
                        highlight_list.append("\n") 
                highlight_list.append(highlight["highlights"])

                # join list
                highlight_string = ''.join([str(item) for item in highlight_list])

                # join one highlight to all list
                highlight_all_list.append(highlight_string)
            
            if debug5:
                print()
                print("highlight_all_list: \n", highlight_all_list)
            
            # compile all different highlights in a single string
            compiled_highlights = '\n\n'.join(str(item) for item in highlight_all_list)

            if debug5:
                print()
                print("compiled_highlights: \n", compiled_highlights)
            
            # concatonate path with user_id and create file
            path = "./static/temporarytxt/compiled_highlights_" + str(user_id) + ".txt"

            # remove previous path
            os.remove(path)

            # write string into text file
            text_file = open(path, 'w')
            text_file.write(compiled_highlights)
            text_file.close()

            # send file
            return send_file(path, as_attachment=True)

    return render_template("error.html", message="Format Failed To Load")


@app.route("/credit")
def credit():
    return send_file("credits.txt", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=False)