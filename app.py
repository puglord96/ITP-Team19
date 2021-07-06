from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response
from database import SingletonDatabase
from UserSingleton import UserSingleton
from scripts import tutor_calendar
from pyzoom import ZoomClient
from UserFactory import *
from datetime import datetime as dt
from base64 import b64encode
import os

app = Flask(__name__)
SECRET_KEY = os.urandom(24)
app.secret_key = SECRET_KEY

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


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    tutortuteename = DatabaseInstance.getUserDetails(2)[4] + " " + DatabaseInstance.getUserDetails(2)[5]
    userRole = UserInstance.getUser().getUserRole()

    meetingid = request.cookies.get("meeting_id")

    if userRole == 2:
        subjectRole = 3
    else:
        subjectRole = 2



    if request.method == "POST":
        feedbacktuteetutor = request.form.get('tutortuteename')
        feedbacksessionrating = request.form.get('sessionrating')
        feedbacktutortuteerating = request.form.get('tutortuteerating')
        feedbackremarks = request.form.get('remarks')


        DatabaseInstance.executeInsertQueryWithParameters(
            "Insert into feedback(sessionrating,tutortuteerating,remark,tutortuteename,subjectrole) values(%s,%s,%s,%s,%s)",
            [feedbacksessionrating, feedbacktutortuteerating, feedbackremarks, feedbacktuteetutor,subjectRole])

        if userRole == 2:
            DatabaseInstance.executeUpdateQueryWithParameters(
                "update meeting set tutorsurvey = 'done' where meetingid = %s", [meetingid])
        elif userRole == 3:
            DatabaseInstance.executeUpdateQueryWithParameters(
                "update meeting set tuteesurvey = 'done' where meetingid = %s", [meetingid])
    return render_template("feedback.html", tutortuteename=tutortuteename)


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

                return redirect('/home')
    return render_template('login.html')




@app.route('/ztest')
def zoom_test():
    # Creating a meeting
    # meeting = client.meetings.create_meeting('Test Meeting', start_time=dt.now().isoformat(), duration_min=60,
    #                                          password='password')

    # client.meetings.delete_meeting(86705874597)
    # print(meeting.id)
    return render_template("zoom_meeting_test.html")


@app.route('/sessionbooking', methods=['GET','POST'])
def session_booking():
    disciplinelist = DatabaseInstance.executeSelectMultipleQuery("Select name from degree")
    return render_template("session_booking.html", disciplinelist=disciplinelist)


@app.route('/meeting')
def meeting():
    return render_template("meeting.html")


@app.route('/home')
def home():


    userRole = UserInstance.getUser().getUserRole()
    userName = UserInstance.getUser().getUserName()
    userLandingPage = UserInstance.getUser().landing_page

    if userRole == 2:
        meetingslist = DatabaseInstance.executeSelectMultipleQueryWithParameters("SELECT u.firstname, u.lastname, m.venue,m.starttime,m.endtime,m.topic,m.meetingid from user u,meeting m where m.tuteeID = u.UserID and m.tuteeID = %s", [userRole])
    else:
        meetingslist = DatabaseInstance.executeSelectMultipleQueryWithParameters("SELECT u.firstname, u.lastname, m.venue,m.starttime,m.endtime,m.topic,m.meetingid from user u,meeting m where m.tutorID = u.UserID and m.tuteeID = %s", [userRole])



    landingswitch = {
        1: render_template(userLandingPage),
        3: render_template(userLandingPage,calendar_upcomings=meetingslist),
        2: render_template('tutor_home.html', calendar_requests=tutor_calendar.calendar_requests,
                           calendar_upcomings=tutor_calendar.calendar_upcomings)
    }

    resp = make_response(landingswitch.get(userRole, render_template('error_page.html')))
    # resp.set_cookie('meeting_number', "1000121")
    resp.set_cookie('display_name', userName)
    return resp



@app.route('/tutor_upcoming_meeting')
def tutee_upcoming_meeting():
    userRole = UserInstance.getUser().getUserRole()
    if userRole == 2:
        return render_template("tutor_upcoming_meeting.html", calendar_upcomings=tutor_calendar.calendar_upcomings)
    return render_template ("error_page.html")


