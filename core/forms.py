from django import forms
from django.contrib.auth.models import User
from django.forms import modelformset_factory
from .models import ManagementProfile
from .models import (
    DirectMessage,
    StudentProfile,
    MeetingRecord,
    AttendanceRecord,
    MarksRecord
)

# ======================================================
# 🔹 User Signup Form (For Student or Proctor)
# ======================================================
class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[('student', 'Student'), ('proctor', 'Proctor')])

    usn = forms.CharField(required=False)
    proctor = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='Proctor'),
        required=False,
        help_text="Select your assigned proctor"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'role', 'usn', 'proctor']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")
        if password and password != confirm:
            raise forms.ValidationError("Passwords do not match!")
        return cleaned_data


# ======================================================
# 🔹 Student Profile Form
# ======================================================
class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            'usn', 'branch', 'semester', 'section',
            'blood_group', 'dob', 'phone', 'email',
            'father_name', 'father_phone', 'mother_name', 'mother_phone',
            'permanent_address', 'local_address',
            'first_year_fee', 'second_year_fee', 'third_year_fee', 'fourth_year_fee',
            'proctor'
        ]


# ======================================================
# 🔹 Student Profile Update Form (for Self Edit)
# ======================================================
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ('phone', 'semester', 'branch', 'section')


#-------------management hod or principal-------------
class ManagementSignupForm(forms.ModelForm):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = ManagementProfile
        fields = ['role']   # HOD / Principal

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            is_staff=True  # Allows admin access
        )

        profile = ManagementProfile(
            user=user,
            role=self.cleaned_data['role']
        )

        if commit:
            profile.save()

        return profile


# ======================================================
# 🔹 Meeting Form (for Proctors to Schedule)
# ======================================================
class MeetingForm(forms.ModelForm):
    class Meta:
        model = MeetingRecord
        fields = ['title', 'datetime', 'students', 'notes']
        widgets = {
            'datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'students': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }



# ======================================================
# 🔹 Direct Messaging Form (Student ↔ Proctor)
# ======================================================
class DirectMessageForm(forms.ModelForm):
    class Meta:
        model = DirectMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Type your message...'
            })
        }

class BroadcastMessageForm(forms.Form):
    content = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        label="Broadcast Message"
    )



# ======================================================
# 🔹 Attendance Form and Formset
# ======================================================
class AttendanceForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        # ✅ These field names must match your model
        fields = ['subject', 'total_classes', 'attended_classes']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'total_classes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'attended_classes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

# ✅ Attendance Formset (to handle multiple records at once)
AttendanceFormSet = modelformset_factory(
    AttendanceRecord,
    form=AttendanceForm,
    extra=5,
    can_delete=False
)


# ======================================================
# 🔹 Marks Form and Formset
# ======================================================
class MarksForm(forms.ModelForm):
    class Meta:
        model = MarksRecord
        # ✅ Must exactly match your MarksRecord model fields
        fields = ['subject', 'internal1', 'internal2', 'external']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'internal1': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'internal2': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'external': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

# ✅ Marks Formset
MarksFormSet = modelformset_factory(
    MarksRecord,
    form=MarksForm,
    extra=5,
    can_delete=False
)


# ======================================================
# 🔹 Help / Feedback Form
# ======================================================
class HelpForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}))
