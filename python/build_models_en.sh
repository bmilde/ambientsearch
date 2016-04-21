#!/bin/bash

cd data/
if [ ! -f druid_en.bz ]
then
    # download English DRUID wiki lookup list
    wget http://machinelearning.online/nlp/druid/enwiki_mwe_druid_200_1000_sorted_length.bz2
    mv enwiki_mwe_druid_200_1000_sorted_length.bz2 druid_en.bz2
fi
cd ..

# Build conversational model

mkdir data/ami_raw
cd data/ami_raw

if [ ! -f ami_public_manual_1.6.1.zip ]
then
        echo "Downloading ami transcriptions..." 
        wget http://groups.inf.ed.ac.uk/ami/AMICorpusAnnotations/ami_public_manual_1.6.1.zip
        unzip ami_public_manual_1.6.1.zip
fi

cd ../../
mkdir data/ami_transcripts/

python training/ami2text.py
python training/build_tfidf_conversation_model.py

# Build models for the simple Wikipedia

cd data/
if [ ! -f simplewiki-latest-pages-articles.xml.bz2 ]
then
        echo "Downloading simple Wikipedia"
        wget https://dumps.wikimedia.org/simplewiki/latest/simplewiki-latest-pages-articles.xml.bz2
        tar xvfj simplewiki-latest-pages-articles.xml.bz2
fi
cd ..

python training/build_tfidf_wiki_model.py
python training/build_word2vec_model.py
