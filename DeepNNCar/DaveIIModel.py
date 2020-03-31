import keras.backend as K
import numpy as np
import keras
from keras.models import Model,load_model
from keras.layers import Dense, Dropout, Activation, Flatten, BatchNormalization,Lambda, Input, ELU,Reshape
from keras.layers import Conv2D, MaxPooling2D,Input,AveragePooling2D,InputLayer,Convolution2D
from keras.models import Sequential
import os
import cv2
from keras.callbacks import ModelCheckpoint, LearningRateScheduler, TensorBoard, EarlyStopping, History
import math
#from sklearn.metrics import mean_squared_error
from keras.engine.topology import Layer
from keras.initializers import RandomUniform, Initializer, Constant
from keras.initializers import Initializer
import tensorflow as tf

RBF_LAMBDA = 0.5
# this is a helper function
def softargmax(x,beta=1e10):
    """
    Perform argmax in a differential manner
    :param x: An array with the original inputs. `x` is expected to have spatial dimensions.
    :type x: `np.ndarray`
    :param beta: A large number to approximate argmax(`x`)
    :type y: float
    :return: argmax of tensor
    :rtype: `tensorflow.python.framework.ops.Tensor`
    """
    x = tf.convert_to_tensor(x)
    x_range = tf.range(43)
    x_range = tf.dtypes.cast(x_range,tf.float32)
    return tf.reduce_sum(tf.nn.softmax(x*beta) * x_range, axis=1)

def RBF_Loss(y_true,y_pred):
    """
    
    :param y_true: 
    :type x: `np.ndarray`
    :param beta: A large number to approximate argmax(`x`)
    :type y: float
    :return: Calculated loss
    :rtype: `tensorflow.python.framework.ops.Tensor`
    """
    lam = RBF_LAMBDA
    indices = softargmax(y_true)
    indices = tf.dtypes.cast(indices,tf.int32)
    y_pred = tf.dtypes.cast(y_pred,tf.float32)
    y_true = tf.dtypes.cast(y_true,tf.float32)
    row_ind = K.arange(K.shape(y_true)[0])
    full_indices = tf.stack([row_ind,indices],axis=1)
    d = tf.gather_nd(y_pred,full_indices)
    y_pred = lam - y_pred
    y_pred = tf.nn.relu(y_pred)
    d2 = tf.nn.relu(lam - d)
    S = K.sum(y_pred,axis=1) - d2
    y = K.sum(d + S)
    return y

def RBF_Soft_Loss(y_true,y_pred):
    lam = RBF_LAMBDA
    indices = softargmax(y_true)
    indices = tf.dtypes.cast(indices,tf.int32)
    y_pred = tf.dtypes.cast(y_pred,tf.float32)
    y_true = tf.dtypes.cast(y_true,tf.float32)
    row_ind = K.arange(K.shape(y_true)[0])
    full_indices = tf.stack([row_ind,indices],axis=1)
    d = tf.gather_nd(y_pred,full_indices)
    y_pred = K.log(1+ K.exp(lam - y_pred))
    S = K.sum(y_pred,axis=1) - K.log(1+K.exp(lam-d))
    y = K.sum(d + S)
    return y

def DistanceMetric(y_true,y_pred):
    e  = K.equal(K.argmax(y_true,axis=1),K.argmin(y_pred,axis=1))
    s = tf.reduce_sum(tf.cast(e, tf.float32))
    n = tf.cast(K.shape(y_true)[0],tf.float32)
    return s/n

class RBFLayer(Layer):
    def __init__(self, units, gamma, **kwargs):
        super(RBFLayer, self).__init__(**kwargs)
        self.units = units
        self.gamma = K.cast_to_floatx(gamma)

    def build(self, input_shape):
