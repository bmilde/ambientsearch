/*
ambientsearch.js - Receive and display events from an event stream.

Author: Benjamin Milde
*/


/*Events: relevant documents*/

/*This generates a template function for the template in index.html with the id relevantDocs_tmpl*/
var wikiEntryTemplate = doT.template(document.getElementById('relevant-entry-template').text);
var fadeInTimeMs = 800;
var xlBreakPoint = 1800;
var imageSize = 's';
var timelineInverted = false;
var scrollBottom = true;

function addRelevantEntry(json_event) {
	console.log('addRelevantEntry ' + json_event['entry_id']);

	if(json_event['type'] == 'wiki')
	{
		// create new element from template
		var element = $(wikiEntryTemplate(json_event));

		// insert element at designated location
		if(json_event['insert_before'] == '_end_')
			element.hide().appendTo('#relevant-entries');
		else
			element.hide().insertBefore('#relevant-entries .re-'+json_event['insert_before']);

		// add flickr image
		getFlickrImage(json_event['entry_id'], imageSize, function(image_url) {
			if(image_url)
				element.children('.relevant-entry').prepend('<img src="' + image_url +'" class="flickr-image" alt="' + json_event['entry_id'] + '" />');

			element.fadeIn({
				duration: fadeInTimeMs,
				progress: function() {
					if(scrollBottom) 
						window.scrollTo(0,document.body.scrollHeight);
				}
			});
		});
	}
}

function delRelevantEntry(json_event) {
	console.log('delRelevantEntry ' + json_event['entry_id']);
	
	var element = $('#relevant-entries .re-' + json_event['entry_id'] + ' .relevant-entry');
	if(element.length == 1) {
		// detach content and remove old relevant entry
		element.detach();
		$('#relevant-entries .re-' + json_event['entry_id']).remove();

		// update image size to smaller thumbnail
		if(imageSize == 'q') {
			var image = element.children('.flickr-image')
			var newUrl = image.attr('src').replace('_q.jpg', '_s.jpg');
			image.attr('src', newUrl);
		}

		// construct timeline element
		element.addClass('timeline-panel');
		var newElement = $('<li><div class="timeline-badge"><i class="glyphicon glyphicon-asterisk"></i></div></li>');
		newElement.hide();
		newElement.append(element);
		newElement.addClass('re-' + json_event['entry_id']);
		$('#timeline').append(newElement);

		// determine timeline position (left/right)
		if(timelineInverted)
			newElement.addClass('timeline-inverted');
		timelineInverted = !timelineInverted;

		// slide in new timeline element
		newElement.slideDown( {
			duration: fadeInTimeMs / 2,
			progress: function() {
				if(scrollBottom) 
					window.scrollTo(0,document.body.scrollHeight);
			}
		});
	}

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
		console.log('unstar ' + entry_id);
		$.postJSON('/unstarred', JSON.stringify({"entry_id": entry_id}), function() {
			starredEntries.splice(index, 1);
			$('.re-' + entry_id + ' button.star-icon span').removeClass('glyphicon-star').addClass('glyphicon-star-empty');
		});
	} else { 
		// star entry
		console.log('star ' + entry_id);
		$.postJSON('/starred', JSON.stringify({"entry_id": entry_id}), function() {
			starredEntries.push(entry_id);
			$('.re-' + entry_id + ' button.star-icon span').removeClass('glyphicon-star-empty').addClass('glyphicon-star');
		});
	}

}

function closeEntry(entry_id) {
	console.log('closeEntry ' + entry_id);

	$.postJSON('/closed', JSON.stringify({"entry_id": entry_id}), function() {
		// remove relevant entry
		$('#relevant-entries .re-' + entry_id).remove();

		// remove timeline entry/ies and align following entries left/right
		var timeline_entry = $('#timeline .re-' + entry_id);
		timeline_entry.fadeOut(fadeInTimeMs, function() {
			timeline_entry.remove();
			timeline_entry.nextAll().toggleClass('timeline-inverted');
		});
	});
}

