from math import ceil
from md5 import md5
import logging as log

from google.appengine.api import memcache
from google.appengine.ext import db

from ithank.util import property
import config


PAGINATOR_KEY = 'Paginator'


class Paginator(object):
  '''
  Handles querying, pages caching.
  '''

  def __init__(self, query,
      page=1, page_items=10, page_band_expand=2,
      max_pages=0, total_items=None,
      cache=300, cache_version=''):
    '''
    @param query: The datastore query string, it must not include LIMIT and
        OFFSET.
    @type query: str
    @param page: A 1-based page number, set None if don't want to set up while
        initialization.
    @type page: int or None
    @param page_items: The amount of items (entities) in one page.
    @type page_items: int
    @param page_band_expand:
    @type page_band_expand: int
    @param max_pages: Upper page number cap. Set to 0 or None for unlimited
        pages.
    @type max_pages: int or None
    @param total_items: The total count of items. This is helpful for calculate
        the last page number. Paginator is aware of the possible inaccurate of
        this parameter since Google App Engine doesn't provide precise of
        record (row, entity) counts. Paginator will try to adjust every time it
        tries to query.

        If cache is on and returns KEY_last_page, it will use it, not decide by
        this total_items / page_items.

        If cache is off and total_items sets to 0 or None, Paginator will use
        page or set to 1 if page is not given.
    @type total_items: int or None
    @param cache: If cache is type int, it represent the cache time in secods,
        0 means caching as long as possible. If cache is None, it means caching
        is off.
    @type cache: int, bool
    @param cache_version: When Paginator caches pages, it also append this to
        the key of memcache.
    @type cache_version: str
    '''

    if 'LIMIT' in query or 'OFFSET' in query:
      raise ValueError('LIMIT and/or OFFSET is not allowed being used in Paginator.')

    self._query = query
    self._page_band_expand = page_band_expand
    self._page_items = page_items
    self._max_pages = max_pages
    self._cache = cache

    # Set the current page
    self.page = page

    # Decide the last_page
    if total_items:
      last_page = int(ceil(total_items / float(page_items)))
    elif page:
      last_page = page
    else:
      last_page = 1
    if page > last_page:
      last_page = page

    if cache is not None:
      self._query_hash = md5(query).hexdigest()
      self._mem_key = '%s_%s' % (PAGINATOR_KEY, self._query_hash)
      # Try to retrieve last_page from memcache
      _last_page = memcache.get('%s_last_page' % self._mem_key)
      if _last_page is not None:
        last_page = _last_page

      self._cache_version = cache_version

    self.last_page = last_page

  @property
  def query(self):

    return self._query

  @property
  def page(self):
    
    return self._page

  @page.setter
  def page(self, page=1):
    
    if self.max_pages != 0 and page > self.max_pages:
      self._page = self.max_pages
    else:
      self._page = page

  @property
  def page_band_expand(self):
    
    return self._page_band_expand

  @property
  def max_pages(self):
    
    return self._max_pages

  @property
  def cache(self):

    return self._cache

  @property
  def cache_version(self):

    return self._cache_version

  @property
  def page_items(self):
    '''
    Returns how many items in a page.
    '''

    return self._page_items

  def get_page_items(self, page):
    '''
    Returns items of given page

    If page is 0 or None, it returns None directly.
    '''
    
    if not page:
      return None

    # Try cache first
    if self.cache is not None:
      models = memcache.get('%s_%s_page_%d' % (self._mem_key, self.cache_version, page))
      if models:
        return models

    # Nothing from cache or cache is off
    q = db.GqlQuery(self.query)
    models = q.fetch(self.page_items, (page - 1) * self.page_items)
    # Store it to cache
    if self.cache is not None and models:
      if not memcache.set('%s_%s_page_%d' % (self._mem_key, self.cache_version, page), models):
        log.error('Unable to set %s_%s_page_%d' % (self._mem_key, self.cache_version, page))
    return models

  @property
  def items(self):
    '''
    Returns items of current page.

    Returns None if self.page is 0 or None, or Paginator gets nothing from
    datastore query.

    If query returns no entities, then it will set the self.last_page to
    self.page - 1, even there was no total_items set while
    initialization.
    '''

    return self.get_page_items(self.page)

  @property
  def first_page(self):
    '''
    Returns 1 if there is at least one entity from datastore or it returns
    None.

    If no entities, it also sets self.last_page to 0.
    '''

    if self.get_page_items(1):
      return 1
    return None

  @property
  def prev_page(self):
    '''
    Returns previous page number if there are entities from query of previous
    page or it returns None.
    '''
    
    if self.page > 1:
      return self.page - 1
    return None

  @property
  def next_page(self):
    '''
    Returns next page number if there are entities from query of next page or
    it returns None.
    '''

    if self.page < self.last_page:
      return self.page + 1
    return None

  @property
  def last_page(self):
    '''
    Returns last page number if self._last_page is set and there are entities
    from query.

    Returns None if unable to decide the last page.

    Auto adjust 
    '''

    _last_page = self._last_page
    # Cap the self._last_page
    if self.max_pages and _last_page > self.max_pages:
      self._last_page = self.max_pages 
    if self.get_page_items(self._last_page):
      # If _last_page != max_pages, that means max_pages == 0 or _last_page has
      # not reached max_pages.
      if self._last_page != self.max_pages and \
          self.get_page_items(self._last_page + 1):
        # It has one more page at least
        self._last_page = self._last_page + 1
    else:
      # Auto adjust but not validate if the self._last_page - 1 does have
      # entities or not.
      self._last_page = self._last_page - 1
    
    if _last_page != self._last_page and self.cache is not None:
      # last_page has been updated
      if not memcache.set('%s_last_page' % self._mem_key, _last_page):
        log.error('Unable to set %_last_page to %d' % (
            self._mem_key, _last_page, self.cache))

    return self._last_page

  @last_page.setter
  def last_page(self, last_page):
    '''
    Sets the last page number.

    If self.cache is enabled, then it will also write the value to memcache.

    It does not auto adjust
    '''

    if last_page >= 0:
      self._last_page = last_page
