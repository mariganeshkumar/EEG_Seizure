#!/usr/bin/env bash
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6
echo LD_PRELOAD
export LD_LIBRARY_PATH=/usr/local/cuda/lib64/
echo LD_LIBRARY_PATH
export CUDA_VISIBLE_DEVICES="$5"
python3 src/library/tdnn/train_multi_channel_tdnn.py $1 $2 $3 $4