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
from ithank.counter import Counter
from ithank.paginator import Paginator
from ithank.util import I18NRequestHandler, json_error, send_json, set_topbar_vars
import config
import ithank


class SettingsPage(I18NRequestHandler):

  def get(self):

    language = self.request.COOKIES.get('django_language', '')
    template_values = {
        'config': config,
        'LANGUAGES': settings.LANGUAGES,
        'language': language,
        }
    set_topbar_vars(template_values, self.request.url)
    path = os.path.join(os.path.dirname(__file__), 'template/settings.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):

    messages = []

    language = self.request.get('language')
    if language and language in dict(settings.LANGUAGES).keys():
      self.request.COOKIES['django_language'] = language
      self.reset_language()
      messages.append(('message', _('Language saved')))
    
    template_values = {
        'messages': messages,
        'config': config,
        'LANGUAGES': settings.LANGUAGES,
        'language': language,
        }
    set_topbar_vars(template_values, self.request.url)
    path = os.path.join(os.path.dirname(__file__), 'template/settings.html')
    self.response.out.write(template.render(path, template_values))

  def head(self):

    pass


application = webapp.WSGIApplication([
    ('/settings', SettingsPage),
    ],
    debug=config.debug)


def main():
  """Main function"""
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
