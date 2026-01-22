# core/views.py
from datetime import datetime
import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q
from .forms import ManagementSignupForm
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import BroadcastMessageForm
from .models import BroadcastMessage
from .models import HODProfile
from .models import ProctorProfile, StudentProfile



from .models import (
    StudentProfile,
    ProctorProfile,
    AttendanceRecord,
    MarksRecord,
    MeetingRecord,
    MeetingMessage,
    DirectMessage,
)

from .forms import (
    SignupForm,
    StudentProfileForm,
    MeetingForm,
    AttendanceForm,
    MarksForm,
    ProfileUpdateForm,
    HelpForm,
    DirectMessageForm,
    AttendanceFormSet,   # defined in forms.py
    MarksFormSet,        # defined in forms.py
)

# ------------------- BASIC -------------------
def index(request):
    return render(request, 'core/index.html')

# ------------------- SIGNUP (Student) -------------------
def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        usn = request.POST.get("usn")
        branch = request.POST.get("branch")
        semester = request.POST.get("semester")

        if StudentProfile.objects.filter(usn=usn).exists():
            messages.error(request, "USN already exists.")
            return redirect("signup")

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email
            )

            StudentProfile.objects.create(
                user=user,
                usn=usn,
                branch=branch,
                semester=int(semester),
                proctor=None   # HOD assigns later
            )

            messages.success(request, "Account created successfully!")
            return redirect("login")

        except IntegrityError:
            messages.error(request, "Username already taken!")
            return redirect("signup")

    return render(request, "core/signup.html")



# ------------------- SIGNUP (Proctor) -------------------
def proctor_signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        department = request.POST.get("department")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken. Please choose another one.")
            return redirect("proctor_signup")

        try:
            user = User.objects.create_user(username=username, password=password, email=email)
            ProctorProfile.objects.create(user=user, department=department)
            messages.success(request, "✅ Proctor account created successfully! You can now log in.")
            return redirect("login")
        except Exception as e:
            messages.error(request, f"Error creating account: {e}")
            return redirect("proctor_signup")

    return render(request, "core/proctor_signup.html")

#-------management signup--------------------
def management_signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        department = request.POST.get("department")

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect("management_signup")

        # Create user
        user = User.objects.create_user(username=username, password=password)

        # Add to HOD group
        hod_group, created = Group.objects.get_or_create(name="HOD")
        user.groups.add(hod_group)

        # Create profile
        HODProfile.objects.create(
            user=user,
            department=department
        )

        messages.success(request, "HOD Account Created Successfully!")
        return redirect("login")

    return render(request, "core/management_signup.html")



# ------------------- LOGIN / LOGOUT -------------------

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome, {user.username}!")

            # ✅ SUPERUSER (Admin)
            if user.is_superuser:
                return redirect("/admin/")  # or your custom admin dashboard

            # ✅ HOD ROLE
            if user.groups.filter(name="HOD").exists():
                return redirect("hod_dashboard")

            # ✅ PRINCIPAL ROLE
            if user.groups.filter(name="PRINCIPAL").exists():
                return redirect("principal_dashboard")

            # ✅ PROCTOR ROLE
            if hasattr(user, 'proctorprofile'):
                return redirect('proctor_dashboard')

            # ✅ STUDENT ROLE
            if hasattr(user, 'studentprofile'):
                return redirect('student_dashboard')

            # Fallback
            return redirect('index')

        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'core/login.html')

    return render(request, 'core/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')

# ------------------- ROLE HELPERS -------------------
def is_student(user): return hasattr(user, 'studentprofile')
def is_proctor(user): return hasattr(user, 'proctorprofile')

#---------------STUDENT  DASHBOARD------------------
# ------------------ GRAPH DATA FOR STUDENT ------------------
def get_student_graph_data(student, selected_sem):

    marks = MarksRecord.objects.filter(
        student=student,
        semester=selected_sem
    ).order_by("subject")

    subjects = []
    marks_percentage = []
    attendance_list = []

    for m in marks:

        subjects.append(m.subject)

        internal1 = m.internal1 or 0   # out of 25
        internal2 = m.internal2 or 0   # out of 25
        external = m.external or 0     # out of 50

        total = internal1 + internal2 + external  # out of 100
        percent = (total / 100) * 100

        marks_percentage.append(round(percent, 2))
        attendance_list.append(float(m.attendance_percentage or 0))

    return {
        "subjects": subjects,
        "marks": marks_percentage,
        "attendance": attendance_list,
    }

