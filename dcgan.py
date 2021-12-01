# -*- coding: utf-8 -*-
"""DCGAN.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1TvuLift5mdjtpr4Iz149sRtt9DfgTMIS
"""

import warnings
  
warnings.filterwarnings("ignore")

from keras.datasets import mnist

import keras
from keras.layers import *
from keras.layers.advanced_activations import LeakyReLU
from keras.models import Sequential, Model
from tensorflow.keras.optimizers import Adam
from keras.utils.vis_utils import plot_model

import numpy as np
import matplotlib.pyplot as plt

(X_train , _),(_, _) = mnist.load_data()

for i in range(25):
  plt.subplot(5,5,i+1)
  plt.imshow(X_train[i])
  plt.axis('off')

X_train.shape

##Normalization so that it will lie between -1 to +1, and it will fit in a neutral 
##network
X_train = (X_train-127.5)/127.5

print(X_train.min())
print(X_train.max())

TOTAL_EPOCHS = 200
BATCH_SIZE = 256
HALF_BATCH = 128

NO_OF_BATCHES = int(X_train.shape[0]/BATCH_SIZE)

NOISE_SHAPE = 100

adam = Adam(lr = 2e-4, beta_1 = 0.5)  #changing the learning rate of optimizer

##GENERATOR MODEL

generator = Sequential()

generator.add(Dense(units= 7*7*128, input_shape = (NOISE_SHAPE,)))
generator.add(Reshape((7,7,128)))
generator.add(LeakyReLU(0.2))
generator.add(BatchNormalization())

#(7,7,128) -> (14,14,64)
generator.add(Conv2DTranspose(64, (3,3), strides= (2,2), padding= 'same'))
generator.add(LeakyReLU(0.2))
generator.add(BatchNormalization())

#(14,14,64) -> (28,28,1) [orginial image dimensions]

generator.add(Conv2DTranspose(1, (3,3), strides= (2,2), padding= 'same', activation='tanh'))

generator.compile(loss = keras.losses.binary_crossentropy, optimizer= adam, metrics=['accuracy'])

generator.summary()

plot_model(generator, to_file='generator.png', show_shapes=True, show_layer_names=True)

#DISCRIMINATOR MODEL

#(28,28,1) -> (14,14,64)

discriminator = Sequential()
discriminator.add(Conv2D(64, kernel_size=(3,3), strides=(2,2), padding= 'same', input_shape= [28,28,1]))
discriminator.add(LeakyReLU(0.2))

#(14,14,64) -> (7,7,128)
discriminator.add(Conv2D(128, kernel_size=(3,3), strides=(2,2), padding= 'same'))
discriminator.add(LeakyReLU(0.2))

#(7,7,128) -> 6272  (A scalar value)

discriminator.add(Flatten())
discriminator.add(Dense(100))
discriminator.add(LeakyReLU(0.2))

discriminator.add(Dense(1, activation= 'sigmoid'))

discriminator.compile(loss = keras.losses.binary_crossentropy, optimizer= adam)

discriminator.summary()

plot_model(discriminator, to_file='discriminator_plot.png', show_shapes=True, show_layer_names=True)

#COMBINED MODEL

discriminator.trainable = False

gan_input = Input(shape = (NOISE_SHAPE, ))
generated_img = generator(gan_input)

gan_output = discriminator(generated_img)

#Functional API

combined = Model(gan_input, gan_output)
combined.compile(loss = keras.losses.binary_crossentropy, optimizer= adam)

combined.summary()

plot_model(combined, to_file='combined_plot.png', show_shapes=True, show_layer_names=True)

#Reshaping 

X_train = X_train.reshape(-1, 28, 28, 1)
X_train.shape

def display_images(samples = 25):

  noise = np.random.normal(0,1,size=(samples, NOISE_SHAPE))

  generated_img = generator.predict(noise)

  for i in range(samples):
    plt.subplot(5,5,i+1)
    plt.imshow(generated_img[i].reshape(28,28))
    plt.axis('off')

  plt.show()

##TRAINING LOOP

d_loss =[]  #Discriminator losses
g_loss =[ ]  #Generator losses


for epoch in range(TOTAL_EPOCHS):

  epoch_d_loss = 0.0
  epoch_g_loss = 0.0

  #Mini batch gradient descent
  for step in range(NO_OF_BATCHES):

#STEP1: Training discriminator
    discriminator.trainable = True

    #Get real data
    idx = np.random.randint(0, 60000, HALF_BATCH)
    real_imgs = X_train[idx]

    #Get fake data
    noise = np.random.normal(0, 1, size=(HALF_BATCH, NOISE_SHAPE))
    fake_imgs = generator.predict(noise)

    #Labels
    real_y = np.ones((HALF_BATCH, 1))*0.9  #one-sided label smoothing
    fake_y = np.zeros((HALF_BATCH, 1))

    #Now training discriminator
    d_loss_real = discriminator.train_on_batch(real_imgs, real_y)
    d_loss_fake = discriminator.train_on_batch(fake_imgs, fake_y)

    dis_loss = 0.5*d_loss_real + 0.5*d_loss_fake
    epoch_d_loss +=dis_loss

#STEP2: Training Generator (Discriminator freezes)

    discriminator.trainable = False

    noise = np.random.normal(0, 1, size= (BATCH_SIZE, NOISE_SHAPE))
    ground_truth_y = np.ones((BATCH_SIZE, 1))

    gen_loss = combined.train_on_batch(noise, ground_truth_y)
    epoch_g_loss += gen_loss


  print(f"Epoch{epoch+1}, Disc loss {epoch_d_loss/ NO_OF_BATCHES}, Generator loss {epoch_g_loss/ NO_OF_BATCHES}")

  d_loss.append(epoch_d_loss/NO_OF_BATCHES)
  g_loss.append(epoch_g_loss/NO_OF_BATCHES)

  if (epoch+1) % 10 == 0:
    generator.save("generator.h5")
    display_images()