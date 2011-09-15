import datetime

from django.conf import settings
from django.db import models
from django.db.models import signals
from django.contrib.contenttypes.models import ContentType

class UserTimelineItemManager(models.Manager):
    
    def __init__(self):
      super(models.Manager, self).__init__()
      self._set_creation_counter()
      self.model = None
      self._inherited = False
      self._db = None
      self.models_by_name = {}
        
    def remove_orphans(self, instance, **kwargs):
      """
      When an item is deleted, first delete any UserTimelineItem object that has been created
      on its behalf.
      """
      from timelines.models import UserTimelineItem
      try:
        instance_content_type = ContentType.objects.get_for_model(instance)
        timeline_item = UserTimelineItem.objects.get(content_type=instance_content_type, object_id=instance.pk)
        timeline_item.delete()
      except UserTimelineItem.DoesNotExist:
        return
    
    def create_or_update(self, instance, timestamp=None, **kwargs):
        """
        Create or update a UserTimelineItem from some instance.
        """

        from timelines.models import UserTimelineItem
        # If the instance hasn't already been saved, save it first.
        if instance._get_pk_val() is None:
          try:
            signals.post_save.disconnect(self.create_or_update, sender=type(instance))
          except:
            reconnect = False
          else:
            reconnect = True
          instance.save()
          if reconnect:
            signals.post_save.connect(self.create_or_update, sender=type(instance))

        # Find this object's content type and model class.
        instance_content_type = ContentType.objects.get_for_model(instance)
        instance_model        = instance_content_type.model_class()

        # Look at the TIMELINES_MODELS list in settings.py. It identifies which models
        # should be included in the timeline, as well as what user field, date field and manager
        # we should use for each one.
        for item in settings.TIMELINES_MODELS:
          this_app_label        = item['model'].split('.')[0]
          this_model_label      = item['model'].split('.')[1]
          this_content_type     = ContentType.objects.get(app_label=this_app_label, model=this_model_label)
          this_model            = this_content_type.model_class()
          
          if this_content_type == instance_content_type:
            try:
              manager         = item['manager']
            except:
              manager         = 'objects'
            try:
              timestamp_field = item['date_field']
            except:
              timestamp_field = 'date_published'
            try:
              user_field = item['user_field']
            except:
              user_field = 'user'
        
        # Make sure the item "should" be registered. This is based on the manager argument.
        # If InstanceModel.manager.all() includes this item, then it should be registered.
        # Otherwise, just return and don't add a UserTimelineItem for this object.
        # If we find that it should NOT be registered, check to make sure we haven't already
        # registered this object in the past. If so, delete it.
        try:
            instance_exists = getattr(instance_model, manager).get(pk=instance.pk)
        except instance_model.DoesNotExist:
            try:
              orphaned_timeline_item = UserTimelineItem.objects.get(content_type=instance_content_type, object_id=instance._get_pk_val(),)
              orphaned_timeline_item.delete()
              return
            except UserTimelineItem.DoesNotExist:
              return
        
        # Pull the timestamp from the instance, using the timestamp_field argument.
        timestamp_field_list = timestamp_field.split(".")
        index = 0
        this_instance = instance
        if len(timestamp_field_list) > 0:
          for item in timestamp_field_list:
            if hasattr(this_instance, timestamp_field_list[index]):
              timestamp = getattr(this_instance, timestamp_field_list[index])
              this_instance = timestamp
              index = index + 1
        else:
          if hasattr(this_instance, timestamp_field):
            timestamp = getattr(item, timestamp_field)
        
        # Pull the user from the instance, using the user_field argument.
        if hasattr(instance, user_field):
            user = getattr(instance, user_field)
        
        if user and timestamp and instance:
          # Create the UserTimelineItem object.
          instance_content_type = ContentType.objects.get_for_model(instance)
          timeline_item, created = self.get_or_create(
              user = user,
              content_type = instance_content_type, 
              object_id = instance._get_pk_val(),
              defaults = dict(
                timestamp = timestamp,
              )
          )
          timeline_item.timestamp = timestamp
          # Save and return the item.
          timeline_item.save()
          return timeline_item
        
    def follow_model(self, model):
        """
        Follow a particular model class, updating associated UserTimelineItems automatically.
        """
        if model:
          self.models_by_name[model.__name__.lower()] = model
          signals.post_save.connect(self.create_or_update, sender=model)
          signals.post_delete.connect(self.remove_orphans, sender=model)
        
    def get_for_model(self, model):
        """
        Return a QuerySet of only items of a certain type.
        """
        return self.filter(content_type=ContentType.objects.get_for_model(model))
        
    def get_last_update_of_model(self, model, **kwargs):
        """
        Return the last time a given model's items were updated. Returns the
        epoch if the items were never updated.
        """
        qs = self.get_for_model(model)
        if kwargs:
            qs = qs.filter(**kwargs)
        try:
            return qs.order_by('-timestamp')[0].timestamp
        except IndexError:
            return datetime.datetime.fromtimestamp(0)