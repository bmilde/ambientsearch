# Ambient Search

Ambient search is an open source system released under the Apache license for displaying and retrieving relevant documents in real time for speech input. The system works ambiently, that is, it unobstructively listens to speech streams in the background and continuously serves relevant documents from its index. 

The retrieved documents, in the default installation Wikipedia articles from the [Simple English Wikipedia](https://simple.wikipedia.org/wiki/Main_Page), are visualized in real time in a browser interface and as a user you can choose to interact with the system or merely employ it as an enriched conversation protocol.

Ambient search is implemented in Python and uses the Flask Microframework to interact with its browser interface. It builds on [Kaldi](http://kaldi-asr.org/) and [Kaldi Gstreamer Server](https://github.com/alumae/kaldi-gstreamer-server) for the speech recognition, [Redis](http://redis.io/) to interact and pass messages between its modules and [Gensim](https://radimrehurek.com/gensim/) for topic modelling. 

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

The system extracts keyphrases from speech input. This mainly uses a precomputed [http://maggie.lt.informatik.tu-darmstadt.de/jobimtext/components/druid/](DRUID) list to find possible candidates. These candidates are then ranked using Word2vec and TF-IDF.

Some examples of the keyphrase extraction:

Original:

> Over our lifetimes, we've all contributed to climate change. Actions, choices and behaviors will have led to an increase in greenhouse gas emissions. And I think that that's quite a powerful thought. But it does have the potential to make us feel guilty when we think about decisions we might have made around where to travel to, how often and how, about the energy that we choose to use in our homes or in our workplaces, or quite simply the lifestyles that we lead and enjoy. But we can also turn that thought on its head, and think that if we've had such a profound but a negative impact on our climate already, then we have an opportunity to influence the amount of future climate change that we will need to adapt to. So we have a choice. We can either choose to start to take climate change seriously, and significantly cut and mitigate our greenhouse gas emissions, and then we will have to adapt to less of the climate change impacts in future. Alternatively, we can continue to really ignore the climate change problem. But if we do that, we are also choosing to adapt to very much more powerful climate impacts in future. And not only that. As people who live in countries with high per capita emissions, we're making that choice on behalf of others as well. But the choice that we don't have is a no climate change future.

Kaldi transcript from audio file:

> 

TF-IDF trained on all entries of the DRUID dictionary:

climate
future
emission
impact
greenhouse gas emissions
negative impacts
kurd

Using the method from Habibi and Popescu-Belis: ["Keyword extraction and clustering for document recommendation in conversations"](http://infoscience.epfl.ch/record/203854/files/Habibi_IEEEACMTASLP_2014.pdf)

greenhouse
impacts
emissions
workplaces
gas
behaviors
mitigate
energy
climate
potential



In the above, we have allowed an equal number of words per method, counting multi-word terms as multiple words.

# Installation and running instructions

Prerequisites: you need to index some documents using elastic search. We recommend to index the Simple English Wikipedia with [https://github.com/elastic/stream2es](stream2es). Precompiled models are available for the Simple English Wikipedia, see [https://github.com/bmilde/ambientsearch/blob/master/python/data/download_druid.sh](this download script.)

Clone this project and check out the detailed installation and running instructions in the INSTALL file.

# Training your own models

Coming very soon
