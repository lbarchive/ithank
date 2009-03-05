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
import simple24 as s24


class StatsPage(I18NRequestHandler):

  def get(self):
    
    template_values = {
        'config': config,
        'thanks': Counter('thank').count,
        'thanks_added': s24.get_count('thanks_added'),
        'thanks_added_chart': s24.get_chart_uri('thanks_added'),
        'feed_reqs': s24.get_count('feed'),
        'feed_reqs_chart': s24.get_chart_uri('feed'),
        'API_random_txt_reqs': s24.get_count('random.txt'),
        'API_random_txt_reqs_chart': s24.get_chart_uri('random.txt'),
        'API_random_json_reqs': s24.get_count('random.json'),
        'API_random_json_reqs_chart': s24.get_chart_uri('random.json'),
        }
    set_topbar_vars(template_values, self.request.url)
    path = os.path.join(os.path.dirname(__file__), 'template/stats.html')
    self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication([
    ('/stats/?', StatsPage),
    ],
    debug=config.debug)


def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
