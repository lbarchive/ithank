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
from ithank.util import I18NRequestHandler, json_error, send_json, set_topbar_vars
import config
import ithank


class AdminPage(I18NRequestHandler):

  def get(self):
 
    q = thank.Thank.all()
    q.filter('flags >', 0)
    q.order('-flags')
    thanks = q.fetch(10)
    for thx in thanks:
      # Has to make sure variables in {% blocktrans %} is type str, or this
      # error:
      # UnicodeDecodeError: 'ascii' codec can't decode byte 0xc2 in position 1: ordinal not in range(128)
      thx.name = thx.name.encode('utf-8')

    template_values = {
        'config': config,
        'thanks': thanks
        }
    set_topbar_vars(template_values, self.request.url)
    path = os.path.join(os.path.dirname(__file__), 'template/admin.html')
    self.response.out.write(template.render(path, template_values))

  def head(self):

    pass


class DeleteJSON(I18NRequestHandler):

  def get(self):

    callback = self.request.get('callback') 
    thank_id = self.request.get('thank_id') 
    if thank_id == '':
      json_error(self.response, ithank.ERROR_INVALID_THANK_ID, callback)
      return
    
    # Must log in
    if not users.is_current_user_admin():
      log.warning('Admin login required')
      json_error(self.respoonse, ithank.ERROR_ADMIN_LOGIN_REQUIRED, callback)
      return

    thx = thank.Thank.get_by_thank_id(thank_id)
    if not thx:
      log.warning('Non-existing thank requested: %s' % thank_id)
      json_error(self.response, ithank.ERROR_INVALID_THANK_ID, callback)
      return

    # Begin to delete
    Counter('thank').increment(-1)
    Counter('thank_%s' % thx.language).increment(-1)
    thx.delete()
    log.info('Thank %s has been deleted' % thank_id)

    send_json(self.response, {'delete_msg': _('Deleted'), 'thank_id': thank_id}, callback)


application = webapp.WSGIApplication([
    ('/admin/', AdminPage),
    (r'/admin/delete\.json', DeleteJSON),
    ],
    debug=config.debug)


def main():
  """Main function"""
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
