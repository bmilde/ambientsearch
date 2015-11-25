/*
ambientsearch.js - Receive and display events from an event stream.

Author: Benjamin Milde
*/


/*Events: relevant documents*/

/*This generates a template function for the template in index.html with the id relevantDocs_tmpl*/
var wikiEntryTemplate = doT.template(document.getElementById('relevant-entry-template').text);
var categoryEntryTemplate = doT.template(document.getElementById('relevantCategory_tmpl').text);

var fadeInTimeMs = 800;

var xlBreakPoint = 1800;
var imageSize = 's';

var timelineInverted = false;

var scrollBottom = true;
var scrollChatAreaBottom = true;

var filterStarredOnly = false;
var filterMinScore = 0;

var colorScoreLow = [128,128,255];
var colorScoreHigh = [255,64,64];

var timer = 0;
var runTimer = false;

var debugOutput = false;

function addRelevantEntry(jsonEvent) {
	if(debugOutput)
		console.log('addRelevantEntry ' + jsonEvent['entry_id']);

	if(jsonEvent['type'] == 'wiki')
	{
		// create new entry from template
		var entry = $(wikiEntryTemplate(jsonEvent));
		var entryContent = entry.children('.entry-content');

		// insert entry at designated location
		if(jsonEvent['insert_before'] == '_end_')
			entry.hide().appendTo('#relevant-entries');
		else
			entry.hide().insertBefore('#relevant-entries .entry-'+jsonEvent['insert_before']);

		runTimer = true;

		// add flickr image
		getFlickrImage(jsonEvent['title'], imageSize, function(imageUrl) {
			if(imageUrl) {
				entryContent.prepend('<img src="' + imageUrl +'" class="flickr-image" alt="' + jsonEvent['entry_id'] + '" />');

				// fix image size if entry is moved to timeline by now
				if(entryContent.parents('#timeline').length == 1 && imageSize == 'q') {
					var image = entryContent.children('.flickr-image');
					var newUrl = image.attr('src').replace('_q.jpg', '_s.jpg');
					image.attr('src', newUrl);
				}
			}
			
			entry.fadeIn({
				duration: fadeInTimeMs,
				progress: function() {
					if(scrollBottom) 
						window.scrollTo(0,document.body.scrollHeight);
				}
			});
		});
	}
}

function delRelevantEntry(jsonEvent) {
	if(debugOutput)
		console.log('delRelevantEntry ' + jsonEvent['entry_id']);
	
	var relevantEntry = $('#relevant-entries .entry-' + jsonEvent['entry_id']);
	var entryContent = relevantEntry.children('.entry-content');
	if(relevantEntry.length == 1) {
		// detach content and remove old relevant entry
		entryContent.detach();
		relevantEntry.remove();

		// update image size to smaller thumbnail
		var image = entryContent.children('.flickr-image')
		if(image.length == 1 && imageSize == 'q') {
			var newUrl = image.attr('src').replace('_q.jpg', '_s.jpg');
			image.attr('src', newUrl);
		}

		var starred = entryContent.hasClass('starred');
		var score = parseFloat(entryContent.attr('data-score'));
		var time = parseFloat(entryContent.attr('data-time'));

		// construct timeline entry
		var timeString = getTimeString(time);
		entryContent.addClass('timeline-panel');
		var timelineEntry = $('<li class="timeline-entry"><div class="timeline-badge">' + timeString + '</div></li>');
		timelineEntry.hide();
		timelineEntry.append(entryContent);
		timelineEntry.addClass('entry-' + jsonEvent['entry_id']);
		
		// determine badge color from score
		var score = entryContent.attr('data-score');
		var badge = timelineEntry.children('.timeline-badge');
		var color = getBadgeColor(score);
		badge.css({
			backgroundColor: 'rgb('+color[0]+','+color[1]+','+color[2]+')'
		});

		// insert in timeline (sorted)
		var timelineEntries = $('.timeline-entry');
		var inserted = false;
		timelineEntries.each(function(index, element) {
			var e = $(element);
			var t = parseFloat(e.children('.entry-content').attr('data-time'));
			if(t > time) {
				if(e.hasClass('timeline-inverted'))
					timelineEntry.addClass('timeline-inverted');
				timelineEntry.insertBefore(element);
				timelineEntry.nextAll('.timeline-entry').toggleClass('timeline-inverted');
				timelineInverted = !timelineInverted;
				inserted = true;
				return false;
			}
		});
		if(!inserted) {
			if(timelineInverted)
				timelineEntry.addClass('timeline-inverted');
			timelineInverted = !timelineInverted;
			timelineEntry.insertBefore('#timer');
		}

		if(showEntry(starred, score)) {

			// slide in new timeline entry
			timelineEntry.slideDown( {
				duration: fadeInTimeMs / 2,
				progress: function() {
					if(scrollBottom) 
						window.scrollTo(0,document.body.scrollHeight);
				}
			});
		}

		
	}

}

