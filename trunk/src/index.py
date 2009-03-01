import logging as log
import os

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required, run_wsgi_app

os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.settings'
from django.conf import settings
# Force Django to reload settings
settings._target = None
from django.utils import feedgenerator

import config
from ithank import thank
from ithank.counter import Counter
from ithank.paginator import Paginator
from ithank.util import I18NRequestHandler, json_error, send_json


class HomePage(I18NRequestHandler):

  def get(self):
    
    template_values = {
        'before_head_end': config.before_head_end,
        'after_footer': config.after_footer,
        'before_body_end': config.before_body_end,
        'thank': thank.get_random(1)[0],
        }
    set_topbar_vars(template_values, self.request.url)
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
          'after_footer': config.after_footer,
          'before_body_end': config.before_body_end,
          'thank_link': thx.create_link(),
          'tweet_message': thx.create_tweet(),
          }
      path = os.path.join(os.path.dirname(__file__), 'template/said.html') 
    except ValueError, e:
      # TODO check last thank, must be longer than 10 minutes
      template_values = {
          'before_head_end': config.before_head_end,
          'after_footer': config.after_footer,
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
      log.warning('Non-existing thank requested: %s' % thank_id)
      self.redirect('/')

    thx.name = thx.name.encode('utf-8')
    template_values = {
        'before_head_end': config.before_head_end,
        'after_footer': config.after_footer,
        'before_body_end': config.before_body_end,
        'thank': thx,
        }
    set_topbar_vars(template_values, self.request.url)
    path = os.path.join(os.path.dirname(__file__), 'template/thank.html')
    self.response.out.write(template.render(path, template_values))


class RandomJSON(I18NRequestHandler):

  def get(self):
 
    count = self.request.get('count', 1)
    if count < 1:
      count = 1
    if count > config.thanks_random_max_items:
      count = config.thanks_random_max_items
    language = self.request.get('language') 
    callback = self.request.get('callback') 

    if language:
      if language not in config.dict_valid_languages:
        log.warning('Invalid language: %s' % language)
        json.error(self.response, 3)
        return
      counter_key = 'thank_%s' % language
      query = "SELECT * FROM Thank WHERE language = '%s' ORDER BY published DESC" % language
      lang_path = language + '/'
      title = config.dict_valid_languages[language]
    else:
      counter_key = 'thank'
      query = 'SELECT * FROM Thank ORDER BY published DESC'
      lang_path = ''
      title = _('All')

    thanks = thank.get_random(count, language)
    # TODO

class FlagJSON(I18NRequestHandler):

  def get(self):

    # TODO flag simple24
    thank_id = self.request.get('thank_id') 
    if thank_id == '':
      json_error(self.response, 1, callback)
      return
    callback = self.request.get('callback') 
    
    # Must log in
    user = users.get_current_user()
    if not user:
      log.warning('Login required' % thank_id)
      json_error(self.respoonse, 2, callback)
      return

    thx = thank.Thank.get_by_thank_id(thank_id)
    if not thx:
      log.warning('Non-existing thank requested: %s' % thank_id)
      json_error(self.response, 1, callback)
      return

    # Has not flagged?
    if user not in thx.flaggers:
      # Flagging it
      thank.flag(thx.key().id(), user)

    send_json(self.response, {'thank_id': thank_id}, callback)


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
        'before_head_end': config.before_head_end,
        'after_footer': config.after_footer,
        'before_body_end': config.before_body_end,
        'title': title,
        'current_page': page,
        'thanks': thanks,
        'prev': prev,
        'nav_list': nav_list,
        'next': next,
        'lang_path': lang_path,
        'valid_languages': config.valid_languages,
        'current_user': users.get_current_user(),
        }

    set_topbar_vars(template_values, self.request.url)

    path = os.path.join(os.path.dirname(__file__), 'template/browse.html')
    self.response.out.write(template.render(path, template_values))


class Feed(I18NRequestHandler):

  def get(self, language, page):
 
    page = 1 if not page else int(page)
    # TODO simple24
    if language:
      if language not in config.dict_valid_languages:
        log.warning('Invalid language: %s' % language)
        self.error(500)
        self.response.out.write('Invalid language: %s' % language)
        return
      mem_key = 'feed_%s' % language
    else:
      mem_key = 'feed'

    raw_feed = memcache.get(mem_key)
    if raw_feed:
      self.response.out.write(raw_feed)
      return

    # TODO check cache
    feed = feedgenerator.Rss201rev2Feed(title=_('I Thank'), link=config.base_URI, description=_('Say thanks!'))
    
    query = thank.Thank.all()
    if language:
      feed.language = language
      query.filter('language =', language)
    query.order('-published')

    thanks = query.fetch(config.thanks_feed_items)
    for thx in thanks:
      # TODO strips tags
      feed.add_item(
          title=template.Template('{{ subject|striptags }}').render(template.Context({'subject': thx.subject})),
          link=thx.create_link(),
          description=template.Template('{{ story|striptags|linebreaks }}').render(template.Context({'story': thx.story})),
          author_name=template.Template('{{ name|striptags }}').render(template.Context({'name': thx.name})),
          pubdate=thx.published, unique_id=thx.create_link())

    raw_feed = feed.writeString('utf8')
    self.response.out.write(raw_feed)
  
    # Cache it
    if not memcache.set(mem_key, raw_feed, config.feed_cache):
      log.error('Unable to cache %s' % mem_key)


class StatsPage(I18NRequestHandler):

  def get(self, language, page):

    pass


def set_topbar_vars(template_values, url):

  current_user = users.get_current_user()
  template_values['current_user'] = current_user
  if current_user:
    template_values['nickname'] = current_user.nickname()
    template_values['logout_url'] = users.create_logout_url(url)
  else:
    template_values['login_url'] = users.create_login_url(url)

  
application = webapp.WSGIApplication([
    ('/', HomePage),
    ('/say', SayPage),
    ('/t/([a-zA-Z0-9-_.]+)', ThankPage),
    (r'/random\.json', RandomJSON),
    (r'/flag\.json', FlagJSON),
    ('/browse/?([a-zA-Z_]*)/?([0-9]*)/?', BrowsePage),
    ('/feed/?([a-zA-Z_]*)/?([0-9]*)/?', Feed),
    ('/stats/?', StatsPage),
    ],
    debug=config.debug)


def main():
  """Main function"""
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
