import sys
network_config = sys.argv[1]
split_config = sys.argv[2]
feature_dir = sys.argv[3]
model_dir = sys.argv[4]

seed_value=13003
miniBatchSize=64

halfMiniBS=int(miniBatchSize/2);

# 1. Set `PYTHONHASHSEED` environment variable at a fixed value
import os
os.environ['PYTHONHASHSEED']=str(seed_value)
os.environ['LD_LIBRARY_PATH']='/usr/local/cuda/lib64/'

# 2. Set `python` built-in pseudo-random generator at a fixed value
import random
random.seed(seed_value)

# 3. Set `numpy` pseudo-random generator at a fixed value
import numpy as np
np.random.seed(seed_value)

# 4. Set `tensorflow` pseudo-random generator at a fixed value
import tensorflow as tf
tf.set_random_seed(seed_value)

# 5. Configure a new global `tensorflow` session
from keras import backend as K
session_conf = tf.ConfigProto(intra_op_parallelism_threads=1, inter_op_parallelism_threads=1)
session_conf.gpu_options.allow_growth = True
sess = tf.Session(graph=tf.get_default_graph(), config=session_conf)
K.set_session(sess)
import os
import shutil
import math

from keras.utils.np_utils import to_categorical
from keras import losses

from tdnn_utils import load_training_data
from tdnn_models import get_multichannel_tdnn_model
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau, LearningRateScheduler
from keras.utils.generic_utils import get_custom_objects
from keras.optimizers import Adam

from sklearn.utils import shuffle

split_config = split_config.split(',')[:-1]

split_config = [int(x) for x in split_config]


network_config = network_config.split(',')[:-1]

network_config = [int(x) for x in network_config]
print(split_config)
print('Loading BCKG data')
[bckg_data,bckg_val_data]=load_training_data(feature_dir+'/bckg',split_config)
print('Loading SEIZ data')
[seiz_data,seiz_val_data]=load_training_data(feature_dir+'/seiz',split_config)

feat_size=bckg_data[0][0].shape[1]
num_channels=bckg_data[0][0].shape[0]

seizure_data_epoch_size=0
print('stats on seiz training data')
for id,data in enumerate(seiz_data):
	seizure_data_epoch_size=seizure_data_epoch_size+math.floor(len(data)/halfMiniBS)
	print('total seizure data in split' +str(id)+' : '+str(len(data)))


val_data_epoch_size=0
print('stats on seiz val data')
for id,data in enumerate(seiz_val_data):
	val_data_epoch_size=val_data_epoch_size+math.floor(len(data)/halfMiniBS)
	print('total seizure data in split' +str(id)+' : '+str(len(data)))

print('stats on bckg training data')
for id,data in enumerate(bckg_data):
	print('total seizure data in split' +str(id)+' : '+str(len(data)))

print('stats on bckg val data')
for id,data in enumerate(bckg_val_data):
	print('total seizure data in split' +str(id)+' : '+str(len(data)))


print('No of steps_per_epoch: '+str(seizure_data_epoch_size))
print('No of val steps_per_epoch: '+str(val_data_epoch_size))




