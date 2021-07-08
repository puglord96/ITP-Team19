from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response
from database import SingletonDatabase
from UserSingleton import UserSingleton
from scripts import tutor_calendar
from pyzoom import ZoomClient
from UserFactory import *
from datetime import datetime as dt
from datetime import timedelta
from base64 import b64encode
import os

app = Flask(__name__)
# Upload file size limit to 4GB
app.config['MAX_CONTENT_LENGTH'] = 4086 * 1024 * 1024
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
    subjectRole = UserInstance.getUser().feedback_subject_role

    meetingid = request.cookies.get("meeting_id")

    if request.method == "POST":
        feedbacktuteetutor = request.form.get('tutortuteename')
        feedbacksessionrating = request.form.get('sessionrating')
        feedbacktutortuteerating = request.form.get('tutortuteerating')
        feedbackremarks = request.form.get('remarks')

        DatabaseInstance.executeInsertQueryWithParameters(
            "Insert into feedback(sessionrating,tutortuteerating,remark,tutortuteename,subjectrole) values(%s,%s,%s,%s,%s)",
            [feedbacksessionrating, feedbacktutortuteerating, feedbackremarks, feedbacktuteetutor, subjectRole])

        DatabaseInstance.executeUpdateQuery(UserInstance.getUser().updateFeedbackString(meetingid))

        return redirect('/home')
    return render_template("feedback.html", tutortuteename=tutortuteename)


# 1 - Admin
# 2 - Tutor
# 3 - Tutee
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
                zoomRole = UserInstance.getUser().getZoomRole()

                resp = make_response(redirect('/home'))
                resp.set_cookie('zoom_role', str(zoomRole))

                return resp
    return render_template('login.html')


@app.route('/ztest')
def zoom_test():
    # Creating a meeting
    # meeting = client.meetings.create_meeting('Test Meeting', start_time=dt.now().isoformat(), duration_min=60,
    #                                          password='password')

    # client.meetings.delete_meeting(86705874597)
    # print(meeting.id)
    return render_template("zoom_meeting_test.html")


@app.route('/sessionbooking', methods=['GET', 'POST'])
def session_booking():
    disciplinelist = DatabaseInstance.executeSelectMultipleQuery("Select name from degree")
    return render_template("session_booking.html", disciplinelist=disciplinelist)


@app.route('/meeting')
def meeting():
    return render_template("meeting.html")


@app.route('/home')
def home():
    global upcomingmeetingslist, requestmeetingslist
    userID = UserInstance.getUser().getUserID()
    userRole = UserInstance.getUser().getUserRole()
    userName = UserInstance.getUser().getUserName()
    userLandingPage = UserInstance.getUser().landing_page
    upcomingmeetingslistquery = UserInstance.getUser().upcomingMeetingsList(userID)
    requestmeetingslistquery = UserInstance.getUser().requestMeetingsList(userID)


    if upcomingmeetingslistquery is not None:
        upcomingmeetingslist = DatabaseInstance.executeSelectMultipleQuery(upcomingmeetingslistquery)
    else:
        upcomingmeetingslist = ""

    if requestmeetingslistquery is not None:
        requestmeetingslist = DatabaseInstance.executeSelectMultipleQuery(
            UserInstance.getUser().requestMeetingsList(userID))
    else:
        requestmeetingslist = ""

    landingswitch = {
        1: render_template(userLandingPage),
        3: render_template(userLandingPage, calendar_upcomings=upcomingmeetingslist),
        2: render_template(userLandingPage, calendar_requests=requestmeetingslist,
                           calendar_upcomings=upcomingmeetingslist)
    }

    resp = make_response(landingswitch.get(userRole, render_template('error_page.html')))
    # resp.set_cookie('meeting_number', "1000121")
    resp.set_cookie('display_name', userName)
    return resp


@app.route('/tutor_upcoming_meeting')
def tutor_upcoming_meeting():
    userRole = UserInstance.getUser().getUserRole()
    if userRole == 2:
        print(upcomingmeetingslist)
        return render_template("tutor_upcoming_meeting.html", calendar_upcomings=upcomingmeetingslist)
    return render_template("error_page.html")


@app.route('/tutor_upcoming_request')
def tutor_upcoming_request():
    userRole = UserInstance.getUser().getUserRole()
    if userRole == 2:
        print(requestmeetingslist)
        return render_template("tutor_upcoming_request.html", calendar_requests=requestmeetingslist)
    return render_template("error_page.html")


