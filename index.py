from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from pymongo import Connection, ASCENDING, DESCENDING
from bson.objectid import ObjectId
from flask_login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin)
import datetime
import ConfigParser
import ldapwrap

config = ConfigParser.RawConfigParser()
config.read('pastebin.conf')

#Mongo
mongoHost = config.get('mongodb', 'host')
mongoPort = config.getint('mongodb', 'port')
print 'Connecting to MongoDB at '+mongoHost+':'+ str(mongoPort)
connection = Connection(mongoHost, mongoPort)
db = connection.pastebin
print 'MongoDB Connected'

#LDAP
ldapHost = config.get('ldap', 'host')
ldapBindDN = config.get('ldap', 'bind_dn')
ldapBindPass = config.get('ldap', 'password')
search_filter = config.get('ldap', 'search_filter')
base_dn = config.get('ldap', 'base_dn')
ldapConn = None

def initLDAP():
    global ldapConn
    global ldapBindDN
    global ldapBindPass

    print 'Connecting to ldap at '+ldapHost
    ldapConn = ldapwrap.connect(ldapHost)
    print 'Binding to LDAP as: '+ldapBindDN
    ldapwrap.bind(ldapConn, ldapBindDN, ldapBindPass)
initLDAP()

#login Manager
login_manager = LoginManager()

# create the little application object
app = Flask(__name__)
app.secret_key = "asdfasdfsdafdsafdsji234u982343289"
login_manager.init_app(app)
login_manager.login_view = "login"

@app.route('/')
def index():
    return redirect(url_for('paste'))

@app.route('/paste/', methods=['GET', 'POST'])
@login_required
def paste():
    if request.method == 'POST':
        #save paste to mongo
        paste = {"user": current_user.id,
                 "posted": datetime.datetime.utcnow(),
                 "title": request.form['title'],
                 "paste_content": request.form['paste_content']
                 }
        pasteid = db.pastes.insert(paste)

        return redirect('/paste/' + str(pasteid) + '/')
    else:
        return render_template('index.html')

@app.route('/paste/<paste>/')
@login_required
def get_paste(paste):
    # get paste from mongo
    paste = db.pastes.find_one({'_id': ObjectId(paste)})
    paste['posted'] = paste['posted'].strftime('%d-%m-%Y %H:%M:%S')
    return render_template('paste.html', paste=paste)

@app.route('/edit/<paste>/')
@login_required
def edit_paste(paste):
    # get paste from mongo
    paste = db.pastes.find_one({'_id': ObjectId(paste)})
    #check if user is allowed to edit
    paste['posted'] = paste['posted'].strftime('%d-%m-%Y %H:%M:%S')
    return render_template('edit.html', paste=paste)

@app.route('/user/<user>/')
@login_required
def get_list(user):
    # get list of pastes for user
    pastes = []

    for paste in db.pastes.find({'user': user}).sort('posted', DESCENDING):
        paste['id'] = str(paste['_id'])
        pastes.append(paste)
    data = {'user': user, 'pastes': pastes}
    return render_template('list.html', data=data)

#login manager routes
@app.route("/login", methods=["GET", "POST"])
def login():
    global ldapConn
    global ldapHost
    global search_filter
    global base_dn

    if request.method == 'POST':
        #search ldap for the username
        if ldapConn == None:
            print ldapConn
            initLDAP()
        ldapuser = ldapwrap.getUser(ldapConn, base_dn, search_filter, request.form['user'])
        if ldapuser != None:
            #found the user, try binding with that dn and supplied password
            #TODO: should just be able to auth against the password attrib?

            tmpConn = ldapwrap.connect(ldapHost)
            if ldapwrap.bind(tmpConn, ldapuser['dn'], request.form['pass']):
                #succesfully bound, good password!
                tmpConn.unbind()
                #Create the flask-login user object and log the user in
                UserObj = User(ldapuser['cn'][0], ldapuser['uid'][0], active=True)
                login_user(UserObj)

                next = request.args.get('next', '')
                if next:
                    return redirect(next)
                else:
                    return redirect('/paste/')
            else:
                return 'Bad password'
        else:
            return 'User not found'
    return render_template('login.html')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/paste/')

@login_manager.user_loader
def load_user(userid):
    #get from ldap!
    global ldapConn
    global search_filter
    global base_dn
    if ldapConn != None:
        initLDAP()
    ldapuser = ldapwrap.getUser(ldapConn, base_dn, search_filter, userid)
    if ldapuser != None:
        return User(ldapuser['cn'][0], ldapuser['uid'][0], active=True)
    else:
        return None


#user class
class User(UserMixin):
    def __init__(self, name, id, active=True):
        self.name = name
        self.id = id
        self.active = active

    def is_active(self):
        return self.active

if __name__ == "__main__":
    app.debug = False
    app.run(host='0.0.0.0')
