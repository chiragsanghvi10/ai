import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from utils import vad
from utils import misc
from utils import objects
import librosa
import numpy as np
import pandas as pd
import os
from keras.models import model_from_json
import jsonpickle
import shutil
from flask import Flask
from flask import request
import time
import tensorflow as tf


def emotion(channel_files, loaded_model, task_folder, task_id):
    tf.keras.backend.clear_session()
    folder = task_folder + 'emotion_chunks/' + task_id+'/'
    if os.path.exists(folder) and os.path.isdir(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    # Download the task audio
    agent_snippets = vad.perform_vad(channel_files[0], folder)
    cust_snippets = vad.perform_vad(channel_files[1], folder)
    for snippet in agent_snippets:
        predicted, score = getEmotionPredictionChunk(
            snippet.path, loaded_model)
        snippet.add_signal(objects.Signal(predicted, score))
        snippet.set_speaker('Agent')
        if float(score) > 0.6:
            print('Agent: For time: ' + str(snippet.from_time) + ' to time: ' +
                  str(snippet.to_time) + ' Predicted label - > ' + predicted + ' with score -> ' + score + ' on file: ' + snippet.path)
    for snippet in cust_snippets:
        predicted, score = getEmotionPredictionChunk(
            snippet.path, loaded_model)
        snippet.add_signal(objects.Signal(predicted, score))
        snippet.set_speaker('Customer')
        if float(score) > 0.6:
            print('Customer: For time: ' + str(snippet.from_time) + ' to time: ' +
                  str(snippet.to_time) + ' Predicted label - > ' + predicted + ' with score -> ' + score + ' on file: ' + snippet.path)
    snips = agent_snippets + cust_snippets
    snips.sort(key=lambda x: x.from_time, reverse=False)
    #shutil.rmtree(folder)
    return snips


def getModel(model_path="NA", weight_path = "NA"):
    if model_path == "NA":
        model_path = os.getcwd() + '/speech/emotion/models/model.json'
    if weight_path == "NA":
        weight_path = os.getcwd() + "/speech/emotion/models/Emotion_Voice_Detection_Model.h5"
    json_file = open(model_path, 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)
    loaded_model.load_weights(weight_path)
    print("Loaded model and weights from disk")
    return loaded_model


def getEmotionPredictionChunk(f, loaded_model):
    labels = ['female_angry', 'female_calm', 'female_fearful', 'female_happy',
              'female_sad', 'male_angry', 'male_calm', 'male_fearful', 'male_happy', 'male_sad']
    X, sample_rate = librosa.load(
        f, res_type='kaiser_fast', duration=2.5, sr=22050*2, offset=0)
    sample_rate = np.array(sample_rate)
    mfccs = np.mean(librosa.feature.mfcc(
        y=X, sr=sample_rate, n_mfcc=13), axis=0)
    featurelive = mfccs
    livedf2 = featurelive
    livedf2 = pd.DataFrame(data=livedf2)
    livedf2 = livedf2.stack().to_frame().T
    twodim = np.expand_dims(livedf2, axis=2)
    livepreds = loaded_model.predict(twodim,
                                     batch_size=32,
                                     verbose=1)
    livepreds1 = livepreds.argmax(axis=1)
    return labels[livepreds1[0]], str(livepreds[0][livepreds1[0]])

if __name__ == '__main__':
    loaded_model = getModel("/home/absin/Documents/dev/sentenceSimilarity/speech/emotion/models/model.json",
    "/home/absin/Documents/dev/sentenceSimilarity/speech/emotion/models/Emotion_Voice_Detection_Model.h5")
    loaded_model._make_predict_function()
    print(getEmotionPredictionChunk('/home/absin/Downloads/output.wav',loaded_model))
