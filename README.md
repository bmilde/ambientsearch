# Ambient Search

Ambient search is an open source system released under the Apache license for displaying and retrieving relevant documents in real time for speech input. The system works ambiently, that is, it unobstructively listens to speech streams in the background and continuously serves relevant documents from its index. 

The retrieved documents, in the default installation Wikipedia articles from the [Simple English Wikipedia](https://simple.wikipedia.org/wiki/Main_Page), are visualized in real time in a browser interface and as a user you can choose to interact with the system or merely employ it as an enriched conversation protocol.

Ambient search is implemented in Python and uses the Flask Microframework to interact with its browser interface. It builds on [Kaldi](http://kaldi-asr.org/) and [Kaldi Gstreamer Server](https://github.com/alumae/kaldi-gstreamer-server) for the speech recognition, [Redis](http://redis.io/) to interact and pass messages between its modules and [Gensim](https://radimrehurek.com/gensim/) for topic modelling. 

# Impressions

Impression of the system after listening to the TED talk ["We’re too late to prevent climate change - here is how we adapt"](https://www.ted.com/talks/alice_bows_larkin_we_re_too_late_to_prevent_climate_change_here_s_how_we_adapt?language=en):

<p align="center">
<img src="https://github.com/bmilde/ambientsearch/raw/master/screenshots/screenshot1.png" width="600px" align="center">
</p>

Detail view to read an article:

<p align="center">
<img src="https://github.com/bmilde/ambientsearch/raw/master/screenshots/screenshot2.png" width="600px" align="center">
</p>

# Overview
![overview](https://github.com/bmilde/ambientsearch/raw/master/screenshots/overview.png)

At ﬁrst, the speech signal is transcribed by an online ASR system (1). The ASR system emits the partial sentence hypothesis and also predicts sentence boundaries. Once a full sentence has been hypothesized, new keywords/keyphrases are extracted in the current sentence, if available (2). These keyphrases are then ranked (3) and merged with the ones from previous sentences. A query is then composed, which is submitted to a precomputed index of documents (4). Eventually, the returned documents are also aggregated (5a), i.e. older documents found with previous sentences decay their score over time and newer documents are sorted into a list of n best documents. This list is thus sorted by topical relevance of the documents and by time, with newer documents having precedence. Finally, the n best relevant documents are presented to the user (5b) and updated as soon as changes become available. Alongside the n best documents,a timeline of previously suggested articles is also maintained and displayed.

# Keyphrase extraction

The system extracts keyphrases from speech input. This mainly uses a precomuted DRUID list, to find possible candidates. These candidates are then ranked using word2vec and TF-IDF

Some exmamples of the keyphrase extraction:

TODO

# Installation instructions

Prerequisits: you need to index some documents using elastic search. We recommend to index the Simple English Wikipedia with [https://github.com/elastic/stream2es](stream2es)

Detailed installation instructions coming  very soon
