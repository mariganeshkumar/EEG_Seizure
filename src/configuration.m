
classdef configuration

    properties ( Constant = false )

        %%location of EEG Lab
        eeg_lab_location='../subject_id_revisions/src/eeglab/'

        %% Experiment Name
        exp_name='LFCC_0_60';
        
        %GPU to use
        GPU_Number = 1;
        %% Random seed value.
        seed=0;


        %% Directory in which the continues data are stored; Data needs to be present for the program to run.
        tuh_raw_data_dir='/p1/common/datasets/EEG/tuh_eeg_dataset/tuh_eeg_seizure/v1.5.1/edf/';
        data_dir='data/tuh_v1.5.1/' 
        
        %% channels to load TUH data
        %tuh_channels={'EEG FZ-REF','EEG F7-REF', 'EEG F8-REF', 'EEG C3-REF','EEG C4-REF', 'EEG T5-REF', 'EEG T6-REF', 'EEG O1-REF', 'EEG O2-REF', 'EEG FP1-REF', 'EEG FP2-REF', 'EEG F3-REF', 'EEG F4-REF', 'EEG P3-REF','EEG P4-REF', 'EEG T3-REF', 'EEG T4-REF', 'EEG CZ-REF', 'EEG PZ-REF'};
        %tuh_channels_LE={'EEG FZ-LE','EEG F7-LE', 'EEG F8-LE', 'EEG C3-LE','EEG C4-LE', 'EEG T5-LE', 'EEG T6-LE', 'EEG O1-LE', 'EEG O2-LE', 'EEG FP1-LE', 'EEG FP2-LE', 'EEG F3-LE', 'EEG F4-LE','EEG P3-LE', 'EEG P4-LE', 'EEG T3-LE', 'EEG T4-LE', 'EEG CZ-LE', 'EEG PZ-LE'};
        tuh_channels={'EEG FZ-REF','EEG F7-REF', 'EEG F8-REF', 'EEG C3-REF','EEG C4-REF', 'EEG T5-REF', 'EEG T6-REF', 'EEG O1-REF', 'EEG O2-REF'};
        tuh_channels_LE={'EEG FZ-LE','EEG F7-LE', 'EEG F8-LE', 'EEG C3-LE','EEG C4-LE', 'EEG T5-LE', 'EEG T6-LE', 'EEG O1-LE', 'EEG O2-LE'};
        %% splits used to train the network
        splits = [40, 30, 20]
        
        %% test only. if set to one training part will be skipped.
        test_only = 0;        
        
        %% Directory in which the models will be saved for training and testing will be stored; will be created by the program.
        base_history_dir='model_history_v2/';
        history_save = '';
        
        %% number of channels in EEG
        num_channels = 9;
        
        %% Name of the feature to be used
        feature_name = {...
        'spectral_power',...            %1
        'LFCC',...                      %2
        'multitaper_spectrogram',...    %3
        };
        feature = 2;
        feature_function={@average_power_spectrogram, @LFCC_from_front_end_dsp, @multitaper_spectrum};
        
        
        %% Name of the classifier to be used
        classifier_name={...
        'modified-x-vector_Cosine',...      %1
        };
        classifier = 11;
        
        classifier_function={
            @classify_using_mod_x_vector_cosine,...
            };
        
        
        %% Sampling rate used to record data
        samp_rate =250;
        
        %% window size in ms
        win_size = 300;
        
        
        %% overlap size in ms
        overlap = 150;
        
        %% no of fft points
        nfft = 1024
        
        %% low frequency limit in Hz
        %todo: replace this with bands
        lfreq = 0.3
        
        %% high frequency limit in Hz
        %todo: replace this with bands
        hfreq = 60
        
        %% Dir for saving the features
        features_base_dir='features/';
        features_dir='';
        
        
        %% FFT order (log_{2} of fft size) --> need only for LFCC
        fftorder = 10;
        
        %% Number of filters --> need only for LFCC
        numfilters = 20;
        
        %% Number of Ceps --> need only for LFCC
        numceps = 15;
        
        %% Delta Needed ?--> need only for LFCC
        delta_1 = 0;
        
        %% Delta^2 needed? --> needed only for LFCC
        delta_2 = 0;
        
        %% hidden layer config for ANN
        %%  hiddenlayers = [256 256 256 128 32 32 ];
        hiddenlayers = [256 256 128 256 32 32 ];
        
       
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Parameters that
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% doesn't change
        
        %% Directory to save models
        ubm_model_dir = 'ubm_model';
        dnn_model_files = 'dnn_models';

        %% permenenet temp dir
        per_tmp_dir='tmp/'

        exp_dir = ''

        tmp_dir = '';

    end

    methods 
        function self = configuration(self)
            %% Directory in which the models will be saved for training and testing will be stored; will be created by the program.
            self.history_save=['exp/',self.exp_name,'/',self.base_history_dir];

            %% Dir for saving the features
            self.features_dir=['exp/',self.exp_name,'/',self.features_base_dir];

            self.exp_dir=['exp/',self.exp_name]
            
            %% UpdateTMPDir
            self.tmp_dir=[self.per_tmp_dir,'/',self.exp_name,'/'];
        end

        function self = updateModelLocation(self)
            %% Directory in which the models will be saved for training and testing will be stored; will be created by the program.
            self.history_save=['../model_history/','/',self.exp_name];
            
        end

        function self = updateFeaturesLocation(self, exp_name)
            %% Directory in which the models will be saved for training and testing will be stored; will be created by the program.
            self.features_dir=[self.features_base_dir, exp_name];

            
        end

        function self = updateTmpLocation(self)
             %% UpdateTMPDir
            self.tmp_dir=[self.per_tmp_dir,'/',self.exp_name,'/'];
        end

        function self = updateCustomTmpLocation(self,tmp_name)
             %% UpdateTMPDir
            self.tmp_dir=[self.per_tmp_dir,'/',tmp_name,'/'];
        end
    end
end





