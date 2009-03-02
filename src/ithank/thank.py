
from base64 import urlsafe_b64encode, urlsafe_b64decode
from random import Random
from struct import pack, unpack
import logging as log

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db

from ithank.counter import Counter
from ithank.util import transaction
import config


class Thank(db.Model):

  name = db.StringProperty(verbose_name='Name', required=True)
  language = db.StringProperty(verbose_name='Language', default='')
  subject = db.StringProperty(verbose_name='Subject', required=True)
  story = db.TextProperty(verbose_name='Story', required=True)
  published = db.DateTimeProperty(verbose_name='Published', required=True, auto_now_add=True)
  user = db.UserProperty(verbose_name='User', required=True, auto_current_user_add=True)
  flags = db.IntegerProperty(verbose_name='Flags', default=0)
  flaggers = db.ListProperty(users.User, verbose_name='Flaggers')

  def encode_thank_id(self):
    '''
    Encodes model's id to a url-friendly string

    Procedure is
     - Packs with litten-endian long long,
     - Strips tailing \\x00 bytes,
     - Encodes with Base64-url-friendly,
     - Replaces padding = with period.
    '''
    
    if '_thank_id' in dir(self):
      return self._thank_id
    
    id = self.key().id()

    if config.debug:
      log.debug('encode_thank_id: %d' % id)

    self._thank_id = urlsafe_b64encode(pack('<Q', id).rstrip('\x00')).replace('=', '.')
    return self._thank_id

  @classmethod
  def decode_thank_id(cls, thank_id):
    '''
    Decodes the thank id to the model's id
    
    Procedure is
     - Replaces period with original padding =,
     - Decodes with Base64-url-friendly,
     - Appends \\x00 to make the length of 8,
     - Unpacks with litten-endian long long.
    '''
    
    thank_id = str(thank_id)

    if config.debug:
      log.debug('decode_thank_id: %s' % thank_id)

    try:
      thank_id = urlsafe_b64decode(thank_id.replace('.', '='))
      id = unpack('<Q', thank_id + '\x00' * (8 - len(thank_id)))
    except:
      log.warning('Invalid thank_id: %s' % thank_id)
      return None

    if config.debug:
      log.debug('decoded id: %d' % id)

    return id

  @classmethod
  def get_by_thank_id(cls, thank_id):
    '''
    Returns model instance by the thank_id
    '''

    id = Thank.decode_thank_id(thank_id)
    if not id:
      return None

    return get(id)

  def create_link(self):

    thank_id = self.encode_thank_id()
    return '%st/%s' % (config.base_URI, thank_id)

  def create_tweet(self):
    
    link = self.create_link()
    return '%s %s' % (self.subject[:(140 - 1 - len(link))], link)


def _cache(thx):

  if not memcache.set('Thank_%d' % thx.key().id(), thx, config.thank_cache):
    log.error('Unable to cache Thank_%d' % thx.key().id())


def get(id):

  thx = memcache.get('Thank_%d' % id)
  if thx:
    return thx
  
  thx = Thank.get_by_id(id)
  if thx:
    return thx[0]
  else:
    log.warning('Thank %d is not in datastore' % id)
    return None


def get_random(count, language=None):
  '''
  It may return duplicate items
  '''

  if language:
    if language not in config.dict_valid_languages:
      log.warning('Invalid language: %s' % language)
      raise ValueError('Invalid language: %s' % language)
    counter_key = 'thank_%s' % language
  else:
    counter_key = 'thank'

  counter = Counter(counter_key).count
  log.debug('%s %d' % (counter_key, counter))
  rv = Random()
  q = Thank.all()
  if language:
    q.filter('language =', language)

  log.debug('x')
  random_items = []
  log.debug(len(random_items))
  log.debug(counter)
  while len(random_items) < counter:
    item = q.fetch(1, offset=int(rv.uniform(0, counter)))
    if item:
      # cache it
      _cache(item[0])
      random_items += item
 
  log.debug('x')
  log.debug(random_items)
  return random_items


def increase_count_t(language):
  '''
  Increase two counter thank_count and thank_{language}_count
  '''

  thank_count = Counter('thank')
  thank_count.increment()
  thank_language_count = Counter('thank_%s' % language)
  thank_language_count.increment()


@transaction
def add_t(name, language, subject, story):
  thx = Thank(name=name, language=language, subject=subject, story=story)
  thx.put()
  return thx


def add(name, language, subject, story):
  '''
  Adds a new Thank to datastore

  @return: The new thank or error message
  @rtype: Thank or str if error happens
  '''

  # Validate all properties
  if len(name) < config.thank_min_name:
    raise ValueError('Name must be longer than %d characters!' % config.thank_min_name)
  if len(name) > config.thank_max_name:
    log.warning('Name too long: %s' % name[:config.thank_max_name])
    raise ValueError('Name must be shorter than %d characters!' % config.thank_max_name)

  for lang in config.valid_languages:
    if lang[0] == language:
      break
  else:
    log.warning('Incorrect language: %s' % repr(language))
    raise ValueError('Incorrect language!')
    
  if len(subject) < config.thank_min_subject:
    raise ValueError('Subject must be longer than %d characters!' % config.thank_min_subject)
  if len(subject) > config.thank_max_subject:
    log.warning('Subject too long: %s' % subject[:config.thank_max_subject])
    raise ValueError('Subject must be shorter than %d characters!' % config.thank_max_subject)

  if len(story) < config.thank_min_story:
    raise ValueError('Story must be longer than %d characters!' % config.thank_min_story)
  if len(story) > config.thank_max_story:
    log.warning('Story too long: %d chars' % len(story))
    raise ValueError('Story must be shorter than %d characters!' % config.thank_max_story)

  # Run add transaction
  thx = add_t(name, language, subject, story)
  if thx:
    increase_count_t(language)
    _cache(thx)
    # Clean feed's cache
    memcache.delete_multi(['feed', 'feed_%s' % language])

  return thx

@transaction
def flag(id, flagger):
  # Load from datastore not memcache
  thx = Thank.get_by_id(id)
  if not thx:
    log.warning('%s tried to flag Thank %d' % (flagger, id))
    return
  thx.flaggers += [flagger]
  thx.flags = len(thx.flaggers)
  thx.put()
  # Cache it
  _cache(thx)
  return thx
