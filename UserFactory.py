import abc
from abc import ABC


class User:
    def __init__(self, UserDetails):
        self.details = UserDetails

    def getDetailsList(self):
        return self.details

    def getUserRole(self):
        return self.details[3]

    def getUserName(self):
        return self.details[4] + " " + self.details[5]

    def getUserID(self):
        return self.details[0]


class TuteeUser(User):
    def __init__(self, UserDetails):
        super().__init__(UserDetails)
        self.landing_page = "tutee_home.html"
        self.feedback_subject_role = 2
        self.zoomRole = 0
        self.profile_landing ="tutee_profile.html"

    def getProfileLandingPage(self):
        return self.profile_landing

    def updateFeedbackString(self,meetingid):
        return "update meeting set tuteesurvey = 'done' where meetingid = " + meetingid

    def getFeedbackSubjectNameString(self,meetingid):
        return "select u.firstname,u.lastname from user u,meeting m where m.tutorid = u.userid and m.meetingid = " + meetingid

    def upcomingMeetingsList(self,userID):
        return "SELECT u.firstname, u.lastname, m.venue,m.starttime,m.endtime,m.topic,m.meetingid,s.description,s.calcolour from user u,meeting m,statustype s where m.tutorID = u.UserID and m.tuteeID = "+str(userID)+" and s.statusid = m.statusID"

    def requestMeetingsList(self,userID):
        return None

    def getZoomRole(self):
        return self.zoomRole




class TutorUser(User):
    def __init__(self, UserDetails):
        super().__init__(UserDetails)
        self.landing_page = "tutor_home.html"
        self.feedback_subject_role = 3
        self.zoomRole = 1
        self.profile_landing = "tutor_profile.html"

    def getZoomRole(self):
        return self.zoomRole

    def getProfileLandingPage(self):
        return self.profile_landing

    def updateFeedbackString(self,meetingid):
        return "update meeting set tutorsurvey = 'done' where meetingid = " + meetingid

    def getFeedbackSubjectNameString(self,meetingid):
        return "select u.firstname,u.lastname from user u,meeting m where m.tuteeid = u.userid and m.meetingid = " + meetingid

    def upcomingMeetingsList(self,userID):
        return "SELECT u.firstname, u.lastname, m.venue,m.starttime,m.endtime,m.topic,m.meetingid,s.description,s.calcolour from user u,meeting m,statustype s where m.tuteeID = u.UserID and s.statusid = m.statusID and m.tutorID = "+str(userID)+"  and m.statusID = 1"

    def requestMeetingsList(self,userID):
        return "SELECT u.firstname, u.lastname, m.venue,m.starttime,m.endtime,m.topic,m.meetingid from user u,meeting m where m.tuteeID = u.UserID and m.tutorID = " + str(userID) + "  and statusID = 2"

    def requestMeeting(self, meetingid):
        return "SELECT * FROM meeting WHERE meetingid = " + meetingid

    def getUser(self, userID):
        return "SELECT firstname, lastname FROM user WHERE userid = " + userID

    def getstatustype(self, statustype):
        return "select description from statustype where statusid = " + statustype

    def getMeetingType(self, meetingtypeid):
        return "SELECT description from meetingtype where meetingtypeid = " + meetingtypeid

    def acceptRequest(self, meetingid):
        return "update meeting set statusid = 1 where meetingid = " + meetingid

    def declineRequest(self, meetingid):
        return "update meeting set statusid = 3 where meetingid = " + meetingid

class AdminUser(User):
    def __init__(self, UserDetails):
        super().__init__(UserDetails)
        self.landing_page = "admin_home.html"
        self.profile_landing = "tutor_profile.html"
        self.zoomRole = 1

    def getProfileLandingPage(self):
        return self.profile_landing

    def getZoomRole(self):
        return self.zoomRole

    def upcomingMeetingsList(self, userID):
        return None

    def requestMeetingsList(self, userID):
        return None

    # Implement other exclusive functions of the Admin here


class UserFactory:

    def createUser(self, UserDetails):
        role = UserDetails[3]
        switch = {
            3: TuteeUser(UserDetails),
            2: TutorUser(UserDetails),
            1: AdminUser(UserDetails)
        }

        return switch.get(role, "User not Found")
