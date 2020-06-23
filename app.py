from flask import Flask, render_template, flash, request, redirect, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


# create a instance for flask class
app = Flask(__name__)

#config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] =  'root'
app.config['MYSQL_PASSWORD'] = 'asd@123'
app.config['MYSQL_DB'] = 'MyFlaskApp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#initialize MySQL
mysql = MySQL(app)

#Reports = Reports()

# Index
@app.route('/')
def index():
    return render_template('home.html')

# About
@app.route('/about')
def about():
    return render_template('about.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


# Reports
@app.route('/reports')
@is_logged_in
def reports():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get reports
    result = cur.execute("SELECT * FROM reports")

    reports = cur.fetchall()

    if result > 0:
        return render_template('reports.html', reports=reports)
    else:
        msg = 'No Reports Found'
        return render_template('reports.html', msg=msg)
    # Close connection
    cur.close()


# Single Report
@app.route('/report/<string:id>')
@is_logged_in
def report(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get report
    result = cur.execute("SELECT * FROM reports WHERE id = %s", [id])

    report = cur.fetchone()
    return render_template('report.html', report=report)

    # Close connection
    cur.close()

# Register Form Class
class RegisterForm(Form):
    username = StringField('UserName', [validators.Length(min=1, max=70), validators.DataRequired()])
    email = StringField('Email', [validators.Length(min=6, max=70), validators.DataRequired()])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password do not match')
    ])
    confirm = PasswordField('Confirm Password',[validators.DataRequired()])

# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO user(username, email, password) VALUES(%s, %s, %s)", (username, email, password))

        # commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template ('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM user WHERE username = %s", [username])

        if result > 0:
            # get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            curl.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard', methods=['GET'])
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get reports
    result = cur.execute("SELECT * FROM reports")

    reports = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', reports=reports)
    else:
        msg = 'No Reports Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()

    return render_template('dashboard.html')

# Report Form Class
class ReportForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200), validators.DataRequired()])
    body = TextAreaField('Body', [validators.Length(min=30), validators.DataRequired()])

# Add Report
@app.route('/add_report', methods=['GET', 'POST'])
@is_logged_in
def add_report():
    form = ReportForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO reports(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Report Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_report.html', form=form)

# Edit Report
@app.route('/edit_report/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_report(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get report by id
    result = cur.execute("SELECT * FROM reports WHERE id = %s", [id])

    report = cur.fetchone()

    # Get form
    form = ReportForm(request.form)

    # Populate articles from fields
    form.title.data = report['title']
    form.body.data = report['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("UPDATE reports SET title=%s, body=%s WHERE id = %s", (title, body, id))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Report Edited', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_report.html', form=form)

# Delete report
@app.route('/delete_report/<string:id>', methods=['POST'])
@is_logged_in
def delete_report(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM reports WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    # Close connection
    cur.close()

    flash('Report Deleted', 'success')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key='AAf>%p&vM6(VtB'
    app.run(debug=True)
