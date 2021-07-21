from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response
from database import SingletonDatabase
from UserSingleton import UserSingleton
from scripts import tutor_calendar
from pyzoom import ZoomClient
from UserFactory import *
from datetime import datetime as dt, timedelta
from itertools import chain
from collections import defaultdict, Counter
from datetime import datetime, timedelta
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




# 1 - Admin
# 2 - Tutor
# 3 - Tutee
@app.route('/', methods=['GET', 'POST'])
def login():
    userlist = DatabaseInstance.executeSelectMultipleQuery("Select email,password from user")
    loginmsg = ""
    if request.method == "POST":
        formEmail = request.form.get('email')
        formPassword = request.form.get('password')

        for user in userlist:
            if formEmail == user[0] and formPassword == user[1]:
                userDetailList = DatabaseInstance.getUserDetailsByEmail(formEmail)
                user = UserFactory.createUser(userDetailList)
                UserInstance.setUser(user)
                zoomRole = UserInstance.getUser().getZoomRole()

                resp = make_response(redirect('/home'))
                resp.set_cookie('zoom_role', str(zoomRole))

                return resp
        loginmsg = "Please enter a vaild Username and Password."
        print(loginmsg)
    print("outside")
    print(loginmsg)
    return render_template('login.html', loginmsg=loginmsg)

@app.route('/logout')
def logout():
    UserInstance.removeUser()
    return redirect('/')

@app.route('/meetingredirect')
def meeting_redirect():
    # Creating a meeting
    # meeting = client.meetings.create_meeting('Test Meeting', start_time=dt.now().isoformat(), duration_min=60,
    #                                          password='password')

    # client.meetings.delete_meeting(86705874597)
    # print(meeting.id)
    return render_template("zoom_meeting_test.html")


