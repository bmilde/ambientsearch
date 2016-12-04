#!/bin/bash

cd data/
# English DRUID wiki lookup list
wget http://machinelearning.online/ambient_search/druid_en.bz2

# Experimental German DRUID lookup list
#wget http://machinelearning.online/nlp/druid/denews_mwe_druid_200_1000_scored_sorted_filtered.bz2
#mv denews_mwe_druid_200_1000_scored_sorted_filtered.bz2 druid_de.bz2

# Ambient Search models
wget http://machinelearning.online/ambient_search/simple_enwiki_latest_may2016_models.tar.bz2
tar xvfj simple_enwiki_latest_may2016_models.tar.bz2
rm simple_enwiki_latest_may2016_models.tar.bz2
wget http://machinelearning.online/ambient_search/conversation.tfidf

cd ..
