# CNN Training, Testing and Evaluation

This directory has scripts used for training, testing and evaluating the CNN models.

***Keras***
This has the modified DAVE-II CNN model along with the training, validation and evaluation scripts.

***TF***
This has the original DAVE-II CNN model along with the training, validation and evaluation scripts.

***ProcessTrialData.py***
This script is used to synchronize the images, steering (PWM) and speed (PWM) data collected during the data collection mode. Once this script is run in the image folder, it generates a ProcessData.csv file which has all the time synchronized image, steering and speed data. This script has to be run to generate the ProcessData.csv file which is then used for training and testing of CNN.

Note: Sample datasets of images is available at https://drive.google.com/drive/folders/1cozxPGA6WnwNYARmAAvQPylbEPq_YqZn?usp=sharing 

# Training and validation

To train a CNN, you could use any one of the tensorflow or keras models. However, first you would need to collect a dataset of images and corresponding speed and steering values. All the steps related to data collection is explained in [DataCollection](https://github.com/scope-lab-vu/deep-nn-car/tree/master/DataCollection), and then the data has to be processed using the ProcessTrialData.py script. Also, Please look at the sample datasets which has the images and a csv file ProcessData.csv, which has the synchronized steering and speed values.

Run the following commands in the client terminal to train, validate and evaluate the CNN model.

Train the CNN model using the train.py script. Parameters like batch size and, number of epochs can be varied.

```
python train.py
```

Once the training is complete the models are saved in one of the following ways, (1) If you have used the tensorflow model, then the checkpointed and best model gets saved in the path (save folder) given in the train.py script, (2) If you use the keras model, then model files (model.h5, model.json and weights.best.hdf5) are stored in the same directory as the train.py script. 

Using the trained model you can use a second dataset to validate the trained CNN. The test.py script uses the trained model to predict the steering values for the second test dataset. This script also saves the predicted steering values to a csv file to perform an evaluation.

```
python test.py
```

The PerformanceCalculator.py script is used to evaluate the performance of the trained model. It evaluates the mean square error (MSE) between the original steering value and the predicted steering values of the test dataset. 

```
python PerformanceCalculator.py
```

After the training and validation of the CNN model, it can be used in the autonomous mode. You need to copy the trained model files to the RPi3 directory in which you are running your autonomous mode scripts. You could use the USB drive to copy the model or you could copy the model files to the required directory using scp.

To copy model files from the host machine to RPi3 use the following command

```
scp model.h5 pi@IP:Desktop/DeepNNCar
```

