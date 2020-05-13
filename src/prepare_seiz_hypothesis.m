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

	subjects = get_all_sub_dir(features_dir);
	fId = fopen(strcat(model_dir,'/',num2str(thresold),'/hyp.txt'),'w');
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
			for s = 1:length(seizure_starting_ind)
				starting_time = round(seizure_starting_ind(s)*frame_duration,4);
				ending_time  = round(seizure_ending_ind(s)*frame_duration,4);
				score = mean(final_score(seizure_starting_ind(s):seizure_ending_ind(s)));
				hyp_line = strcat(g_filename,{'  '},num2str(starting_time),{' '},...
					num2str(ending_time),{' '},num2str(score));
				fprintf(fId,'%s',string(hyp_line));
				fprintf(fId,'\n');
			end
		end
	end	
	fclose(fId);
	command = strcat('python3 src/library/eval_scripts/nedc_eval_eeg.py',{' '},...
		model_dir,'/ref.txt',{' '},...
		model_dir,'/',num2str(thresold),'/hyp.txt');
	system(string(command))
	command = strcat('mv output',{' '},...
		model_dir,'/',num2str(thresold),'/output');
	system(string(command))
end
