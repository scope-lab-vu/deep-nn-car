# CNN Training, Testing and Evaluation

This directory has scripts used for training, testing and evaluating the CNN models.

***Keras**
This has the modified DAVE-II CNN model along with the training, validation and evaluation scripts.

***TF***
This has the original DAVE-II CNN model along with the training, validation and evaluation scripts.

***ProcessTrialData.py***
This script is used to synchronize the images, steering (PWM) and speed (PWM) data collected during the data collection mode. Once this script is run in the image folder, it generates a ProcessData.csv file which has all the time synchronized image, steering and speed data. This script has to be run to generate the ProcessData.csv file which is then used for training and testing of CNN.

Note: A sample dataset of images is available at    