#       self._last_page = last_page
#     if self.get_page_items(last_page):
#       self._last_page = last_page
#     else:
#       self._last_page = last_page - 1

#   @property
#   def backward_list(self):

  @property
  def navigation_list(self):
    '''
    Each call on naviagtion_list() can correct last_page by 2 at most.

    page_band_expand is 1:
      No entities in datastore:
      None
      Current page 2, 3 pages total:
      [1, 2, 3]
      Current page 2, 6 pages total:
      [1, 2, 3, 0, 5, 6]
      Current page 3, 12 pages total:
      [1, 2, 3, 4, 0, 11, 12]
      Current page 11, 21 pages total:
      [1, 2, 0, 10, 11, 12, 0, 20, 21]

    The return value is a 3-tuple:
      (previous page number, naviation list, next page number)
    If current page is the first page, then previous page number is None;
    if current page is the last page, then next page number is None.
    '''

    f = self.first_page
    if not f:
      # No entities in datastore
      return (None, None, None)

    p = self.prev_page
    n = self.next_page
    l = self.last_page
    if n > l:
      # n corrects one time, l does another time, therefore it's possible n >
      # l.
      n = l
    if n == 1:
      n = None
    c = self.page
    
    if not l:
      # If no last page number available, then use current page as last page
      # number.
      l = c
    
    expand = self.page_band_expand

    f_band = range(1, min(l, f + expand) + 1)
    c_band = range(max(1, c - expand), min(l, c + expand) + 1)
    l_band = range(max(1, l - expand), l + 1)

    def band_merger(lower, upper):
      lower = list(lower)
      upper = list(upper)

      if upper[0] > lower[-1] + 1:
        # There is a gap between f_band and c_band
        lower += [0] + upper
      else:
        # Need to merge them
        for page in upper:
          if page not in lower:
            lower += [page]

      return lower

    nav = band_merger(f_band, c_band)
    nav = band_merger(nav, l_band)

    return (p, nav, n)

#   @property
#   def forward_list(self):

