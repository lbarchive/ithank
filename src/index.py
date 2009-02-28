import logging
import os

from google.appengine.api import users      
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required, run_wsgi_app

os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.settings'
from django.conf import settings
# Force Django to reload settings
settings._target = None
 
import config
from ithank import thank
from ithank.util import I18NRequestHandler


class HomePage(I18NRequestHandler):

  def get(self):
    import sys
    template_values = {
        'before_head_end': config.before_head_end,
        'after_footer': str(sys.path), #config.after_footer,
        'before_body_end': config.before_body_end,
        }
    path = os.path.join(os.path.dirname(__file__), 'template/home.html')
    self.response.out.write(template.render(path, template_values))


class SayPage(I18NRequestHandler):

  @login_required
  def get(self):

    user = users.get_current_user()

    template_values = {
        'before_head_end': config.before_head_end,
        'after_footer': config.after_footer,
        'before_body_end': config.before_body_end,
        'name': user.nickname(),
        'valid_languages': config.valid_languages,
        'subject': _('I thank '),
        'story': _('Write the story here at least %d characters' % config.thank_min_story),
        }
    path = os.path.join(os.path.dirname(__file__), 'template/say.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):

    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url('/say'))
    
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
          'after_footer': users.create_logout_url('/'),
          #'after_footer': config.after_footer,
          'before_body_end': config.before_body_end,
          'thank_link': thx.create_link(),
          'tweet_message': thx.create_tweet(),
          }
      path = os.path.join(os.path.dirname(__file__), 'template/said.html') 
    except ValueError, e:
      # TODO check last thank, must be longer than 10 minutes
      template_values = {
          'before_head_end': config.before_head_end,
          'after_footer': users.create_logout_url('/'),
          #'after_footer': config.after_footer,
          'before_body_end': config.before_body_end,
          'messages': (('error', e.message), ),
          'name': name,
          'valid_languages': config.valid_languages,
          'language': language,
          'subject' : subject,
          'story' : story,
          }
      path = os.path.join(os.path.dirname(__file__), 'template/say.html')
      
    self.response.out.write(template.render(path, template_values))


class ThankPage(I18NRequestHandler):

  def get(self, thank_id):
    
    thx = thank.Thank.get_by_thank_id(thank_id)

    if not thx:
      self.redirect('/')

    logging.debug(thx)
    template_values = {
        'before_head_end': config.before_head_end,
        'after_footer': config.after_footer,
        'before_body_end': config.before_body_end,
        'thank': thx,
        'current_user': users.get_current_user(),
        }
    path = os.path.join(os.path.dirname(__file__), 'template/thank.html')
    self.response.out.write(template.render(path, template_values))


class RandomJSON(I18NRequestHandler):

  def get(self, count):
 
    pass


class ReportJSON(I18NRequestHandler):

  def get(self, thank_id):
 
    pass


class BrowsePage(I18NRequestHandler):

  def get(self, language, page):

    page = 1 if not page else int(page)


class Feed(I18NRequestHandler):

  def get(self, language, page):
 
    page = 1 if not page else int(page)


application = webapp.WSGIApplication([
    ('/', HomePage),
    ('/say', SayPage),
    ('/t/([a-zA-Z0-9-_.]+)', ThankPage),
    (r'/random\.json?count=([0-9]+)', RandomJSON),
    (r'/report\.json?thank_id=([a-zA-Z0-9-_.]+)', ReportJSON),
    ('/browse/?([a-zA-Z_]*)/?([0-9]*)/?', BrowsePage),
    ('/feed/?([a-zA-Z_]*)/?([0-9]*)/?', Feed),
    ],
    debug=config.debug)


def main():
  """Main function"""
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
