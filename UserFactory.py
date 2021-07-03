import abc
from abc import ABC


class User:
    def __init__(self, UserDetails):
        self.details = UserDetails

    def getDetailsList(self):
        return self.details

    def getUserRole(self):
        return self.details[3]


class TuteeUser(User):
    def __init__(self, UserDetails):
        super().__init__(UserDetails)
        self.landing_page = "tutor_home.html"

    pass

    # Implement other exclusive functions of the tutor here


class TutorUser(User):
    def __init__(self, UserDetails):
        super().__init__(UserDetails)
        self.landing_page = "tutor_home.html"

    # Implement other exclusive functions of the tutor here


class AdminUser(User):
    def __init__(self, UserDetails):
        super().__init__(UserDetails)
        self.landing_page = "admin_home.html"

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
