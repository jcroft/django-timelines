from django.contrib import admin

from timelines.models import UserTimelineItem

class UserTimelineItemAdmin(admin.ModelAdmin):
  list_display    = ('__unicode__','user','content_type','timestamp')

admin.site.register(UserTimelineItem, UserTimelineItemAdmin)