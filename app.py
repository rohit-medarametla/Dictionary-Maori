from flask import Flask, render_template, redirect, request, session

app = Flask(__name__)


@app.route('/')
def render_homepage():
    return render_template('test.html')

if __name__ == '__main__':
    app.run()
