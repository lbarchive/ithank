class Paginator:
  '''
  Handles querying, pages caching.
  '''

  def __init__(self, GQL_query, page_no=1, page_items=10, max_pages=0,
      total_items=None, no_cache=False):
    '''
    GQL_query must not include LIMIT and OFFSET
    '''

  def create_nav_list(self):
    pass