@app.route('/sessionbooking', methods=['GET','POST'])
def session_booking():
    disciplinelist = DatabaseInstance.executeSelectMultipleQuery("Select name from degree")
    tutorTable = []
    if request.method == "POST":
        formExpertise = request.form.get('expertise')
        formDiscipline = request.form.get('discipline')
        formGender = request.form.get('gender')
        formRating= request.form.get('rating')
        if not formExpertise:
            expertiseSearch = DatabaseInstance.executeSelectMultipleQuery("SELECT DISTINCT u.userid, u.firstname, u.lastname FROM user u, userexpertises e "
                                                                          "WHERE e.userid = u.userid ")
        else:
            expertiseSearch = DatabaseInstance.executeSelectMultipleQuery("SELECT DISTINCT u.userid, u.firstname, u.lastname, e."+formExpertise+" FROM user u, userexpertises e "
                                                                          "WHERE e.userid = u.userid AND e."+formExpertise+" = TRUE ")
        print("===Expetise===")
        try:
            for row in expertiseSearch:
                expertiseSearchList = [row[0] for row in expertiseSearch]
            print(expertiseSearchList)
        except:
            print("No Matches.")

        if not formDiscipline:
            disciplineSearch = DatabaseInstance.executeSelectMultipleQuery("SELECT u.userid, u.firstname, u.lastname, d.Name FROM user u, degree d "
                                                                           "WHERE u.Degree = d.DegreeID ")
        else:
            disciplineSearch = DatabaseInstance.executeSelectMultipleQueryWithParameters("SELECT u.userid, u.firstname, u.lastname, d.Name FROM user u, degree d "
                                                                                         "WHERE u.Degree = d.DegreeID AND d.Name = %s", [formDiscipline])
        print("===Discipline===")
        try:
            for row in disciplineSearch:
                disciplineSearchList = [row[0] for row in disciplineSearch]
            print(disciplineSearchList)
        except:
            disciplineSearchList =[]
            print("No Matches.")

        if not formGender:
            genderSearch = DatabaseInstance.executeSelectMultipleQuery("SELECT u.userid, u.firstname, u.lastname FROM user u, gender g "
                                                                       "WHERE g.gender_id = u.gender ")
        else:
            genderSearch = DatabaseInstance.executeSelectMultipleQueryWithParameters("SELECT u.userid, u.firstname, u.lastname FROM user u, gender g "
                                                                                     "WHERE g.gender_id = u.gender AND g.gender = %s ", [formGender])
        print("===Gender===")
        try:
            for row in genderSearch:
                genderSearchList = [row[0] for row in genderSearch]
            print(genderSearchList)
        except:
            print("No Matches.")

        if not formRating:
            # ratingSearch = DatabaseInstance.executeSelectMultipleQuery("SELECT u.userid, u.firstname, u.lastname FROM user u, feedback f "
            #                                                            "WHERE f.tutortuteeid = u.UserID GROUP BY u.userid")
            ratingSearch = DatabaseInstance.executeSelectMultipleQuery("SELECT UserID, FirstName, LastName FROM user AS u "
                                                                       "LEFT JOIN (SELECT TutorID, feedbackid FROM meeting) AS m ON u.UserID = m.TutorID "
                                                                       "LEFT JOIN (SELECT feedbackid, sessionrating AS AvgRating FROM feedback) AS fb ON m.feedbackid = fb.feedbackid "
                                                                       "WHERE u.UserType = (2) GROUP BY u.UserID ORDER BY u.UserID ASC;")

        else:
            # ratingSearch = DatabaseInstance.executeSelectMultipleQueryWithParameters("SELECT u.userid, u.firstname, u.lastname, AVG(tutortuteerating) AS average FROM user u, feedback f "
            #                                                                          "WHERE f.tutortuteeid = u.UserID GROUP BY u.userid HAVING average >= %s ", [formRating])
            ratingSearch = DatabaseInstance.executeSelectMultipleQueryWithParameters(
                'SELECT UserID, FirstName, LastName, MAX(AvgRating) FROM user AS u LEFT JOIN (SELECT TutorID, feedbackid FROM meeting) AS m ON u.UserID = m.TutorID LEFT JOIN (SELECT feedbackid, AVG(sessionrating) AS AvgRating FROM feedback) AS fb ON m.feedbackid = fb.feedbackid WHERE u.UserType = (2) GROUP BY u.UserID HAVING AvgRating >= %s ORDER BY u.UserID ASC;', [formRating])
        print("===Rating===")
        try:
            for row in ratingSearch:
                ratingSearchList = [row[0] for row in ratingSearch]
            print(ratingSearchList)
        except:
            ratingSearchList =[]
            print("No Matches.")

        print("===Ranking===")
        # rankingList = frequency(expertiseSearchList, disciplineSearchList, genderSearchList, ratingSearchList)
        # print(rankingList)
        # print(Counter(rankingList))
        rankingList = [expertiseSearchList, disciplineSearchList, genderSearchList, ratingSearchList]
        frequencyList = frequency(expertiseSearchList, disciplineSearchList, genderSearchList, ratingSearchList)
        print(frequencyList)
        occurences = Counter(x for xs in rankingList for x in set(xs))
        for tutorID in frequencyList:
            tutorQuery = DatabaseInstance.executeSelectOneQueryWithParameters('SELECT UserID, ProfilePicture, FirstName, LastName, MAX(AvgRating) FROM user AS u LEFT JOIN (SELECT TutorID, feedbackid, Attendance FROM meeting) AS m ON u.UserID = m.TutorID LEFT JOIN (SELECT feedbackid, AVG(sessionrating) AS AvgRating FROM feedback) AS fb ON m.feedbackid = fb.feedbackid WHERE u.UserType = (2) AND u.UserID = %s GROUP BY u.UserID;', [tutorID])
            tutorTable.append(tutorQuery)
            percentage = int(occurences[tutorID] / 5 * 100)
            # tutorTable.append(percentage)
        # print(tutorTable)
        return render_template("session_booking_results.html", disciplinelist=disciplinelist, tutorTable=tutorTable)
    return render_template("session_booking.html", disciplinelist=disciplinelist)

def frequency(*lists):
    counter = defaultdict(int)
    for x in chain(*lists):
        counter[x] += 1
    return [key for (key, value) in
        sorted(counter.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)]

