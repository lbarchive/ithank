import logging as log
import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

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
import simple24 as s24


class ThankPage(I18NRequestHandler):

  def get(self, thank_id):
    
    thx = thank.Thank.get_by_thank_id(thank_id)

    template_values = {
        'config': config,
        }

    if not thx:
      log.warning('Non-existing thank requested: %s' % thank_id)
      self.error(404)
      template_values['messages'] = [('error', _('This thank is not existing!'))]
    else:
      thx.name = thx.name.encode('utf-8')
      template_values['thank'] =  thx

    set_topbar_vars(template_values, self.request.url)
    path = os.path.join(os.path.dirname(__file__), 'template/thank.html')
    self.response.out.write(template.render(path, template_values))

  def head(self, thank_id):

    thx = thank.Thank.get_by_thank_id(thank_id)

    if not thx:
      self.error(404)


class FlagJSON(I18NRequestHandler):

  def get(self):

    callback = self.request.get('callback') 
    thank_id = self.request.get('thank_id') 
    if thank_id == '':
      json_error(self.response, ithank.ERROR_INVALID_THANK_ID, callback)
      return
    
    # Must log in
    user = users.get_current_user()
    if not user:
      log.warning('Login required')
      json_error(self.respoonse, ithank.ERROR_LOGIN_REQUIRED, callback)
      return

    thx = thank.Thank.get_by_thank_id(thank_id)
    if not thx:
      log.warning('Non-existing thank requested: %s' % thank_id)
      json_error(self.response, ithank.ERROR_INVALID_THANK_ID, callback)
      return

    # Has not flagged?
    if user not in thx.flaggers:
      # Flagging it
      thank.flag(thx.key().id(), user)
      s24.incr('flagged')

    send_json(self.response, {'flag_msg': _('Flagged'), 'thank_id': thank_id}, callback)


class BrowsePage(I18NRequestHandler):

  def get(self, language, page):

    page = 1 if not page else int(page)

    # TODO catch timeouts, CapDisabled...
    # TODO doesn't not allow page > max_pages
    # TODO add simple24

    # TODO add limit to flags
    # Get thanks count
    if language:
      if language not in config.dict_valid_languages:
        log.warning('Invalid language: %s' % language)
        self.redirect('/browse')
      counter_key = 'thank_%s' % language
      query = "SELECT * FROM Thank WHERE language = '%s' ORDER BY published DESC" % language
      lang_path = language + '/'
      title = config.dict_valid_languages[language]
    else:
      counter_key = 'thank'
      query = 'SELECT * FROM Thank ORDER BY published DESC'
      lang_path = ''
      title = _('All')

    count = Counter(counter_key).count
    # TODO put max_pages, cache into config
    pger = Paginator(query,
        page, page_items=config.thanks_per_page, page_band_expand=2,
        max_pages=config.thanks_max_pages, total_items=count,
        cache=config.browse_page_cache, cache_version=str(count))
    del counter_key, query, count

    prev, nav_list, next = pger.navigation_list
    if page != pger.page:
      log.error('Page not matched %d, %d' % (page, pger.page))
      # Possibly page > last_page
      # Redirect it
      raise 'page'

    thanks = pger.items
    for thx in thanks:
      # Has to make sure variables in {% blocktrans %} is type str, or this
      # error:
      # UnicodeDecodeError: 'ascii' codec can't decode byte 0xc2 in position 1: ordinal not in range(128)
      thx.name = thx.name.encode('utf-8')

    template_values = {
        'config': config,
        'title': title,
        'current_page': page,
        'thanks': thanks,
        'prev': prev,
        'nav_list': nav_list,
        'next': next,
        'lang_path': lang_path,
        'language': language,
        'cut_story': True,
        'feed_link': '%sfeed/%s' % (config.base_URI, lang_path),
        }

    set_topbar_vars(template_values, self.request.url)

    path = os.path.join(os.path.dirname(__file__), 'template/browse.html')
    self.response.out.write(template.render(path, template_values))

  def head(self, language, page):

    pass


application = webapp.WSGIApplication([
    ('/t/([a-zA-Z0-9-_.]+)', ThankPage),
    (r'/flag\.json', FlagJSON),
    ('/browse/?([a-zA-Z_]*)/?([0-9]*)/?', BrowsePage),
    ],
    debug=config.debug)


def main():
  """Main function"""
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