# ------------------- STUDENT DASHBOARD -------------------
@login_required
def student_dashboard(request):
    if not is_student(request.user):
        return HttpResponseForbidden("Not allowed")

    student = get_object_or_404(StudentProfile, user=request.user)

    semesters = range(1, 9)
    selected_sem = int(request.GET.get("sem", student.semester))

    marks = MarksRecord.objects.filter(student=student, semester=selected_sem)

    performance_data = get_student_graph_data(student, selected_sem)

    broadcasts = BroadcastMessage.objects.filter(
        department=student.branch
    ).order_by("-timestamp")

    return render(request, "core/student_dashboard.html", {
        "student": student,
        "marks": marks,
        "semesters": semesters,
        "selected_sem": selected_sem,
        "broadcasts": broadcasts,
        "performance_data_json": json.dumps(performance_data),
    })



#---------------student_proctor _dashboard-----------------------
# ------------------ GRAPH DATA FOR PROCTOR ------------------
def get_proctor_graph_data(student, selected_sem):

    marks = MarksRecord.objects.filter(
        student=student,
        semester=selected_sem
    ).order_by("subject")

    subjects = []
    marks_percentage = []
    attendance_list = []

    for m in marks:

        subjects.append(m.subject)

        # Correct marking scheme
        internal1 = m.internal1 or 0   # out of 25
        internal2 = m.internal2 or 0   # out of 25
        external = m.external or 0     # out of 50

        total = internal1 + internal2 + external  # out of 100
        percent = (total / 100) * 100             # convert to %

        marks_percentage.append(round(percent, 2))
        attendance_list.append(float(m.attendance_percentage or 0))

    return {
        "subjects": subjects,
        "marks": marks_percentage,
        "attendance": attendance_list,
    }



# ------------------ PROCTOR VIEW STUDENT DASHBOARD ------------------
@login_required
def proctor_view_student_dashboard(request, usn):

    # Only proctor or HOD can access
    if not (is_proctor(request.user) or request.user.groups.filter(name="HOD").exists()):
        return HttpResponseForbidden("Not allowed")

    student = get_object_or_404(StudentProfile, usn=usn)

    semesters = range(1, 9)
    selected_sem = int(request.GET.get("sem", student.semester))

    # Marks for selected sem
    marks = MarksRecord.objects.filter(
        student=student,
        semester=selected_sem
    ).order_by("subject")

    # Call graph function
    performance_data = get_proctor_graph_data(student, selected_sem)

    # Broadcast messages from department
    broadcasts = BroadcastMessage.objects.filter(
        department=student.branch
    ).order_by("-timestamp")

    return render(request, "core/proctor_view_student_dashboard.html", {
        "student": student,
        "semesters": semesters,
        "selected_sem": selected_sem,
        "marks": marks,
        "broadcasts": broadcasts,

        # IMPORTANT: JSON passed to JS
        "performance_data_json": json.dumps(performance_data),
    })


#------------------HOD DASHBOARD----------------------------
@login_required
def hod_dashboard(request):
    user = request.user

    # Get HOD profile
    hod_profile = HODProfile.objects.filter(user=user).first()

    if not hod_profile:
        messages.error(request, "HOD profile not found. Contact admin.")
        return redirect("index")

    # Get proctors in this HOD’s department
    proctors = ProctorProfile.objects.filter(department=hod_profile.department)

    # Get students in same department
    students = StudentProfile.objects.filter(branch=hod_profile.department)

    return render(request, "core/hod_dashboard.html", {
        "hod_profile": hod_profile,
        "proctors": proctors,
        "students": students,
    })


