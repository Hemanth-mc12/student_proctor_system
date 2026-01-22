from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# =====================================================
# 🔹 Branch and Section (optional)
# =====================================================
class Branch(models.Model):
    name = models.CharField(max_length=50, default='CSE')

    def __str__(self):
        return self.name


class Section(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


# =====================================================
# 🔹 Proctor Profile
# =====================================================
class ProctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Proctor: {self.user.username}"


# =====================================================
# 🔹 Student Profile (Enhanced)
# =====================================================
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    usn = models.CharField(max_length=20)
    branch = models.CharField(max_length=50)
    semester = models.IntegerField(default=1)
    section = models.CharField(max_length=5, blank=True, null=True)

    # Personal info
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # Family info
    father_name = models.CharField(max_length=100, blank=True, null=True)
    father_phone = models.CharField(max_length=15, blank=True, null=True)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    mother_phone = models.CharField(max_length=15, blank=True, null=True)

    # Addresses
    permanent_address = models.TextField(blank=True, null=True)
    local_address = models.TextField(blank=True, null=True)

    # Fee details
    first_year_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    second_year_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    third_year_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fourth_year_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # Linked to proctor (User)
    proctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='students')

    def __str__(self):
        return f"{self.user.username} ({self.usn})"
    

#---------------------Management  models-----------------
class ManagementProfile(models.Model):
    ROLE_CHOICES = (
        ('HOD', 'HOD'),
        ('PRINCIPAL', 'Principal'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.role} - {self.user.username}"
    
class HODProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)

    def __str__(self):
        return f"HOD: {self.user.username} ({self.department})"




# =====================================================
# 🔹 Marks Record
# =====================================================
class MarksRecord(models.Model):
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE)
    semester = models.IntegerField(default=1)

    subject = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=20, blank=True, null=True)

    # Proctor enters all marks manually
    internal1 = models.FloatField(default=0)
    internal2 = models.FloatField(default=0)
    total_internal = models.FloatField(default=0)

    external = models.FloatField(default=0)
    total_marks = models.FloatField(default=0)

    attendance_percentage = models.FloatField(default=0)

    # Final subject percentage (manual - NOT calculated)
    percentage = models.FloatField(default=0)

    def __str__(self):
        return f"{self.student.usn} - {self.subject} (Sem {self.semester})"



# =====================================================
# 🔹 Attendance Record
# =====================================================
class AttendanceRecord(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    total_classes = models.IntegerField(default=0)
    attended_classes = models.IntegerField(default=0)

    @property
    def attendance_percent(self):
        if self.total_classes == 0:
            return 0
        return round((self.attended_classes / self.total_classes) * 100, 2)

    def __str__(self):
        return f"{self.student.usn} - {self.subject}"


# =====================================================
# 🔹 Meeting Record (for both Proctor and Student)
# =====================================================
class MeetingRecord(models.Model):
    title = models.CharField(max_length=100)
    datetime = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        'ProctorProfile', on_delete=models.CASCADE, related_name='meetings'
    )
    students = models.ManyToManyField('StudentProfile', related_name='meetings')

    def __str__(self):
        return f"{self.title} ({self.datetime.strftime('%Y-%m-%d %H:%M')})"


class MeetingMessage(models.Model):
    meeting = models.ForeignKey(MeetingRecord, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"

# =====================================================
# 🔹 Direct Message (Student ↔ Proctor)
# =====================================================
class DirectMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.content[:25]}"
    

#---------------HOD broad cast message------------------
class BroadcastMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


# =====================================================
# 🔹 Help / Feedback Message
# =====================================================
class HelpMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Help from {self.name} ({self.email})"
