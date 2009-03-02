import logging as log
import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required, run_wsgi_app

os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.settings'
from django.conf import settings
# Force Django to reload settings
settings._target = None

from ithank import thank
from ithank.util import I18NRequestHandler, json_error, send_json, set_topbar_vars
import config
import ithank


class ThankNowPage(I18NRequestHandler):

  @login_required
  def get(self):

    user = users.get_current_user()

    template_values = {
        'before_head_end': config.before_head_end,
        'after_footer': config.after_footer,
        'before_body_end': config.before_body_end,
        'name': user.nickname(),
        'name_maxlength': config.thank_max_name,
        'valid_languages': config.valid_languages,
        'subject': _('I thank '),
        'subject_maxlength': config.thank_max_subject,
        'story': _('Write the story here at least %d characters' % config.thank_min_story),
        'story_maxlength': config.thank_max_story,
        }
    path = os.path.join(os.path.dirname(__file__), 'template/thank_now.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):

    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url('/thank'))
    
    # Get values
    name = self.request.get('name')
    language = self.request.get('language')
    subject = self.request.get('subject')
    story = self.request.get('story')

    try:
      thx = thank.add(name, language, subject, story)
      # TODO check last thank, must be longer than 10 minutes
      template_values = {
          'before_head_end': config.before_head_end,
          'after_footer': config.after_footer,
          'before_body_end': config.before_body_end,
          'thank_link': thx.create_link().encode('utf-8'),
          'tweet_message': thx.create_tweet().encode('utf-8'),
          }
      path = os.path.join(os.path.dirname(__file__), 'template/thanked.html') 
    except ValueError, e:
      # TODO check last thank, must be longer than 10 minutes
      template_values = {
          'before_head_end': config.before_head_end,
          'after_footer': config.after_footer,
          'before_body_end': config.before_body_end,
          'messages': (('error', e.message), ),
          'name': name,
          'name_maxlength': config.thank_max_name,
          'valid_languages': config.valid_languages,
          'language': language,
          'subject' : subject,
          'subject_maxlength': config.thank_max_subject,
          'story' : story,
          'story_maxlength': config.thank_max_story,
          }
      path = os.path.join(os.path.dirname(__file__), 'template/thank_now.html')
    self.response.out.write(template.render(path, template_values))


class PreviewJSON(I18NRequestHandler):

  def post(self):
    # TODO simple24
    user = users.get_current_user()
    if not user:
      log.warning('Login required')
      json_error(self.response, ithank.LOGIN_REQUIRED)
      return
    
    # Get values
    name = self.request.get('name')
    language = self.request.get('language')
    subject = self.request.get('subject')
    story = self.request.get('story')
    callback = self.request.get('callback') 

    thx = thank.Thank(name=name, language=language, subject=subject, story=story)
    thx.name = thx.name.encode('utf-8')
    thx.create_link = '#'
    thx.encode_thank_id = '#'
    template_values = {
        'thank': thx,
        }
    set_topbar_vars(template_values, self.request.url)
    path = os.path.join(os.path.dirname(__file__), 'template/thank_item.html')
    send_json(self.response, {'preview_header': 'Preview of Your Thank', 'thank_preview': template.render(path, template_values)}, callback)

  
application = webapp.WSGIApplication([
    ('/thank', ThankNowPage),
    (r'/preview\.json', PreviewJSON),
    ],
    debug=config.debug)


def main():
  """Main function"""
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
