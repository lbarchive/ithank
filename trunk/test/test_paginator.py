import logging as log
import unittest

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.webapp import template

from ithank.paginator import Paginator


class NoMemcacheNoVersion(unittest.TestCase):

  def testNoEntities(self):

    wipe_test_data()

    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=2, max_pages=0, total_items=None, cache=None)

    self.assertEqual((
        None,
        None,
        None,
        ), pger.navigation_list)

  def testOneToNoEntities(self):

    wipe_test_data()
    create_data(1)

    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=None, cache=None)

    self.assertEqual((
        None,
        [1],
        None,
        ), pger.navigation_list)

    wipe_test_data()

    self.assertEqual((
        None,
        None,
        None,
        ), pger.navigation_list)
 
  def testOneToTwoPages(self):

    wipe_test_data()
    create_data(9)

    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=None, cache=None)

    self.assertEqual((
        None,
        [1],
        None,
        ), pger.navigation_list)
   
    create_data(1)
    
    self.assertEqual((
        None,
        [1],
        None,
        ), pger.navigation_list)

    create_data(1)
    
    self.assertEqual((
        None,
        [1, 2],
        2,
        ), pger.navigation_list)

  def testTwoToOnePage(self):

    wipe_test_data()
    create_data(11)

    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=None, cache=None)

    self.assertEqual((
        None,
        [1, 2],
        2,
        ), pger.navigation_list)
   
    delete_data(1)
    
    self.assertEqual((
        None,
        [1],
        None,
        ), pger.navigation_list)

    delete_data(1)
    
    self.assertEqual((
        None,
        [1],
        None,
        ), pger.navigation_list)


  def testOneToFivePagesCorrection(self):

    wipe_test_data()
    create_data(45)

    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=None, cache=None)

    self.assertEqual((
        None,
        [1, 2, 3],
        2,
        ), pger.navigation_list)
    self.assertEqual((
        None,
        [1, 2, 0, 4, 5],
        2,
        ), pger.navigation_list)
    self.assertEqual((
        None,
        [1, 2, 0, 4, 5],
        2,
        ), pger.navigation_list)

  def testToFivePagesCorrectionWithIncorrectTotalItems(self):

    wipe_test_data()
    create_data(45)

    # Incorrect total_items = 15 results 2 pages
    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=15, cache=None)

    self.assertEqual((
        None,
        [1, 2, 3, 4],
        2,
        ), pger.navigation_list)
    self.assertEqual((
        None,
        [1, 2, 0, 4, 5],
        2,
        ), pger.navigation_list)
    self.assertEqual((
        None,
        [1, 2, 0, 4, 5],
        2,
        ), pger.navigation_list)

  def testToOnePageCorrectionWithIncorrectTotalItems(self):

    wipe_test_data()
    create_data(5)

    # Incorrect total_items = 15 results 2 pages
    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=45, cache=None)

    self.assertEqual((
        None,
        [1, 2, 3],
        2,
        ), pger.navigation_list)
    self.assertEqual((
        None,
        [1],
        None,
        ), pger.navigation_list)
    self.assertEqual((
        None,
        [1],
        None,
        ), pger.navigation_list)


  def testBandsWithoutTotalItems(self):

    wipe_test_data()
    # 11 Pages
    create_data(110)

    # In page 7
    pger = Paginator('SELECT * FROM Data', page=7, page_items=10,
      page_band_expand=1, max_pages=0, total_items=None, cache=None)

    self.assertEqual((
        6,
        [1, 2, 0, 6, 7, 8, 9],
        8,
        ), pger.navigation_list)

    pger.page = 6
    
    self.assertEqual((
        5,
        [1, 2, 0, 5, 6, 7, 0, 10, 11],
        7,
        ), pger.navigation_list)

    # Doing exactly same as above should get same result since we don't enable
    # the cache.
    pger = Paginator('SELECT * FROM Data', page=7, page_items=10,
      page_band_expand=1, max_pages=0, total_items=None, cache=None)

    self.assertEqual((
        6,
        [1, 2, 0, 6, 7, 8, 9],
        8,
        ), pger.navigation_list)

    pger.page = 6
    
    self.assertEqual((
        5,
        [1, 2, 0, 5, 6, 7, 0, 10, 11],
        7,
        ), pger.navigation_list)

  def testBands(self):

    wipe_test_data()
    # 11 Pages
    create_data(110)

    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=110, cache=None)

    self.assertEqual((
        None,
        [1, 2, 0, 10, 11],
        2,
        ), pger.navigation_list)

    pger.page = 6
    
    self.assertEqual((
        5,
        [1, 2, 0, 5, 6, 7, 0, 10, 11],
        7,
        ), pger.navigation_list)

    pger.page = 9
    
    self.assertEqual((
        8,
        [1, 2, 0, 8, 9, 10, 11],
        10
        ), pger.navigation_list)

    pger.page = 10
    
    self.assertEqual((
        9,
        [1, 2, 0, 9, 10, 11],
        11,
        ), pger.navigation_list)

    pger.page = 11
    
    self.assertEqual((
        10,
        [1, 2, 0, 10, 11],
        None,
        ), pger.navigation_list)


