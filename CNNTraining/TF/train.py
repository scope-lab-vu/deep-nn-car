#train.py
#Authored: Shreyas Ramakrishna
#Reference: https://github.com/mbechtel2/DeepPicar-v2
#Last Edited: 08/14/2018
#Description: Model training in tensorflow, which saves the model and weights with lowest loss

import os
import tensorflow as tf
import time
import csv
import imageprocess1
import preprocess
import model
import sys

best_train_loss = 0.0
last_improvement = 0
i=0
full_data_training =  True
batch_data_training = False

csvfile = open("trial1117r.csv", "w")
#######Parameters########
save_path = "./trial1117r"
model_name = "test"
training_steps=200
model_load_file="test.ckpt"
#########################

##########Saving Directories##########
save_dir = os.path.abspath('trial1117r')
######################################


def main():

	#if not os.path.isdir(out_dir):
	#   os.makedirs(out_dir)

	if not os.path.isdir(save_dir):
	    os.makedirs(save_dir)

	def join(dirpath, filename):
	    return os.path.join(dirpath, filename)

	sess = tf.InteractiveSession()
	loss=tf.losses.mean_squared_error(model.y_,model.y)
	#Use adam optimizer
	train_step = tf.train.AdamOptimizer(0.0001).minimize(loss)
	saver = tf.train.Saver()
	model_load_path = join(save_dir, model_load_file)
	print("....Loading existing model from.... %s" %model_load_path)

	if os.path.exists(model_load_path + ".index"):
	    print ("....Loading initial weights from %s...." % model_load_path)
	    saver.restore(sess, model_load_path)
	else:
	    print ("....Initialize weights....")
	init = tf.global_variables_initializer()

	sess.run(init)
	n = 0
	k = 0
	for i in range(training_steps):
		lossdata =[]
		#Unshuffled Full data training and validation
		if(full_data_training == True):
			
			if((i+1) % 10)!=0:
				print("...............training step {}...............".format(i+1))
				inputs = imageprocess1.load_training_images()
				outputs= imageprocess1.read_training_output_data()


			if((i+1) % 10)==0:
				print("...............validation step {}...............".format(i+1))
				inputs = imageprocess1.load_validation_images()
				outputs= imageprocess1.read_validation_output_data()


		#Shuffled batch data for training and validation
		if(batch_data_training == True):

			if((i+1) % 10)!=0:
				print("...............training step {}...............".format(i+1))
				inputs,outputs = imageprocess1.load_batch_data('train')


			if((i+1) % 10)==0:
				print("...............validation step {}...............".format(i+1))
				inputs,outputs = imageprocess1.load_batch_data('validation')

		
       		 #Running the model with the data
		train_step.run(feed_dict={model.x: inputs, model.y_:outputs})
		t_loss = loss.eval(feed_dict={model.x: inputs, model.y_:outputs})
		print("step {} of {},train loss {}".format(i+1, training_steps, t_loss))
		v_loss = loss.eval(feed_dict={model.x: inputs1, model.y_: outputs1})
		print("step {} of {},validation loss {}".format(i+1, training_steps, v_loss))
		
		if((i+1) % 10)!= 0:
			#getting the training loss
			t_loss = loss.eval(feed_dict={model.x: inputs, model.y_: outputs})
			print("step {} of {},train loss {}".format(i+1, training_steps, t_loss))
			writer = csv.writer(csvfile)
			writer.writerow([t_loss])

		if((i+1) % 10) == 0:

  			#t_loss = loss.eval(feed_dict={model.x: inputs, model.y_: outputs})
			v_loss = loss.eval(feed_dict={model.x: inputs, model.y_: outputs})
			print("step {} of {},validation loss {}".format(i+1, training_steps, v_loss))
			writer = csv.writer(csvfile)
			writer.writerow([v_loss])
		
		if(i==0):
		    best_train_loss = t_loss
		    saver.save(sess, save_path + '/' + model_name + '.ckpt')
		    print("Saving the first model with name {} for training step{}:".format(model_name, i+1))

		if(i>0 and t_loss < best_train_loss):
			k = 0
			epoch_num=i
			#loss = (best_train_loss - t_loss)
			print("loss has improved by %f"%(best_train_loss - t_loss))
			saver.save(sess, save_path + '/' + model_name + '.ckpt')
			print("Saving the best model with name {} for training step{}:".format(model_name, i+1))
			best_train_loss = t_loss

		if(i>0 and t_loss > best_train_loss):
			k = k+1#counter for not entering the overfitting phase
			if(k==5):
				assert (k == 5),"Entering the overfitting phase!"

		# appending loss data for plotting
		lossdata.append(t_loss)
		lossdata.append(v_loss)
		writer = csv.writer(csvfile)
		writer.writerow(lossdata)

	print("The best model was saved at epoch {} and has a loss of {}".format(epoch_num+1, best_train_loss))
	time.sleep(20)


if __name__ == '__main__':
         main()
