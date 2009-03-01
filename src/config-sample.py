import os

debug = True

# Cache
browse_page_cache = 3600
feed_cache = 3600
thank_cache = 86400

# Template
before_head_end = ''''''
after_footer = ''''''
before_body_end = ''''''

# Thank
thank_min_name = 3
thank_max_name = 50
thank_min_subject = 5
thank_max_subject = 100
thank_min_story = 100
thank_max_story = 4000

thanks_per_page = 10
thanks_max_pages = 100

thanks_random_max_items = 1

thanks_feed_items = 100

# Valid language to submit
valid_languages = (
    # 'en', 'zh_TW' should match the directories in conf/locale/*
    ('en', _('English')),  
#    ('zh_TW', _('Chinese')),
    )

dict_valid_languages = dict(valid_languages)


# Should not edit settings below
################################

# Under development server?
dev = os.environ['SERVER_SOFTWARE'].startswith('Development')

# Base URI
if dev:
  base_URI = 'http://localhost:8080/'
else:
  base_URI = 'http://%s.appspot.com/' % os.environ['APPLICATION_ID']

# Application version
app_version = os.environ['CURRENT_VERSION_ID']
