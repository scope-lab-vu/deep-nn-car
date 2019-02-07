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

To train a CNN, you could use any one of the tensorflow or keras models. However, first you would need to collect a dataset of images and corresponding speed and steering values. All the steps related to data collection is explained in [DataCollection](https://github.com/scope-lab-vu/deep-nn-car/tree/master/DataCollection), and then the data has to be processed using the ProcessTrialData.py script.

