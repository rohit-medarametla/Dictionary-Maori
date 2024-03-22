from flask import Flask, render_template, redirect, request, session

app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello Worgiugild!'

@app.route('/home')
def render_contact_page():
    return render_template('home.html')

if __name__ == '__main__':
    app.run()
