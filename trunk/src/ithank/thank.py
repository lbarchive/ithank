
from base64 import urlsafe_b64encode, urlsafe_b64decode
from md5 import md5
from os import urandom
from struct import pack, unpack
from time import time
import logging

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
  flagers = db.ListProperty(users.User, verbose_name='Flagers')

  def encode_thank_id(self):
    '''
    Encodes model's id to a url-friendly string

    Procedure is
     - Packs with litten-endian long long,
     - Strips tailing \\x00 bytes,
     - Encodes with Base64-url-friendly,
     - Replaces padding = with period.
    '''

    id = self.key().id()

    if config.debug:
      logging.debug('encode_thank_id: %d' % id)

    return urlsafe_b64encode(pack('<Q', id).rstrip('\x00')).replace('=', '.')

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

    if config.debug:
      logging.debug('decode_thank_id: %s' % thank_id)

    try:
      thank_id = urlsafe_b64decode(thank_id.replace('.', '='))
      id = unpack('<Q', thank_id + '\x00' * (8 - len(thank_id)))
    except:
      logging.warning('Invalid thank_id: %s' % thank_id)
      return None

    if config.debug:
      logging.debug('decoded id: %d' % id)

    return id

  @classmethod
  def get_by_thank_id(cls, thank_id):
    '''
    Returns model instance by the thank_id
    '''

    id = Thank.decode_thank_id(thank_id)
    if not id:
      return None

    thx = Thank.get_by_id(id)
    if len(thx) == 1:
      return thx[0]
    return None

  def create_link(self):

    thank_id = self.encode_thank_id()
    return '%st/%s' % (config.base_URI, thank_id)

  def create_tweet(self):
    
    link = self.create_link()
    return '%s %s' % (self.subject[:(140 - 1 - len(link))], link)


def generate_unique_key_name(user=None):
  '''
  Generates unique key_name by User, current time, and 128 bits radnom number.

  @param user: If None, it will try to get current user.
  @return: A 12 bytes string with 't' prefixing.
  @rtype: str
  '''

  if not user:
    user = users.get_current_user()
    #FIXME if the user isn't logged in
    # Raise not login

  m = md5(str(time.time()) + urandom(8) + user.email())
  return 't' + urlsafe_b64encode(m.digest())[:12]


@transaction
def add_t(name, language, subject, story):
#  thx = Thank(key_name=generate_unique_key_name(), name=name,
#      language=language, subject=subject, story=story)
  thx = Thank(name=name, language=language, subject=subject, story=story)
  thx.put()
  return thx


#@transaction
def increase_count_t(language):
  '''
  Increase two counter thank_count and thank_{language}_count
  '''

  logging.debug('Increase counter thank and thank_%s' % language)
  thank_count = Counter('thank')
  thank_count.increment()
  thank_language_count = Counter('thank_%s' % language)
  thank_language_count.increment()


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
    logging.warning('Name too long: %s' % name[:config.thank_max_name])
    raise ValueError('Name must be shorter than %d characters!' % config.thank_max_name)

  for lang in config.valid_languages:
    if lang[0] == language:
      break
  else:
    logging.warning('Incorrect language: %s' % repr(language))
    raise ValueError('Incorrect language!')
    
  if len(subject) < config.thank_min_subject:
    raise ValueError('Subject must be longer than %d characters!' % config.thank_min_subject)
  if len(subject) > config.thank_max_subject:
    logging.warning('Subject too long: %s' % subject[:config.thank_max_subject])
    raise ValueError('Subject must be shorter than %d characters!' % config.thank_max_subject)

  if len(story) < config.thank_min_story:
    raise ValueError('Story must be longer than %d characters!' % config.thank_min_story)
  if len(story) > config.thank_max_story:
    logging.warning('Story too long: %d chars' % len(story))
    raise ValueError('Story must be shorter than %d characters!' % config.thank_max_story)

  # Run add transaction
  thx = add_t(name, language, subject, story)
  if thx:
    increase_count_t(language)

  return thx
