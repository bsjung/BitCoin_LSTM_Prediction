import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
from config import cfg
import csv
import os

tf.set_random_seed(777)  # reproducibility

class Learning:
	def __init__(self):
		# AccPrice AccVolume open low high close ma boll rsi
		self.seq_length = cfg.seq_length
		self.data_dim = cfg.data_dim
		self.hidden_dim = cfg.hidden_dim
		self.output_dim = cfg.output_dim
		self.learning_rate = cfg.learning_rate
		self.iterations = cfg.iterations
		self.train_percent = cfg.train_percent

		self.trainX = []
		self.trainY = []
		self.textX = []
		self.textY= []

		self.DataLoading()

		self.X = tf.placeholder(tf.float32, [None, self.seq_length, self.data_dim])
		self.Y = tf.placeholder(tf.float32, [None, self.output_dim])

	def DataLoading(self):
		data = []
		with open('data_revise.csv', newline="") as csvfile:
			spam = csv.reader(csvfile)
			for row in spam:
				row = [float(i) for i in row]
				data.append(row)
		data = data[::-1]
		data = self.MinMaxScaler(data) #normalize
		x = data
		y = data[:, [-1]]  # Close as label
		dataX = []
		dataY = []

		for i in range(0, len(y) - self.seq_length):
			_x = x[i:i + self.seq_length]
			_y = y[i + 5]  # Next close price
			print(_x, "->", _y)
			dataX.append(_x)
			dataY.append(_y)

		train_size = int(len(dataY) * self.train_percent)
		test_size = len(dataY) - train_size
		self.trainX, self.testX = np.array(dataX[0:train_size]), np.array(
			dataX[train_size:len(dataX)])
		self.trainY, self.testY = np.array(dataY[0:train_size]), np.array(
			dataY[train_size:len(dataY)])

	def MinMaxScaler(self, data):
		numerator = data - np.min(data, 0)
		denominator = np.max(data, 0) - np.min(data, 0)
		# noise term prevents the zero division
		return numerator / (denominator + 1e-7)

	def build_arch(self):
		cell = tf.contrib.rnn.BasicLSTMCell(num_units=self.hidden_dim, state_is_tuple=True, activation=tf.tanh)

		self.lstm_output, _states = tf.nn.dynamic_rnn(cell, self.X, dtype=tf.float32)

		self.Y_pred = tf.contrib.layers.fully_connected( self.lstm_output[:, self.output_dim], self.output_dim, activation_fn=None)

	def loss(self):
		self.Euclidian_loss = tf.reduce_sum(tf.square(self.Y_pred - self.Y))  # sum of the squares
		self.optimizer = tf.train.AdamOptimizer(self.learning_rate)
		self.train = self.optimizer.minimize(self.Euclidian_loss)

	def check(self):
		self.targets = tf.placeholder(tf.float32, [None, self.output_dim])
		self.predictions = tf.placeholder(tf.float32, [None, self.output_dim])
		self.rmse = tf.sqrt(tf.reduce_mean(tf.square(self.targets - self.predictions)))

	def run(self):
		self.DataLoading()
		self.build_arch()
		self.loss()
		self.check()

		with tf.Session() as sess:
			init = tf.global_variables_initializer()
			sess.run(init)
			self.savor = tf.train.Saver()
			# Training step
			if not os.path.exists(cfg.save_dir):
				os.mkdir(cfg.save_dir)
			else:
				if cfg.is_loading:
					ckpt_state = tf.train.get_checkpoint_state("saved")
					# Training step
					point = ckpt_state.all_model_checkpoint_paths[-1]
					self.savor.restore(sess, point)
			
			for i in range(self.iterations):
				_, step_loss = sess.run([self.train, self.Euclidian_loss], feed_dict={
					self.X: self.trainX, self.Y: self.trainY})
				print("[step: {}] loss: {}".format(i, step_loss))
				if i % 100 == 0:
					self.savor.save(sess, 'saved/test_model', global_step=i) # max_to_keep=None

			# Test step
			test_predict = sess.run(self.Y_pred, feed_dict={self.X: self.testX})
			rmse_val = sess.run(self.rmse, feed_dict={
				self.targets: self.testY, self.predictions: test_predict})
			print("RMSE: {}".format(rmse_val))

			# Plot predictions
			print(self.testY)
			print(test_predict)
			plt.plot(self.testY, label='actual')
			plt.plot(test_predict, label='predict')
			plt.xlabel("Time Period")
			plt.ylabel("Stock Price")
			plt.show()

if __name__ == "__main__":
	base_Learning = Learning()
	base_Learning.run()
