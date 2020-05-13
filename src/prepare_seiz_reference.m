function [] = prepare_seiz_reference(config,subset)
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
	model_dir = strcat(config.history_save,'/',num2str(config.feature));

	if ~exist(feature_dir, 'dir')
	   mkdir(feature_dir)
	end

	all_annotations={};
	annotat_ind=1;
	subset_dir = strcat(data_dir,'/',subset);
	montages = get_all_sub_dir(subset_dir);
	for m=1:length(montages)
		montage_dir = strcat(subset_dir,'/',montages{m});
		sub_dirs = get_all_sub_dir(montage_dir);
		for sd=1:length(sub_dirs)
			sub_dir = strcat(montage_dir,'/',sub_dirs{sd});
			subjects = get_all_sub_dir(sub_dir);
			for subj = 1:length(subjects)
				subj_dir = strcat(sub_dir,'/',subjects{subj});
				sessions = get_all_sub_dir(subj_dir);
				for sess = 1:length(sessions)
					sess_dir=strcat(subj_dir,'/',sessions{sess});
					disp(strcat('Extracting annotations For:',sess_dir))
					annotations = dir([sess_dir,'/*.tse_bi']);
					annotations = {annotations(:).name};
					for r = 1:length(annotations)
						filename = annotations{r};
						g_filename=strsplit(filename,'.');
						g_filename=g_filename{1};
						annotations_fp = fopen(strcat(sess_dir,'/',g_filename,'.tse_bi'),'r');
						splited_annotation={};
						while ~feof(annotations_fp)
							gt_line = fgets(annotations_fp);
							ground_truth=strsplit(gt_line,' ');
							if length(ground_truth) < 4
								continue;
							else
								all_annotations{annotat_ind}=ground_truth;
								all_annotations{annotat_ind}{5}=g_filename;
								annotat_ind=annotat_ind+1;
							end
						end	
					end
				end
			end
		end
	end
	fId = fopen(strcat(model_dir,'/ref.txt'),'w');
	for i = 1:length(all_annotations)
		ref_line = strcat(all_annotations{i}{5},{'  '},...
			all_annotations{i}{1},{' '},...
			all_annotations{i}{2},{' '},...
			all_annotations{i}{3},{' '},...
			all_annotations{i}{4});
		disp(string(ref_line))
		fprintf(fId,'%s',string(ref_line));
		fprintf(fId,'\n');
	end	
end

function []= SaveFeatures(dir,filename,feature)
	if ~isdir(dir)
	   mkdir(dir)
	end
	save(strcat(dir,'/',filename),'feature')
end

