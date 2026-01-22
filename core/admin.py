from django.contrib import admin

# Register your models here.
# core/admin.py
from django.contrib import admin
from .models import Branch, Section, ProctorProfile, StudentProfile, AttendanceRecord, MarksRecord, MeetingRecord,HelpMessage,BroadcastMessage,HODProfile

admin.site.register(Branch)
admin.site.register(Section)
admin.site.register(ProctorProfile)
admin.site.register(StudentProfile)
admin.site.register(AttendanceRecord)
admin.site.register(MarksRecord)
admin.site.register(MeetingRecord)
admin.site.register(HelpMessage)
admin.site.register(BroadcastMessage)



@admin.register(HODProfile)
class HODProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department')