class MemcacheNoVersion(unittest.TestCase):

  def testNoEntities(self):

    memcache.flush_all()

    wipe_test_data()

    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=2, max_pages=0, total_items=None, cache=0)

    self.assertEqual((
        None,
        None,
        None,
        ), pger.navigation_list)

  def testOneToNoEntities(self):

    memcache.flush_all()

    wipe_test_data()
    create_data(1)

    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=None, cache=0)

    self.assertEqual((
        None,
        [1],
        None,
        ), pger.navigation_list)

    wipe_test_data()

    self.assertEqual((
        None,
        [1],
        None,
        ), pger.navigation_list)
 
  def testOneToTwoPages(self):

    memcache.flush_all()

    wipe_test_data()
    create_data(9)

    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=None, cache=0)

    self.assertEqual((
        None,
        [1],
        None,
        ), pger.navigation_list)
   
    create_data(1)
    
    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=None, cache=0)

    self.assertEqual((
        None,
        [1],
        None,
        ), pger.navigation_list)

    create_data(1)
    
    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=None, cache=0)

    self.assertEqual((
        None,
        [1, 2],
        2,
        ), pger.navigation_list)

  def testTwoToOnePage(self):

    memcache.flush_all()

    wipe_test_data()
    create_data(11)

    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=None, cache=0)

    self.assertEqual((
        None,
        [1, 2],
        2,
        ), pger.navigation_list)
   
    delete_data(1)
    
    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=None, cache=0)

    self.assertEqual((
        None,
        [1, 2],
        2,
        ), pger.navigation_list)

    delete_data(1)
    
    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=None, cache=0)

    self.assertEqual((
        None,
        [1, 2],
        2,
        ), pger.navigation_list)

  def testOneToFivePagesCorrection(self):

    memcache.flush_all()

    wipe_test_data()
    create_data(45)

    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=None, cache=0)

    self.assertEqual((
        None,
        [1, 2, 3],
        2,
        ), pger.navigation_list)

    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=None, cache=0)

    self.assertEqual((
        None,
        [1, 2, 3, 4],
        2,
        ), pger.navigation_list)
    
    pger = Paginator('SELECT * FROM Data', page=3, page_items=10,
      page_band_expand=1, max_pages=0, total_items=None, cache=0)

    self.assertEqual((
        2,
        [1, 2, 3, 4, 5],
        4,
        ), pger.navigation_list)

  def testToFivePagesCorrectionWithIncorrectTotalItems(self):

    memcache.flush_all()

    wipe_test_data()
    create_data(45)

    # Incorrect total_items = 15 results 2 pages
    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=15, cache=0)

    self.assertEqual((
        None,
        [1, 2, 3, 4],
        2,
        ), pger.navigation_list)
    
    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
      page_band_expand=1, max_pages=0, total_items=15, cache=0)

    self.assertEqual((
        None,
        [1, 2, 0, 4, 5],
        2,
        ), pger.navigation_list)
    
    pger = Paginator('SELECT * FROM Data', page=3, page_items=10,
      page_band_expand=1, max_pages=0, total_items=15, cache=0)

    self.assertEqual((
        2,
        [1, 2, 3, 4, 5],
        4,
        ), pger.navigation_list)

  def testToOnePageCorrectionWithIncorrectTotalItems(self):

    memcache.flush_all()

    wipe_test_data()
    create_data(5)

    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
        page_band_expand=1, max_pages=0, total_items=45, cache=0)

    self.assertEqual((
        None,
        [1, 2, 3],
        2,
        ), pger.navigation_list)
 
    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
        page_band_expand=1, max_pages=0, total_items=45, cache=0)

    self.assertEqual((
        None,
        [1, 2],
        2,
        ), pger.navigation_list)
    
    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
        page_band_expand=1, max_pages=0, total_items=45, cache=0)

    self.assertEqual((
        None,
        [1],
        None,
        ), pger.navigation_list)


  def testBandsWithoutTotalItems(self):

    memcache.flush_all()

    wipe_test_data()
    # 11 Pages
    create_data(110)

    # In page 7
    pger = Paginator('SELECT * FROM Data', page=7, page_items=10,
        page_band_expand=1, max_pages=0, total_items=None, cache=0)

    self.assertEqual((
        6,
        [1, 2, 0, 6, 7, 8, 9],
        8,
        ), pger.navigation_list)

    pger.page = 6
    
    self.assertEqual((
        5,
        [1, 2, 0, 5, 6, 7, 0, 10, 11],
        7,
        ), pger.navigation_list)

    pger = Paginator('SELECT * FROM Data', page=7, page_items=10,
        page_band_expand=1, max_pages=0, total_items=None, cache=0)

    self.assertEqual((
        6,
        [1, 2, 0, 6, 7, 8, 0, 10, 11],
        8,
        ), pger.navigation_list)

    pger.page = 6
    
    self.assertEqual((
        5,
        [1, 2, 0, 5, 6, 7, 0, 10, 11],
        7,
        ), pger.navigation_list)

  def testBands(self):

    memcache.flush_all()

    wipe_test_data()
    # 11 Pages
    create_data(110)

    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
       page_band_expand=1, max_pages=0, total_items=110, cache=0)

    self.assertEqual((
        None,
        [1, 2, 0, 10, 11],
        2,
        ), pger.navigation_list)

    pger.page = 6
    
    self.assertEqual((
        5,
        [1, 2, 0, 5, 6, 7, 0, 10, 11],
        7,
        ), pger.navigation_list)

    pger.page = 9
    
    self.assertEqual((
        8,
        [1, 2, 0, 8, 9, 10, 11],
        10
        ), pger.navigation_list)

    pger.page = 10
    
    self.assertEqual((
        9,
        [1, 2, 0, 9, 10, 11],
        11,
        ), pger.navigation_list)

    pger.page = 11
    
    self.assertEqual((
        10,
        [1, 2, 0, 10, 11],
        None,
        ), pger.navigation_list)


