if [ $# != 13 ]; then
	echo "Provide the following parameters"
	echo "Arg1: Window size "
	echo "Arg2: Advance Samples "
	echo "Arg3: number of cepstral Coefficients (13/14/.../29) "
	echo "Arg4: number of filters"
	echo "Arg5: fft size"
	echo "Arg6: fft order"
	echo "Arg7: sampling rate"
	echo "Arg8: filter order"
	echo "Arg9: Min Frequency"
	echo "Arg10: Max Frequency"
	echo "Arg11: FeatExtraction Delta Flag (0/1)"
	echo "Arg12: FeatExtraction DeltaDelta Flag (0/1)"
	echo "Arg13: Rawdata path"
	

exit
fi
v_WS=$1
v_AS=$2
v_numceps=$3
v_numfilters=$4
v_fftsize=$5
v_fftorder=${6}
v_fs=${7}
v_filterorder=${8}
v_fmin=${9}
v_fmax=${10}
v_delta=${11}
v_deltadelta=${12}
v_datapath=${13}

if  [ $v_delta -eq 1 ] && [ $v_deltadelta -eq 1 ]; then
	feature_to_extract_name='frameLinearCepstrum+frameLinearDeltaCepstrum+frameLinearDeltaDeltaCepstrum'

elif [ $v_delta -eq 1 ] && [ $v_deltadelta -eq 0 ]; then
	feature_to_extract_name='frameLinearCepstrum+frameLinearDeltaCepstrum'
elif [ $v_delta -eq 0 ] && [ $v_deltadelta -eq 0 ]; then
	feature_to_extract_name='frameLinearCepstrum'
fi



dumpforfiles=tmp/dumpforfiles_tomari
dumpforubm=dumpforubm


mkdir $dumpforfiles

########################## STEP - 1: Feature Extraction #################################################################
	echo "Feature Extraction start ${run_id}"
	sed -e "s/v_WS/$v_WS/" library/features/templates/fe-ctrl.base > $dumpforfiles/fe-ctrl.base
	sed -i -e "s/v_AS/$v_AS/" $dumpforfiles/fe-ctrl.base
	sed -i -e "s/v_numceps/$v_numceps/" $dumpforfiles/fe-ctrl.base
	sed -i -e "s/v_numfilters/$v_numfilters/" $dumpforfiles/fe-ctrl.base
	sed -i -e "s/v_fftsize/$v_fftsize/" $dumpforfiles/fe-ctrl.base
	sed -i -e "s/v_fftorder/$v_fftorder/" $dumpforfiles/fe-ctrl.base
	sed -i -e "s/v_filterorder/$v_filterorder/" $dumpforfiles/fe-ctrl.base
	sed -i -e "s/v_fs/$v_fs/" $dumpforfiles/fe-ctrl.base
	sed -i -e "s/v_fmin/$v_fmin/" $dumpforfiles/fe-ctrl.base
	sed -i -e "s/v_fmax/$v_fmax/" $dumpforfiles/fe-ctrl.base

	v_config_file=$dumpforfiles/fe-ctrl.base

	ls -v $v_datapath>$dumpforfiles/rawfiles.lst
	#ls -v $train_data_folder>$dumpforfiles/tmp_raw_train.lst
	#ls -v $test_data_folder>$dumpforfiles/tmp_raw_test.lst

	#less $dumpforfiles/tmp_raw_ubm.lst | parallel -v -j20 library/ubm-gmm/bin/ComputeFeatures $v_config_file  {1} $feature_to_extract $dumpforfiles/${ubm_data_folder}_${feature_to_extract}/{1/.}.${feature_to_extract} 0.0 A
	#mkdir $dumpforfiles/train_${feature_to_extract}
	#mkdir $dumpforfiles/test_${feature_to_extract}
	mkdir tmp/features
	echo "less $dumpforfiles/rawfiles.lst | parallel -v -j20 library/ubm-gmm/bin/ComputeFeatures $v_config_file  $v_datapath/{1} $feature_to_extract_name tmp/features/{1/.} 0.0 A" > $dumpforfiles/par_fe.sh

	#echo "less $dumpforfiles/tmp_raw_test.lst | parallel -v -j20 library/ubm-gmm/bin/ComputeFeatures $v_config_file  $test_data_folder/{1} $feature_to_extract_name $dumpforfiles/test_${feature_to_extract}/{1/.}.${feature_to_extract} 0.0 A" >>$dumpforfiles/par_fe.sh
	
	less $dumpforfiles/par_fe.sh | parallel -v

	echo "Feature Extraction end "
