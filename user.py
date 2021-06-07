class user:
    __instance__ = None

    def __init__(self):

        self.role = None
        if user.__instance__ is None:
            user.__instance__ = self
        else:
            raise Exception("You cannot create another user class")

    @staticmethod
    def get_instance():
        """ Static method to fetch the current instance.
        """
        if not user.__instance__:
            user()
        return user.__instance__

    def setRole(self,role):
        self.role = role

    def getRole(self):
        return self.role
