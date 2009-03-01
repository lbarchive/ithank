google.load("jquery", "1");
google.setOnLoadCallback(function() {
  $("#messages").ajaxError(function(event, request, settings){
    switch(request.status) {
      case 404:
        $(this).html("Oops! Got 404 NOT FOUND, this should be a bug, you may notify the problem generator, the creator of I Thank.");
        break;
      case 500:
        $(this).html("It is 500! Server does not want to serve you! :-)");
        break;
      default:
        $(this).html("Unknown problem!");
      }
    });
  });

function flag(thank_id) {
  var query_url = 'http://i-thank.appspot.com/';
  if (window.location.href.indexOf('localhost') >= 0)
    query_url = 'http://localhost:8080/';
  $.getJSON('flag.json?thank_id=' + thank_id + '&callback=?', function(json) {
    if (json.err == 0) {
      $("a.flag").each(function(){
        var $ele = $(this)
        if ($ele.attr('href').indexOf("('" + json.thank_id + "')") >= 0) {
          $ele.replaceWith('Flagged');
          $('#messages').html();
          return false;
          }
        });
      }
    else
      $('#messages').html(json.err_msg);
    });
  }
