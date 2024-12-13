import flask
import numpy as np
from PIL import Image
import keras
import json
from keras.models import load_model
import random
import time
from flask_cors import CORS, cross_origin
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from stroke_preprocessing import vector_to_raster

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, manage_session=False)
CORS(app, resources={r"/*": {"origins": "*"}})

# Load model and class names
model = load_model('models/adam_npy_model2.keras')

with open('real_class_names.json', 'r') as f:
    class_names = json.load(f)  # Ensure this is a list

# online users and their game status
online_users = {}
# maintain current game sessions - game code, users and scores
game_sessions = {}
# user to session id
user_sids = {}  

@app.route('/')
def enter():
    return render_template('enter.html')

@app.route('/main', methods=['POST'])
def main_page():
    username = request.form.get('username')
    if not username:
        return "Username is required", 400
    session['username'] = username
    online_users[username] = {'status': 'online', 'game_code': None}
    print(f"{username} is ready to play.")
    return render_template('main.html', username=username, online_users=online_users)


@socketio.on('sandbox')
def handle_sandbox(data):
    username = data['player']
    print(f"{username} is in the sandbox.")
    emit('redirect', {'url': url_for('sandbox')})

@app.route('/sandbox')
def sandbox():
    username = session.get('username')
    return render_template('sandbox.html', username=username)

@app.route('/game/<game_code>')
def game_page(game_code):
    if game_code in game_sessions:
        return render_template('game.html', game_code=game_code)
    return "Game not found", 404

@socketio.on('connect')
def handle_connect():
    username = session.get('username')
    print(f"connect from user {username}")

    if username:
        user_sids[username] = request.sid  
        sid = user_sids[username]
        print(f"set user {username}, sid to {sid}")
        online_users[username] = {'status': 'online', 'game_code': None}
        print(f"{username} connected")
    emit('update_online_users', online_users, broadcast=True)