@app.route('/tutorBooking/<tutorID>', methods=['GET','POST'])
def tutorBooking(tutorID):
    if request.method == 'POST':
        userID = UserInstance.getUser().getUserID()
        formTimeSlot = request.form.get('timeslot')
        formStartTime, formEndTime = formTimeSlot.split(' - ', 1)
        StartTime = datetime.strptime(formStartTime,'%H:%M').time()
        EndTime = datetime.strptime(formEndTime,'%H:%M').time()
        formatStart = dt.combine(dt.today(), StartTime)
        formatEnd = dt.combine(dt.today(), EndTime)
        print("%s %s"% (formatStart,formatEnd))
        DatabaseInstance.executeInsertQueryWithParameters(
            "INSERT INTO meeting (tutorID, tuteeID, meetingtypeID, statusID, StartTime, EndTime) VALUES (%s,%s,2,2,%s,%s)",
            [tutorID, userID, formatStart, formatEnd])
        # Sample Inser Statement
        # INSERT INTO `meeting` VALUES (1,2,3,1,1,'88600763699','2','2021-07-07 00:10:00','2021-07-07 01:00:00','',NULL,10,'Report','00:00:00')

    pageTitle = "Tutor Booking"
    userdetail = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT * FROM user WHERE userID = (%s)', [tutorID])
    faculty = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT name from faculty where FacultyID = (%s)', [userdetail[8]]
    )
    gender = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT gender from gender where gender_id = (%s)', [userdetail[12]]
    )
    appointments = DatabaseInstance.executeSelectMultipleQueryWithParameters(
        'SELECT StartTime, EndTime FROM meeting WHERE tutorID = (%s)', [tutorID]
    )
    sortedAppointments = sorted(appointments, key=lambda x: x[1])
    # datetime(2021, 7, 7, 10)
    # ‘year’, ‘month’, ‘date’, ‘hour’
    timeslots = get_slots(hours, sortedAppointments)
    return render_template("tutor_booking.html", pageTitle=pageTitle, userdetail=userdetail, faculty=faculty[0], gender=gender[0], timeslots = timeslots)
    # appointments sample input
    # appointments = [(datetime(2012, 5, 22, 10), datetime(2012, 5, 22, 10, 30)),
    #                 (datetime(2012, 5, 22, 12), datetime(2012, 5, 22, 13)),
    #                 (datetime(2012, 5, 22, 15, 30), datetime(2012, 5, 22, 17, 10))]

hours = (datetime(2021, 7, 7, 9, 0), datetime(2021, 7, 7, 18, 0))

def get_slots(hours, appointments, duration=timedelta(hours=0.5)):
    slots = sorted([(hours[0], hours[0])] + appointments + [(hours[1], hours[1])])
    slot = []
    for start, end in ((slots[i][1], slots[i+1][0]) for i in range(len(slots)-1)):
        assert start <= end, "Cannot attend all appointments"
        while start + duration <= end and len(slot) < 12:
            slot.append("{:%H:%M} - {:%H:%M}".format(start, start + duration))
            start += duration
            # print(slot)
    return slot

@app.route('/meeting')
def meeting():
    global meeting_starttime
    meeting_starttime = dt.now()
    return render_template("meeting.html")

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():

    tutortuteenamearray = DatabaseInstance.executeSelectOneQuery(UserInstance.getUser().getFeedbackSubjectNameString(request.cookies.get("meeting_id")))
    tutortuteename = tutortuteenamearray[0] + " " + tutortuteenamearray[1]
    subjectRole = UserInstance.getUser().feedback_subject_role
    userRole = UserInstance.getUser().getUserRole()

    meetingid = request.cookies.get("meeting_id")

    meetingduration = dt.now() - meeting_starttime
    print(meetingduration)

    if request.method == "POST":
        feedbacksessionrating = request.form.get('sessionrating')
        feedbacktutortuteerating = request.form.get('tutortuteerating')
        feedbackremarks = request.form.get('remarks')

        if userRole == 2:
            DatabaseInstance.executeUpdateQueryWithParameters("update meeting set meetingtimeelapsed = %s where meetingid = %s",[meetingduration,meetingid])

        DatabaseInstance.executeInsertQueryWithParameters(
            "Insert into feedback(sessionrating,tutortuteerating,remark) values(%s,%s,%s)",
            [feedbacksessionrating, feedbacktutortuteerating, feedbackremarks])

        DatabaseInstance.executeUpdateQuery(UserInstance.getUser().getUpdateFeedbackString(meetingid))

        return redirect('/home')
    return render_template("feedback.html", tutortuteename=tutortuteename)

