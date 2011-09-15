from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from timelines.models import UserTimelineItem

for item in settings.TIMELINES_MODELS:
  try:
    app_label     = item['model'].split('.')[0]
    model         = item['model'].split('.')[1]
    content_type  = ContentType.objects.get(app_label=app_label, model=model)
    model         = content_type.model_class()
    UserTimelineItem.objects.follow_model(model)
  except ContentType.DoesNotExist:
    pass