/*Events: speech recognition feedback*/

function addUtterance(jsonEvent) {
	$('#chat-area').append('<p>'+renderUtterance(jsonEvent)+' </p>')
	if(scrollChatAreaBottom)
		document.getElementById('chat-area').scrollTop = document.getElementById('chat-area').scrollHeight;
}

function replaceLastUtterance(jsonEvent) {
	$('#chat-area p:last').html(renderUtterance(jsonEvent))
	if(scrollChatAreaBottom)
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
	jsonEvent = JSON.parse(event.data);

	if (jsonEvent.handle == 'addUtterance')
	{
		utts.push(jsonEvent.utterance);
		addUtterance(jsonEvent);
	}
	else if (jsonEvent.handle == 'replaceLastUtterance')
	{
		utts.pop();
		utts.push(jsonEvent.utterance);
		replaceLastUtterance(jsonEvent);
	}else if (jsonEvent.handle == 'addRelevantEntry')
	{
		addRelevantEntry(jsonEvent);
	}else if (jsonEvent.handle == 'delRelevantEntry')
	{
		delRelevantEntry(jsonEvent);
	}else if (jsonEvent.handle == 'setCategories')
	{
		setCategories(jsonEvent);
	}
	else if (jsonEvent.handle == 'reset')
	{
		reset();
	}
};


/* user called methods */

function starEntry(entryID) {
	var entryContent = $('.entry-' + entryID + ' .entry-content');

	if(entryContent.hasClass('starred')) { 
		// unstar entry
		if(debugOutput)
			console.log('unstar ' + entryID);
		$.postJSON('/unstarred', JSON.stringify({"entry_id": entryID}), function() {
			entryContent.find('button.star-icon span').removeClass('glyphicon-star').addClass('glyphicon-star-empty');
			entryContent.removeClass('starred');

			// determine badge color from score
			var score = entryContent.attr('data-score');
			var timelineEntry = $('.timeline-entry.entry-' + entryID);
			var badge = timelineEntry.children('.timeline-badge');
			var color = getBadgeColor(score);
			badge.css({
				backgroundColor: 'rgb('+color[0]+','+color[1]+','+color[2]+')'
			});
		});
	} else { 
		// star entry
		if(debugOutput)
			console.log('star ' + entryID);
		$.postJSON('/starred', JSON.stringify({"entry_id": entryID}), function() {
			entryContent.find('button.star-icon span').removeClass('glyphicon-star-empty').addClass('glyphicon-star');
			entryContent.addClass('starred');

			// set badge color to score==1
			var timelineEntry = $('.timeline-entry.entry-' + entryID);
			var badge = timelineEntry.children('.timeline-badge');
			var color = getBadgeColor(1);
			badge.css({
				backgroundColor: 'rgb('+color[0]+','+color[1]+','+color[2]+')'
			});
		});
	}

}

function closeEntry(entryID) {
	if(debugOutput)
		console.log('closeEntry ' + entryID);

	$.postJSON('/closed', JSON.stringify({"entry_id": entryID}), function() {
		// remove relevant entry
		$('#relevant-entries .entry-' + entryID).remove();

		// remove timeline entry/ies
		var timelineEntry = $('#timeline .entry-' + entryID);
		timelineEntry.fadeOut(fadeInTimeMs, function() {
			timelineEntry.remove();
			filterTimeline();
			$(this).remove();
		});
	});
}

