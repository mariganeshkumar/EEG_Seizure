import sys
network_config = sys.argv[1]
split_config = sys.argv[2]
feature = sys.argv[3]
outfile = sys.argv[4]
model_file = sys.argv[5] 

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
import scipy.io as sio

split_config = split_config.split(',')[:-1]

split_config = [int(x) for x in split_config]


network_config = network_config.split(',')[:-1]

network_config = [int(x) for x in network_config]
#print(split_config)

data = sio.loadmat(feature)
data = data['feature'];

num_channels=data.shape[0]
feat_dim=data.shape[1]
#print([num_channels, feat_dim])

def split_EEG(data, split_frames):
	total_frames=data.shape[2]
	split_data=[]
	for i in range(total_frames):
		if i+split_frames<=total_frames:
			split_data.append(data[:,:,i:i+split_frames])
		else:
			split_data.append(data[:,:,-split_frames:])
	return split_data


model = get_multichannel_tdnn_model(feat_dim, 2, num_channels, network_config)
adam_opt = Adam(lr=0.001, clipvalue=1)
model.compile(loss=losses.categorical_crossentropy, optimizer=adam_opt,
              metrics=['accuracy'])
#model.summary()
model.load_weights(model_file,by_name=True)
seizure_probilities=[]
for s in split_config:
	split_data=split_EEG(data,s)
	split_data = np.asarray(split_data)
	split_data = np.swapaxes(split_data,2,3)
	prediction = model.predict(split_data,batch_size = 256, verbose = 0)
	seizure_prob = prediction[:,1]
	seizure_probilities.append(seizure_prob)

seizure_probilities = np.asarray(seizure_probilities)
result_dict={}
result_dict['result'] = seizure_probilities;

sio.savemat(outfile,result_dict)






