from flask import Flask, render_template, request
from database import SingletonDatabase

app = Flask(__name__)

# Update the settings of our database below

databaseIP = 'itp.ckmrtwiqitmd.ap-southeast-1.rds.amazonaws.com'
databaseUserName = 'admin'
databasePassword = 'iloveitp'
databaseName = 'itp'

database = SingletonDatabase(app, databaseIP, databaseUserName, databasePassword, databaseName)

testDatabaseInstance = database.get_instance()



@app.route('/')
def login():
    testDatabaseInstance.executeNonSelectQuery("CREATE TABLE IF NOT EXISTS itp.Persons (PersonID int, LastName varchar(255), FirstName varchar(255), Address varchar(255), City varchar(255)) ")
    return render_template('login.html')


@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')


@app.route('/register')
def register():
    return render_template('register.html')


if __name__ == '__main__':
    app.run()