@app.route('/home')
def home():
    global upcomingmeetingslist, requestmeetingslist
    userID = UserInstance.getUser().getUserID()
    userRole = UserInstance.getUser().getUserRole()
    userName = UserInstance.getUser().getUserName()
    userLandingPage = UserInstance.getUser().landing_page
    upcomingmeetingslistquery = UserInstance.getUser().getUpcomingMeetingsList(userID)
    requestmeetingslistquery = UserInstance.getUser().getMeetingsRequestList(userID)


    if upcomingmeetingslistquery is not None:
        upcomingmeetingslist = DatabaseInstance.executeSelectMultipleQuery(upcomingmeetingslistquery)
    else:
        upcomingmeetingslist = ""

    if requestmeetingslistquery is not None:
        requestmeetingslist = DatabaseInstance.executeSelectMultipleQuery(
            UserInstance.getUser().getMeetingsRequestList(userID))
    else:
        requestmeetingslist = ""

    if userRole == 1:
        pageTitle = "Home"
        title = "Daily Appointments for past 30 day"
        subtitle = dt.today().strftime('%d-%b-%Y, %I:%M%p')
        tmr = dt.today() + timedelta(days=1)
        total = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT COUNT(MeetingID) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL 30 DAY AND (%s);',
            [dt.today().strftime('%Y-%m-%d'), dt.today().strftime('%Y-%m-%d')])
        completedApp = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT COUNT(MeetingID) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL 30 DAY AND (%s) AND Attendance >= 2',
            [dt.today().strftime('%Y-%m-%d'), dt.today().strftime('%Y-%m-%d %H:%M:%S')])
        avgRating = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT AVG(Rating) FROM meeting as m LEFT JOIN (SELECT feedbackid, sessionrating as Rating FROM feedback) as fb ON m.feedbackid = fb.feedbackid WHERE StartTime BETWEEN (%s) - INTERVAL 30 DAY AND (%s) AND Attendance >= 0',
            [dt.today().strftime('%Y-%m-%d'), dt.today().strftime('%Y-%m-%d %H:%M:%S')])
        avgMeetingTime = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT AVG(timestampdiff(MINUTE, StartTime,EndTime)) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL 30 DAY AND (%s) AND Attendance >= 2',
            [dt.today().strftime('%Y-%m-%d'), dt.today().strftime('%Y-%m-%d')])
        popularRequest = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT  Topic, COUNT(*) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL 30 DAY AND (%s)',
            [dt.today().strftime('%Y-%m-%d'), dt.today().strftime('%Y-%m-%d')])
        dataTotalApp = []
        dataComApp = []
        for i in range(29, -1, -1):
            dailyTotalApp = DatabaseInstance.executeSelectOneQueryWithParameters(
                'SELECT COUNT(MeetingID) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL (%s) DAY AND (%s) - INTERVAL (%s) DAY',
                [dt.today().strftime('%Y-%m-%d '), i, tmr.strftime('%Y-%m-%d '), i])
            dailyCompletedApp = DatabaseInstance.executeSelectOneQueryWithParameters(
                'SELECT COUNT(MeetingID) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL (%s) DAY AND (%s) - INTERVAL (%s) DAY AND Attendance >= 2',
                [dt.today().strftime('%Y-%m-%d '), i, tmr.strftime('%Y-%m-%d '), i])
            dataTotalApp.append(dailyTotalApp[0])
            dataComApp.append(dailyCompletedApp[0])
    else:
        pageTitle = title = subtitle = dataTotalApp = dataComApp = ""
        total = completedApp = avgRating = avgMeetingTime = popularRequest = [""]

    landingswitch = {
        1: render_template(userLandingPage, pageTitle=pageTitle, title=title, subtitle=subtitle, total=total[0],
                           completedApp=completedApp[0], avgRating=avgRating[0], avgMeetingTime=avgMeetingTime[0],
                           popularRequest=popularRequest[0], dataTotalApp=dataTotalApp, dataComApp=dataComApp),
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
        requestMeeting = DatabaseInstance.executeSelectMultipleQuery(UserInstance.getUser().getMeetingDetailsString(meetingid))
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
            update_meeting_info = DatabaseInstance.executeSelectOneQueryWithParameters("select venue,topic from meeting where meetingid=%s",[meetingid])
            # print(meetingtype)
            if update_meeting_info[0] is None or update_meeting_info[0] == "":
                meeting = client.meetings.create_meeting(update_meeting_info[1], start_time=dt.now().isoformat(), duration_min=60,
                                                         password='password')
                DatabaseInstance.executeUpdateQueryWithParameters("update meeting set venue = %s where meetingid = %s",[meeting.id,meetingid])
            print("accept")

            DatabaseInstance.executeUpdateQuery(UserInstance.getUser().acceptMeetingRequest(meetingid))
            return redirect('/home')
        elif request.form.get("decline"):
            print("decline")
            DatabaseInstance.executeUpdateQuery(UserInstance.getUser().declineRequest(meetingid))
            return redirect('/home')
    userRole = UserInstance.getUser().getUserRole()
    if userRole == 2:
        requestMeeting = DatabaseInstance.executeSelectMultipleQuery(UserInstance.getUser().getMeetingDetailsString(meetingid))
        userID = UserInstance.getUser().getUserID()
        # prevent injection of URL (make sure that tutor is tutor of the meeting)
        if userID == requestMeeting[0][1] and requestMeeting[0][4] == 2:
            tutorname = DatabaseInstance.getUserDetailsByUserID(str(requestMeeting[0][1]))
            tutorname = tutorname[4] + " " + tutorname[5]
            tuteename = DatabaseInstance.getUserDetailsByUserID(str(requestMeeting[0][2]))
            tuteename = tuteename[4] + " " + tuteename[5]
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
        formGender = request.form.get('gender')
        DatabaseInstance.executeInsertQueryWithParameters(
            "INSERT INTO user(email, password, usertype, firstname, lastname, faculty, degree, graduationyear,gender,DateJoin) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [formEmail, formPassword, formUserType, formFirstName, formLastName, formFaculty, formDegree, formGradYear,formGender,
             dt.today().strftime('%Y-%m-%d ')])
        return redirect('/')

    facultyList = DatabaseInstance.executeSelectMultipleQuery('SELECT * FROM faculty ORDER BY FacultyID ASC')
    genderList = DatabaseInstance.executeSelectMultipleQuery('select * from gender')
    return render_template('register.html', facultyList=facultyList,genderList = genderList)