function showModal(entryID) {
	if(debugOutput)
		console.log('showModal ' + entryID);

	$.postJSON('/viewing', JSON.stringify({"entry_id": entryID}), function() {
		
		var entryContent = $('.entry-' + entryID + ' .entry-content');

		// set title & iframe content
		var title = entryContent.attr('data-title');
		var url = entryContent.attr('data-modal-url');
		$('#entry-modal h4.modal-title').html(title);
		$('#entry-modal-iframe').attr('src', url + '&printable=yes');

		// register onClose-event
		$('#entry-modal').on('hide.bs.modal', function(e) {
			if(debugOutput)
				console.log('closeModal ' + entryID);

			$('#entry-modal').off('hide.bs.modal');
			$.postJSON('/viewingClosed', JSON.stringify({"entry_id": entryID}), null);
		});

		$('#entry-modal').modal('show');
	});
}

function resetConversation() {
	if(debugOutput)
		console.log('resetConversation() called');
	$.get('/reset');
	reset();
}

function filterTimeline() {
	if(debugOutput)
		console.log('filterTimeline starredOnly=' + filterStarredOnly + ' minScore=' + filterMinScore);

	var entries = $('li.timeline-entry');
	entries.removeClass('timeline-inverted');

	timelineInverted = false;
	entries.each(function() {
		var entry = $(this);
		var entryContent = entry.children('.entry-content');

		var starred = entryContent.hasClass('starred');
		var score = entryContent.attr('data-score');

		if(showEntry(starred, score)) {
			if(timelineInverted)
				entry.addClass('timeline-inverted');
			timelineInverted = !timelineInverted;
			
			entry.show();
		} else {
			entry.hide();
		}
	});
}

/* utility */

/* Render a set of catgeories */
function setCategories(json_event)
{
    arrayOfCategories = json_event['categories']
	var innerHTML = '';
	var category = '';
	for (var i = 0, l=arrayOfCategories.length; i<l; i++) 
	{
		innerHTML = innerHTML + categoryEntryTemplate(arrayOfCategories[i]);
		category = arrayOfCategories[i].title;
		//m_listOfHistoricalCategories.push(category);  // adding a new category to the historical category list.
	}	
	
	$("#categorylist").html(innerHTML);
	//updateHistoricalCategories();
}

function renderUtterance(jsonEvent) {
	return '<span>'+jsonEvent.speaker+':</span> '+jsonEvent.utterance
}

function reset() {
	if(debugOutput)
		console.log('reset called');

	timer = 0;
	runTimer = false;
	updateTimerGUI();

	scrollChatAreaBottom = true;
	scrollBottom = true;

	filterMinScore = 0;
	filterStarredOnly = false;
	$('#filter-starredOnly').bootstrapSwitch('state', false);
	$('#filter-minScore').slider('setValue', filterMinScore);

	$('#chat-area').empty();
	$('#relevant-entries').empty();
	$('#categorylist').empty();
	$('.timeline-entry').remove();
}

function getFlickrImage(searchTerm, size, callback) {
	var flickrSort = $('#flickrSort').val();
	var flickrApiKey = 'fed915bcf3c85271ac6f9ef1823175bf';
	var flickrRequestUrl = 'https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=' + flickrApiKey + '&text="' + searchTerm + '"&sort=' + flickrSort + '&is_commons=&per_page=1&page=1&format=json&nojsoncallback=1';

	$.getJSON(flickrRequestUrl, function(data) {
		var imageUrl = "";
		if(data['stat'] == "ok" && data['photos']['photo'].length > 0) {
			var photo = data['photos']['photo'][0];
			imageUrl = "https://farm" + photo['farm'] + ".staticflickr.com/" + photo['server'] + "/" + photo['id'] + "_" + photo['secret'] + "_" + size + ".jpg";
		}

		callback(imageUrl);
	});
}

