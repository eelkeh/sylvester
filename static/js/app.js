$(document).ready( function() {
	
	$('form').submit( function() {
		var postUrl = $(this).attr('action');
		$('.results').html("<em>Loading...</em>");
		$.post(postUrl, $(this).serialize(), function(res) {
			console.log(res);
			$('.results').html("<a href='/download/" + res.filepath + "'>Download tab separated file</a>");
		});
		return false;
	});
});