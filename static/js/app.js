$(document).ready( function() {
	
	$('form').submit( function() {
		var postUrl = $(this).attr('action');
		$('.results').html("<em>Loading...</em>");
		$.post(postUrl, $(this).serialize(), function(res) {
			console.log(res);
			$('.results').html(
				"<a style='display:block;' href='/download/" + res.tweets_filepath + "'>Tweets - Download tab separated file</a>" +
				"<a style='display:block;' href='/download/" + res.hashtags_filepath + "'>Hashtags - Download tab separated file</a>" +
				"<a style='display:block;' href='/download/" + res.urls_filepath + "'>Urls - Download tab separated file</a>"				
			);
		});
		return false;
	});
});