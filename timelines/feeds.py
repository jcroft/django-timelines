import datetime
import time

from django.conf import settings
from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import *

from timelines import UserTimelineItem

site = Site.objects.get(id=settings.SITE_ID)
site_url = "http://%s/" % site.domain

class LatestUserTimelineItems(Feed):
  """ A feed of the latest UserTimelineItem objects added to the site. """

  title_template = 'timelines/feeds/item_title.html'
  description_template = 'timelines/feeds/item_description.html'

  title = "%s: Newest timeline items" % site.name
  link = site_url
  description = "The latest timeline items added at %s" % site.name

  def items(self):
    return UserTimelineItem.objects.all().order_by('-timestamp')[:15]

  def item_pubdate(self, item):
      return item.timestamp

  def item_author_name(self, item):
    try:
      # Attempt to use Savoy's profile name, first.
      return item.user.profile.name.encode("utf-8")
    except:
      # If Savoy's profile app isn't present, just use username
      return item.user.username.encode("utf-8")

  item_author_email = ""

  def item_link(self, item):
    try:
      return item.get_absolute_url()
    except:
      return ""

  def item_author_link(self, item):
    try:
      # Try to return Savoy's profile app's user profile, first
      return item.user.profile.get_absolute_url()
    except:
      # If Savoy's profile app isn't present, just return None
      return None
      
class LatestUserTimelineItemsPerUser(Feed):
  """ A feed of the latest UserTimelineItem objects added to the site by a particular user. """

  title_template = 'timelines/feeds/item_title.html'
  description_template = 'timelines/feeds/item_description.html'

  link = site_url
  description = "The latest timeline items added at %s" % site.name

  def get_object(self, bits):
    username = bits[0]
    try:
      return User.objects.get(username=username)
    except ValueError:
        raise FeedDoesNotExist

  def title(self, obj):
    try:
      # If Savoy's profile app is installed, use the profile name.
      return "%s: Activity for %s" % (site.name, obj.profile.name.encode("utf-8"))
    except:
      # If not, just use the username
      return "%s: Activity for %s" % (site.name, obj.username)

  def items(self, obj):
    return UserTimelineItem.objects.filter(user=obj)[:15]

  def item_pubdate(self, item):
      return item.timestamp

  def item_author_name(self, item):
    try:
      return item.user.profile.name.encode("utf-8")
    except:
      return item.user.username

  def item_link(self, item):
    try:
      return item.get_absolute_url()
    except:
      return ""

  def item_author_email(self, item):
    return ""

  def item_author_link(self, item):
    try:
      # Try to return Savoy's profile app's user profile, first
      return item.user.profile.get_absolute_url()
    except:
      # If Savoy's profile app isn't present, just return None
      return None