@app.route('/register/faculty/<Faculty>')
def degree_by_faculty(Faculty):
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
def update_profile():
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
            DBexpertisesList = ['EssayWriting', 'TechnicalProposal', 'OralPresentation', 'ReaderResponse', 'Reflection']
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

        userDetailList = DatabaseInstance.getUserDetailsByUserID(str(user[0]))
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


def admin():
    pageTitle = "Home"
    title = "Daily Appointments for past 30 day"
    subtitle = dt.today().strftime('%d-%b-%Y, %I:%M%p')
    tmr = dt.today() + timedelta(days=1)
    total = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT COUNT(MeetingID) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL 30 DAY AND (%s);',
        [dt.today().strftime('%Y-%m-%d'), dt.today().strftime('%Y-%m-%d')])
    completedApp = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT COUNT(MeetingID) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL 30 DAY AND (%s) AND Attendance >= 2',
        [dt.today().strftime('%Y-%m-%d'), dt.today().strftime('%Y-%m-%d %H:%M:%S')])
    avgRating = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT AVG(Rating) FROM meeting as m LEFT JOIN (SELECT feedbackid, sessionrating as Rating FROM feedback) as fb ON m.feedbackid = fb.feedbackid WHERE StartTime BETWEEN (%s) - INTERVAL 30 DAY AND (%s) AND Attendance >= 0',
        [dt.today().strftime('%Y-%m-%d'), dt.today().strftime('%Y-%m-%d %H:%M:%S')])
    avgMeetingTime = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT AVG(timestampdiff(MINUTE, StartTime,EndTime)) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL 30 DAY AND (%s) AND Attendance >= 2',
        [dt.today().strftime('%Y-%m-%d'), dt.today().strftime('%Y-%m-%d')])
    popularRequest = DatabaseInstance.executeSelectOneQueryWithParameters(
        'SELECT  Topic, COUNT(*) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL 30 DAY AND (%s)',
        [dt.today().strftime('%Y-%m-%d'), dt.today().strftime('%Y-%m-%d')])
    dataTotalApp = []
    dataComApp = []
    for i in range(29, -1, -1):
        dailyTotalApp = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT COUNT(MeetingID) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL (%s) DAY AND (%s) - INTERVAL (%s) DAY',
            [dt.today().strftime('%Y-%m-%d '), i, tmr.strftime('%Y-%m-%d '), i])
        dailyCompletedApp = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT COUNT(MeetingID) FROM meeting WHERE StartTime BETWEEN (%s) - INTERVAL (%s) DAY AND (%s) - INTERVAL (%s) DAY AND Attendance >= 2',
            [dt.today().strftime('%Y-%m-%d '), i, tmr.strftime('%Y-%m-%d '), i])
        dataTotalApp.append(dailyTotalApp[0])
        dataComApp.append(dailyCompletedApp[0])
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
    userRole = UserInstance.getUser().getUserRole()
    if userRole == 1:
        pageTitle = "Tutor Managment"
        tutorList = DatabaseInstance.executeSelectMultipleQuery(
            'SELECT UserID, ProfilePicture, FirstName, LastName, DateJoin, MAX(AvgRating) FROM user AS u LEFT JOIN (SELECT TutorID, feedbackid, Attendance FROM meeting) AS m ON u.UserID = m.TutorID LEFT JOIN (SELECT feedbackid, AVG(sessionrating) AS AvgRating FROM feedback) AS fb ON m.feedbackid = fb.feedbackid WHERE u.UserType = (2) GROUP BY u.UserID ORDER BY u.UserID ASC;')
        return render_template('admin_tutor_management.html', pageTitle=pageTitle, tutorList=tutorList)
    else:
        return redirect(url_for('home'))


