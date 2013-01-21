//var ws = new WebSocket("ws://37.230.96.207/twitter/timeline");
var ws = new WebSocket("ws://37.230.96.207:8080/twitter/timeline");

ws.onmessage = function (evt) {
	console.log(evt);
	var data = JSON.parse(evt.data);
	var msg = data.message;
    
    $('.message .m').html(msg);

    var results = data.results;
    if (results) {
    	$('.message')
    		.addClass('alert-success')
    
    	$('.results')
    		.html(results)
    }
};




$('.nav a').click( function(e) {
	var link = $(this).attr('href').substring(1);
	$(this).parent().siblings().removeClass('active');
	$(this).parent().addClass('active');

	$('.method').hide();
	$('[data-link="' + link + '"]').show();
});


$('form').submit( function(e) {
	e.preventDefault();

	var method = $(this).attr('data-method');

	$('.message, .results').empty();

	$('.message').removeClass('alert-success');
	$('.message').append('<div class="m"></div>');

	//					<div class="progress progress-striped active">' +
  	//					'<div class="bar" style="width: 10%;"></div>' +
	//					'</div>');

	var serializedForm = $(this).serializeArray();
	var fields = {};
	for (var i=0; i < serializedForm.length; i++) {
		fields[serializedForm[i]['name']] = serializedForm[i]['value'];
	}

	var formData = {
		'method': method,
		'fields': fields,
	};

	ws.send(JSON.stringify(formData));
	
	//var postUrl = $(this).attr('action');
	
	
	

		/*$('.results').html(
			"<a style='display:block;' href='/download/" + res.tweets_filepath + "'>Tweets - Download tab separated file</a>" +
			"<a style='display:block;' href='/download/" + res.hashtags_filepath + "'>Hashtags - Download tab separated file</a>" +
			"<a style='display:block;' href='/download/" + res.urls_filepath + "'>Urls - Download tab separated file</a>"				
		);*/			

	return false;
});


$('.nav a[href="#timeline"]').click()

