#!/bin/bash
cd ~/storywriter/
git pull
if [ ! -d ~/storywriter/ ]; then
    gsutil -m cp -r  gs://ks-story-ew4-storage/hg_models/ .
fi

python3 writer.py --model-name plot_summary
