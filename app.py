from flask import Flask,render_template, request
from database import database

app = Flask(__name__)

databaseIP = 'localhost'
databaseUserName = 'root'
databasePassword = 'sceptile101'
databaseName = 'itpproject'

database = database(app,databaseIP,databaseUserName,databasePassword,databaseName)


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