#         print(input_shape)
#         print(self.units)
        self.mu = self.add_weight(name='mu',
                                  shape=(int(input_shape[1]), self.units),
                                  initializer=keras.initializers.RandomUniform(minval=-1, maxval=1, seed=1234),
                                  trainable=True)
        super(RBFLayer, self).build(input_shape)

    def call(self, inputs):
        diff = K.expand_dims(inputs) - self.mu
        l2 = K.sum(K.pow(diff, 2), axis=1)
        #l2 = tf.keras.backend.l2_normalize(diff,axis=1)
        res = K.exp(0.0)*l2
        return res

    def compute_output_shape(self, input_shape):
        return (input_shape[0], self.units)

    def get_config(self):
        # have to define get_config to be able to use model_from_json
        config = {
            'units': self.units,
            'gamma': self.gamma
        }
        base_config = super(RBFLayer, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

class DaveIIModel():
    def __init__(self,RBF=False,anomalyDetector=False):
        self.input_size = (66, 200, 3)
        self.num_classes = 10
        self.isRBF = RBF
        self.isAnomalyDetector = anomalyDetector
        assert not (self.isRBF and self.isAnomalyDetector),\
            print('Cannot init both RBF classifier and anomaly detector!')
        model = Sequential()
        input1= Input(shape=(66,200,3), name='image')
        steer_inp = BatchNormalization(epsilon=0.001, axis=-1,momentum=0.99)(input1)
        layer1 = Conv2D(24, (5, 5), padding="valid", strides=(2, 2), activation="relu")(steer_inp)
        layer2 = Conv2D(36, (5, 5), padding="valid", strides=(2, 2), activation="relu")(layer1)
        layer3 = Conv2D(48, (5, 5), padding="valid", strides=(2, 2), activation="relu")(layer2)
        layer4 = Conv2D(64, (3, 3), padding="valid", strides=(1, 1), activation="relu")(layer3)
        layer5 = Conv2D(64, (3, 3), padding="valid", strides=(1, 1))(layer4) # add relu for old time sake
        layer6 = Flatten()(layer5)
        if (RBF):
            layer6 = Activation('relu')(layer6) # remove me for old time sake
            layer7 = Dense(1164, activation='relu')(layer6)
            layer8 = Dense(500, activation='relu')(layer7)
            layer9 = Dense(64, activation='tanh')(layer8)
            prediction = RBFLayer(10,0.5)(layer9)
            model=Model(inputs=input1, outputs=prediction)
            model.compile(loss=RBF_Soft_Loss,optimizer=keras.optimizers.Adam(),metrics=[DistanceMetric])
        elif(anomalyDetector):
            layer7 = Activation('tanh')(layer6)
            prediction = RBFLayer(10,0.5)(layer7)
            model=Model(inputs=input1, outputs=prediction)
            model.compile(loss=RBF_Soft_Loss,optimizer=keras.optimizers.Adam(),metrics=[DistanceMetric])
        else:
            layer6 = Activation('relu')(layer6) # remove me for old time sake
            layer7 = Dense(1164, activation='relu')(layer6)
            layer8 = Dense(100, activation='relu')(layer7)
            layer9 = Dense(50, activation='relu')(layer8)
            layer10 = Dense(10, activation='relu')(layer9)
            prediction = Dense(10, name='predictions',activation="softmax")(layer10)
            model=Model(inputs=input1, outputs=prediction)
            model.compile(loss='categorical_crossentropy',optimizer=keras.optimizers.Adam(),metrics=['accuracy'])
            # model_noSoftMax = innvestigate.utils.model_wo_softmax(model) # strip the softmax layer
            # self.analyzer = innvestigate.create_analyzer('lrp.alpha_1_beta_0', model_noSoftMax) # create the LRP analyzer
        self.model = model

    def predict(self,X):
        predictions = self.model.predict(X)
        if (self.isRBF or self.isAnomalyDetector):
            lam = RBF_LAMBDA
            Ok = np.exp(-1*predictions)
            top = Ok*(1+np.exp(lam)*Ok)
            bottom = np.prod(1+np.exp(lam)*Ok,axis=1)
            predictions = np.divide(top.T,bottom).T
        return predictions

    def preprocess(self,X):
        return X/255.

    def unprocess(self,X):
        return X*255.

    def getInputSize(self):
        return self.input_size

    def getNumberClasses(self):
        return self.num_classes

    def train(self,train_data_generator,validation_data_generator,saveTo,epochs=10,class_weight=None):

        if (self.isRBF or self.isAnomalyDetector):
            checkpoint = ModelCheckpoint(saveTo, monitor='DistanceMetric', verbose=1, save_best_only=True, save_weights_only=False, mode='max', period=1)
        else:
            checkpoint = ModelCheckpoint(saveTo, monitor='val_acc', verbose=1, save_best_only=True, save_weights_only=False, mode='auto', period=1)
        self.model.fit_generator(
            train_data_generator,
            steps_per_epoch = math.ceil(train_data_generator.samples/train_data_generator.batch_size),
            epochs = epochs,
            validation_data = validation_data_generator,
            validation_steps = math.ceil(validation_data_generator.samples/validation_data_generator.batch_size),
            callbacks = [checkpoint],
            class_weight=class_weight)

    def train_data(self,X,Y,saveTo,epochs=10,class_weight=None):
        if (self.isRBF or self.isAnomalyDetector):
            checkpoint = ModelCheckpoint(saveTo, monitor='DistanceMetric', verbose=1, save_best_only=True, save_weights_only=False, mode='max', period=1)
        else:
            checkpoint = ModelCheckpoint(saveTo, monitor='val_acc', verbose=1, save_best_only=True, save_weights_only=False, mode='auto', period=1)
        self.model.fit(X, Y,
                batch_size=8,
                epochs=epochs,
                verbose=1,
                callbacks=[checkpoint],
                shuffle=True,
                class_weight=class_weight)
                
    def save(self):
        raise NotImplementedError

    def load(self,weights):
        if (self.isRBF or self.isAnomalyDetector):
            self.model = load_model(weights, custom_objects={'RBFLayer': RBFLayer,'DistanceMetric':DistanceMetric,'RBF_Soft_Loss':RBF_Soft_Loss})
        else:
            self.model = load_model(weights)
        
    def evaluate(self,X,Y):
        predictions = self.predict(X)
        accuracy = np.sum(np.argmax(predictions,axis=1) == np.argmax(Y, axis=1)) / len(Y)
        print('The accuracy of the model: ', accuracy)
        #mse = mean_squared_error(np.argmax(Y, axis=1),np.argmax(predictions,axis=1))
        #print('MSE of model: ', mse)
        print('Number of samples: ', len(Y))
    
    def evaluate_with_reject(self,X,Y):
        predictions = self.predict_with_reject(X)
        accuracy = np.sum(np.argmax(predictions,axis=1) == np.argmax(Y, axis=1)) / len(Y)
        print('The accuracy of the model: ', accuracy)
        #mse = mean_squared_error(np.argmax(Y, axis=1),np.argmax(predictions,axis=1))
        #print('MSE of model: ', mse)
        print('Number of samples: ', len(Y))
    
    def predict_with_reject(self,X):
        assert self.isRBF or self.isAnomalyDetector, \
            print('Cannot reject a softmax classifier')
        predictions = self.model.predict(X)
        lam = RBF_LAMBDA
        Ok = np.exp(-1*predictions)
        bottom = np.prod(1+np.exp(lam)*Ok,axis=1)
        reject = 1.0/bottom
        top = Ok*(1+np.exp(lam)*Ok)
        predictions = np.divide(top.T,bottom).T
        predictions = np.concatenate((predictions,np.expand_dims(reject,axis=1)),axis=1)
        return predictions
    
    def reject(self,X):
        assert self.isRBF or self.isAnomalyDetector, \
            print('Cannot reject a softmax classifier')
        predictions = self.model.predict(X)
        lam = RBF_LAMBDA
        Ok = np.exp(-1*predictions)
        bottom = np.prod(1+np.exp(lam)*Ok,axis=1)
        return 1.0/bottom
