function [] = transcribe_EEG_using_multi_channel_tdnn(config,subset)
	
	if ~exist('config','var')
		config = configuration;
	end
	path=genpath('src/library');
	addpath(path);
	features_dir = strcat(config.features_dir,'/',num2str(config.feature),'/',subset);
	model_dir = strcat(config.history_save,'/',num2str(config.feature));

	if ~exist(strcat(model_dir,'/keras.model'), 'file')
		disp('trained_model_not_found in ');
		disp(strcat(model_dir,'/keras.model'));
		return;
	end	

	network_config="";
	for i = 1:length(config.hiddenlayers)
		network_config = strcat(network_config,num2str(config.hiddenlayers(i)),',');
	end	

	splits_config="";
	for i = 1:length(config.splits)
		split_in_frames = (config.splits(i) * config.samp_rate)
		split_in_frames = split_in_frames/round((config.win_size-config.overlap)/1000 * config.samp_rate)
		split_in_frames=ceil(split_in_frames)
		splits_config = strcat(splits_config,num2str(split_in_frames),',');
	end

	subjects = get_all_sub_dir(features_dir);
	if ~isempty(gcp('nocreate'))
		delete(gcp('nocreate'))
	end
	parpool(2)	
	for i = 1:length(subjects)
		disp(strcat('Extracting transcription for subject :',...
			num2str(i),'/',num2str(length(subjects))))
		subject_dir = strcat(features_dir,'/',subjects{i});
		subject_save_dir = strcat(model_dir,'/transcription/',subset,'/',subjects{i});
		recordings = dir([subject_dir,'/*.mat']);
		recordings = {recordings(:).name};
		parfor r = 1:length(recordings)
			EEG_filename = recordings{r};
			EEG_g_filename=strsplit(EEG_filename,'.');
			EEG_g_filename=EEG_g_filename{1};
			EEG_g_filename=strsplit(EEG_g_filename,'_');
			EEG_g_filename=strcat(EEG_g_filename{1},'_',EEG_g_filename{2},'_',EEG_g_filename{3});
			if exist(strcat(subject_save_dir,'/',EEG_g_filename,'_tdnn_trans.mat'),'file')
				continue
			elseif ~exist(strcat(subject_save_dir),'dir')
				mkdir(subject_save_dir)
			end 
			disp(EEG_g_filename)
			python3_inference_command=strcat('bash src/library/tdnn/transcribe_using_multi_channel_tdnn.bash',...
				{' '},network_config,{' '},splits_config,{' '},...
				subject_dir,'/',EEG_filename,{' '},...
				subject_save_dir,'/',EEG_g_filename,'_tdnn_trans.mat',....
				{' '},model_dir,'/keras.model',{' '},...
				num2str(mod(r,2)));
			
			[status,cmdout]=system(python3_inference_command);
			if status == 1
				disp('EEG transcription failed');
				disp(python3_inference_command);
			end
		end
	end	

end