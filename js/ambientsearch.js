/*Events: relevant documents*/

wikiEntryTemplate = doT.template(document.getElementById('relevantDocs_tmpl').text);

function addRelevantEntry(json_event) {
	if (json_event["type"] == "wiki")
	{
		html = wikiEntryTemplate(json_event);
		console.log(html);
		$(html).hide().appendTo("#relevantDocs").fadeIn(800);
	}
}

function delRelevantEntry(json_event) {
	$("#"+json_event["entry_id"]).remove();
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
	$("#chat-area").empty();
	$("#relevantDocs").empty();
}

/*Dispatch events from EventSource*/

var source = new EventSource('/stream');
var utts = [];

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