@app.route('/admin/appointmentmanagement')
def appointmentmanagement():
    userRole = UserInstance.getUser().getUserRole()
    if userRole == 1:
        meetingsdict = {}
        meetingslistquery = DatabaseInstance.executeSelectMultipleQuery("Select meetingid,tutorid,tuteeid,topic,starttime,meetingtypeID,venue,tutorsurvey,tuteesurvey,statusid from meeting")

        for meetings in meetingslistquery:
            meetingsarray = []

            meetingdate = meetings[4].date()
            tutorname = DatabaseInstance.executeSelectOneQueryWithParameters("select concat(firstname,' ',lastname) from user where userid = %s", str(meetings[1]))[0]
            tuteename = DatabaseInstance.executeSelectOneQueryWithParameters("select concat(firstname,' ',lastname) from user where userid = %s", str(meetings[2]))[0]
            meetingtype = DatabaseInstance.executeSelectOneQueryWithParameters("select description from meetingtype where meetingtypeid = %s", str(meetings[5]))[0]
            meetingstatus = DatabaseInstance.executeSelectOneQueryWithParameters("select description from statustype where statusid = %s", str(meetings[9]))[0]

            meetingsarray.append(meetings[0])
            meetingsarray.append(tutorname)
            meetingsarray.append(tuteename)
            meetingsarray.append(meetings[3])
            meetingsarray.append(meetings[4])
            meetingsarray.append(meetingtype)
            meetingsarray.append(meetings[6])
            meetingsarray.append(meetings[7])
            meetingsarray.append(meetings[8])
            meetingsarray.append(meetingstatus)

            if meetingdate not in meetingsdict:
                meetingsdict[meetingdate] = []

            meetingsdict[meetingdate].append(meetingsarray)

        print(meetingsdict)
        return render_template('admin_appointments.html',meetingsdict=meetingsdict)

    else:
        return redirect(url_for('home'))





@app.route('/admin/tutor/<tutorID>')
def adminTutor(tutorID):
    userRole = UserInstance.getUser().getUserRole()
    if userRole == 1:
        pageTitle = "Tutor Managment"
        userdetail = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT * FROM user WHERE userID = (%s)', [tutorID])
        rating = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT MAX(AvgRating) FROM user AS u LEFT JOIN (SELECT TutorID, feedbackid, Attendance FROM meeting) AS m ON u.UserID = m.TutorID LEFT JOIN (SELECT feedbackid, AVG(sessionrating) AS AvgRating FROM feedback) AS fb ON m.feedbackid = fb.feedbackid WHERE u.UserID = (%s) ORDER BY u.UserID ASC',[tutorID])
        history = DatabaseInstance.executeSelectMultipleQueryWithParameters(
            #attendance change to 2 after demo
            'SELECT * , TIMESTAMPDIFF(MINUTE, StartTime,EndTime) as Duration from meeting WHERE Attendance >= 0 AND TutorID = (%s) ORDER BY meetingID DESC LIMIT 5',[tutorID])
        historyList = []
        for i in history:
            tuteeName = DatabaseInstance.executeSelectOneQueryWithParameters(
                'SELECT FirstName FROM user WHERE UserID = (%s)',[i[2]])
            historyList.append((tuteeName[0], i[7], i[11],i[13]))

        faculty = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT name from faculty where FacultyID = (%s)',[userdetail[8]]
        )

        gender = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT gender from gender where gender_id = (%s)',[userdetail[12]]
        )
        return render_template('admin_tutor.html', pageTitle=pageTitle, userdetail=userdetail, rating=rating, historyList=historyList, faculty=faculty[0], gender=gender[0])
    else:
        return redirect(url_for('home'))

