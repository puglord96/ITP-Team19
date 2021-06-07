from flask import Flask, render_template, request, redirect, url_for
from database import SingletonDatabase
from user import user

app = Flask(__name__)

# Update the settings of our database below

databaseIP = 'itp.ckmrtwiqitmd.ap-southeast-1.rds.amazonaws.com'
databaseUserName = 'admin'
databasePassword = 'iloveitp'
databaseName = 'itp'

database = SingletonDatabase(app, databaseIP, databaseUserName, databasePassword, databaseName)


DatabaseInstance = database.get_instance()
UserInstance = user().get_instance()


@app.route('/',methods=['GET','POST'])
def login():
    userlist = DatabaseInstance.executeSelectMultipleQuery("Select email,password from user")



    if request.method == "POST":
        formEmail = request.form.get('email')
        formPassword = request.form.get('password')

        for user in userlist:

            if formEmail == user[0] and formPassword == user[1]:
                userRole = DatabaseInstance.executeSelectOneQuery("SELECT ut.description from user as u,usertype as ut where u.usertype = ut.usertypeid and u.email = '" + user[0]+"'")[0]

                UserInstance.setRole(userRole.lower())
                print(userRole)
                print("user found:" + user[0])
                return redirect('/home')
    return render_template('login.html')


@app.route('/home')
def home():
    userRole = UserInstance.getRole()
    if userRole == "admin":
        return render_template('admin_test.html')
    elif userRole == "tutee":
        return render_template('tutee_test.html')
    elif userRole == "tutor":
        return render_template('tutor_test.html')
    else:
        return render_template('error_page.html')

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')


@app.route('/register')
def register():
    return render_template('register.html')




if __name__ == '__main__':
    app.run()
