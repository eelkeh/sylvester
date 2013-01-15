$(document).ready( function() {
	
	$('form').submit( function() {
		var postUrl = $(this).attr('action');
		$('.results').html("Loading...");
		$.post(postUrl, function(data) {
			console.log(data);
			$('.results').html("<a href='/" + data.filepath + "'>Download tab separated file</a>");
		});
		return false;
	});
});