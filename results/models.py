
from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import CustomUser
from school_management.utils import SHIFT_CHOICES,GENDER_CHOICES,LANGUAGE_CHOICES



class Grade(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=3, unique=True)  # e.g., "A+", "A", "B+" etc.
    grade_point=models.FloatField(null=True,blank=True)
    min_marks = models.IntegerField()  # Minimum marks for the grade
    max_marks = models.IntegerField()  # Maximum marks for the grade
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.min_marks >= self.max_marks:
            raise ValidationError("Minimum marks should be less than maximum marks.")

    def __str__(self):
        return f"{self.name}"


class Exam(models.Model):
    name = models.CharField(max_length=50)
    academic_year = models.IntegerField(null=True, blank=True)
    exam_start_date = models.DateField(null=True,blank=True)
    is_exam_over = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.academic_year})"


class ExamType(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_types',null=True, blank=True)
    subject = models.ForeignKey('school_management.Subject', on_delete=models.CASCADE, related_name='exam_type_subjects', null=True, blank=True)
    exam_marks = models.IntegerField() 
    exam_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time   = models.TimeField(null=True, blank=True)
    room = models.ForeignKey('school_management.ClassRoom', on_delete=models.CASCADE,null=True, blank=True) 
    academic_class = models.ForeignKey('school_management.AcademicClass', on_delete=models.CASCADE, related_name='exam_type_classes', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
  
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'exam','academic_class','subject',                
                ],
                name='unique_exam_type_per_context'
            )
        ]


    def __str__(self):
        return f"{self.exam.name}--{self.academic_class.name}--{self.subject.name} "
    


from django.db.models import Avg, Sum, Count

class Result(models.Model):  
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='student_results')    
    academic_year = models.CharField(max_length=10,null=True,blank=True) 
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, related_name='exam_results')
    subject_teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, null=True, blank=True, related_name='result_subject_teachers')
    exam_date = models.DateField()  
    exam_marks = models.FloatField(null=True, blank=True)
    obtained_marks = models.FloatField()   
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)
    grade_point = models.FloatField(default=0.00,null=True, blank=True)
    final_result = models.ForeignKey('results.StudentFinalResult', on_delete=models.CASCADE, null=True, blank=True, related_name='results')
    status = models.CharField(max_length=20, choices=[('pass', 'Pass'), ('fail', 'Fail'), ('withhold', 'Withhold')], null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):      
        if self.exam_marks and self.exam_marks > 0:
            percentage = (self.obtained_marks / self.exam_marks) * 100
        else:
            percentage = 0
        grade = Grade.objects.filter(
            min_marks__lte=percentage,
            max_marks__gte=percentage
        ).first()
        self.grade = grade 
        self.grade_point = grade.grade_point if grade else 0.0
        super().save(*args, **kwargs)
  
    def __str__(self):
        return f"Result for Student ID {self.student_id}, Subject ID {self.exam_type_id}"



    def get_enrollment_details(self):
        enrollment = self.student.enrolled_students.first()  
        return {
            'class': enrollment.academic_class if enrollment else None,
            'section': enrollment.section if enrollment and enrollment.section else None
        }

   

class StudentFinalResult(models.Model):   
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    academic_year = models.IntegerField()
    faculty = models.ForeignKey('school_management.Faculty', on_delete=models.CASCADE,null=True,blank=True)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name="final_results") 
    academic_class = models.ForeignKey('school_management.AcademicClass', on_delete=models.CASCADE,null=True,blank=True)  
    section = models.ForeignKey('school_management.Section', on_delete=models.CASCADE, null=True, blank=True)   
    subject = models.ForeignKey('school_management.Subject', on_delete=models.CASCADE, related_name="final_results")   
    total_obtained_marks = models.FloatField(default=0)
    total_assigned_marks = models.FloatField(default=0)
    percentage = models.FloatField(null=True, blank=True)
    final_grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)
    grade_point = models.FloatField(default=0.00)
    is_golden_gpa = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.academic_year} - {self.percentage:.2f}% - {self.final_grade}"

    @staticmethod
    def calculate_final_result(student, academic_year, academic_class=None, section=None, subject=None, faculty=None):
        if not all([student, academic_year, academic_class, section, subject, faculty]):
            print("❌ Missing one or more required arguments for calculating final result.")
            return None

        try:
            results = Result.objects.filter(
                student=student,
                academic_year=academic_year,
                exam_type__subject = subject
               
            )

            if academic_class:
                results = results.filter(subject__academic_class=academic_class)
            if section:
                results = results.filter(student__enrolled_students__section=section)

            total_obtained_marks = sum(r.obtained_marks for r in results)
            total_assigned_marks = sum(r.exam_marks for r in results)

            percentage = (total_obtained_marks / total_assigned_marks) * 100 if total_assigned_marks else 0
            final_grade = Grade.objects.filter(min_marks__lte=percentage, max_marks__gte=percentage).first()
            grade_point = final_grade.grade_point if final_grade else 0.00
            is_golden_gpa = all(
                r.final_result and r.final_result.final_grade and r.final_result.final_grade.grade_point == 5.0
                for r in results
            )

            print(f"🔍 Creating/Updating StudentFinalResult: {student}, {subject}, {academic_year}")

            final_result, created = StudentFinalResult.objects.update_or_create(
                student=student,
                academic_year=academic_year,
                academic_class=academic_class,
                section=section,
                subject=subject,
                faculty=faculty,
                defaults={
                    'total_obtained_marks': total_obtained_marks,
                    'total_assigned_marks': total_assigned_marks,
                    'percentage': percentage,
                    'final_grade': final_grade,
                    'grade_point': grade_point,
                    'is_golden_gpa': is_golden_gpa
                }
            )

            print("✅ FinalResult calculated and saved.")
            return final_result

        except Exception as e:
            print("❌ Error in calculate_final_result:", e)
            return None