class MemcacheVersion(unittest.TestCase):

  def testOneToTwoPages(self):

    memcache.flush_all()

    wipe_test_data()
    create_data(9)

    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
        page_band_expand=1, max_pages=0, total_items=None, cache=0,
        cache_version='9')

    self.assertEqual((
        None,
        [1],
        None,
        ), pger.navigation_list)
   
    create_data(1)
    
    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
        page_band_expand=1, max_pages=0, total_items=None, cache=0,
        cache_version='10')

    self.assertEqual((
        None,
        [1],
        None,
        ), pger.navigation_list)

    create_data(1)
    
    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
        page_band_expand=1, max_pages=0, total_items=None, cache=0,
        cache_version='11')

    self.assertEqual((
        None,
        [1, 2],
        2,
        ), pger.navigation_list)

  def testTwoToOnePage(self):

    memcache.flush_all()

    wipe_test_data()
    create_data(11)

    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
        page_band_expand=1, max_pages=0, total_items=None, cache=0,
        cache_version='11')

    self.assertEqual((
        None,
        [1, 2],
        2,
        ), pger.navigation_list)
   
    delete_data(1)
    
    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
        page_band_expand=1, max_pages=0, total_items=None, cache=0,
        cache_version='10')

    self.assertEqual((
        None,
        [1],
        None,
        ), pger.navigation_list)

    delete_data(1)
    
    pger = Paginator('SELECT * FROM Data', page=1, page_items=10,
        page_band_expand=1, max_pages=0, total_items=None, cache=0,
        cache_version='9')

    self.assertEqual((
        None,
        [1],
        None,
        ), pger.navigation_list)


# Utilities and Helpers
# =====================

class Data(db.Model):
  name = db.StringProperty()


def wipe_test_data():

  log.debug('Started to wipe test data.')
  while True:
    models = Data.all().fetch(1000)
    if models:
      db.delete(models)
    else:
      break
  log.debug('All data has been wiped.')


def create_data(count):

  log.debug('Started to create test data.')
  for i in range(count):
    model = Data(name='%d' % i)
    model.put()
  log.debug('%d entities created.' % count)


def delete_data(count):

  log.debug('Started to delete test data.')
  del_count = 0
  while del_count < count:
    if del_count < count - 1000:
      models = Data.all().fetch(1000)
      del_count += 1000
    else:
      models = Data.all().fetch(count - del_count)
      del_count = count
    db.delete(models)
  log.debug('%d entities created.' % count)



