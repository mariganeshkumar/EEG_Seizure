#!/usr/bin/env bash
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6
export LD_LIBRARY_PATH=/usr/local/cuda/lib64/${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export CUDA_VISIBLE_DEVICES="$6"
python3 src/library/tdnn/transcribe_using_multi_channel_tdnn.py $1 $2 $3 $4 $5