import os
import csv

def log_hyperparameters(file_path, hyperparameters, accuracy, loss):
    # Check if file exists
    file_exists = os.path.isfile(file_path)

    with open(file_path, 'a', newline='') as file: 
        # Create a csv writer object
        writer = csv.writer(file)
        # Write headerS if file doesnt exist
        if not file_exists:
            writer.writerow(["learning_rate", "batch_size", "num_epochs", "dropout_rate", "activation_function", "optimizer", "accuracy", "loss"])
        #add hyperparameters and metrics to csv file in a new row
        writer.writerow([ 
            hyperparameters['learning_rate'],
            hyperparameters['batch_size'],
            hyperparameters['num_epochs'],
            hyperparameters['dropout_rate'],
            hyperparameters['activation_function'],
            hyperparameters['optimizer'],
            accuracy,
            loss
        ])
