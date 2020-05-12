function [] = make_features(config,subset)
	if ~exist('config','var')
		config = configuration();
	end
	path=genpath('src/library');
	addpath(path);
	addpath(config.eeg_lab_location());
	tuh_channels = config.tuh_channels

	data_dir = config.data_dir
	splits=config.splits;
	feature_dir = strcat(config.features_dir,'/',num2str(config.feature))

	if ~exist(feature_dir, 'dir')
	   mkdir(feature_dir)
	end

	
	subset_dir = strcat(data_dir,'/',subset);
	montages = get_all_sub_dir(subset_dir);
	for m=1:length(montages)
		montage_dir = strcat(subset_dir,'/',montages{m});
		sub_dirs = get_all_sub_dir(montage_dir);
		parfor sd=1:length(sub_dirs)
			sub_dir = strcat(montage_dir,'/',sub_dirs{sd});
			subjects = get_all_sub_dir(sub_dir);
			for subj = 1:length(subjects)
				subj_dir = strcat(sub_dir,'/',subjects{subj});
				sessions = get_all_sub_dir(subj_dir);
				for sess = 1:length(sessions)
					sess_dir=strcat(subj_dir,'/',sessions{sess});
					disp(strcat('Extracting Feature For:',sess_dir))
					recordings = dir([sess_dir,'/*.mat']);
					recordings = {recordings(:).name};
					annotations = dir([sess_dir,'/*.tse_bi']);
					annotations = {annotations(:).name};
					save_dir=strcat(feature_dir,'/',subset,...
						'/',subjects{subj},'/');
					for r = 1:length(recordings)
						EEG_filename = recordings{r};
						saved_data=load(strcat(sess_dir,'/',EEG_filename));
						EEG_data=saved_data.data;
						EEG_srate=saved_data.sampling_rate;

						EEG_g_filename=strsplit(EEG_filename,'.');
						EEG_g_filename=EEG_g_filename{1};
						extract_features(config,EEG_data,EEG_srate,save_dir,EEG_g_filename)
					end
				end
			end
		end
	end
end

function []= SaveFeatures(dir,filename,feature)
	if ~isdir(dir)
	   mkdir(dir)
	end
	save(strcat(dir,'/',filename),'feature')
end

function extract_features(config,EEG_data,EEG_srate,save_dir,EEG_g_filename)
	data=EEG_data;
	data = data - mean(data,2);
	feature = config.feature_function{config.feature}(config,data, EEG_srate);
	SaveFeatures(save_dir,...
		strcat('/',EEG_g_filename,'.mat'),feature);	
end


									