@socketio.on('user_connect')
def handle_user_connect(data):
    username = data.get('username')
    game_code = data.get('game_code')
    if username:
        if username in user_sids:
            print(f"{username} reconnected.")
        user_sids[username] = request.sid  
        online_users[username] = {'status': 'online', 'game_code': game_code}
        print(f"{username} connected, game {game_code}, sid {user_sids[username]}")
        emit('update_online_users', online_users, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username')
    online_users[username] = {'status': 'offline'}
    print(f"{username} disconnected.")
   
@socketio.on('leave_game')
def handle_leave_game(data):
    game_code = data['game_code']
    username = data['username']
    if username:
        user_sids.pop(username, None)  # Remove the SID mapping
        online_users.pop(username, None)
        print(f"{username} disconnected.")
        emit('update_online_users', online_users, broadcast=True)
        leave_room(user_sids.get(username))
    if game_code in game_sessions and username in game_sessions[game_code]['players']:
        other_player = other_player(username, game_code)
        game_sessions[game_code]['scores'][other_player] += 1
        round_winner = other_player
        next_round(game_code, round_winner, "Other user left the game, victory by default!")
        

@socketio.on('invite')
def handle_invite(data):
    inviter = data['inviter']
    invitee = data['invitee']
    if invitee not in online_users:
        print(f"{invitee} is not online.")
        return

    print(f"{inviter} is inviting {invitee}.")
    game_code = str(random.randint(100000, 999999))
    game_sessions[game_code] = {
        'players': [inviter, invitee], 
        'status': 'waiting', 
        'round': 0, 
        'scores': {inviter: 0, invitee: 0}
    }
    online_users[inviter]['game_code'] = game_code
    print("inviter session ID:", user_sids.get(inviter))
    online_users[invitee]['game_code'] = game_code
    print("invitee session ID:", user_sids.get(invitee))
    print(f"Game session created with code {game_code} for {inviter} and {invitee}.")

    # Emit an invite to the invitee 
    invitee_sid = user_sids.get(invitee)
    if invitee_sid:
        socketio.emit('invite', {'inviter': inviter, 'game_code': game_code}, to=invitee_sid)
        socketio.emit('update_game_session', {'game_code': game_code})

@app.route('/game/<game_code>')
def game(game_code):
    return render_template('game.html', game_code=game_code)

@socketio.on('accept_invite')
def handle_accept_invite(data):
    game_code = data['game_code']
    invitee = data['username']
    inviter = data['inviter']
    print('hello from accept_invite')

    if invitee and game_code in game_sessions and invitee in game_sessions[game_code]['players']:
        
        # Check if both players have joined the game
        if all(player in online_users and online_users[player]['game_code'] == game_code for player in game_sessions[game_code]['players']):
            inviter_sid =  user_sids[inviter] #user_sids.get(game_sessions[game_code]['players'][0])
            invitee_sid =  user_sids[invitee] #user_sids.get(game_sessions[game_code]['players'][1])

            print(f"{invitee} accepted the invite for game code {game_code}.")

            # Emit an event to redirect both players to game.html with the game_code
            socketio.emit('redirect_to_game', {'game_code': game_code}, to=inviter_sid)
            socketio.emit('redirect_to_game', {'game_code': game_code}, to=invitee_sid)

            # wait for players to reconnet after redirect to new page, then start game
            time.sleep(2)
            start_game(game_code)
    
def start_game(game_code):
    if game_code in game_sessions:
        game_sessions[game_code]['round'] = 1
        game_sessions[game_code]['status'] = 'in_progress'
        try:
            category = random.choice(class_names)
            print(category)
        except Exception as e:
            print(f"Error selecting category: {e}")
            category = "default_category"

        game_sessions[game_code]['category'] = category
        print(f"Starting game with category: {category}") 
        socketio.emit('start_game', {
            'category': category, 
            'round': 1, 
            'game_code': game_code,
            'opponent': game_sessions[game_code]['players'][1]
        }, to=user_sids.get(game_sessions[game_code]['players'][0]))
        socketio.emit('start_game', {
            'category': category, 
            'round': 1, 
            'game_code': game_code,
            'opponent': game_sessions[game_code]['players'][0]
        }, to=user_sids.get(game_sessions[game_code]['players'][1]))

@socketio.on('predict')
def handle_predict(data):
    game_code = data['game_code']
    username = data['username']
    prediction = data['prediction']
    
    if game_code in game_sessions and username in game_sessions[game_code]['players']:
        category = game_sessions[game_code]['category']
        if prediction == category:
            game_sessions[game_code]['scores'][username] += 1
            round_winner = username
            next_round(game_code, round_winner, "You won this round!")
            next_round(game_code, other_player(round_winner, game_code), "You lost this round!")

def next_round(game_code, player, message):
    if game_code in game_sessions:
        game_sessions[game_code]['round'] += 1
        if game_sessions[game_code]['round'] > 5:
            end_game(game_code)
        else:
            socketio.emit('round_winner', {'winner': player, 'message': message}, to=user_sids.get(player))
            start_game(game_code)

def other_player(username, game_code):
    return [player for player in game_sessions[game_code]['players'] if player != username][0]

def end_game(game_code):
    if game_code in game_sessions:
        scores = game_sessions[game_code]['scores']
        winner = max(scores, key=scores.get)
        socketio.emit('game_winner', {'winner': winner}, room=game_code)
        del game_sessions[game_code]

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    strokes = data.get('strokes')

    # Process strokes
    image = vector_to_raster(strokes)
    image = np.expand_dims(image, axis=(0, -1)) 

    # Normalize the image
    image = image / 255.0

    # Make prediction
    prediction = model.predict(image)
    predicted_class_index = np.argmax(prediction)
    predicted_class = class_names[predicted_class_index]
    confidence = prediction[0][predicted_class_index] * 100
    if confidence < 20.0:
        predicted_class = "Unknown"

    print(f"Prediction: {prediction}")
    print(f"Predicted class index: {predicted_class_index}")
    print(f"Predicted class: {predicted_class}")
    print(f"Confidence: {confidence}")
    
    response = {
        'prediction': predicted_class,
        'confidence': confidence,
    }
    return jsonify(response)

if __name__ == '__main__':
    socketio.run(app, debug=True)
