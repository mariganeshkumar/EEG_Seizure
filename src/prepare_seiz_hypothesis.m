function [] = prepare_seiz_hypothesis(config,subset,thresold)
	if ~exist('config','var')
		config = configuration;
	end
	path=genpath('src/library');
	addpath(path);
	features_dir = strcat(config.features_dir,'/',num2str(config.feature),'/',subset);
	model_dir = strcat(config.history_save,'/',num2str(config.feature));

	if ~exist(strcat(model_dir,'/',num2str(thresold)), 'dir')
		mkdir(strcat(model_dir,'/',num2str(thresold)))
	end	

	frame_duration=(config.win_size-config.overlap)/1000;

	channel_config = config.tuh_channels;
	channel_str=num2str(length(channel_config))
	for channel = 1:length(channel_config)
		channel_str=strcat(channel_str,{' '},channel_config{channel});
	end

	subjects = get_all_sub_dir(features_dir);
	fId = fopen(strcat(model_dir,'/',num2str(thresold),'/',subset,'_hyp.txt'),'w');
	for i = 1:length(subjects)
		disp(strcat('Predicting Sizure for subject :',...
			num2str(i),'/',num2str(length(subjects))))
		subject_dir = strcat(features_dir,'/',subjects{i});
		transcription = dir([subject_dir,'/*_tdnn_trans.mat']);
		transcription = {transcription(:).name};
		for r = 1:length(transcription)
			filename = transcription{r};
			g_filename=strsplit(filename,'.');
			g_filename=g_filename{1};
			g_filename=strsplit(g_filename,'_');
			g_filename=strcat(g_filename{1},'_',g_filename{2},'_',g_filename{3});
			trans = load(strcat(subject_dir,'/',filename));
			trans = trans.result;
			final_score = mean(trans,1);
			seizure_frames = final_score > thresold;
			if sum(seizure_frames) == 0
				continue;
			elseif sum(seizure_frames) == length(seizure_frames)
				hyp_line = strcat(g_filename,{'  '});
				hyp_line = strcat(hyp_line,'0.0',{' '});
				EEG_duration = (length(seizure_frames) - 1)*frame_duration; 
				EEG_duration = round(EEG_duration, 4);
				hyp_line = strcat(hyp_line,num2str(EEG_duration),{' '});
				hyp_line = strcat(hyp_line,num2str(mean(final_score)));
				fprintf(fId,'%s',string(hyp_line));
				fprintf(fId,'\n');
				continue;
			end	
			seizure_starting_ind = strfind(seizure_frames, [0 1]);
			seizure_ending_ind = strfind(seizure_frames, [1 0]);
			if length(seizure_starting_ind) > length(seizure_ending_ind) && seizure_frames(end)==1
				seizure_starting_ind=seizure_starting_ind(1:end-1);
			elseif length(seizure_starting_ind) < length(seizure_ending_ind) && seizure_frames(1)==1
				seizure_ending_ind = seizure_ending_ind(2:end);
			elseif seizure_starting_ind(1) > seizure_ending_ind(1)
				seizure_ending_ind = seizure_ending_ind(2:end);
				seizure_starting_ind=seizure_starting_ind(1:end-1);
			end
			if length(seizure_starting_ind) ~= length(seizure_ending_ind)
				disp('Some condition missed in getting hypothesis');
				disp(length(seizure_starting_ind))
				disp(length(seizure_ending_ind))
				continue
			end	
			s = 1;
			while s <= length(seizure_starting_ind)
				starting_ind = seizure_starting_ind(s);
				ending_ind = seizure_ending_ind(s);

				starting_time = round(starting_ind*frame_duration,4);
				ending_time  = round(ending_ind*frame_duration,4);

				hypothesis_length = ending_time - starting_time;
				if hypothesis_length < 40
					s=s+1;
					continue;
				end

				if s < length(seizure_starting_ind)
					next_starting_time =  round(seizure_starting_ind(s+1)*frame_duration,4);
					next_ending_time =  round(seizure_ending_ind(s+1)*frame_duration,4);
					while next_starting_time - ending_time < 80 && s < length(seizure_starting_ind)
						disp('Applying New Rule')
						ending_ind = seizure_ending_ind(s+1);
						ending_time  = round(ending_ind*frame_duration,4);
						s=s+1;
						if s < length(seizure_starting_ind)
							next_starting_time =  round(seizure_starting_ind(s+1)*frame_duration,4);
							next_ending_time =  round(seizure_ending_ind(s+1)*frame_duration,4);
						end
					end
				end

				

				score = mean(final_score(starting_ind:ending_ind));
				hyp_line = strcat(g_filename,{'  '},num2str(starting_time),{' '},...
					num2str(ending_time),{' '},num2str(score));
				if strcmp(subset,'eval')~=0
					hyp_line=strcat(hyp_line,{' '},channel_str);
				end
				fprintf(fId,'%s',string(hyp_line));
				fprintf(fId,'\n');
				s=s+1;
			end
		end
	end	
	fclose(fId);
	if strcmp(subset,'eval')==0
		command = strcat('python3 src/library/eval_scripts/nedc_eval_eeg.py',{' '},...
			'-odir',{' '},model_dir,'/',num2str(thresold),'/output',{' '},...
			model_dir,'/ref.txt',{' '},...
			model_dir,'/',num2str(thresold),'/',subset,'_hyp.txt');
		system(string(command))
	end
end
