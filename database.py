from flask_mysqldb import MySQL


class database:

    def __init__(self, app, hostip, user, password, dbname):
        app.config['MYSQL_HOST'] = hostip
        app.config['MYSQL_USER'] = user
        app.config['MYSQL_PASSWORD'] = password
        app.config['MYSQL_DB'] = dbname

        self.mysql = MySQL(app)

    def getDatabase(self):
        return self.mysql

    def executeNonSelectQuery(self, query):
        cur = self.mysql.connection.cursor()
        cur.execute(query)
        self.mysql.connection.commit()
        cur.close()

    def executeSelectQuery(self,query):
        cur = self.mysql.connection.cursor()
        cur.execute(query)
        myresult = cur.fetchall()
        return myresult
