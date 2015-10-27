/*
ambientsearch.js - Receive and display events from an event stream.

Author: Benjamin Milde
*/


/*Events: relevant documents*/

/*This generates a template function for the template in index.html with the id relevantDocs_tmpl*/
wikiEntryTemplate = doT.template(document.getElementById('relevantDocs_tmpl').text);
fadeInTimeMs = 800

function addRelevantEntry(json_event) {
	if (json_event['type'] == 'wiki')
	{
		/*Get html for a wikiEntry with the dot.js template function (See also relevantDocs_tmpl in index.html)*/
		html = wikiEntryTemplate(json_event);
		//console.log(html);
		if(json_event['insert_before'] == '#end#')
		{
			//Insert entry as the least important entry
			$(html).hide().appendTo('#relevantDocs');
		}else{
			//Insert entry and show that it is more imortant than the entry in 'insert_before'
			$(html).hide().insertBefore('#'+json_event['insert_before']);
		}

		// request image from flickr
		var flickr_request_url = "https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=fed915bcf3c85271ac6f9ef1823175bf&text=" + json_event['entry_id'] + "&sort=relevance&per_page=1&page=1&format=json&nojsoncallback=1";
		$.getJSON(flickr_request_url, function(data) {
			//console.log(data);

			if(data['stat'] == "ok" && data['photos']['photo'].length > 0) {
				var photo = data['photos']['photo'][0];
				var image_url = "https://farm" + photo['farm'] + ".staticflickr.com/" + photo['server'] + "/" + photo['id'] + "_" + photo['secret'] + "_q.jpg";

				$('<img src="' + image_url +'" alt="' + json_event['entry_id'] + '" />').insertBefore('#'+json_event['entry_id']+' div.caption');
				//console.log(json_event['entry_id'] + " " + image_url);
			} else {
				//console.log(json_event['entry_id'] + " no image found");
			}
		});

		$('#'+json_event['entry_id']).fadeIn(fadeInTimeMs);
	}
}

function delRelevantEntry(json_event) {
	$('#'+json_event['entry_id']).remove();
}

/*Events: speech recognition feedback*/
function renderUtterance(json_event) {
	return '<span>'+json_event.speaker+':</span> '+json_event.utterance
}

function addUtterance(json_event) {
	$('#chat-area').append('<p>'+renderUtterance(json_event)+' _</p>')
	document.getElementById('chat-area').scrollTop = document.getElementById('chat-area').scrollHeight;
}

function replaceLastUtterance(json_event) {
	$('#chat-area p:last').html(renderUtterance(json_event))
	document.getElementById('chat-area').scrollTop = document.getElementById('chat-area').scrollHeight;
}

function reset() {
	$('#chat-area').empty();
	$('#relevantDocs').empty();
}

/*Dispatch events from EventSource*/

var source = new EventSource('/stream');
var utts = [];

/*
Currently, we have following events: addUtterance, replaceLastUtterance, addRelevantEntry, delRelevantEntry and reset.

addUtterance and replaceLastUtterance are used to stream and display speech hypothesis to the user in real time.
The old hypothesis are replaced with new ones until a new utterance (sentence) is added.

E.g.
{"handle": "addUtterance", "utterance": "just like.", "speaker": "You"}
{"handle": "replaceLastUtterance", "utterance": "just like you.", "old_utterance": "just like.", "speaker": "You"}

addRelevantEntry and delRelevantEntry add or delete relevant entries to the display. Currently, there is only one type, "wiki". Since there is a ranking between displayed entries, "insert_before" indicates the id of the relevant entry that should be after this new element. The special marker "#end#" is used to indicate that element should be added as the last relevant in the current list.

E.g.
{"handle": "delRelevantEntry", "type": "wiki", "entry_id": "EXPOSE",  "title": "EXPOSE"}
{"handle": "addRelevantEntry", "type": "wiki", "insert_before": "Just_Show_Me_How_to_Love_You", "score": 0.5138, "title": "Just Like", "url": "https://en.wikipedia.org/w/index.php?title=Just_Like", "entry_id": "Just_Like", "text": "\\"Just Like\\" is a song recorded by Marvin Gaye in 1978 but wasn\'t released until after the release of Gaye\'s posthumous 1985 album, Romantically Yours."}

Lastely, the "reset" handle is used to indicate that all text in the speech recognition and all relevant entries should be deleted, i.e. the website should reset itself to its initial state.

E.g.
{"handle": "reset"}

*/

source.onmessage = function (event) {
	json_event = JSON.parse(event.data);
	if (json_event.handle == 'addUtterance')
	{
		utts.push(json_event.utterance);
		addUtterance(json_event);
	}
	else if (json_event.handle == 'replaceLastUtterance')
	{
		utts.pop();
		utts.push(json_event.utterance);
		replaceLastUtterance(json_event);
	}else if (json_event.handle == 'addRelevantEntry')
	{
		addRelevantEntry(json_event);
	}else if (json_event.handle == 'delRelevantEntry')
	{
		delRelevantEntry(json_event);
	}else if (json_event.handle == 'reset')
	{
		reset();
	}
};
