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


class HomePage(I18NRequestHandler):

  def get(self):
    
    thx = thank.get_random(1)
    if thx:
      thx = thx[0]
      thx.name = thx.name.encode('utf-8')
    
    template_values = {
        'config': config,
        'thank': thx,
        }
    set_topbar_vars(template_values, self.request.url)
    path = os.path.join(os.path.dirname(__file__), 'template/home.html')
    self.response.out.write(template.render(path, template_values))


class AboutPage(I18NRequestHandler):

  def get(self):
 
    template_values = {
        'config': config,
        }
    set_topbar_vars(template_values, self.request.url)
    path = os.path.join(os.path.dirname(__file__), 'template/about.html')
    self.response.out.write(template.render(path, template_values))


class TermsPage(I18NRequestHandler):

  def get(self):
 
    template_values = {
        'config': config,
        }
    set_topbar_vars(template_values, self.request.url)
    path = os.path.join(os.path.dirname(__file__), 'template/terms.html')
    self.response.out.write(template.render(path, template_values))


class EverywherePage(I18NRequestHandler):

  def get(self):
 
    template_values = {
        'config': config,
        }
    set_topbar_vars(template_values, self.request.url)
    path = os.path.join(os.path.dirname(__file__), 'template/everywhere.html')
    self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication([
    ('/', HomePage),
    ('/about', AboutPage),
    ('/terms', TermsPage),
    ('/everywhere', EverywherePage),
    ],
    debug=config.debug)


def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