#-------------------------------Assigning multiple students into proctors---------------------
@login_required
def assign_multiple(request):
    if not request.user.groups.filter(name="HOD").exists():
        return HttpResponseForbidden("Not allowed")

    if request.method == "POST":
        student_ids = request.POST.getlist("students")
        proctor_id = request.POST.get("proctor_id")

        if not student_ids:
            messages.error(request, "No students selected.")
            return redirect("hod_dashboard")

        proctor_user = User.objects.get(id=proctor_id)

        for sid in student_ids:
            student = StudentProfile.objects.get(id=sid)
            student.proctor = proctor_user
            student.save()

        messages.success(request, "Students assigned successfully!")
        return redirect("hod_dashboard")


# ------------------- STUDENT HISTORY -------------------
@login_required
def student_history(request, usn):
    student = get_object_or_404(StudentProfile, usn=usn)

    # ALLOW: Student viewing self
    is_student = (
        hasattr(request.user, "studentprofile") and
        request.user.studentprofile.usn == usn
    )

    # ALLOW: Proctor assigned to this student
    is_proctor = (
        hasattr(request.user, "proctorprofile") and
        student.proctor == request.user
    )

    # ALLOW: HOD
    is_hod = request.user.groups.filter(name="HOD").exists()

    # PERMISSION CHECK
    if not (is_student or is_proctor or is_hod):
        return HttpResponseForbidden("Not allowed")

    # ---------- HISTORY DATA ----------
    attendance = AttendanceRecord.objects.filter(student=student)
    marks = MarksRecord.objects.filter(student=student)
    today = datetime.now()

    return render(request, "core/student_history.html", {
        "student": student,
        "attendance": attendance,
        "marks": marks,
        "today": today,
    })


    # ---------- FETCH HISTORY DATA ----------
    # (Your history logic stays same below this)


# ------------------- STUDENT INFO UPLOAD (Proctor/Admin) -------------------
@login_required
def student_info_upload(request, usn):
    student = get_object_or_404(StudentProfile, usn=usn)
    # Permissions: student (self), proctor assigned, or admin
    if not (
        request.user.is_superuser
        or (is_student(request.user) and request.user.studentprofile == student)
        or (is_proctor(request.user) and student.proctor == request.user)
    ):
        return HttpResponseForbidden('Not allowed')

    if request.method == "POST":
        form = StudentProfileForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Student information for {student.usn} updated successfully.")
            return redirect('student_history', usn=student.usn)
        messages.error(request, "⚠️ Please correct the errors below.")
    else:
        form = StudentProfileForm(instance=student)
    return render(request, "core/student_info_form.html", {"form": form, "student": student})

# ------------------- PROCTOR DASHBOARD -------------------
@login_required
def proctor_dashboard(request):
    if not (is_proctor(request.user) or request.user.is_superuser):
        return HttpResponseForbidden('Not allowed')

    proctor = getattr(request.user, "proctorprofile", None)

    # Students assigned to this proctor
    students = StudentProfile.objects.filter(proctor=request.user)

    # Meetings created by this proctor
    meetings = MeetingRecord.objects.filter(
        created_by=proctor
    ).order_by('-datetime')

    # ✅ Get only broadcasts for this proctor's department
    # Assuming ProctorProfile has: department or branch
    proctor_department = proctor.department if hasattr(proctor, "department") else None

    broadcasts = BroadcastMessage.objects.filter(
        department=proctor_department
    ).order_by("-timestamp")

    return render(request, 'core/proctor_dashboard.html', {
        'proctor': proctor,
        'students': students,
        'meetings': meetings,

        # important!
        'broadcasts': broadcasts,
    })


