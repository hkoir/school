from django.db import models

from students.models import Student
from school_management.models import Subject
from accounts.models import CustomUser



class Performance(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    result_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.student} - {self.subject.name} - {self.result_score} Score"
