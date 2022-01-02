cd storywriter/
gsutil -m cp -r  gs://ks-story-ew4-storage/hg_models/ .
python3 writer.py --model-name plot_summary
