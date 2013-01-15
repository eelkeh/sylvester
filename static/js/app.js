$(document).ready( function() {
	
	$('form').submit( function() {
		var postUrl = $(this).attr('action');
		$('.results').html("<em>Loading...</em>");
		$.post(postUrl, function(data) {
			console.log(data);
			$('.results').html("<a href='/download/" + data.filepath + "'>Download tab separated file</a>");
		});
		return false;
	});
});