#-----------proctor_student_dashboard (FINAL WITH GRAPH DATA)----------------------
@login_required
def proctor_view_student_dashboard(request, usn):
    student = get_object_or_404(StudentProfile, usn=usn)

    # Allow: Proctor assigned OR HOD OR Superuser
    if not (
        hasattr(request.user, "proctorprofile") and student.proctor == request.user
        or request.user.groups.filter(name="HOD").exists()
        or request.user.is_superuser
    ):
        return HttpResponseForbidden("Not allowed")

    semesters = range(1, 9)
    selected_sem = int(request.GET.get("sem", student.semester))

    marks = MarksRecord.objects.filter(
        student=student,
        semester=selected_sem
    ).order_by("subject")

    # ---- PERFORMANCE DATA FOR GRAPH ----
    subjects = []
    subject_marks = []
    subject_attendance = []

    for m in marks:
        subjects.append(m.subject)
        total_marks = (m.internal1 or 0) + (m.internal2 or 0) + (m.external or 0)
        subject_marks.append(total_marks)
        subject_attendance.append(m.attendance_percentage or 0)

    performance_data = {
        "subjects": subjects,
        "marks": subject_marks,
        "attendance": subject_attendance,
    }

    broadcasts = BroadcastMessage.objects.filter(
        department=student.branch
    ).order_by("-timestamp")

    return render(request, "core/proctor_student_dashboard.html", {
        "student": student,
        "semesters": semesters,
        "selected_sem": selected_sem,
        "marks": marks,
        "broadcasts": broadcasts,
        "performance_data_json": json.dumps(performance_data),
    })

# ------------------- STUDENT DETAIL -------------------
@login_required
def student_detail(request, usn):
    student = get_object_or_404(StudentProfile, usn=usn)

    # Allow: Superuser, Proctor assigned, The student himself, and HOD
    if not (
        request.user.is_superuser
        or request.user.groups.filter(name="HOD").exists()
        or (is_proctor(request.user) and student.proctor == request.user)
        or (is_student(request.user) and request.user.studentprofile == student)
    ):
        return HttpResponseForbidden('Not allowed')

    attendance = AttendanceRecord.objects.filter(student=student)
    marks = MarksRecord.objects.filter(student=student)

    return render(request, 'core/student_detail.html', {
        'student': student,
        'attendance': attendance,
        'marks': marks
    })


# ------------------- PERFORMANCE API -------------------
@login_required
def student_performance_api(request, usn):
    student = get_object_or_404(StudentProfile, usn=usn)
    if not (
        request.user.is_superuser
        or (is_proctor(request.user) and student.proctor == request.user)
        or (is_student(request.user) and request.user.studentprofile == student)
    ):
        return JsonResponse({'detail': 'forbidden'}, status=403)

    # Attendance %
    records = AttendanceRecord.objects.filter(student=student)
    total_classes = sum(r.total_classes for r in records)
    total_attended = sum(r.attended_classes for r in records)
    attendance_percent = (total_attended / total_classes * 100) if total_classes else 0.0

    # Subject-wise average % from existing fields
    marks = MarksRecord.objects.filter(student=student)
    subjects = {}
    for m in marks:
        total = (m.internal1 or 0) + (m.internal2 or 0) + (m.external or 0)
        max_total = 100.0  # adjust if you have a different scheme
        subjects.setdefault(m.subject, []).append((total, max_total))

    subject_avg = {
        s: (sum(x for x, _ in vals) / sum(mx for _, mx in vals) * 100 if sum(mx for _, mx in vals) else 0.0)
        for s, vals in subjects.items()
    }

    data = {
        'attendance_percent': round(attendance_percent, 2),
        'subject_avg': {k: round(v, 2) for k, v in subject_avg.items()},
    }
    return JsonResponse(data)

# ------------------- MEETING SCHEDULE (Proctor) -------------------
@login_required
def meeting_schedule(request):
    """Allow proctors to schedule meetings and notify assigned students."""
    if not hasattr(request.user, 'proctorprofile'):
        messages.error(request, "Only proctors can schedule meetings.")
        return redirect('login')

    proctor = request.user.proctorprofile

    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.created_by = proctor
            meeting.save()
            form.save_m2m()

            # ✅ Notify selected students (optional: display message)
            selected_students = form.cleaned_data['students']
            for student in selected_students:
                DirectMessage.objects.create(
                    sender=request.user,
                    receiver=student.user,
                    content=f"📅 New meeting scheduled: {meeting.title} on {meeting.datetime.strftime('%d %b %Y, %I:%M %p')}."
                )

            messages.success(request, "✅ Meeting scheduled successfully and students notified!")
            return redirect('proctor_dashboard')
    else:
        form = MeetingForm()
        form.fields['students'].queryset = StudentProfile.objects.filter(proctor=request.user)

    return render(request, 'core/meeting_form.html', {'form': form})

