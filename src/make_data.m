function [] = make_data()
	path=genpath('library');
	addpath(path);
	eeglab_toolbox = dir([matlabroot,'/toolbox/eeglab*']); %remove all other eeglab toolboxes
	for g = 1:length(eeglab_toolbox)
	    rmpath([matlabroot,'/toolbox/',eeglab_toolbox(g).name]);
	end
	config=configuration();
	addpath(config.eeg_lab_location());
	tuh_channels = config.tuh_channels

	raw_data_dir = config.tuh_raw_data_dir;

	save_dir = config.data_dir

	if ~exist(save_dir, 'dir')
       mkdir(save_dir)
    end

	subsets = get_all_sub_dir(raw_data_dir);
	eeglab;
	for s=1:length(subsets)
		subset_dir = strcat(raw_data_dir,'/',subsets{s});
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
						recordings = dir([sess_dir,'/*.edf']);
        				recordings = {recordings(:).name};
        				annotations = dir([sess_dir,'/*.tse_bi']);
        				annotations = {annotations(:).name};
        				session_save_dir=strcat(save_dir,'/',subsets{s},'/',montages{m},'/',...
        					sub_dirs{sd},'/',subjects{subj},'/',sessions{sess});
    					if ~isdir(session_save_dir)
    					   disp('creating dir')
    				       mkdir(session_save_dir)
    				    end
        				for r = 1:length(recordings)
        					EEG_filename = recordings{r};
        					try
        					    EEG = pop_biosig(strcat(sess_dir,'/',EEG_filename), 'importevent', 'off');
        					catch
        					    fId = fopen(strcat(save_dir,'/Error_files'),'a');
        					    fprintf(fId,['Read Failed: ',EEG_filename,'\n']);
        					    fclose(fId);
        					    continue;
        					end

        					try
	        					EEG = eeg_checkset( EEG );
	        					EEG = pop_reref( EEG, []);
	        					EEG = pop_eegfiltnew(EEG, 0.5,60,1690,0,[],0);
	        					EEG = pop_eegfiltnew(EEG, [],0.5,1690,1,[],0);
	        					EEG = pop_eegfiltnew(EEG, [],60,58,0,[],0);
	        					EEG = pop_eegfiltnew(EEG, 59.5,60.5,1690,1,[],0);
	        					EEG = pop_eegfiltnew(EEG, 49.5,50.5,1690,1,[],0);  

	        					samp_rate = EEG.srate;
	        					if samp_rate ~= 250
	        					    EEG = pop_resample( EEG, 250);
	        					end
	        					sampling_rate=250;

	        					chanlocs = {EEG.chanlocs.labels};

	        					ind=1;
	        					data=[];
	        					c_id=[];
	        					for c = 1:length(tuh_channels)
	        					        c_id(ind) = find(strcmp(chanlocs,tuh_channels{c}));
	        					        data(ind,:)=EEG.data(c_id(ind),:);
	        					        ind=ind+1;
	        					end



	        					save_file(session_save_dir,EEG_filename,data,sampling_rate)
	        					disp(['cp ',sess_dir,'/',annotations{r},' ',session_save_dir,'/',annotations{r}])
	        					system(['cp ',sess_dir,'/',annotations{r},' ',session_save_dir,'/',annotations{r}])

        					catch
        					    fId = fopen(strcat(save_dir,'/Error_files'),'a');
        					    fprintf(fId,['processing failed: ',EEG_filename,'\n']);
        					    fclose(fId);
        					    continue;
        					end
        				end
					end
				end
			end
		end
	end
end

function [] = save_file(location,filename,data,sampling_rate)
	save(strcat(location,'/',filename,'.mat'),'data','sampling_rate')
end