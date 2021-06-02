from flask import Flask, render_template, request
from database import SingletonDatabase

app = Flask(__name__)

# Update the settings of our database below

databaseIP = 'localhost'
databaseUserName = 'root'
databasePassword = 'sceptile101'
databaseName = 'itpproject'

database = SingletonDatabase(app, databaseIP, databaseUserName, databasePassword, databaseName)

testDatabaseInstance = database.get_instance()



@app.route('/')
def hello_world():
    testDatabaseInstance.executeNonSelectQuery("CREATE TABLE Persons (PersonID int, LastName varchar(255), FirstName varchar(255), Address varchar(255), City varchar(255)) ")
    return 'Hello World!'

if __name__ == '__main__':
    app.run()