# ------------------- STUDENT MEETINGS (for student) -------------------
@login_required
def student_meetings(request):
    if not is_student(request.user):
        messages.error(request, "Only students can view this page.")
        return redirect('login')
    student = request.user.studentprofile
    meetings = student.meetings.all().order_by('-datetime')
    return render(request, 'core/student_meetings.html', {'meetings': meetings})

# ------------------- MEETING CHAT (both sides) -------------------
from django.utils import timezone

@login_required
def meeting_chat(request, meeting_id):
    meeting = get_object_or_404(MeetingRecord, id=meeting_id)

    user = request.user
    # access control:
    if is_student(user):
        if request.user.studentprofile not in meeting.students.all():
            return HttpResponseForbidden("You are not part of this meeting.")
    elif is_proctor(user):
        if meeting.created_by != getattr(user, 'proctorprofile', None):
            return HttpResponseForbidden("You are not the assigned proctor.")
    else:
        return HttpResponseForbidden("Access denied.")

    if request.method == 'POST':
        text = request.POST.get('message', '').strip()
        if text:
            MeetingMessage.objects.create(
                meeting=meeting,
                sender=user,
                content=text,
                timestamp=timezone.now()
            )
            messages.success(request, "Message sent.")
            return redirect('meeting_chat', meeting_id=meeting.id)

    all_messages = meeting.messages.order_by('timestamp')
    return render(request, 'core/meeting_chat.html', {'meeting': meeting, 'messages': all_messages})

# ------------------- DIRECT MESSAGES (1–1) -------------------
@login_required
def direct_messages(request):
    user = request.user
    receiver = None
    student = None

    # 🧩 Case 1 — If the user is a Student
    if hasattr(user, 'studentprofile'):
        student = user.studentprofile
        if not student.proctor:
            messages.warning(request, "No proctor assigned to you yet.")
            return redirect('student_dashboard')
        receiver = student.proctor  # ✅ FIX: student.proctor is already a User

    # 🧩 Case 2 — If the user is a Proctor
    elif hasattr(user, 'proctorprofile'):
        usn = request.GET.get('usn')
        if not usn:
            messages.info(request, "Select a student to chat with.")
            return redirect('proctor_dashboard')
        student = get_object_or_404(StudentProfile, usn=usn)
        receiver = student.user

    else:
        return HttpResponseForbidden("Access denied.")

    # 📨 Message send handling
    if request.method == "POST":
        form = DirectMessageForm(request.POST)
        if form.is_valid():
            DirectMessage.objects.create(
                sender=user,
                receiver=receiver,
                content=form.cleaned_data['content']
            )
            if hasattr(user, 'proctorprofile'):
                return redirect(f"{request.path}?usn={student.usn}")
            else:
                return redirect('direct_messages')
    else:
        form = DirectMessageForm()

    # 🧾 Fetch all messages between the two users
    messages_list = DirectMessage.objects.filter(
        Q(sender=user, receiver=receiver) | Q(sender=receiver, receiver=user)
    ).order_by('timestamp')

    return render(request, 'core/direct_messages.html', {
        'form': form,
        'messages_list': messages_list,
        'receiver': receiver
    })

#---------------HOD BROADCAST MESSAGE-----------------
@login_required
def hod_broadcast_message(request):
    if not request.user.groups.filter(name="HOD").exists():
        return redirect("index")

    # Auto-create HODProfile if missing
    hod_profile, created = HODProfile.objects.get_or_create(
        user=request.user,
        defaults={"department": "CSE"}   # Change based on your project
    )

    broadcasts = BroadcastMessage.objects.filter(
        department=hod_profile.department
    ).order_by("-timestamp")

    if request.method == "POST":
        form = BroadcastMessageForm(request.POST)
        if form.is_valid():
            BroadcastMessage.objects.create(
                sender=request.user,
                content=form.cleaned_data["content"],
                department=hod_profile.department
            )
            messages.success(request, "Broadcast message sent successfully!")
            return redirect("hod_broadcast")
    else:
        form = BroadcastMessageForm()

    return render(request, "core/hod_broadcast.html", {
        "form": form,
        "broadcasts": broadcasts
    })


