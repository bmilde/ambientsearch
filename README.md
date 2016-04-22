# Ambient Search

Ambient search is an open source system for displaying and retrieving relevant documents in real time for speech input. The system works ambiently, that is, it unobstructively listens to speech streams in the background and continuously serves relevant documents from its index. 

The retrieved documents, in the default installation Wikipedia articles from the [Simple English Wikipedia](https://simple.wikipedia.org/wiki/Main_Page), are visualized in real time in a browser interface and as a user you can choose to interact with the system or merely employ it as an enriched conversation protocol.

Ambient search is implemented in Python and uses the Flask Microframework to interact with its browser interface. It builds on [Kaldi](http://kaldi-asr.org/) and [Kaldi Gstreamer Server](https://github.com/alumae/kaldi-gstreamer-server) for the speech recognition, [Redis](http://redis.io/) to interact and pass messages between its modules, [DRUID](http://jobimtext.org/components/druid/) for keyphrase extraction and [Gensim](https://radimrehurek.com/gensim/) for topic modelling. 

# Impressions

Impression of the system after listening to the TED talk ["We’re too late to prevent climate change - here is how we adapt"](https://www.ted.com/talks/alice_bows_larkin_we_re_too_late_to_prevent_climate_change_here_s_how_we_adapt?language=en):

<p align="center">
<img src="https://github.com/bmilde/ambientsearch/raw/master/screenshots/screenshot1.png" width="600px">
</p>

Detail view to read an article:

<p align="center">
<img src="https://github.com/bmilde/ambientsearch/raw/master/screenshots/screenshot2.png" width="600px">
</p>

# Overview

<p align="center">
<img src="https://github.com/bmilde/ambientsearch/raw/master/screenshots/overview.png">
</p>

At ﬁrst, the speech signal is transcribed by an online ASR system (1). The ASR system emits the partial sentence hypothesis and also predicts sentence boundaries. Once a full sentence has been hypothesized, new keywords/keyphrases are extracted in the current sentence, if available (2). These keyphrases are then ranked (3) and merged with the ones from previous sentences. A query is then composed, which is submitted to a precomputed index of documents (4). Eventually, the returned documents are also aggregated (5a), i.e. older documents found with previous sentences decay their score over time and newer documents are sorted into a list of n best documents. This list is thus sorted by topical relevance of the documents and by time, with newer documents having precedence. Finally, the n best relevant documents are presented to the user (5b) and updated as soon as changes become available. Alongside the n best documents,a timeline of previously suggested articles is also maintained and displayed.

# Keyphrase extraction

The system extracts keyphrases from speech input. This mainly uses a precomputed [DRUID](http://maggie.lt.informatik.tu-darmstadt.de/jobimtext/components/druid/) list to find possible candidates. These candidates are then ranked using a combined Word2vec and TF-IDF measure in Ambient Search.

Examples of keyphrase extraction in speech transcriptions using various methods:

Manual transcript:

> But dangerous climate change can be subjective. So if we think about an extreme weather event that might happen in some part of the world, and if that happens in a part of the world where there is good infrastructure, where there are people that are well-insured and so on, then that impact can be disruptive. It can cause upset, it could cause cost. It could even cause some deaths. But if that exact same weather event happens in a part of the world where there is poor infrastructure, or where people are not well-insured, or they're not having good support networks, then that same climate change impact could be devastating. It could cause a significant loss of home, but it could also cause significant amounts of death. So this is a graph of the CO2 emissions at the left-hand side from fossil fuel and industry, and time from before the Industrial Revolution out towards the present day. And what's immediately striking about this is that emissions have been growing exponentially. If we focus in on a shorter period of time from 1950, we have established in 1988 the Intergovernmental Panel on Climate Change, the Rio Earth Summit in 1992, then rolling on a few years, in 2009 we had the Copenhagen Accord, where it established avoiding a two-degree temperature rise in keeping with the science and on the basis of equity. And then in 2012, we had the Rio+20 event. And all the way through, during all of these meetings and many others as well, emissions have continued to rise. And if we focus on our historical emission trend in recent years, and we put that together with our understanding of the direction of travel in our global economy, then we are much more on track for a four-degree centigrade global warming than we are for the two-degree centigrade.

Kaldi transcript from the corresponding audio file:

> but dangerous climate change can be subjective so if we think about extreme weather event that might happen in some part of the world and if that happens in a part of the world where there is good. infrastructure whether people are well insured and so on then time had can be disruptive it can cause upsets it could cause cost it could even cause some deaths but if the exact same weather event happens in a part of the world where there is poor infrastructure or where people are not. well insured over not having good support networks then assign climate change impacts could be devastating it could cause a significant loss of home but it could also cause significant amounts of deaths so this is a graph of the c o two emissions of the left hand side from fossil fuels. an industry and time from before the industrial revolution out towards the present child and was immediately striking about best is the emissions have been growing exponentially. if we focus in on a shorter period of time from nineteen fifty we have established in nineteen eighty eight the intergovernmental panel on climate change. the rio earth summit in ninety ninety two than rolling on a few years in two thousand and nine we had the copenhagen accord were established avoiding a two degree temperature rise in keeping with the science and on the basis of equity and then in twenty twelve we had the rio plus twenty. event and all the way through during all of these meetings and many others as well and missions have continued to rise. and if we focus on our historical and mission trend in recent years and we put that together with our understanding of the direction of travel in our global economy then we're much more on track for a full degree centigrade global warming family are for the two degree centigrade

Keyphrase extraction using TF-IDF, using a TF-IDF model of all entries of the DRUID dictionary, trained on Wikipedia:

*centigrade | climate | emission | infrastructure | rio | significant | o | mission | event | equity | fossil fuel | industrial revolution*

Using the method from Habibi and Popescu-Belis ["Keyword extraction and clustering for document recommendation in conversations"](http://infoscience.epfl.ch/record/203854/files/Habibi_IEEEACMTASLP_2014.pdf):

*warming | impacts | global | infrastructure | insured | climate | subjective | understanding | emissions | economy | disruptive | cost | immediately | trend*

Ambient Search:

*emission | climate | infrastructure | significant | centigrade | global warming | event | fossil fuel | trend | mission | disruptive | graph*

In the above, we have allowed each method to propose its 14 best ranking words (keywords), counting proposed multi-word terms (key phrases) as multiple words. You can find many more examples of how the methods choose their keywords and keyphrases in the python/data folder.

# Installation and running instructions

Prerequisites: you need to index some documents using elastic search. We recommend to index the Simple English Wikipedia with [stream2es](https://github.com/elastic/stream2es). Precompiled models are available for the Simple English Wikipedia, see [this download script.](https://github.com/bmilde/ambientsearch/blob/master/python/download_models_en.sh)

Clone this project and check out the detailed installation and running instructions in the [INSTALL](https://github.com/bmilde/ambientsearch/blob/master/INSTALL) file.

# Training your own models

If you want to train your own models, see our [training script](https://github.com/bmilde/ambientsearch/blob/master/python/build_models_en.sh). You can of course also change the input corpus from the simple Wikipedia to the full Wikipedia, but it will take considerably longer to train your models. Instructions to train your own DRUID lookup table can be found on the [JoBimText / DRUID website](http://jobimtext.org/components/druid/).
