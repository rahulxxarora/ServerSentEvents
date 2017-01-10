from flask import Flask, render_template, request
from flask.ext.sse import sse, send_event
from werkzeug import check_password_hash
from logging.handlers import RotatingFileHandler
import json, logging, MySQLdb

# Global app configurations

app = Flask(__name__)
app.register_blueprint(sse, url_prefix='/events')

handler = RotatingFileHandler('broadcast_system.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

# Database configurations

cnx = {'host': 'localhost',
       'username': 'root',
       'password': 'root',
       'db': 'gossip_girl'}

# Connecting to the database

conn = MySQLdb.connect(cnx['host'], cnx['username'], cnx['password'], cnx['db'])  
curr = conn.cursor()

# Contains the list of all available series

available_series = [] 

##############################################################################################
# This function is called once on starting the application and it fetched data from DB
##############################################################################################

def startup_code():
    query = """SELECT * FROM series"""
    curr.execute(query)
    row = curr.fetchall()

    for name in row:
        available_series.append(name[0].strip())

##############################################################################################
# This route is accessed when the user tries to add a new subscription.
# It checks whether the given series is available or not?
# If available, it send back the series name to the user and a listener is added for the same
##############################################################################################

@app.route('/check_existence', methods=['POST'])
def check_existence():
    series_name = request.json['series_name']

    if series_name in available_series:
        data = {'message':'Success'}
        return json.dumps(data)

    data = {'message':'Failure'}

    return json.dumps(data)

##############################################################################################
# This route is only be used by admin
# Receives series' name to be added to the list along with credentials
# Checks credentials, if success then the series is added to the list
##############################################################################################

@app.route('/add_series', methods=['POST'])
def add_series():
    try:
        series_name = request.json['title']
        username = request.json['username']
        password = request.json['password']
    except:
        app.logger.error('Improper format')
        return json.dumps({'message':'Improper format'}), 400, {'ContentType':'application/json'}

    query = """SELECT password FROM admin WHERE username='{}'""".format(username)
    curr.execute(query)
    row = curr.fetchall()
    fetched_password = row[0][0].strip()
    if check_password_hash(fetched_password, password)==0:
        app.logger.error('Authentication error')
        return json.dumps({'message':'Authentication error'}), 401, {'ContentType':'application/json'}

    if series_name not in available_series:
        available_series.append(series_name)
        data = {'message': series_name}
        send_event('new_series_added', json.dumps(data), channel='series_broadcast')
        app.logger.info('New series added ' + series_name)
        query = """INSERT INTO series VALUES('{}')""".format(series_name)
        curr.execute(query)
        conn.commit()
        return json.dumps({'message':'Series Added Successfully'}), 201, {'ContentType':'application/json'} 

    app.logger.error('Already Exists : ' + series_name)
    return json.dumps({'message':'Already Exists'}), 400, {'ContentType':'application/json'}

##############################################################################################
# This route is also accessible by admin
# Receives series' name, an update for the same and credentials
# Checks credentials, if success then Broadcasts the update to the concerned listeners 
##############################################################################################

@app.route('/post', methods=['POST'])
def post():
    try:
        series_name = request.json['title']
        message = request.json['message']
        username = request.json['username']
        password = request.json['password']
    except:
        app.logger.error('Improper format')
        return json.dumps({'message':'Improper format'}), 400, {'ContentType':'application/json'}

    query = """SELECT password FROM admin WHERE username='{}'""".format(username)
    curr.execute(query)
    row = curr.fetchall()
    fetched_password = row[0][0].strip()
    if check_password_hash(fetched_password, password)==0:
        app.logger.error('Authentication error')
        return json.dumps({'message':'Authentication error'}), 401, {'ContentType':'application/json'}

    if series_name in available_series:
        app.logger.info('Received message ' + message + ' from series ' + series_name)
        data = {'message': message}
        send_event(series_name, json.dumps(data), channel='series_broadcast')
        query = """INSERT INTO series_text VALUES('{}', '{}')""".format(message, series_name)
        curr.execute(query)
        conn.commit()
        return json.dumps({'message':'Broadcast Successful'}), 201, {'ContentType':'application/json'}

    app.logger.error('Unknown name : ' + series_name)
    return json.dumps({'message':'Unknown name'}), 400, {'ContentType':'application/json'}

##############################################################################################
# The route is called by default when a user lands on the website
# Returns an HTML page containing the logic for adding subscriptions
##############################################################################################

@app.route('/')
def index():
    return render_template('index.html', available_series=available_series)

startup_code()