@login_required
def student_broadcasts(request):
    user = request.user

    # If PROCTOR
    if hasattr(user, "proctorprofile"):
        dept = user.proctorprofile.department
        broadcasts = BroadcastMessage.objects.filter(
            department=dept
        ).order_by("-timestamp")
        return render(request, "core/student_broadcasts.html", {
            "broadcasts": broadcasts,
            "role": "proctor"
        })

    # If STUDENT
    if hasattr(user, "studentprofile"):
        dept = user.studentprofile.branch
        broadcasts = BroadcastMessage.objects.filter(
            department=dept
        ).order_by("-timestamp")
        return render(request, "core/student_broadcasts.html", {
            "broadcasts": broadcasts,
            "role": "student"
        })

    return HttpResponseForbidden("Access denied")




# ------------------- ATTENDANCE FORMSET PAGE -------------------
@login_required
def attendance_upload(request, usn):
    # Students may edit self, Proctor/Admin may edit assigned
    student = get_object_or_404(StudentProfile, usn=usn)
    if not (
        request.user.is_superuser
        or (is_student(request.user) and request.user.studentprofile == student)
        or (is_proctor(request.user) and student.proctor == request.user)
    ):
        return HttpResponseForbidden('Not allowed')

    queryset = AttendanceRecord.objects.filter(student=student)
    formset = AttendanceFormSet(request.POST or None, queryset=queryset)

    if request.method == 'POST':
        if formset.is_valid():
            instances = formset.save(commit=False)
            for inst in instances:
                inst.student = student
                inst.save()
            if hasattr(formset, 'deleted_objects'):
                for obj in formset.deleted_objects:
                    obj.delete()
            messages.success(request, "Attendance saved successfully.")
            return redirect('student_dashboard')
        else:
            print("Formset errors:", formset.errors)

    return render(request, 'core/attendance_formset.html', {'student': student, 'formset': formset})

#----------------SELECTING SEMESTER-----------------------------
@login_required
def proctor_select_semester(request, usn):
    student = get_object_or_404(StudentProfile, usn=usn)

    return render(request, "core/proctor_select_semester.html", {
        "student": student,
    })



#--------------------------proctor enter ing marks---------------------------
@login_required
def proctor_enter_marks(request, usn, semester):
    student = get_object_or_404(StudentProfile, usn=usn)

    # Show only selected semester marks
    marks = MarksRecord.objects.filter(student=student, semester=semester)

    if request.method == "POST":

        # SAVE EXISTING ROWS
        for m in marks:
            m.subject = request.POST.get(f"subject_{m.id}")
            m.subject_code = request.POST.get(f"subject_code_{m.id}")
            m.internal1 = request.POST.get(f"internal1_{m.id}") or 0
            m.internal2 = request.POST.get(f"internal2_{m.id}") or 0
            m.total_internal = request.POST.get(f"total_internal_{m.id}") or 0
            m.external = request.POST.get(f"external_{m.id}") or 0
            m.total_marks = request.POST.get(f"total_marks_{m.id}") or 0

            # ✅ FIXED FIELD NAME
            m.attendance_percentage = request.POST.get(f"attendance_percentage_{m.id}") or 0

            m.save()

        # ADD NEW ROW
        new_subject = request.POST.get("new_subject")
        if new_subject:
            MarksRecord.objects.create(
                student=student,
                semester=semester,
                subject=new_subject,
                subject_code=request.POST.get("new_subject_code"),

                internal1=request.POST.get("new_internal1") or 0,
                internal2=request.POST.get("new_internal2") or 0,
                total_internal=request.POST.get("new_total_internal") or 0,
                external=request.POST.get("new_external") or 0,
                total_marks=request.POST.get("new_total_marks") or 0,

                # ✅ FIXED FIELD NAME
                attendance_percentage=request.POST.get("new_attendance_percentage") or 0,
            )

        messages.success(request, "Marks updated successfully!")
        return redirect("proctor_enter_marks", usn=usn, semester=semester)

    return render(request, "core/proctor_enter_marks.html", {
        "student": student,
        "semester": semester,
        "marks": marks,
    })


