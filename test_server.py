import flask
import numpy as np
from PIL import Image
import keras
import io
from keras.models import load_model
import base64
import tensorflow as tf
import os
import json
import random
from flask_cors import CORS, cross_origin
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from stroke_preproccesing import vector_to_raster

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, manage_session=False)
CORS(app, resources={r"/*": {"origins": "*"}})

# Load model and class names
model = load_model('models/adam_npy_model.keras')
with open('app/class_names.json', 'r') as f:
    class_names = json.load(f)  # Ensure this is a list


@app.route('/')
def enter():
    return render_template('canvas.html')
    
@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    strokes = data.get('strokes')

    # Process strokes
    image, large_image = vector_to_raster(strokes)
    image = np.expand_dims(image, axis=(0, -1))
    large_image = np.expand_dims(large_image, axis=(0, -1))
    # Make prediction
    prediction = model.predict(image)
    predicted_class = class_names[np.argmax(prediction)]
    confidence = np.max(prediction) * 100

    # Prepare response image 
    result_image = Image.fromarray(large_image.squeeze())
    result_image_bytes = io.BytesIO()
    result_image.save(result_image_bytes, format='PNG')
    result_image_base64 = base64.b64encode(result_image_bytes.getvalue()).decode('utf-8')

    response = {
        'prediction': predicted_class,
        'confidence': confidence,
        'resultImage': result_image_base64
    }
    return jsonify(response)

if __name__ == '__main__':
    socketio.run(app, debug=True)