@app.route('/view_meeting/<meetingid>')
def view_meeting(meetingid):
    # if request.method == "POST":
    #     if request.form.get('accept'):
    #         print("accept")
    #         DatabaseInstance.executeUpdateQuery(UserInstance.getUser().acceptRequest(meetingid))
    #         return redirect('/home')
    #     elif request.form.get("decline"):
    #         print("decline")
    #         DatabaseInstance.executeUpdateQuery(UserInstance.getUser().declineRequest(meetingid))
    #         return redirect('/home')
    userRole = UserInstance.getUser().getUserRole()
    if userRole == 2:
        requestMeeting = DatabaseInstance.executeSelectMultipleQuery(UserInstance.getUser().requestMeeting(meetingid))
        userID = UserInstance.getUser().getUserID()
        # prevent injection of URL (make sure that tutor is tutor of the meeting)
        if userID == requestMeeting[0][1] and requestMeeting[0][4] == 1:
            tutorname = DatabaseInstance.executeSelectMultipleQuery(
                UserInstance.getUser().getUser(str(requestMeeting[0][1])))
            tutorname = tutorname[0][0] + " " + tutorname[0][1]
            tuteename = DatabaseInstance.executeSelectMultipleQuery(
                UserInstance.getUser().getUser(str(requestMeeting[0][2])))
            tuteename = tuteename[0][0] + " " + tuteename[0][1]
            meetingtype = DatabaseInstance.executeSelectMultipleQuery(
                UserInstance.getUser().getMeetingType(str(requestMeeting[0][3])))
            meetingtype = meetingtype[0][0]
            status = DatabaseInstance.executeSelectMultipleQuery(
                UserInstance.getUser().getstatustype(str(requestMeeting[0][4])))
            status = status[0][0]
            venue = requestMeeting[0][5]
            attendance = requestMeeting[0][6]
            starttime = requestMeeting[0][7]
            endtime = requestMeeting[0][8]
            topic = requestMeeting[0][12]
            return render_template('view_meeting.html', meetingid=meetingid, tutorname=tutorname, tuteename=tuteename,
                                   meetingtype=meetingtype, status=status, venue=venue, attendance=attendance,
                                   starttime=starttime
                                   , endtime=endtime, topic=topic)
    return redirect(url_for('home'))


@app.route('/view_request/<meetingid>', methods=['GET', 'POST'])
def view_request(meetingid):
    if request.method == "POST":
        if request.form.get('accept'):
            print("accept")
            DatabaseInstance.executeUpdateQuery(UserInstance.getUser().acceptRequest(meetingid))
            return redirect('/home')
        elif request.form.get("decline"):
            print("decline")
            DatabaseInstance.executeUpdateQuery(UserInstance.getUser().declineRequest(meetingid))
            return redirect('/home')
    userRole = UserInstance.getUser().getUserRole()
    if userRole == 2:
        requestMeeting = DatabaseInstance.executeSelectMultipleQuery(UserInstance.getUser().requestMeeting(meetingid))
        userID = UserInstance.getUser().getUserID()
        # prevent injection of URL (make sure that tutor is tutor of the meeting)
        if userID == requestMeeting[0][1] and requestMeeting[0][4] == 2:
            tutorname = DatabaseInstance.executeSelectMultipleQuery(
                UserInstance.getUser().getUser(str(requestMeeting[0][1])))
            tutorname = tutorname[0][0] + " " + tutorname[0][1]
            tuteename = DatabaseInstance.executeSelectMultipleQuery(
                UserInstance.getUser().getUser(str(requestMeeting[0][2])))
            tuteename = tuteename[0][0] + " " + tuteename[0][1]
            meetingtype = DatabaseInstance.executeSelectMultipleQuery(
                UserInstance.getUser().getMeetingType(str(requestMeeting[0][3])))
            meetingtype = meetingtype[0][0]
            status = DatabaseInstance.executeSelectMultipleQuery(
                UserInstance.getUser().getstatustype(str(requestMeeting[0][4])))
            status = status[0][0]
            venue = requestMeeting[0][5]
            attendance = requestMeeting[0][6]
            starttime = requestMeeting[0][7]
            endtime = requestMeeting[0][8]
            topic = requestMeeting[0][12]
            return render_template('view_request.html', meetingid=meetingid, tutorname=tutorname, tuteename=tuteename,
                                   meetingtype=meetingtype, status=status, venue=venue, attendance=attendance,
                                   starttime=starttime
                                   , endtime=endtime, topic=topic)
    return redirect(url_for('home'))


