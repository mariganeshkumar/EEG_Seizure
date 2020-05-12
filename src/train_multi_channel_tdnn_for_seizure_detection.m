function [] = train_multi_channel_tdnn_for_seizure_detection(config)
	if ~exist('config','var')
		config = configuration;
	end
	path=genpath('src/library');
	addpath(path);
	features_dir = strcat(config.features_dir,'/',num2str(config.feature),'/train');
	model_dir = strcat(config.history_save,'/',num2str(config.feature));
	network_config="";
	for i = 1:length(config.hiddenlayers)
		network_config = strcat(network_config,num2str(config.hiddenlayers(i)),',');
	end	

	splits_config="";
	for i = 1:length(config.splits)
		splits_config = strcat(splits_config,num2str(config.splits(i)),',');
	end	
	python3_training_command=strcat('bash src/library/tdnn/train_multi_channel_tdnn.bash',...
		{' '},network_config,{' '},splits_config,{' '},features_dir,{' '},model_dir,{' '},num2str(config.GPU_Number));
	disp(python3_training_command);
	system(python3_training_command);

end