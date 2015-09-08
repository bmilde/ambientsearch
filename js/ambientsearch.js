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

var source = new EventSource('/stream');
var utts = []

source.onmessage = function (event) {
	json_event = JSON.parse(event.data);
	if (json_event.handle == 'addUtterance')
	{
		utts.push(json_event.utterance)
		addUtterance(json_event)
	}
	else if (json_event.handle == 'replaceLastUtterance')
	{
		utts.pop()
		utts.push(json_event.utterance)
		replaceLastUtterance(json_event)
	}
};