# @app.route('/view_request/<string:meetingid>', methods=['POST'])
# def view_request(meetingid):
#     meetingid = json.loads(meetingid)
#     meetingid = meetingid['id'][:-1]
#     print(meetingid)
#     return redirect(url_for('tutor_test', meetingid=meetingid))


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
            "INSERT INTO user(email, password, usertype, firstname, lastname, faculty, degree, graduationyear, DateJoin) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [formEmail, formPassword, formUserType, formFirstName, formLastName, formFaculty, formDegree, formGradYear,
             dt.today().strftime('%Y-%m-%d ')])
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


@app.route('/profile')
def profile():
    user = UserInstance.getUser().getDetailsList()
    userRole = UserInstance.getUser().getUserRole()
    landingpage = UserInstance.getUser().getProfileLandingPage()

    expertisesList = ['Essay Writing', 'Technical Proposal', 'Oral Presentation', 'Reader Response', 'Reflection']
    timeSlotList = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    gender = \
    DatabaseInstance.executeSelectOneQueryWithParameters('Select gender from gender where gender_id = %s', [user[12]])[
        0]
    faculty = \
    DatabaseInstance.executeSelectOneQueryWithParameters('Select name from faculty where facultyid = %s', [user[8]])[0]
    degree = \
    DatabaseInstance.executeSelectOneQueryWithParameters('SELECT name FROM degree WHERE  DegreeID = %s', [user[9]])[0]
    profilePic = ""
    if user[11]:
        profilePic = b64encode(user[11]).decode("utf-8")

    userExpertisesList = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT EssayWriting, TechnicalProposal, OralPresentation, ReaderResponse, Reflection FROM userexpertises WHERE UserID = (%s)',
        [user[0]])

    userexpertise = []
    expertiseListIndex = 0
    if userExpertisesList:
        for expertise in userExpertisesList:
            if expertise == 1:
                userexpertise.append(expertisesList[expertiseListIndex])
            expertiseListIndex += 1

    userTimeSlotList = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday FROM usertimeslotpreference WHERE UserID = (%s)',
        [user[0]])

    timeslot = []
    timeslotindex = 0
    if userTimeSlotList:
        for usertimeslot in userTimeSlotList:
            if usertimeslot == 1:
                timeslot.append(timeSlotList[timeslotindex])
            timeslotindex += 1

    landingswitch = {
        1: render_template(landingpage, faculty=faculty, degree=degree, user=user,
                           profilePic=profilePic, expertisesList=expertisesList, timeSlotList=timeSlotList,
                           userexpertise=userexpertise, userTimeSlotList=userTimeSlotList, gender=gender,
                           timeslot=timeslot),
        2: render_template(landingpage, faculty=faculty, degree=degree, user=user,
                           profilePic=profilePic, expertisesList=expertisesList, timeSlotList=timeSlotList,
                           userexpertise=userexpertise, userTimeSlotList=userTimeSlotList, gender=gender,
                           timeslot=timeslot),
        3: render_template(landingpage, faculty=faculty, degree=degree, user=user,
                           profilePic=profilePic, gender=gender)
    }
    return landingswitch.get(userRole, render_template('error_page.html'))


