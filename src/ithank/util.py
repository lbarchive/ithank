from Cookie import BaseCookie
import simplejson as json
import logging
import os
import sys
import UserDict

from google.appengine.ext import db
from google.appengine.ext import webapp

from django.utils import translation

import config


# Base on http://appengine-cookbook.appspot.com/recipe/decorator-to-getset-from-the-memcache-automatically/
def cache(key, time=60):
  def decorator(fxn):
    def wrapper(*args, **kwargs):
      key = keyformat % args[0:keyformat.count('%')]
      data = memcache.get(key)
      if data is not None:
        return data
      data = fxn(*args, **kwargs)
      memcache.set(key, data, time)
      return data
    return wrapper
  return decorator if not settings.DEBUG else fxn


# http://appengine-cookbook.appspot.com/recipe/define-a-decorator-for-transactions/
def transaction(method):
  def decorate(*args, **kwds):
    return db.run_in_transaction(method, *args, **kwds)
  return decorate


# http://appengine-cookbook.appspot.com/recipe/a-simple-cookie-class/
class Cookies(UserDict.DictMixin):
    def __init__(self,handler,**policy):
        self.response = handler.response
        self._in = handler.request.cookies
        self.policy = policy
        if 'secure' not in policy and handler.request.environ.get('HTTPS', '').lower() in ['on', 'true']:
            policy['secure']=True
        self._out = {}
    def __getitem__(self, key):
        if key in self._out:
            return self._out[key]
        if key in self._in:
            return self._in[key]
        raise KeyError(key)
    def __setitem__(self, key, item):
        self._out[key] = item
        self.set_cookie(key, item, **self.policy)
    def __contains__(self, key):
        return key in self._in or key in self._out
    def keys(self):
        return self._in.keys() + self._out.keys()
    def __delitem__(self, key):
        if key in self._out:
            del self._out[key]
            self.unset_cookie(key)
        if key in self._in:
            del self._in[key]
            p = {}
            if 'path' in self.policy: p['path'] = self.policy['path']
            if 'domain' in self.policy: p['domain'] = self.policy['domain']
            self.delete_cookie(key, **p)
    #begin WebOb functions
    def set_cookie(self, key, value='', max_age=None,
                   path='/', domain=None, secure=None, httponly=False,
                   version=None, comment=None):
        """
        Set (add) a cookie for the response
        """
        cookies = BaseCookie()
        cookies[key] = value
        for var_name, var_value in [
            ('max-age', max_age),
            ('path', path),
            ('domain', domain),
            ('secure', secure),
            ('HttpOnly', httponly),
            ('version', version),
            ('comment', comment),
            ]:
            if var_value is not None and var_value is not False:
                cookies[key][var_name] = str(var_value)
            if max_age is not None:
                cookies[key]['expires'] = max_age
        header_value = cookies[key].output(header='').lstrip()
        self.response.headers._headers.append(('Set-Cookie', header_value))
    def delete_cookie(self, key, path='/', domain=None):
        """
        Delete a cookie from the client.  Note that path and domain must match
        how the cookie was originally set.
        This sets the cookie to the empty string, and max_age=0 so
        that it should expire immediately.
        """
        self.set_cookie(key, '', path=path, domain=domain,
                        max_age=0)
    def unset_cookie(self, key):
        """
        Unset a cookie with the given name (remove it from the
        response).  If there are multiple cookies (e.g., two cookies
        with the same name and different paths or domains), all such
        cookies will be deleted.
        """
        existing = self.response.headers.get_all('Set-Cookie')
        if not existing:
            raise KeyError(
                "No cookies at all have been set")
        del self.response.headers['Set-Cookie']
        found = False
        for header in existing:
            cookies = BaseCookie()
            cookies.load(header)
            if key in cookies:
                found = True
                del cookies[key]
            header = cookies.output(header='').lstrip()
            if header:
                self.response.headers.add('Set-Cookie', header)
        if not found:
            raise KeyError(
                "No cookie has been set with the name %r" % key)
    #end WebOb functions


class I18NRequestHandler(webapp.RequestHandler):

  def initialize(self, request, response):

    webapp.RequestHandler.initialize(self, request, response)

    self.request.COOKIES = Cookies(self)
    self.request.META = os.environ
    self.reset_language()

  def reset_language(self):

    # Decide the language from Cookies/Headers
    language = translation.get_language_from_request(self.request)
    translation.activate(language)
    self.request.LANGUAGE_CODE = translation.get_language()

    # Set headers in response
    self.response.headers['Content-Language'] = translation.get_language()
#    translation.deactivate()

# For Python 2.5-, this will enable the simliar property mechanism as in
# Python 2.6+/3.0+. The code is based on
# http://bruynooghe.blogspot.com/2008/04/xsetter-syntax-in-python-25.html
if sys.version_info[:2] <= (2, 5):
  class property(property):

      def __init__(self, fget, *args, **kwargs):

          self.__doc__ = fget.__doc__
          super(property, self).__init__(fget, *args, **kwargs)

      def setter(self, fset):

          cls_ns = sys._getframe(1).f_locals
          for k, v in cls_ns.iteritems():
              if v == self:
                  propname = k
                  break
          cls_ns[propname] = property(self.fget, fset,
                                      self.fdel, self.__doc__)
          return cls_ns[propname]

      def deleter(self, fdel):

          cls_ns = sys._getframe(1).f_locals
          for k, v in cls_ns.iteritems():
              if v == self:
                  propname = k
                  break
          cls_ns[propname] = property(self.fget, self.fset,
                                      fdel, self.__doc__)
          return cls_ns[propname]


def send_json(response, obj, callback, error=False):
  """Sends JSON to client-side"""
  json_result = obj
  if isinstance(obj, (str, unicode)):
    json_result = json.loads(obj)
  if not error:
    json_result['err'] = 0
  json_result = json.dumps(obj)
 
  response.headers['Content-Type'] = 'application/json'
  if callback:
    response.out.write('%s(%s)' % (callback, json_result))
  else:
    response.out.write(json_result)


def json_error(response, err, callback, err_msg=''):
  """Sends error in JSON to client-side
  """
  if err_msg == '':
    errors = {
      1: _('Invalid thank_id'),
      2: _('Login required'),
      3: _('Invalid language'),
      }
    err_msg = errors[err]

  send_json(response, {'err': err, 'err_msg': err_msg}, callback, True)