function showModal(entry_id) {
	console.log('showModal ' + entry_id);

	$.postJSON('/viewing', JSON.stringify({"entry_id": entry_id}), function() {
		
		// set title
		var title = $('.re-' + entry_id + ' h3').text();
		$('#entry-modal h4.modal-title').html(title);
		
		// set iframe content
		var url = $('.re-' + entry_id + ' .relevant-entry').attr('data-modal-url');
		$('#entry-modal-iframe').attr('src', url + '&printable=yes');

		// register onClose-event
		$('#entry-modal').on('hide.bs.modal', function(e) {
			console.log('closeModal ' + entry_id);

			$('#entry-modal').off('hide.bs.modal');
			$.postJSON('/viewingClosed', JSON.stringify({"entry_id": entry_id}), null);
		});

		$('#entry-modal').modal('show');
	});
}

function resetConversation() {
	console.log('resetConversation() called');
	$.get('/reset');
}



/* utility */

function reset() {
	console.log('reset called');
	starredEntries = [];
	$('#chat-area').empty();
	$('#relevant-entries').empty();
	$('#timeline').empty();
}

function getFlickrImage(searchTerm, size, callback) {
	var flickr_sort = $('#flickrSort').val();
	var flickr_api_key = 'fed915bcf3c85271ac6f9ef1823175bf';
	var flickr_request_url = 'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=' + flickr_api_key + '&text=' + searchTerm + '&sort=' + flickr_sort + '&is_commons=&per_page=1&page=1&format=json&nojsoncallback=1';


	$.getJSON(flickr_request_url, function(data) {
		var image_url = "";
		if(data['stat'] == "ok" && data['photos']['photo'].length > 0) {
			var photo = data['photos']['photo'][0];
			image_url = "https://farm" + photo['farm'] + ".staticflickr.com/" + photo['server'] + "/" + photo['id'] + "_" + photo['secret'] + "_" + size + ".jpg";
		}

		callback(image_url);
	});
}

jQuery["postJSON"] = function( url, data, callback ) {
    return jQuery.ajax({
        url: url,
        type: "POST",
        contentType:"application/json; charset=utf-8",
        data: data,
        success: callback
    });
};


/* bindings */

$(document).ready(function() {
	resetConversation();

	// determine image size depending on window width
	if($(window).width() >= xlBreakPoint)
		imageSize = 'q';
	else
		imageSize = 's';
});

$('#flickrSort').change(function() {
	console.log('flickrSort updated');

	// update images
	$('.relevant-entry').each(function(index, element) {
		var element = $(this);
		var entry_id = element.attr('data-entry-id');

		// determine image size ('s' for timeline and 'q' or 's' for relevant entries depending on current image size)
		var size = 's';
		if(element.parents('#relevant-entries').length > 0)
			size = imageSize;

		getFlickrImage(entry_id, size, function(image_url) {
			if(image_url) {
				if(element.has('.flickr-image')) {
					// replace image
					element.children('.flickr-image').attr('src', image_url);
				} else {
					// add image
					element.prepend('<img src="' + image_url +'" class="flickr-image" alt="' + entry_id + '" />');	
				}
			} else {
				// remove image
				element.children('.flickr-image').remove();
			}
		}); 
	});
});

$(window).resize(function() {
	// determine new image size
	var oldSize = imageSize;
	var newSize = 's';
	if($(window).width() >= xlBreakPoint)
		newSize = 'q';

	// update images if size changed
	if(oldSize != newSize) {
		console.log('image size changed');

		imageSize = newSize;

		$('#relevant-entries .flickr-image').each(function() {
			var url = $(this).attr('src');
			url = url.replace('_'+oldSize+'.jpg', '_'+newSize+'.jpg');
			$(this).attr('src', url);
		});
	}
});

$(window).scroll(function() { 
	// check if user has scrolled to bottom of the page  
	if($(window).scrollTop() + $(window).height() == $(document).height()) {
		scrollBottom = true;
	} else {
		scrollBottom = false;
	}
});
