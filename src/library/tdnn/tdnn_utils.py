import os
import math
import scipy.io as sio
from tqdm import tqdm 
from joblib import Parallel, delayed
from random import shuffle

def load_subjects_data(main_dir,subject,split):
	feat_list=[];
	final_data_dir = main_dir+'/'+subject+'/'+str(split)
	if os.path.exists(final_data_dir):
		data_files = [f.name for f in os.scandir(final_data_dir) if f.is_file()]
		for data_file in data_files:
			data_file_path=final_data_dir+'/'+data_file
			try:
				data = sio.loadmat(data_file_path)
				feat_list.append(data['feature'])
			except:
				print('read_error_occured')
				continue
	return feat_list

def load_training_data(main_dir,split_config):
	print(split_config)
	train_data =[]
	val_data = []
	subjects = [f.name for f in os.scandir(main_dir) if f.is_dir()]
	shuffle(subjects)
	subjects_for_training=math.ceil(len(subjects)*0.9)
	for i in range(len(split_config)):

		print('Loading Training data for split '+str(split_config[i]))
		subject_wise_data = Parallel(n_jobs=15)(delayed(load_subjects_data)(main_dir,subjects[j],split_config[i]) for j in tqdm(range(subjects_for_training)))
		t_data=[]
		for d in subject_wise_data:
			t_data=t_data+d
		shuffle(t_data)
		train_data.append(t_data)
		#print(train_data[i][0].shape)
		print('Loading Val data for split '+str(split_config[i])) #
		subject_wise_data = Parallel(n_jobs=15)(delayed(load_subjects_data)(main_dir,subjects[j],split_config[i]) for j in tqdm(range(subjects_for_training,len(subjects))))
		v_data=[]
		for d in subject_wise_data:
			v_data=v_data+d
		shuffle(v_data)
		val_data.append(v_data)
			
	return train_data,val_data



# def load_training_data(main_dir,split_config):
# 	train_data =[]
# 	val_data = []
# 	subjects = [f.name for f in os.scandir(main_dir) if f.is_dir()]
# 	subjects.sort()
# 	subjects_for_training=math.ceil(len(subjects)*0.9)
# 	for i in range(len(split_config)):
# 		train_data.append([])
# 		val_data.append([])
# 		for j in tqdm(range(len(subjects))):
# 			final_data_dir = main_dir+'/'+subjects[j]+'/'+str(split_config[i])
# 			data_files = [f.name for f in os.scandir(final_data_dir) if f.is_file()]
# 			for dat[j]a_file in data_files:
# 				data_file_path=final_data_dir+'/'+data_file
# 				data = sio.loadmat(data_file_path)
# 				if j <= subjects_for_training:
# 					train_data[i].append(data['feature'])
# 				else:
# 					val_data[i].append(data['feature'])
# 	return train_data,val_data