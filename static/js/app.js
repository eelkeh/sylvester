
var ws = new WebSocket("ws://127.0.0.1:5000/twitter/timeline");

ws.onmessage = function (evt) {
	console.log(evt);
	var data = JSON.parse(evt.data);
	var msg = data.message;
    $('.message').html(msg);

    var results = data.results;
    if (results) {
    	$('.results').html(results);
    }
};

$('form').submit( function(e) {
	e.preventDefault();
	
	var formData = {
		'name': $('[name="name"]').val(),
		'start': $('[name="start"]').val(),
		'end': $('[name="end"]').val(),
	};

	ws.send(JSON.stringify(formData));
	
	//var postUrl = $(this).attr('action');
	
	$('.message').html();
	$('.results').html();
	

		/*$('.results').html(
			"<a style='display:block;' href='/download/" + res.tweets_filepath + "'>Tweets - Download tab separated file</a>" +
			"<a style='display:block;' href='/download/" + res.hashtags_filepath + "'>Hashtags - Download tab separated file</a>" +
			"<a style='display:block;' href='/download/" + res.urls_filepath + "'>Urls - Download tab separated file</a>"				
		);*/			

	return false;
});

