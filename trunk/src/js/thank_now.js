google.load("language", "1");

/*
function prettify_lang_name(lang) {
  var words = lang.split('_');
  var result = new Array();
  for (var i=0; i<words.length; i++) {
    var word = words[i].charAt(0).toUpperCase() + words[i].substr(1).toLowerCase();
    result.push(word);
    }
  return result.join(' ');
  }
*/

function detect_language() {
  google.language.detect($('#subject').val(), function(result) {
    if (!result.error) {
      var language = 'unknown';
      for (l in google.language.Languages) {
        if (google.language.Languages[l] == result.language) {
          language = l;
          break;
          }
        }
      if (language != 'unknown')
        $('#language').get(0).selectedIndex = $('#language option[value=' + result.language + ']').get(0).index
      else
        alert("Google Translate couldn't detect!");
      }
    else
      alert("Google Translate responded an error!");
    });
  }


function preview_thank() {
  var query_url = 'http://i-thank.appspot.com/';
  if (window.location.href.indexOf('localhost') >= 0)
    query_url = 'http://localhost:8080/';
  $.post(query_url + 'preview.json', {name: $('#name').val(), language: $('#language').val(), subject: $('#subject').val(), story: $('#story').val()}, function(json) {
    if (json.err == 0)
      $("#preview").html('<div class="preview-header">' + json.preview_header + '</div>' + json.thank_preview)
    else
      $('#messages').html(json.err_msg);
    }, 'json');
  }


function init_thank_now() {
  /*
  var langs = google.language.Languages;
  for (var lang in langs)
    $('<option value="' + langs[lang] + '">' + prettify_lang_name(lang) + '</option>').appendTo($('#language'));
  */
  $('#subject').keypress(function() {
      $('#subject-counter').text($(this).val().length);
      })
      .keypress();
  $('#story').keypress(function() {
      $('#story-counter').text($(this).val().length);
      })
      .keypress();
  }

google.setOnLoadCallback(init_thank_now);