@app.route('/updateprofile', methods=['GET', 'POST'])
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
        formGender = request.form.get('Gender')

        print(formGender)
        if formPassword:
            if BinaryPicture:
                DatabaseInstance.executeUpdateQueryWithParameters(
                    'UPDATE user SET Email = %s, Password = %s, UserType = %s, FirstName = %s, LastName = %s, Alias = %s, MobileNumber = %s, Faculty = %s, Degree = %s, GraduationYear = %s, ProfilePicture = %s,gender=%s WHERE UserID = %s',
                    [formEmail, formPassword, formUserType, formFirstName, formLastName, formAlist, formMoblieNumber,
                     formFaculty, formDegree, formGradYear, BinaryPicture, formGender, user[0]])
            else:
                DatabaseInstance.executeUpdateQueryWithParameters(
                    'UPDATE user SET Email = %s, Password = %s, UserType = %s, FirstName = %s, LastName = %s, Alias = %s, MobileNumber = %s, Faculty = %s, Degree = %s, GraduationYear = %s,gender=%s WHERE UserID = %s',
                    [formEmail, formPassword, formUserType, formFirstName, formLastName, formAlist, formMoblieNumber,
                     formFaculty, formDegree, formGradYear, formGender, user[0]])
        else:
            if BinaryPicture:
                DatabaseInstance.executeUpdateQueryWithParameters(
                    'UPDATE user SET Email = %s, UserType = %s, FirstName = %s, LastName = %s, Alias = %s, MobileNumber = %s, Faculty = %s, Degree = %s, GraduationYear = %s, ProfilePicture = %s,gender=%s WHERE UserID = %s',
                    [formEmail, formUserType, formFirstName, formLastName, formAlist, formMoblieNumber, formFaculty,
                     formDegree, formGradYear, BinaryPicture, formGender, user[0]])
            else:
                DatabaseInstance.executeUpdateQueryWithParameters(
                    'UPDATE user SET Email = %s, UserType = %s, FirstName = %s, LastName = %s, Alias = %s, MobileNumber = %s, Faculty = %s, Degree = %s, GraduationYear = %s,gender=%s WHERE UserID = %s',
                    [formEmail, formUserType, formFirstName, formLastName, formAlist, formMoblieNumber, formFaculty,
                     formDegree, formGradYear, formGender, user[0]])

        formExpertises = request.form.getlist("expertises")
        formTimeSlot = request.form.getlist("timeSlot")
        if formExpertises:
            DBexpertisesList = ['Essay Writing', 'Technical Proposal', 'Oral Presentation', 'Reader Response',
                                'Reflection']
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

    expertisesList = ['Essay Writing', 'Technical Proposal', 'Oral Presentation', 'Reader Response', 'Reflection']
    timeSlotList = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    facultyList = DatabaseInstance.executeSelectMultipleQuery('SELECT * FROM faculty ORDER BY FacultyID ASC')
    degreeList = DatabaseInstance.executeSelectMultipleQueryWithParameters(
        'SELECT * FROM degree WHERE FacultyID = (%s) ORDER BY DegreeID ASC', [user[8]])
    genderList = DatabaseInstance.executeSelectMultipleQuery('Select * from gender')
    print(user[12])
    print(genderList[0][0])
    profilePic = ""
    if user[11]:
        profilePic = b64encode(user[11]).decode("utf-8")

    userExpertisesList = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT EssayWriting, TechnicalProposal, OralPresentation, ReaderResponse, Reflection FROM userexpertises WHERE UserID = (%s)',
        [user[0]])
    userTimeSlotList = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday FROM usertimeslotpreference WHERE UserID = (%s)',
        [user[0]])

    return render_template('update_profile.html', facultyList=facultyList, degreeList=degreeList, user=user,
                           profilePic=profilePic, expertisesList=expertisesList, timeSlotList=timeSlotList,
                           userExpertisesList=userExpertisesList, userTimeSlotList=userTimeSlotList,
                           genderList=genderList)


@app.route('/admin')
def admin():
    pageTitle = "Home"
    title = "Daily Appointments for past 30 day"
    subtitle = dt.today().strftime('%d-%b-%Y, %I:%M%p')
    tmr = dt.today() + timedelta(days=1)
    total = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT COUNT(MeetingID) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL 30 DAY AND (%s);',
        [dt.today().strftime('%Y-%m-%d'), tmr.strftime('%Y-%m-%d')])
    completedApp = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT COUNT(MeetingID) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL 30 DAY AND (%s) AND Attendance >= 2',
        [dt.today().strftime('%Y-%m-%d'), dt.today().strftime('%Y-%m-%d %H:%M:%S')])
    avgRating = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT AVG(Rating) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL 30 DAY AND (%s) AND Attendance >= 2',
        [dt.today().strftime('%Y-%m-%d'), dt.today().strftime('%Y-%m-%d %H:%M:%S')])
    avgMeetingTime = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT AVG(timestampdiff(MINUTE, StartTime,EndTime)) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL 30 DAY AND (%s) AND Attendance >= 2',
        [dt.today().strftime('%Y-%m-%d'), tmr.strftime('%Y-%m-%d')])
    popularRequest = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT  Topic, COUNT(*) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL 30 DAY AND (%s)',
        [dt.today().strftime('%Y-%m-%d'), tmr.strftime('%Y-%m-%d')])
    dataTotalApp = []
    dataComApp = []
    for i in range(29, -1, -1):
        totalApp = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT COUNT(MeetingID) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL (%s) DAY AND (%s) - INTERVAL (%s) DAY',
            [dt.today().strftime('%Y-%m-%d '), i, tmr.strftime('%Y-%m-%d '), i])
        completedApp = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT COUNT(MeetingID) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL (%s) DAY AND (%s) - INTERVAL (%s) DAY AND Attendance >= 2',
            [dt.today().strftime('%Y-%m-%d '), i, tmr.strftime('%Y-%m-%d '), i])
        dataTotalApp.append(totalApp[0])
        dataComApp.append(completedApp[0])
    return render_template('admin_home.html', pageTitle=pageTitle, title=title, subtitle=subtitle, total=total[0],
                           completedApp=completedApp[0], avgRating=avgRating[0], avgMeetingTime=avgMeetingTime[0],
                           popularRequest=popularRequest[0], dataTotalApp=dataTotalApp, dataComApp=dataComApp)


