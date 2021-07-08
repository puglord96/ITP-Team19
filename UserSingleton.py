class UserSingleton:
    __instance__ = None

    def __init__(self):

        self.user = None
        if UserSingleton.__instance__ is None:
            UserSingleton.__instance__ = self
        else:
            raise Exception("You cannot create another user class")

    @staticmethod
    def get_instance():
        """ Static method to fetch the current instance.
        """
        if not UserSingleton.__instance__:
            UserSingleton()
        return UserSingleton.__instance__

    def setUser(self, user):
        self.user = user

    def getUser(self):
        return self.user

    def removeUser(self):
        self.user = None
