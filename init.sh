#!/bin/bash
cd ~/storywriter/
git pull
pip3 install -r requirements.txt
if [ ! -d ~/storywriter/hg_models/ ]; then
    gsutil -m cp -r  gs://ks-story-ew4-storage/hg_models/ .
fi

while true
do
	python3 writer.py --model-name plot_summary
	python3 writer.py --model-name default
	python3 writer.py --model-name as
done