function showEntry(starred, score) {
	return (starred || (!filterStarredOnly && score >= filterMinScore));
}

function getTimeString(seconds) {
	var minutesFormatted = Math.floor(seconds / 60);
	var secondsFormatted = Math.round(seconds % 60);
	if(secondsFormatted < 10)
		secondsFormatted = '0' + secondsFormatted;

	return minutesFormatted + ':' + secondsFormatted;
}

function updateTimerGUI() {
	var timeString = getTimeString(timer);
	$('#timer .timeline-badge').html(timeString);
}

function getBadgeColor(score) {
	return [Math.round(colorScoreLow[0] + score * (colorScoreHigh[0] - colorScoreLow[0])), Math.round(colorScoreLow[1] + score * (colorScoreHigh[1] - colorScoreLow[1])), Math.round(colorScoreLow[2] + score * (colorScoreHigh[2] - colorScoreLow[2]))];
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

jQuery.fn.reverse = [].reverse;


/* bindings */

$(document).ready(function() {

	// init filter-starred-swicth
	$("[name='filter-starredOnly']").bootstrapSwitch({
		state: filterStarredOnly,
		size: 'mini',
		onSwitchChange: function(event, state) {
			filterStarredOnly = state;
			filterTimeline();
		}
	});

	// init filter-minScore-slider
	var slider = $('#filter-minScore');
	slider.slider({
		min: 0,
		max: 1,
		step: 0.05,
		value: filterMinScore,
		tooltip_position: 'bottom',
		ticks: [0,1],
		ticks_positions: [0,100],
		ticks_labels: ['-', '+']
	});

	slider.on('change', function(event) {
		filterMinScore = event['value']['newValue'];
		filterTimeline();
	});

	$('.slider-track').css({
		background: 'linear-gradient(to right, rgb('+colorScoreLow[0]+','+colorScoreLow[1]+','+colorScoreLow[2]+'), rgb('+colorScoreHigh[0]+','+colorScoreHigh[1]+','+colorScoreHigh[2]+'))'
	});

	resetConversation();

	// determine image size depending on window width
	if($(window).width() >= xlBreakPoint)
		imageSize = 'q';
	else
		imageSize = 's';
});

$('#speechInputSetting').change(function() {
	var val = $('#speechInputSetting').val();
	if (val == 'On')
	{
		$('#speech-input').show();
	}else if (val == 'Off')
	{
		$('#speech-input').hide();
	}
});

$('#categorySetting').change(function() {
	var val = $('#categorySetting').val();
	if (val == 'On')
	{
		$('#additional-information').show();
	}else if (val == 'Off')
	{
		$('#additional-information').hide();
	}
});

$('#flickrSort').change(function() {
	if(debugOutput)
		console.log('flickrSort updated');

	// update images
	$('.entry-content').each(function(index, element) {
		var element = $(this);
		var entryID = element.attr('data-entry-id');
		var title = element.attr('data-title');

		// determine image size ('s' for timeline and 'q' or 's' for relevant entries depending on current image size)
		var size = 's';
		if(element.parents('#relevant-entries').length > 0)
			size = imageSize;

		getFlickrImage(title, size, function(imageUrl) {
			if(imageUrl) {
				if(element.has('.flickr-image')) {
					// replace image
					element.children('.flickr-image').attr('src', imageUrl);
				} else {
					// add image
					element.prepend('<img src="' + imageUrl +'" class="flickr-image" alt="' + entryID + '" />');	
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
		if(debugOutput)
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
	if($(window).scrollTop() + $(window).height() == $(document).height())
		scrollBottom = true;
	else
		scrollBottom = false;
});

$('#chat-area').scroll(function() { 
	var element = $(this);
	// check if user has scrolled to bottom of the chat area  
	if(element[0].scrollHeight - element.scrollTop() == element.innerHeight())
		scrollChatAreaBottom = true;
	else
		scrollChatAreaBottom = false;
});

window.setInterval(function() {
	if(runTimer) {
		timer = timer + 1;
		updateTimerGUI();
	}
}, 1000);
