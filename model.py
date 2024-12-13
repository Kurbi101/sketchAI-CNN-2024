import numpy as np
import os
import tensorflow as tf
from sklearn.model_selection import train_test_split
from keras import layers, models, Sequential
from keras.callbacks import EarlyStopping
from keras.layers import BatchNormalization, Dropout, LeakyReLU
import json
from keras.optimizers import Adam, SGD, RMSprop, Adamax, Nadam
from log_hyperparameters import log_hyperparameters
from load_data import load_data


# print tensorflow version, make sure its the correct version
print("TensorFlow version:", tf.__version__) 

#print avaliable devices, check if gpu is available
print("Available devices:", tf.config.experimental.list_physical_devices()) 

#load class names from json file
with open('real_class_names.json', 'r') as f: 
    class_names = json.load(f)  

#save hyperparameters in a dictionary
hyperparameters = {
    'learning_rate': 0.001,
    'batch_size': 128,
    'num_epochs': 100,
    'activation_function': 'leaky_relu',
    'optimizer': 'adam',
    'dropout_rate': 0.25
}

#source directory
data_dir = 'npy_data'

#set optimizer
if hyperparameters['optimizer'] == 'adam':
  optimizer = Adam(learning_rate= hyperparameters['learning_rate'], )
if hyperparameters['optimizer'] == 'sgd':
  optimizer = SGD(learning_rate= hyperparameters['learning_rate'])
if hyperparameters['optimizer'] == 'rmsprop':
  optimizer = RMSprop(learning_rate= hyperparameters['learning_rate'])
if hyperparameters['optimizer'] == 'adamax':
  optimizer = Adamax(learning_rate= hyperparameters['learning_rate'])
if hyperparameters['optimizer'] == 'nadam':
  optimizer = Nadam(learning_rate= hyperparameters['learning_rate'])

#load data from data_dir
data, labels = load_data(data_dir, class_names, 1000) 

#reshape and normalize data
data = data.reshape(-1, 28, 28, 1) / 255.0 

#split data into training and validation
train_data, val_data, train_labels, val_labels = train_test_split(data, labels, test_size=0.2,train_size=0.8, random_state=123)  


with tf.device('/device:GPU:0'): 
  data_augmentation = Sequential( 
      [
        layers.GaussianNoise(0.2, input_shape=(28, 28, 1))
      ]
    )

#use gpu for training
with tf.device('/device:GPU:0'): 

  #create model, set layers
  model = models.Sequential([ 
          data_augmentation,
          layers.Conv2D(32, (3, 3), padding='same', input_shape=(28, 28, 1)), 
          BatchNormalization(),
          layers.Activation(hyperparameters['activation_function']),
          layers.Conv2D(32, (3, 3), padding='same'),
          BatchNormalization(),
          layers.Activation(hyperparameters['activation_function']),
          layers.MaxPooling2D((2, 2)),
          Dropout(hyperparameters['dropout_rate']),

          layers.Conv2D(64, (3, 3), padding='same'),
          BatchNormalization(),
          layers.Activation(hyperparameters['activation_function']),
          layers.Conv2D(64, (3, 3), padding='same'),
          BatchNormalization(),
          layers.Activation(hyperparameters['activation_function']),
          layers.MaxPooling2D((2, 2)),
          Dropout(hyperparameters['dropout_rate']),

          layers.Conv2D(128, (3, 3), padding='same'),
          BatchNormalization(),
          layers.Activation(hyperparameters['activation_function']),
          layers.Conv2D(128, (3, 3), padding='same'),
          BatchNormalization(),
          layers.Activation(hyperparameters['activation_function']),
          layers.MaxPooling2D((2, 2)),
          Dropout(hyperparameters['dropout_rate']),

          layers.Conv2D(256, (3, 3), padding='same'),
          BatchNormalization(),
          layers.Activation(hyperparameters['activation_function']),
          layers.Conv2D(256, (3, 3), padding='same'),
          BatchNormalization(),
          layers.Activation(hyperparameters['activation_function']),
          layers.MaxPooling2D((2, 2)),
          Dropout(hyperparameters['dropout_rate']),

          layers.GlobalAveragePooling2D(),
          layers.Dense(512),
          BatchNormalization(),
          layers.Activation(hyperparameters['activation_function']),
          Dropout(hyperparameters['dropout_rate']),
          layers.Dense(len(class_names), activation='softmax')
      ])

with tf.device('/device:GPU:0'):
  #compile model
  model.compile( 
              optimizer=optimizer,
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

with tf.device('/device:GPU:0'):
  #early stopping, stop training if validation loss does not improve after 10 epochs
  early_stopping = EarlyStopping(monitor='val_loss',  
                                 patience=10,
                                 restore_best_weights=True)

with tf.device('/device:GPU:0'):
    #train model
    history = model.fit( 
        train_data,
        train_labels,
        epochs=hyperparameters['num_epochs'],
        validation_data=(val_data, val_labels),
        batch_size=hyperparameters['batch_size'],
        callbacks=[early_stopping],
    )

#save model
model.save('models/adam_npy_model.keras')
print("Model saved successfully.")

#evaluate model and log hyperparameters for comparison
loss, accuracy = model.evaluate(val_data, val_labels) 
log_hyperparameters('hyperparameters_log.csv', hyperparameters, accuracy, loss) 
