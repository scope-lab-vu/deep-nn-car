#train.py
#Authored: Shreyas Ramakrishna
#Last Edited: 10/12/2018
#Description: Modified DAVE-II CNN which takes images and speed as inputs to predict steering

import keras
import keras.models as models
from keras.models import Sequential, Model
from keras.layers.core import Dense, Dropout, Activation, Flatten, Reshape
from keras.layers import BatchNormalization,Input, add, concatenate
from keras.layers.recurrent import SimpleRNN, LSTM
from keras.layers.convolutional import Conv2D
from keras.optimizers import SGD, Adam, RMSprop
from keras.models import model_from_json, load_model
from sklearn.model_selection import train_test_split
#import sklearn.metrics as metrics
from keras.callbacks import ModelCheckpoint
import cv2
import numpy as np
import json
import matplotlib.pyplot as plt
plt.ion()
import imageprocess1
from pathlib import Path
from keras.callbacks import CSVLogger
from sklearn.model_selection import GridSearchCV
seed = 7
np.random.seed(seed)

history = CSVLogger('kerasloss.csv', append=True, separator=';')



def loadData():
    
    X = imageprocess1.load_training_images()
    A, Y = imageprocess1.read_training_output_data()
    X = np.array(X)
    A = np.array(A)
    Y = np.array(Y)
    return X,A,Y

def createModel():

    model = Sequential()
    input1= Input(shape=(66,200,3), name='image')
    input2=Input(shape=(1,), name='speed')
    steer_inp = BatchNormalization(epsilon=0.001, axis=-1,momentum=0.99)(input1)
    layer1 = Conv2D(24, (5, 5), padding="valid", strides=(2, 2), activation="relu")(steer_inp)
    layer2 = Conv2D(36, (5, 5), padding="valid", strides=(2, 2), activation="relu")(layer1)
    layer3 = Conv2D(48, (5, 5), padding="valid", strides=(2, 2), activation="relu")(layer2)
    layer4 = Conv2D(64, (3, 3), padding="valid", strides=(1, 1), activation="relu")(layer3)
    layer5 = Conv2D(64, (3, 3), padding="valid", strides=(1, 1), activation="relu")(layer4)
    layer6 = Flatten()(layer5)
    layer7 = Dense(1164, activation='relu')(layer6)
    layer8 = Dense(100, activation='relu')(layer7)
    layer9 = Dense(100, activation= 'relu')(input2)
    merged=add([layer8, layer9])
    layer10 = Dense(50, activation='relu')(merged)
    layer11 = Dense(50, activation='relu')(layer10)
    layer12 = Dense(10, activation='relu')(layer11)
    steer_out = Dense(1, activation='tanh')(layer12)
    model=Model(inputs=[input1,input2], outputs=steer_out)
    return model


def trainModel(model, X, A, Y):
    adam = keras.optimizers.Adam(lr=0.0001, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=False)
    model.compile(loss='mse', optimizer=adam)
    # checkpoint
    filePath = "weights.best.hdf5"
    checkpoint = ModelCheckpoint(filePath, monitor='loss', verbose=1, save_best_only=True, mode='min')
    callbacks_list = [checkpoint, history]
    model.fit([X,A], Y, epochs=200,batch_size=64, callbacks=callbacks_list, verbose=2)

def saveModel(model):
	#model.save('my_model.h5')

	model_json = model.to_json()
	with open("model.json", "w") as json_file:
		json_file.write(model_json)

	model.save_weights("model.h5")
	print("Saved model to disk")


if __name__ == "__main__":
	X, A, Y = loadData()
	#X, Y = normalizeData(X, Y)

	if (Path("model.json").is_file() and Path("weights.best.hdf5").is_file()):
	       with open('model.json', 'r') as jfile:
	              model = model_from_json(jfile.read())
	       model.load_weights("weights.best.hdf5")
	       print("load from the existing model...")
	else:
		model = createModel()
		print("create a new model")
		#print(model.summary())

	trainModel(model, X, A, Y)
	saveModel(model)
