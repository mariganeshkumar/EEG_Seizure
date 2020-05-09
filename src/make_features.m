function [] = make_features()
	path=genpath('library');
	addpath(path);
	config=configuration();
	addpath(config.eeg_lab_location());
	tuh_channels = config.tuh_channels

	data_dir = config.data_dir
	split=config.split;
	feature_dir = strcat(config.features_dir,'/',num2str(split),'/',num2str(config.feature))

	if ~exist(feature_dir, 'dir')
       mkdir(feature_dir)
    end

    

	subsets = get_all_sub_dir(data_dir);
	for s=1:length(subsets)
		subset_dir = strcat(data_dir,'/',subsets{s});
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
        				seiz_save_dir=strcat(feature_dir,'/',subsets{s},'/seiz/',montages{m},'/',...
 						'/',subjects{subj},'/',sessions{sess});
 						bckg_save_dir=strcat(feature_dir,'/',subsets{s},'/bckg/', montages{m},'/',...
 						'/',subjects{subj},'/',sessions{sess});
        				for r = 1:length(recordings)
        					EEG_filename = recordings{r};
        					saved_data=load(strcat(sess_dir,'/',EEG_filename));
        					EEG_data=saved_data.data;
        					EEG_srate=saved_data.sampling_rate;

        					EEG_g_filename=strsplit(EEG_filename,'.');
        					EEG_g_filename=EEG_g_filename{1};

        					annotations = fopen(strcat(sess_dir,'/',EEG_g_filename,'.tse_bi'),'r'); 

        					while ~feof(annotations)
        						gt_line = fgets(annotations);
        						ground_truth=strsplit(gt_line,' ');
        						if length(ground_truth) < 4
        							continue;
        						else
        							start_ind=1+round(str2num(ground_truth{1}))*EEG_srate;
        							end_ind=floor(str2num(ground_truth{2}))*EEG_srate;
        							increment = split*EEG_srate;
        							while start_ind + increment < end_ind
        								data=EEG_data(:, start_ind:start_ind+increment);
        								feature = config.feature_function{config.feature}(config,data, EEG_srate);
        								%disp(size(feature))	
	        							if ground_truth{3}=='bckg'
	        								SaveFeatures(bckg_save_dir,strcat('/',EEG_g_filename,'_',...
	        							    	num2str(start_ind),'.mat'),feature);
	        							elseif ground_truth{3}=='seiz'
	        								SaveFeatures(seiz_save_dir,strcat('/',EEG_g_filename,'_',...
	        							    	num2str(start_ind),'.mat'),feature);
	        							end
	        							start_ind=start_ind+increment+1
	        						end
        						end
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
