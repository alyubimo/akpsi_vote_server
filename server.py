import os
from gevent import monkey
monkey.patch_all()

import time
from threading import Thread
from flask import Flask, render_template, session, request
from flask.ext.socketio import SocketIO, emit, disconnect
from flask.ext.cas import CAS, login, logout, login_required

app = Flask(__name__)

socketio = SocketIO(app)
cas = CAS(app)

app.debug = True
app.config['SECRET_KEY'] = 'secret!'
app.config['CAS_SERVER'] = 'https://login.umd.edu'
app.config['CAS_LOGIN_ROUTE'] = '/cas/login'
app.config['CAS_AFTER_LOGIN'] = 'index'

admins = set()
admins.add('cgonza1')

clients = set()
thread = None

def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        time.sleep(10)
        count += 1

# socketio.emit('my response',
#               {'data': 'Server generated event', 'count': count},
#               namespace='/vote')

# global thread
# if thread is None:
#     thread = Thread(target=background_thread)
#     thread.start()

#
# Route definition
#

@app.route('/')
@login_required
def index():
    # Check if already connected, only admins are allowed to do this
    if cas.username not in admins and cas.username in clients:
        return render_template('error.html', error="duplicate")
    else:
        clients.add(cas.username)
        return render_template('index.html', username = cas.username)

@app.route('/admin')
@login_required
def admin_panel():
    if cas.username not in admins:
        return render_template('error.html', error="denied")
    else:
        return render_template('admin.html')

#
# Admin socket context functions
#

@socketio.on('start_vote', namespace='/vote')
def start_vote(message):
    if cas.username in admins:
        emit('vote_start', {'name': message['name'], 'abstain': message['abstain']}, broadcast=True)

@socketio.on('end_vote', namespace='/vote')
def end_vote():
    if cas.username in admins:
        emit('vote_end', broadcast=True)


#
# Socket context functions
#

@socketio.on('my event', namespace='/vote')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']})

@socketio.on('submit_vote', namespace='/vote')
def function():
    pass

@socketio.on('disconnect_req', namespace='/vote')
def disconnect_request():
    if cas.username in clients:
        print('Client disconnecting, removing: ' + cas.username)
        clients.remove(cas.username)
    disconnect()

@socketio.on('connect', namespace='/vote')
def socket_attach():
    print('Socket attached: ' + cas.username)

@socketio.on('disconnect', namespace='/vote')
def socket_detach():
    print('Socket disconnected')

if __name__ == "__main__":
    # Fetch the environment variable (so it works on Heroku):
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
