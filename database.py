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

    def executeNonSelectQuery(self, query):
        cur = self.mysql.connection.cursor()
        cur.execute(query)
        self.mysql.connection.commit()
        cur.close()

    def executeSelectQuery(self, query):
        cur = self.mysql.connection.cursor()
        cur.execute(query)
        myresult = cur.fetchall()
        return myresult