def adminhrsly():
    pageTitle = "Home"
    title = "Hourly Successful Appointments for past 24 Hour"
    subtitle = dt.today().strftime('%d-%b-%Y, %I:%M%p')
    tmr = dt.today() + timedelta(days=1)
    total = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT COUNT(MeetingID) FROM meeting WHERE StartTime BETWEEN (%s) AND (%s)',
        [dt.today().strftime('%Y-%m-%d'), tmr.strftime('%Y-%m-%d')])
    completedApp = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT COUNT(MeetingID) FROM meeting WHERE EndTime BETWEEN (%s) AND (%s)  AND Attendance >= 2',
        [dt.today().strftime('%Y-%m-%d'), dt.today().strftime('%Y-%m-%d %H:%M:%S')])
    avgRating = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT AVG(Rating) FROM meeting WHERE EndTime BETWEEN (%s) AND (%s)',
        [dt.today().strftime('%Y-%m-%d'), dt.today().strftime('%Y-%m-%d %H:%M:%S')])
    avgMeetingTime = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT AVG(timestampdiff(MINUTE, StartTime,EndTime)) FROM meeting WHERE StartTime BETWEEN (%s) AND (%s)',
        [dt.today().strftime('%Y-%m-%d'), tmr.strftime('%Y-%m-%d')])
    popularRequest = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT  Topic, COUNT(*) FROM meeting WHERE StartTime BETWEEN (%s) AND (%s)',
        [dt.today().strftime('%Y-%m-%d'), tmr.strftime('%Y-%m-%d')])
    dataTotalApp = []
    dataComApp = []
    for i in range(0, 24):
        totalApp = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT COUNT(MeetingID) FROM meeting WHERE StartTime BETWEEN (%s) AND (%s)',
            [(str(dt.today().strftime('%Y-%m-%d ')) + str(i) + ':00:00'),
             (str(dt.today().strftime('%Y-%m-%d ')) + str(i) + ':59:59')])
        completedApp = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT COUNT(MeetingID) FROM meeting WHERE EndTime BETWEEN (%s) AND (%s)',
            [(str(dt.today().strftime('%Y-%m-%d ')) + str(i) + ':00:00'),
             (str(dt.today().strftime('%Y-%m-%d ')) + str(i) + ':59:59')])
        dataTotalApp.append(totalApp[0])
        dataComApp.append(completedApp[0])
    return render_template('admin_home.html', pageTitle=pageTitle, title=title, subtitle=subtitle, total=total[0],
                           completedApp=completedApp[0], avgRating=avgRating[0], avgMeetingTime=avgMeetingTime[0],
                           popularRequest=popularRequest[0], dataTotalApp=dataTotalApp, dataComApp=dataComApp)


@app.route('/admin/tutormanagment')
def tutormanagment():
    pageTitle = "Tutor Managment"
    tutorList = DatabaseInstance.executeSelectMultipleQuery(
        'SELECT UserID, ProfilePicture, FirstName, LastName, DateJoin, AvgRating FROM user AS u LEFT JOIN (SELECT TutorID, AVG(Rating) as AvgRating FROM meeting) AS m ON u.UserID = m.TutorID WHERE u.UserType = (2) ORDER BY u.UserID ASC')
    return render_template('admin_tutor_management.html', pageTitle=pageTitle, tutorList=tutorList)


@app.route('/admin/tutor/<tutorID>')
def adminTutor(tutorID):
    pageTitle = "Tutor Managment"
    userdetail = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT * FROM user WHERE userID = (%s)', [tutorID])
    return render_template('admin_tutor.html', pageTitle=pageTitle, userdetail=userdetail)


def picDeCode(pic64):
    if pic64:
        return b64encode(pic64).decode("utf-8")
    else:
        return ""


def formatdt(date):
    if date:
        return date.strftime('%d-%b-%Y')
    else:
        return ""


app.jinja_env.filters['formatdt'] = formatdt
app.jinja_env.filters['picdecode'] = picDeCode
if __name__ == '__main__':
    app.run(debug=True)
