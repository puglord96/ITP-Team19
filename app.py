from flask import Flask, render_template, request, redirect, url_for
from flask import jsonify
from database import SingletonDatabase
from UserSingleton import UserSingleton
from scripts import tutee_calendar
from pyzoom import ZoomClient
from UserFactory import *

app = Flask(__name__)
client = ZoomClient('0Q8s81KuT_2jFfxq3HYPNQ', 'IGZG9x2f4T4Z7JWfnkELg3sbRDg8YctQ5Ajp')

# Update the settings of our database below

databaseIP = 'itp.ckmrtwiqitmd.ap-southeast-1.rds.amazonaws.com'
databaseUserName = 'admin'
databasePassword = 'iloveitp'
databaseName = 'itp'

database = SingletonDatabase(app, databaseIP, databaseUserName, databasePassword, databaseName)

DatabaseInstance = database.get_instance()
UserInstance = UserSingleton().get_instance()
UserFactory = UserFactory()


@app.route('/', methods=['GET', 'POST'])
def login():
    userlist = DatabaseInstance.executeSelectMultipleQuery("Select email,password from user")
    if request.method == "POST":
        formEmail = request.form.get('email')
        formPassword = request.form.get('password')
        for user in userlist:
            if formEmail == user[0] and formPassword == user[1]:
                userDetailList = DatabaseInstance.getDetailListOfUser(formEmail)

                user = UserFactory.createUser(userDetailList)

                UserInstance.setUser(user)

                print(user.getUserRole())

                return redirect('/home')
    return render_template('login.html')


@app.route('/home')
def home():
    userRole = UserInstance.getUser().getUserRole()

    switch = {
        1: render_template('admin_test.html'),
        2: render_template('tutee_home.html', calendar_requests=tutee_calendar.calendar_requests,
                           calendar_upcomings=tutee_calendar.calendar_upcomings),
        3: render_template('tutor_test.html')
    }
    return switch.get(userRole, render_template('error_page.html'))


@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == "POST":
        formEmail = request.form.get('email')
        formPassword = request.form.get('password')
        formUserType = 2
        formFirstName = request.form.get('firstName')
        formLastName = request.form.get('lastName')
        formFaculty = request.form.get('faculty')
        formDegree = request.form.get('pursuingDegree')
        formGradYear = request.form.get('gradyear')
        DatabaseInstance.executeInsertQuery("INSERT INTO user(email, password, usertype, firstname, lastname, faculty, degree, graduationyear) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", [formEmail, formPassword, formUserType, formFirstName, formLastName, formFaculty, formDegree, formGradYear])
        return redirect('/')

    facultyList = DatabaseInstance.executeSelectMultipleQuery('SELECT * FROM faculty ORDER BY FacultyID ASC')
    return render_template('register.html', facultyList=facultyList)

@app.route('/register/faculty/<Faculty>')
def DegreeByFaculty(Faculty):
    degreeList = DatabaseInstance.executeSelectMultipleQueryWithParameters('SELECT * FROM degree WHERE FacultyID = (%s) ORDER BY DegreeID ASC', [Faculty])
    degreeArray = []
    for row in degreeList:
        degreeOjb = {}
        degreeOjb['id'] = row[0]
        degreeOjb['name'] = row[2]
        degreeArray.append(degreeOjb)
    return jsonify({'degreeList': degreeArray})

if __name__ == '__main__':
    app.run()
