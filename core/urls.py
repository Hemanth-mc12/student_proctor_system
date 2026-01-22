# core/urls.py
from django.urls import path
from . import views
from core.views import login_view

urlpatterns = [
    # ---------- HOME ----------
    path('', views.index, name='index'),

    # ---------- AUTH ----------
    path('signup/', views.signup_view, name='signup'),
    path('proctor/signup/', views.proctor_signup, name='proctor_signup'),
    path('login/', views.login_view, name='login'),
    path('accounts/login/', login_view),  # for admin redirect
    path('logout/', views.logout_view, name='logout'),
    path('management-signup/', views.management_signup, name='management_signup'),

    # ---------- DASHBOARDS ----------
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('proctor/dashboard/', views.proctor_dashboard, name='proctor_dashboard'),
    path("hod/dashboard/", views.hod_dashboard, name="hod_dashboard"),

    # PROCTOR → View student's dashboard
    path(
        "proctor/student/<str:usn>/dashboard/",
        views.proctor_view_student_dashboard,
        name="proctor_view_student_dashboard"
    ),

    # ---------- BROADCAST ----------
    path("broadcasts/", views.student_broadcasts, name="student_broadcasts"),

    # ---------- PROCTOR MANAGEMENT ----------
    path("manage-proctors/", views.manage_proctors, name="manage_proctors"),
    path("manage-students/", views.manage_students, name="manage_students"),
    path('proctor/<int:id>/edit/', views.edit_proctor, name='edit_proctor'),
    path('proctor/<int:id>/delete/', views.delete_proctor, name='delete_proctor'),
    path("admin/reassign/<str:usn>/", views.reassign_proctor, name="reassign_proctor"),

    # ---------- MARKS ENTRY ----------
    path('proctor/marks/<str:usn>/', views.proctor_select_semester, name='proctor_select_semester'),
    path('proctor/marks/<str:usn>/<int:semester>/', views.proctor_enter_marks, name='proctor_enter_marks'),

    # ---------- STUDENT CRUD ----------
    path('student/<int:id>/edit/', views.edit_student, name='edit_student'),
    path('student/<int:id>/delete/', views.delete_student, name='delete_student'),

    # ---------- MEETINGS ----------
    path('meeting/schedule/', views.meeting_schedule, name='meeting_schedule'),
    path('student/meetings/', views.student_meetings, name='student_meetings'),
    path('meeting/<int:meeting_id>/chat/', views.meeting_chat, name='meeting_chat'),
    path('messages/', views.direct_messages, name='direct_messages'),

    path("hod/broadcast/", views.hod_broadcast_message, name="hod_broadcast"),
    path("hod/assign/", views.assign_multiple, name="assign_multiple"),
    path("proctor/student/<str:usn>/dashboard/", views.proctor_view_student_dashboard, name="proctor_view_student_dashboard"),


    # ---------- STUDENT INFORMATION ----------
    path('student/<str:usn>/history/', views.student_history, name='student_history'),
    path('student/<str:usn>/edit/', views.student_info_upload, name='student_info_upload'),

    # **IMPORTANT: KEEP LAST**
    path('student/<str:usn>/', views.student_detail, name='student_detail'),

    # ---------- API ----------
    path('api/student/<str:usn>/performance/', views.student_performance_api, name='student_performance_api'),

    # ---------- ATTENDANCE / MARKS ----------
    path('attendance/upload/<str:usn>/', views.attendance_upload, name='attendance_upload'),
    path('attendance/edit/<int:pk>/', views.attendance_upload, name='attendance_edit'),

    path('marks/upload/<str:usn>/', views.marks_upload, name='marks_upload'),
    path('marks/edit/<int:pk>/', views.marks_upload, name='marks_edit'),

    # ---------- MISC ----------
    path('profile/update/', views.profile_update, name='profile_update'),
    path('help/', views.help_view, name='help'),
]
