google.load("jquery", "1");


// Global error indicator
function init_error_indicator() {
  $("#messages").ajaxError(function(event, request, settings){
    var err_msg;
    switch(request.status) {
      case 404:
        err_msg = "Oops! Got 404 NOT FOUND, this should be a bug, you may notify the problem generator, the creator of I Thank.";
        break;
      case 500:
        err_msg = "It is 500! Server does not want to serve you! :-)";
        break;
      default:
        err_msg = "Unknown problem!";
      }
    $(this).html('<div class="error">' + err_msg + '</div>');
    });
  }


// Flagging
function flag(thank_id) {
  var query_url = 'http://i-thank.appspot.com/';
  if (window.location.href.indexOf('localhost') >= 0)
    query_url = 'http://localhost:8080/';
  if (thank_id == '#')
    return;
  $.getJSON(query_url + 'flag.json?thank_id=' + thank_id + '&callback=?', function(json) {
    if (json.err == 0) {
      $("a.flag").each(function(){
        var $ele = $(this)
        if ($ele.attr('href').indexOf("('" + json.thank_id + "')") >= 0) {
          $ele.replaceWith(json.flag_msg);
          $('#messages').html();
          return false;
          }
        });
      }
    else
      $('#messages').html(json.err_msg);
    });
  }


function init_header() {
  // Hooking
  $('img.language-hover').each(function() {
    // Caching images
    var img = new Image()
    img.src = this.src;
    var img_hover = new Image();
    img_hover.src = this.src.replace('.png', '') + '-hover.png';

    $(this).hover(
      function() {
        this.src = img_hover.src;
      },
      function() {
        this.src = img.src;
      }
      );
    });
  }


// Initialize Disqus
// Based on http://disqus.com/integrate/ithank/generic/
function init_disqus() {
  var links = document.getElementsByTagName('a');
  var query = '?';
  for(var i = 0; i < links.length; i++) {
    if(links[i].href.indexOf('#disqus_thread') >= 0) {
      query += 'url' + i + '=' + encodeURIComponent(links[i].href) + '&';
      }
    }
  $.getScript("http://disqus.com/forums/ithank/get_num_replies.js" + query);
  }


google.setOnLoadCallback(function () {
  init_error_indicator();
  init_header();
  init_disqus();
  });
