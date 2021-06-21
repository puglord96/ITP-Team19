from flask import Flask
from flask_mysqldb import MySQL

"""
In your main program, create an instance of the SingletonDatabase class before assessing its functions
"""


class SingletonDatabase:
    __instance__ = None

    def __init__(self, app, hostip, user, password, dbname):
        app.config['MYSQL_HOST'] = hostip
        app.config['MYSQL_USER'] = user
        app.config['MYSQL_PASSWORD'] = password
        app.config['MYSQL_DB'] = dbname

        self.mysql = MySQL(app)

        if SingletonDatabase.__instance__ is None:
            SingletonDatabase.__instance__ = self
        else:
            raise Exception("You cannot create another SingletonDatabase class")

    @staticmethod
    def get_instance():
        """ Static method to fetch the current instance.
        """
        if not SingletonDatabase.__instance__:
            SingletonDatabase()
        return SingletonDatabase.__instance__

    def getDetailListOfAllUsers(self):
        cur = self.mysql.connection.cursor()
        cur.execute("Select * from users")
        myresult = cur.fetchall()
        return myresult

    def getDetailListOfUser(self, email):
        cur = self.mysql.connection.cursor()
        cur.execute("SELECT * FROM user where email = '" + email+"'")
        myresult = cur.fetchone()
        return myresult

    def executeNonSelectQuery(self, query):
        cur = self.mysql.connection.cursor()
        cur.execute(query)
        self.mysql.connection.commit()
        cur.close()

    def executeSelectMultipleQuery(self, query):
        cur = self.mysql.connection.cursor()
        cur.execute(query)
        myresult = cur.fetchall()
        return myresult

    def executeSelectMultipleQueryWithParameters(self, query, values):
        cur = self.mysql.connection.cursor()
        cur.execute(query, values)
        myresult = cur.fetchall()
        return myresult

    def executeSelectOneQuery(self, query):
        cur = self.mysql.connection.cursor()
        cur.execute(query)
        myresult = cur.fetchone()
        return myresult

    def executeInsertQuery(self, query, values):
        try:
            cur = self.mysql.connection.cursor()
            cur.execute(query, values)
            self.mysql.connection.commit()
            cur.close()
            return True
        except Exception as e:
            print("Problem inserting into database: " + str(e))
            return False
