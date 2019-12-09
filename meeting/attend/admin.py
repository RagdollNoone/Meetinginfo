from django.contrib import admin

# Register your models here.
from attend.models import Group, Events, Attendees, Room, User


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('Id','Groupname')
    fields = ('Id','Groupname')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('Id','Openid','Address','Name','Group')
    fields = ('Id','Openid','Address','Name','Group')

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('Id','Meetingroom')
    fields = ('Id','Meetingroom')

@admin.register(Attendees)
class AttendeesAdmin(admin.ModelAdmin):
    list_display = ('Id','Eventid','Name','Address','Isattend','Meetingtime','Attendtime')
    fields = ('Id','Eventid','Name','Address','Isattend','Meetingtime','Attendtime')

@admin.register(Events)
class EventsAdmin(admin.ModelAdmin):
    list_display = ('Id','Subject','Organizer','Organizeraddress','Start','End','Location')
    fields = ('Id','Subject','Organizer','Organizeraddress','Start','End','Location')