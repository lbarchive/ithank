import logging as log
import os

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.settings'
from django.conf import settings
# Force Django to reload settings
settings._target = None
from django.utils import feedgenerator

from ithank import thank
from ithank.util import I18NRequestHandler, send_json
import config
import simple24 as s24


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
        json_error(self.response, ERROR_INVALID_LANGUAGE, callback)
        return
    
    try:
      thanks = thank.get_random(count, language)
    except ValueError, e:
      json_error(self.response, ithank.ERROR, e.message, callback)
      return

    if thanks:
      thanks_json = []
      for thx in thanks:
        thanks_json.append({
            'subject': template.Template('{{ subject|striptags }}').render(template.Context({'subject': thx.subject})),
            'link': thx.create_link(),
            'story': template.Template('{{ story|striptags|linebreaks }}').render(template.Context({'story': thx.story})),
            'thanker': template.Template('{{ name|striptags }}').render(template.Context({'name': thx.name})),
            # TODO
            # 'published': convert_to_foo(thx.published),
            })

    send_json(self.response, {'thanks': thanks_json}, callback)
    s24.incr('random.json')


class RandomRSS(I18NRequestHandler):

  def get(self):
 
    count = self.request.get('count', 1)
    if count < 1:
      count = 1
    if count > config.thanks_random_max_items:
      count = config.thanks_random_max_items
    language = self.request.get('language') 

    if language:
      if language not in config.dict_valid_languages:
        log.warning('Invalid language: %s' % language)
        self.error(500)
        return
    
    try:
      thanks = thank.get_random(count, language)
    except ValueError, e:
      self.error(500)
      return

    feed = feedgenerator.Rss201rev2Feed(
        title=_('I Thank'),
        link=config.base_URI,
        description=_('Say thanks!'),
        feed_url=self.request.uri,
        feed_copyright='Creative Commons Attribution-Share Alike 3.0 Unported License',
        )

    if thanks:
      for thx in thanks:
        feed.add_item(
            title=template.Template('{{ subject|striptags }}').render(template.Context({'subject': thx.subject})),
            link=thx.create_link(),
            description=template.Template('{{ story|striptags|linebreaks }}').render(template.Context({'story': thx.story})),
            author_name=template.Template('{{ name|striptags }}').render(template.Context({'name': thx.name})),
            author_email='noreply@i-thank.appspot.com',
            pubdate=thx.published, unique_id=thx.create_link())

    raw_feed = feed.writeString('utf8')
    self.response.out.write(raw_feed)

    s24.incr('random.rss')


class RandomText(I18NRequestHandler):

  def get(self):
    '''
    Returns plain text of a random thank.
    '''

    language = self.request.get('language')
    try:
      thanks = thank.get_random(1, language)
    except ValueError, e:
      self.error(500)
      self.response.out.write(e.message)
      return

    if thanks:
      thx = thanks[0]
      self.response.out.write(template.Template('{{ thank.subject|striptags }}\n\n{{ thank.story|striptags }}\n\n{{ thank.name|striptags }}\n').render(template.Context({'thank': thx})))
      s24.incr('random.txt')
    else:
      self.response.out.write(_('No thanks available.'))


class Feed(I18NRequestHandler):

  def get(self, language, page):
 
    page = 1 if not page else int(page)
    
    if language:
      if language not in config.dict_valid_languages:
        log.warning('Invalid language: %s' % language)
        self.error(500)
        self.response.out.write('Invalid language: %s' % language)
        return
      mem_key = 'feed_%s' % language
      feed_url = '%sfeed/%s/' % (config.base_URI, language)
    else:
      mem_key = 'feed_all'
      feed_url = '%sfeed/' % config.base_URI

    raw_feed = memcache.get(mem_key)
    if raw_feed:
      self.response.out.write(raw_feed)
      return

    feed = feedgenerator.Rss201rev2Feed(
        title=_('I Thank'),
        link=config.base_URI,
        description=_('Say thanks!'),
        feed_url=feed_url,
        feed_copyright='Creative Commons Attribution-Share Alike 3.0 Unported License',
        )
    
    query = thank.Thank.all()
    if language:
      feed.language = language
      query.filter('language =', language)
    query.order('-published')

    thanks = query.fetch(config.thanks_feed_items)
    for thx in thanks:
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

    # Simple24
    s24.incr('feed')
    s24.incr(mem_key)


application = webapp.WSGIApplication([
    (r'/random\.json', RandomJSON),
    (r'/random\.rss', RandomRSS),
    (r'/random\.txt', RandomText),
    ('/feed/?([a-zA-Z_]*)/?([0-9]*)/?', Feed),
    ],
    debug=config.debug)


def main():
  """Main function"""
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
