from django.db import models
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from timelines.managers import UserTimelineItemManager

class UserTimelineItem(models.Model):
  user                = models.ForeignKey(User, related_name="timeline_items")
  content_type        = models.ForeignKey(ContentType)
  object_id           = models.PositiveIntegerField()
  content_object      = GenericForeignKey()
  timestamp           = models.DateTimeField()

  objects             = UserTimelineItemManager()
  
  def __unicode__(self):
    return "%s: %s" % (self.content_type.model_class().__name__, unicode(self.content_object))
  
  def get_absolute_url(self):
    """ Call the get_absolute_url() method of this ContentItem's content object. """
    return self.content_object.get_absolute_url()
  
  def save(self, *args, **kwargs):
    super(UserTimelineItem, self).save(*args, **kwargs)
    
  class Meta:
    ordering          = ['-timestamp']
    unique_together   = [('content_type', 'object_id')]
    get_latest_by     = 'timestamp'