@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        formEmail = request.form.get('email')
        formPassword = request.form.get('password')
        formUserType = 3
        formFirstName = request.form.get('firstName')
        formLastName = request.form.get('lastName')
        formFaculty = request.form.get('faculty')
        formDegree = request.form.get('pursuingDegree')
        formGradYear = request.form.get('gradyear')
        DatabaseInstance.executeInsertQueryWithParameters(
            "INSERT INTO user(email, password, usertype, firstname, lastname, faculty, degree, graduationyear) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            [formEmail, formPassword, formUserType, formFirstName, formLastName, formFaculty, formDegree, formGradYear])
        return redirect('/')

    facultyList = DatabaseInstance.executeSelectMultipleQuery('SELECT * FROM faculty ORDER BY FacultyID ASC')
    return render_template('register.html', facultyList=facultyList)


@app.route('/register/faculty/<Faculty>')
def DegreeByFaculty(Faculty):
    degreeList = DatabaseInstance.executeSelectMultipleQueryWithParameters(
        'SELECT * FROM degree WHERE FacultyID = (%s) ORDER BY DegreeID ASC', [Faculty])
    degreeArray = []
    for row in degreeList:
        degreeOjb = {}
        degreeOjb['id'] = row[0]
        degreeOjb['name'] = row[2]
        degreeArray.append(degreeOjb)
    return jsonify({'degreeList': degreeArray})


@app.route('/profile', methods=['GET', 'POST'])
def UpdateProfile():
    user = UserInstance.getUser().getDetailsList()
    if request.method == "POST":
        BinaryPicture = ""
        uploaded_file = request.files['image_file']
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
        if formPassword:
            if BinaryPicture:
                DatabaseInstance.executeUpdateQueryWithParameters(
                    'UPDATE user SET Email = %s, Password = %s, UserType = %s, FirstName = %s, LastName = %s, Alias = %s, MobileNumber = %s, Faculty = %s, Degree = %s, GraduationYear = %s, ProfilePicture = %s WHERE UserID = %s',
                    [formEmail, formPassword, formUserType, formFirstName, formLastName, formAlist, formMoblieNumber,
                     formFaculty, formDegree, formGradYear, BinaryPicture, user[0]])
            else:
                DatabaseInstance.executeUpdateQueryWithParameters(
                    'UPDATE user SET Email = %s, Password = %s, UserType = %s, FirstName = %s, LastName = %s, Alias = %s, MobileNumber = %s, Faculty = %s, Degree = %s, GraduationYear = %sWHERE UserID = %s',
                    [formEmail, formPassword, formUserType, formFirstName, formLastName, formAlist, formMoblieNumber,
                     formFaculty, formDegree, formGradYear, user[0]])
        else:
            if BinaryPicture:
                DatabaseInstance.executeUpdateQueryWithParameters(
                    'UPDATE user SET Email = %s, UserType = %s, FirstName = %s, LastName = %s, Alias = %s, MobileNumber = %s, Faculty = %s, Degree = %s, GraduationYear = %s, ProfilePicture = %s WHERE UserID = %s',
                    [formEmail, formUserType, formFirstName, formLastName, formAlist, formMoblieNumber, formFaculty,
                     formDegree, formGradYear, BinaryPicture, user[0]])
            else:
                DatabaseInstance.executeUpdateQueryWithParameters(
                    'UPDATE user SET Email = %s, UserType = %s, FirstName = %s, LastName = %s, Alias = %s, MobileNumber = %s, Faculty = %s, Degree = %s, GraduationYear = %s WHERE UserID = %s',
                    [formEmail, formUserType, formFirstName, formLastName, formAlist, formMoblieNumber, formFaculty,
                     formDegree, formGradYear, user[0]])

        formExpertises = request.form.getlist("expertises")
        formTimeSlot = request.form.getlist("timeSlot")
        if formExpertises:
            DBexpertisesList = ['EssayWriting', 'ReportWriting', 'OralPresentation', 'GrammarCheck', 'SpellingCheck']
            if DatabaseInstance.executeSelectOneQuery('SELECT * FROM userexpertises WHERE UserID = {}'.format(user[0])):
                for i in DBexpertisesList:
                    DatabaseInstance.executeUpdateQuery(
                        'UPDATE userexpertises SET {} = 0 WHERE UserID = {}'.format(i, user[0]))
                for i in formExpertises:
                    DatabaseInstance.executeUpdateQuery(
                        'UPDATE userexpertises SET {} = 1 WHERE UserID = {}'.format(DBexpertisesList[int(i)], user[0]))
            else:
                DatabaseInstance.executeInsertQueryWithParameters('INSERT INTO userexpertises (UserID) VALUES (%s)',
                                                                  [user[0]])
                for i in formExpertises:
                    DatabaseInstance.executeUpdateQuery(
                        'UPDATE userexpertises SET {} = 1 WHERE UserID = {}'.format(DBexpertisesList[int(i)], user[0]))
        if formTimeSlot:
            DBtimeSlotList = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            if DatabaseInstance.executeSelectOneQuery(
                    'SELECT * FROM usertimeslotpreference WHERE UserID = {}'.format(user[0])):
                for i in DBtimeSlotList:
                    DatabaseInstance.executeUpdateQuery(
                        'UPDATE usertimeslotpreference SET {} = 0 WHERE UserID = {}'.format(i, user[0]))
                for i in formTimeSlot:
                    DatabaseInstance.executeUpdateQuery(
                        'UPDATE usertimeslotpreference SET {} = 1 WHERE UserID = {}'.format(DBtimeSlotList[int(i)],
                                                                                            user[0]))
            else:
                DatabaseInstance.executeInsertQueryWithParameters(
                    'INSERT INTO usertimeslotpreference (UserID) VALUES (%s)', [user[0]])
                for i in formTimeSlot:
                    DatabaseInstance.executeUpdateQuery(
                        'UPDATE usertimeslotpreference SET {} = 1 WHERE UserID = {}'.format(DBtimeSlotList[int(i)],
                                                                                            user[0]))

        userDetailList = DatabaseInstance.getUserDetails(str(user[0]))
        user = UserFactory.createUser(userDetailList)
        UserInstance.setUser(user)
        return redirect('/profile')

    expertisesList = ['Essay Writing', 'Report Writing', 'Oral Presentation', 'Gammar Check', 'Spelling Check']
    timeSlotList = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    facultyList = DatabaseInstance.executeSelectMultipleQuery('SELECT * FROM faculty ORDER BY FacultyID ASC')
    degreeList = DatabaseInstance.executeSelectMultipleQueryWithParameters(
        'SELECT * FROM degree WHERE FacultyID = (%s) ORDER BY DegreeID ASC', [user[8]])
    profilePic = ""
    if user[11]:
        profilePic = b64encode(user[11]).decode("utf-8")

    userExpertisesList = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT EssayWriting, ReportWriting, OralPresentation, GrammarCheck, SpellingCheck FROM userexpertises WHERE UserID = (%s)',
        [user[0]])
    userTimeSlotList = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday FROM usertimeslotpreference WHERE UserID = (%s)',
        [user[0]])

    return render_template('profile.html', facultyList=facultyList, degreeList=degreeList, user=user,
                           profilePic=profilePic, expertisesList=expertisesList, timeSlotList=timeSlotList,
                           userExpertisesList=userExpertisesList, userTimeSlotList=userTimeSlotList)

@app.route('/admin')
def index(chartID = 'container', chart_type = 'line', chart_height = 350):
	chart = {"renderTo": chartID, "type": chart_type, "height": chart_height,}
	series = [{'name': 'data1', "data": [1,2,3]}, {"name": 'data2', "data": [4, 5, 6]}]
	title = {"{text": 'Today}'}
	xAxis = {"categories": ['xAxis Data1', 'xAxis Data2']}
	yAxis = {"title": {"text": 'yAxis Label'}}
	return render_template('admin_home.html', chartID=chartID, chart=chart, series=series, title=title, xAxis=xAxis, yAxis=yAxis)

if __name__ == '__main__':
    app.run(debug=True)
