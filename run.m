
%%%%%%%%%%%%%%%%%%%%%%%%
%use these lines to configure the experiemnt
stage = 0
config = configuration();
%%%%%%%%%%%%%%%%%%%%%%%%

addpath('src/');

% This stage extracts the nessesary channel data for seizure detection 
if stage <= 0
	make_data(config);
end

% This stage splits the EEG data into multiple fixed length duration for training TDNN achitecture
if stage <= 1
	make_split_features_for_training(config);
end


% This stage trains the TDNN using the splited data.  
if stage <= 2
	train_tdnn_for_seizure_detection(config);
end