@app.route('/admin/tuteemanagment')
def tuteemanagment():
    userRole = UserInstance.getUser().getUserRole()
    if userRole == 1:
        pageTitle = "Tutee Managment"
        tuteeList = DatabaseInstance.executeSelectMultipleQuery(
            'SELECT UserID, ProfilePicture, FirstName, LastName, DateJoin, MAX(AvgRating) FROM user AS u LEFT JOIN (SELECT TuteeID, feedbackid, Attendance FROM meeting) AS m ON u.UserID = m.TuteeID LEFT JOIN (SELECT feedbackid, AVG(sessionrating) AS AvgRating FROM feedback) AS fb ON m.feedbackid = fb.feedbackid WHERE u.UserType = (3) GROUP BY u.UserID ORDER BY u.UserID ASC')
        return render_template('admin_tutee_management.html', pageTitle=pageTitle, tuteeList=tuteeList)
    else:
        return redirect(url_for('home'))

@app.route('/admin/feedbackmanagement')
def feedbackmanagement():

    userRole = UserInstance.getUser().getUserRole()
    if userRole == 1:
        feedbackList = DatabaseInstance.executeSelectMultipleQuery("SELECT f.tutortuteerating,f.remark,concat(u.firstname,u.lastname) from feedback f, user u, meeting m where u.userid = m.TutorID and f.FeedBackID = m.FeedBackID")
        return render_template('admin_feedback_management.html',feedbackList = feedbackList)
    else:
        return redirect(url_for('home'))



@app.route('/admin/tutee/<tuteeID>')
def adminTutee(tuteeID):
    userRole = UserInstance.getUser().getUserRole()
    if userRole == 1:
        pageTitle = "Tutee Managment"
        userdetail = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT * FROM user WHERE userID = (%s)', [tuteeID])
        rating = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT MAX(AvgRating) FROM user AS u LEFT JOIN (SELECT TutorID, feedbackid, Attendance FROM meeting) AS m ON u.UserID = m.TutorID LEFT JOIN (SELECT feedbackid, AVG(sessionrating) AS AvgRating FROM feedback) AS fb ON m.feedbackid = fb.feedbackid WHERE u.UserID = (%s) ORDER BY u.UserID ASC',[tuteeID])
        history = DatabaseInstance.executeSelectMultipleQueryWithParameters(
            #attendance change to 2 after demo
            'SELECT * , TIMESTAMPDIFF(MINUTE, StartTime,EndTime) as Duration from meeting WHERE Attendance >= 0 AND TuteeID = (%s) ORDER BY meetingID DESC LIMIT 5',[tuteeID])
        historyList = []
        for i in history:
            print(i[2])
            tuteeName = DatabaseInstance.executeSelectOneQueryWithParameters(
                'SELECT FirstName FROM user WHERE UserID = (%s)',[i[2]])
            historyList.append((tuteeName[0], i[7], i[11],i[13]))

        faculty = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT name from faculty where FacultyID = (%s)',[userdetail[8]]
        )

        gender = DatabaseInstance.executeSelectOneQueryWithParameters(
            'SELECT gender from gender where gender_id = (%s)',[userdetail[12]]
        )

        return render_template('admin_tutee.html', pageTitle=pageTitle, userdetail=userdetail, rating=rating, historyList=historyList, faculty=faculty[0], gender=gender[0])
    else:
        return redirect(url_for('home'))

def decode_pic(pic64):
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
app.jinja_env.filters['picdecode'] = decode_pic
if __name__ == '__main__':
    app.run(debug=True)