no_of_splits=len(split_config)
def seiz_data_generator(se_data,bc_data):
	step=0
	current_seiz_inds=[0]*no_of_splits
	current_bckg_inds=[0]*no_of_splits
	while True:
		for s in range(no_of_splits):
			if(step%no_of_splits==s):
				seiz_start_ind=current_seiz_inds[s]
				bckg_start_ind=current_bckg_inds[s]
				if seiz_start_ind+halfMiniBS <= len(se_data[s]):
					seiz_batch_data=se_data[s][seiz_start_ind:seiz_start_ind+halfMiniBS]	
				else:
					seiz_batch_data=se_data[s][seiz_start_ind:]
					end_ind = (seiz_start_ind+halfMiniBS)%len(se_data[s]) 
					seiz_batch_data=seiz_batch_data+se_data[s][:end_ind]
				current_seiz_inds[s] = (seiz_start_ind+halfMiniBS)%len(se_data[s])

				if bckg_start_ind+halfMiniBS <= len(bc_data[s]):
					bckg_batch_data=bc_data[s][bckg_start_ind:bckg_start_ind+halfMiniBS]	
				else:
					bckg_batch_data=bc_data[s][bckg_start_ind:]
					end_ind = (bckg_start_ind+halfMiniBS)%len(bc_data[s]) 
					bckg_batch_data=bckg_batch_data+bc_data[s][:end_ind]
				current_bckg_inds[s] = (bckg_start_ind+halfMiniBS)%len(bc_data[s])
				break; 
			else:	
				continue
		seiz_batch_label = [1]*len(seiz_batch_data)
		bckg_batch_label = [0]*len(bckg_batch_data)

		batch_train_data = seiz_batch_data+bckg_batch_data
		batch_train_label = seiz_batch_label+bckg_batch_label

		#shuffly_perm = np.random.permutation(len(batch_train_data)).tolist()
		#batch_train_data=batch_train_data[shuffly_perm]
		#batch_train_label=batch_train_label[shuffly_perm]
		batch_train_data,batch_train_label = shuffle(batch_train_data,batch_train_label)

		batch_train_data = np.asarray(batch_train_data)
		batch_train_label = np.asarray(batch_train_label)

		batch_train_data = np.swapaxes(batch_train_data,2,3)
		batch_train_label = to_categorical(np.squeeze(batch_train_label),num_classes=2)

		step = step+1

		yield batch_train_data, batch_train_label


def fixed_data_generator(se_data,bc_data):
	step=0
	split=0
	split_data=[]
	split_label=[]
	for i in range(no_of_splits):
		split_seiz_data = se_data[i]
		split_bckg_data = bc_data[i]
		split_bckg_data = split_bckg_data[0:len(split_seiz_data)]
		split_seiz_label = [1]*len(split_seiz_data)
		split_bckg_label = [0]*len(split_bckg_data)
		combined_data=split_seiz_data+split_bckg_data
		combined_label=split_seiz_label+split_bckg_label
		combined_data,combined_label=shuffle(combined_data, combined_label)
		split_data.append(combined_data)
		split_label.append(combined_label)

	while True:
		for s in range(no_of_splits):
			if(split%no_of_splits==s):
				start_ind=0
				while (start_ind+miniBatchSize<=len(split_data[s])):
					batch_train_data = split_data[s][start_ind:start_ind+miniBatchSize]
					batch_train_label = split_label[s][start_ind:start_ind+miniBatchSize]

					batch_train_data = np.asarray(batch_train_data)
					batch_train_label = np.asarray(batch_train_label)

					batch_train_data = np.swapaxes(batch_train_data,2,3)
					batch_train_label = to_categorical(np.squeeze(batch_train_label),num_classes=2)
					step=step+1
					start_ind = start_ind + miniBatchSize
					yield batch_train_data, batch_train_label
		split=(split+1)%no_of_splits
		if split==0:
			print('completed first epoch at step : ' +str(step))




model = get_multichannel_tdnn_model(feat_size, 2, num_channels, network_config)
adam_opt = Adam(lr=0.001, clipvalue=1)
model.compile(loss=losses.categorical_crossentropy, optimizer=adam_opt,
              metrics=['accuracy'])
model.summary()

if os.path.exists(model_dir):
    shutil.rmtree(model_dir)
os.makedirs(model_dir)

def lr_schduler(epoch):
	return 0.001/(1+0.1*epoch)

early_stopping = EarlyStopping(patience=10, verbose=1)
model_checkpoint = ModelCheckpoint(model_dir+'/keras.model',monitor='val_acc', mode='max',save_best_only=True, verbose=1)
reduce_lr = ReduceLROnPlateau(factor=0.5, patience=1, min_lr=0.00000000001, verbose=1, monitor='val_acc', mode='max')
lr_epoch_wise_reducer = LearningRateScheduler(lr_schduler)
model.fit_generator(fixed_data_generator(seiz_data,bckg_data),
	validation_data=fixed_data_generator(seiz_val_data,bckg_val_data),
	validation_steps=val_data_epoch_size,
	steps_per_epoch=seizure_data_epoch_size,
	epochs=3000, verbose=1,
	callbacks=[early_stopping, model_checkpoint, reduce_lr])


