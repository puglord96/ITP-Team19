from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import SingletonDatabase
from UserSingleton import UserSingleton
from scripts import tutee_calendar
from pyzoom import ZoomClient
from UserFactory import *
from datetime import datetime as dt

app = Flask(__name__)
client = ZoomClient('TSE_4EYwTrW6_uQYObr4Pg', 'i31hVKhUPjLO6JSp8tFB8DirYI7kauYKOZJF')


# Update the settings of our database below

databaseIP = 'itp.ckmrtwiqitmd.ap-southeast-1.rds.amazonaws.com'
databaseUserName = 'admin'
databasePassword = 'iloveitp'
databaseName = 'itp'

database = SingletonDatabase(app, databaseIP, databaseUserName, databasePassword, databaseName)

DatabaseInstance = database.get_instance()
UserInstance = UserSingleton().get_instance()
UserFactory = UserFactory()


@app.route('/')
def test():
    # Creating a meeting
    #meeting = client.meetings.create_meeting('Test Meeting', start_time=dt.now().isoformat(), duration_min=60,
     #                                         password='')

    #client.meetings.delete_meeting(81168760280)
    #print(meeting.id)
    return render_template("test.html")

@app.route('/test', methods=['GET', 'POST'])
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

@app.route('/meeting')
def meeting():
    return render_template("meeting.html")

@app.route('/home')
def home():
    userRole = UserInstance.getUser().getUserRole()

    switch = {
        1: render_template('admin_test.html'),
        3: render_template('tutee_home.html', calendar_requests=tutee_calendar.calendar_requests,
                           calendar_upcomings=tutee_calendar.calendar_upcomings),
        2: render_template('tutor_test.html')
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

@app.route('/profile', methods=['GET','POST'])
def UpdateProfile():
    user = UserInstance.getUser().getDetailsList()
    facultyList = DatabaseInstance.executeSelectMultipleQuery('SELECT * FROM faculty ORDER BY FacultyID ASC')
    degreeList = DatabaseInstance.executeSelectMultipleQueryWithParameters('SELECT * FROM degree WHERE FacultyID = (%s) ORDER BY DegreeID ASC',[user[8]])
    print("hello")
    print(user[11])
    if request.method == "POST":
        BinaryPicture = ""
        uploaded_file = request.files['image_file']
        print(uploaded_file)
        if uploaded_file.filename != '':
            BinaryPicture = uploaded_file.read()

        formEmail = request.form.get('email')
        formPassword = request.form.get('password')
        formUserType = user[3]
        formFirstName = request.form.get('firstName')
        formLastName = request.form.get('lastName')
        formAlist = request.form.get('alias')
        formMoblieNumber = request.form.get('mobileNumber')
        formFaculty = request.form.get('faculty')
        formDegree = request.form.get('pursuingDegree')
        formGradYear = request.form.get('gradyear')
        DatabaseInstance.executeInsertQuery('UPDATE user SET Email = %s, Password = %s, UserType = %s, FirstName = %s, LastName = %s, Alias = %s, MobileNumber = %s, Faculty = %s, Degree = %s, GraduationYear = %s, ProfilePicture = %s WHERE UserID = %s',
        [formEmail, formPassword, formUserType, formFirstName, formLastName, formAlist, formMoblieNumber, formFaculty, formDegree, formGradYear, BinaryPicture, user[0]])
        userDetailList = DatabaseInstance.getDetailListOfUser(formEmail)
        user = UserFactory.createUser(userDetailList)
        UserInstance.setUser(user)
        return redirect('/profile')
    return render_template('profile.html', facultyList=facultyList, degreeList=degreeList, user=user)

def UploadProfilePic():
    user = UserInstance.getUser().getDetailsList()
    PhotoPath = request.form.get('photo')
    BinaryPicture = convertToBinaryData(PhotoPath)
    DatabaseInstance.executeInsertQuery('UPDATE user SET ProfilePicture = %s WHERE UserID = %s ', [BinaryPicture, user[0]])

def render_picture(data):
    render_pic = ""
    #render_pic = base64.b64encode(data).decode('ascii')
    return render_pic

def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData

if __name__ == '__main__':
    app.run(debug=True)
