addpath('src/');

%%%%%%%%%%%%%%%%%%%%%%%%
%use these lines to configure the experiemnt
stage = 0;
config = configuration();
%%%%%%%%%%%%%%%%%%%%%%%%



% This stage extracts the nessesary channel data for seizure detection 
if stage <= 0
	if ~exist(config.exp_dir,'dir')
		mkdir(config.exp_dir);
		diary(strcat(config.exp_dir,'/config.txt'))
		disp(config)
		diary off;	
	end
	if ~exist(string(config.data_dir),'dir')
		make_data(config);
	end
	
end

% This stage splits the EEG data into multiple fixed length duration for training TDNN achitecture
if stage <= 1
	make_split_features_for_training(config);
end


% This stage trains the TDNN using the splited data.  
if stage <= 2
	train_multi_channel_tdnn_for_seizure_detection(config);
end

% This stage features are extracted for dev  
if stage <= 3
	make_features(config,'dev');
end

% This stage transcribes the EEG data at frame level using TDNN
if stage <= 4
	transcribe_EEG_using_multi_channel_tdnn(config,'dev');
end

% This script crawls TUH EEG dataset to get the seizure ground truth
if stage <= 5
	prepare_seiz_reference(config,'dev');
end

% This script post process the TDNN output to get get the final hypothesis for seizure
if stage <= 6
	prepare_seiz_hypothesis(config,'dev',0.6);
	prepare_seiz_hypothesis(config,'dev',0.7);
	prepare_seiz_hypothesis(config,'dev',0.8);
	prepare_seiz_hypothesis(config,'dev',0.9);
	prepare_seiz_hypothesis(config,'dev',0.95);
end

return

% In this stage features are extracted for eval data and transcribed
if stage <= 7
	make_features(config,'eval');
	transcribe_EEG_using_multi_channel_tdnn(config,'eval');
	prepare_seiz_hypothesis(config,'eval',0.6);
	prepare_seiz_hypothesis(config,'eval',0.7);
	prepare_seiz_hypothesis(config,'eval',0.8);
	prepare_seiz_hypothesis(config,'eval',0.9);
	prepare_seiz_hypothesis(config,'eval',0.95);
end