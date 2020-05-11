function [] = make_split_features_for_training(config)
	if ~exist('config','var')
		config = configuration;
	end
	path=genpath('src/library');
	addpath(path);
	config=configuration();
	addpath(config.eeg_lab_location());
	tuh_channels = config.tuh_channels

	data_dir = config.data_dir
	splits=config.splits;
	feature_dir = strcat(config.features_dir,'/',num2str(config.feature))

	if ~exist(feature_dir, 'dir')
	   mkdir(feature_dir)
	end

	
	subset_dir = strcat(data_dir,'/train');
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
					seiz_save_dir=strcat(feature_dir,'/train/seiz/',...
						'/',subjects{subj},'/');
					bckg_save_dir=strcat(feature_dir,'/train/bckg/',...
						'/',subjects{subj},'/');
					for r = 1:length(recordings)
						EEG_filename = recordings{r};
						saved_data=load(strcat(sess_dir,'/',EEG_filename));
						EEG_data=saved_data.data;
						EEG_srate=saved_data.sampling_rate;

						EEG_g_filename=strsplit(EEG_filename,'.');
						EEG_g_filename=EEG_g_filename{1};
						annotations = fopen(strcat(sess_dir,'/',EEG_g_filename,'.tse_bi'),'r');
						splited_annotation={}
						a_ind=1;
						is_only_bckg=1;
						while ~feof(annotations)
							gt_line = fgets(annotations);
							ground_truth=strsplit(gt_line,' ');
							if length(ground_truth) < 4
								continue;
							else
								splited_annotation{a_ind}=ground_truth;
								a_ind=a_ind+1;
								if ground_truth{3}=='seiz'
									is_only_bckg=0
								end
							end
						end	
						for sp = 1:length(splits)
							split=splits(sp)
							if is_only_bckg
								split_only_bckg_data(config,EEG_data,EEG_srate,split,splited_annotation,bckg_save_dir,EEG_g_filename)
							else
								split_seiz_bckg_data(config,EEG_data,EEG_srate,split,splited_annotation,bckg_save_dir,seiz_save_dir,EEG_g_filename)
							end
						end	
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

function split_only_bckg_data(config,EEG_data,EEG_srate,split,splited_annotation,bckg_save_dir,EEG_g_filename)
   for s = 1:length(splited_annotation)
   		increment = split*EEG_srate;
		start_ind=1+increment+ round(str2num(splited_annotation{s}{1}))*EEG_srate;
		end_ind=floor(str2num(splited_annotation{s}{2}))*EEG_srate;

		while start_ind + increment < end_ind
			data=EEG_data(:, start_ind:start_ind+increment);
			feature = config.feature_function{config.feature}(config,data, EEG_srate);
			SaveFeatures(strcat(bckg_save_dir,'/',num2str(split)),...
				strcat('/',EEG_g_filename,'_',...
				num2str(start_ind),'.mat'),feature);
			start_ind=start_ind+(increment*5)+1;	
		end
   end
end

function split_seiz_bckg_data(config,EEG_data,EEG_srate,split,splited_annotation,bckg_save_dir,seiz_save_dir,EEG_g_filename)
   for s = 1:length(splited_annotation)
   		increment = split*EEG_srate;
		start_ind=1 + round(str2num(splited_annotation{s}{1}))*EEG_srate;
		end_ind=floor(str2num(splited_annotation{s}{2}))*EEG_srate;

		while start_ind + increment < end_ind
			data=EEG_data(:, start_ind:start_ind+increment);
			data = data - mean(data,2);
			feature = config.feature_function{config.feature}(config,data, EEG_srate);
			%disp(size(feature))	
			if splited_annotation{s}{3}=='bckg'
				SaveFeatures(strcat(bckg_save_dir,'/',num2str(split)),...
					strcat('/',EEG_g_filename,'_',...
					num2str(start_ind),'.mat'),feature);
				start_ind=start_ind+(increment)+1;
			elseif splited_annotation{s}{3}=='seiz'
				SaveFeatures(strcat(seiz_save_dir,'/',num2str(split)),...
					strcat('/',EEG_g_filename,'_',...
					num2str(start_ind),'.mat'),feature);
				start_ind=start_ind+floor(increment/3)+1;
			end
			
		end
   end
end

									