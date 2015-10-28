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
		if(json_event['insert_before'] == '#end#')
		{
			//Insert entry as the least important entry
			$(html).hide().appendTo('#relevantDocs');
		}else{
			//Insert entry and show that it is more imortant than the entry in 'insert_before'
			$(html).hide().insertBefore('#'+json_event['insert_before']);
		}

		// add flickr image
		getFlickrImage(json_event['entry_id'], function(image_found, image_url) {
			if(image_found) {
				addImage(json_event['entry_id'], image_url)				
			}

			$('#'+json_event['entry_id']).fadeIn(fadeInTimeMs);
		});
		
	}
}

function delRelevantEntry(json_event) {
	removeEntry(json_event['entry_id']);
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


/* user called methods */

var starredEntries = [];
function starEntry(entry_id) {
	var index = starredEntries.indexOf(entry_id);
	if(index > -1) { 
		// unstar entry
		starredEntries.splice(index, 1);
		//TODO: $.get(unstar_url);
	} else { 
		// star entry
		starredEntries.push(entry_id);
		//TODO: $.get(star_url);
	}

	$('#' + entry_id + ' button.star-icon span').toggleClass('glyphicon-star-empty').toggleClass('glyphicon-star');
}

function closeEntry(entry_id) {
	//TODO: $.get(close_url)
	removeEntry(entry_id);
}

function resetConversation() {
	starredEntries = [];
	//$.get('/reset'); // TODO: change route to GET & calling '/reset' doesn't send 'handle=reset'
	reset(); // TODO: remove
}



/* utility */

function removeEntry(entry_id) {
	if($('#' + entry_id + ' div.modal').is(':visible') === false) {
		$('#' + entry_id).remove();

		var index = starredEntries.indexOf(entry_id);
		if(index > -1) {
			starredEntries.splice(index, 1);
		}
	}
}

function reset() {
	$('#chat-area').empty();
	$('#relevantDocs').empty();
}

function addImage(entry_id, image_url) {
	$('<img src="' + image_url +'" class="flickr-image" alt="' + entry_id + '" />').insertBefore('#'+entry_id+' div.caption');
}

function getFlickrImage(searchTerm, callback) {
	var flickr_sort = $('#flickrSort').val();
	var flickr_api_key = 'fed915bcf3c85271ac6f9ef1823175bf';
	var flickr_request_url = 'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=' + flickr_api_key + '&text=' + searchTerm + '&sort=' + flickr_sort + '&is_commons=&per_page=1&page=1&format=json&nojsoncallback=1';

	$.getJSON(flickr_request_url, function(data) {
		var image_found = (data['stat'] == "ok" && data['photos']['photo'].length > 0);
		var image_url;
		if(image_found) {
			var photo = data['photos']['photo'][0];
			image_url = "https://farm" + photo['farm'] + ".staticflickr.com/" + photo['server'] + "/" + photo['id'] + "_" + photo['secret'] + "_q.jpg";
		}
	
		callback(image_found, image_url);
	});
}


/* bindings */

$('#flickrSort').change(function() {
	// replace flickr images
	$('#relevantDocs > div').each(function(index, element) {
		var entry_id = $(this).attr('id');
		getFlickrImage(entry_id, function(image_found, image_url) {
			$('#' + entry_id + ' .flickr-image').remove();
			if(image_found) {
				addImage(entry_id, image_url);
			}
		}); 
	});
});
