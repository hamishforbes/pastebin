from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from pymongo import Connection, ASCENDING, DESCENDING
from bson.objectid import ObjectId
import datetime

#Mongo
connection = Connection('localhost', 27017)
db = connection.pastebin

# create the little application object
app = Flask(__name__)

@app.route('/')
def index():
    return redirect(url_for('paste'))

@app.route('/paste/', methods=['GET', 'POST'])
def paste():
    if request.method == 'POST':
        #save paste to mongo
        paste = {"user": 'test',
                 "posted": datetime.datetime.utcnow(),
                 "lang": request.form['lang'],
                 "title": request.form['title'],
                 "paste_content": request.form['paste_content']
                 }
        pasteid = db.pastes.insert(paste)

        return redirect('/paste/' + str(pasteid) + '/')
    else:
        return render_template('index.html')

@app.route('/paste/<paste>/')
def get_paste(paste):
    # get paste from mongo
    paste = db.pastes.find_one({'_id': ObjectId(paste)})
    paste['posted'] = paste['posted'].strftime('%d-%m-%Y %H:%M:%S')
    return render_template('paste.html', paste=paste)

@app.route('/user/<user>/')
def get_list(user):
    # get list of pastes for user
    pastes = []

    for paste in db.pastes.find({'user': user}).sort('posted', DESCENDING):
        paste['id'] = str(paste['_id'])
        pastes.append(paste)
    data = {'user': user, 'pastes': pastes}
    return render_template('list.html', data=data)

if __name__ == "__main__":
    #app.debug = True
    app.run()