# ------------------- MARKS FORMSET PAGE -------------------
from django.forms import modelformset_factory

@login_required
def marks_upload(request, usn):
    student = get_object_or_404(StudentProfile, usn=usn)
    if not (
        request.user.is_superuser
        or (is_student(request.user) and request.user.studentprofile == student)
        or (is_proctor(request.user) and student.proctor == request.user)
    ):
        return HttpResponseForbidden('Not allowed')

    LocalMarksFormSet = modelformset_factory(MarksRecord, form=MarksForm, extra=4)

    if request.method == 'POST':
        formset = LocalMarksFormSet(request.POST, queryset=MarksRecord.objects.filter(student=student))
        if formset.is_valid():
            records = formset.save(commit=False)
            for record in records:
                record.student = student
                record.save()
            messages.success(request, "Marks saved successfully.")
            return redirect('student_detail', usn=usn)
    else:
        formset = LocalMarksFormSet(queryset=MarksRecord.objects.filter(student=student))

    return render(request, 'core/marks_formset.html', {'student': student, 'formset': formset})

# ------------------- PROFILE UPDATE (Student self) -------------------
@login_required
def profile_update(request):
    if not (is_student(request.user) or request.user.is_superuser):
        messages.error(request, "Only students can update their profile.")
        return redirect('student_dashboard')

    student = request.user.studentprofile
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('student_dashboard')
    else:
        form = ProfileUpdateForm(instance=student)

    return render(request, 'core/profile_update.html', {'form': form})

#-------reassign proctor----------------
def reassign_proctor(request, usn):
    student = get_object_or_404(StudentProfile, usn=usn)
    proctors = ProctorProfile.objects.all()  # list all teachers

    if request.method == "POST":
        new_proctor_id = request.POST.get("proctor_id")
        new_proctor_user = get_object_or_404(User, id=new_proctor_id)

        student.proctor = new_proctor_user
        student.save()

        messages.success(request, f"Student {student.usn} reassigned successfully!")
        return redirect("admin_dashboard")  # whichever page you use

    return render(request, "core/reassign_proctor.html", {
        "student": student,
        "proctors": proctors
    })

def edit_proctor(request, id):
    proctor = get_object_or_404(ProctorProfile, id=id)

    if request.method == "POST":
        proctor.department = request.POST.get("department")
        proctor.save()
        return redirect("manage_proctors")

    return render(request, "core/edit_proctor.html", {"proctor": proctor})



def delete_proctor(request, id):
    proctor = get_object_or_404(ProctorProfile, id=id)
    proctor.delete()
    return redirect("manage_proctors")


def edit_student(request, id):
    student = get_object_or_404(StudentProfile, id=id)
    proctors = ProctorProfile.objects.all()

    if request.method == "POST":
        student.usn = request.POST.get("usn")
        student.branch = request.POST.get("branch")
        student.semester = request.POST.get("semester")
        student.section = request.POST.get("section")
        student.phone = request.POST.get("phone")
        student.email = request.POST.get("email")

        # Handle proctor assignment
        proctor_id = request.POST.get("proctor")
        if proctor_id:
            student.proctor = User.objects.get(id=proctor_id)
        else:
            student.proctor = None

        student.save()
        return redirect("manage_students")

    return render(request, "core/edit_student.html", {
        "student": student,
        "proctors": proctors,
    })


def delete_student(request, id):
    student = get_object_or_404(StudentProfile, id=id)
    student.delete()
    return redirect("manage_students")

def manage_proctors(request):
    proctors = ProctorProfile.objects.all()
    return render(request, 'core/manage_proctors.html', {'proctors': proctors})

def manage_students(request):
    students = StudentProfile.objects.all()
    return render(request, 'core/manage_students.html', {'students': students})

# ------------------- HELP -------------------
from .models import HelpMessage

def help_view(request):
    if request.method == 'POST':
        form = HelpForm(request.POST)
        if form.is_valid():
            HelpMessage.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                message=form.cleaned_data['message']
            )
            messages.success(request, 'Thanks! Your message was received.')
            return redirect('help')
    else:
        form = HelpForm()

    return render(request, 'core/help.html', {'form': form})
