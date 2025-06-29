

from.models import Result,StudentFinalResult,Grade
from django.db.models import Sum,Max





def calculate_and_create_final_result(student, academic_year, academic_class=None, section=None, subject=None, faculty=None):
    if not all([student, academic_year, academic_class, section, subject, faculty]):
        print("❌ Missing one or more required arguments for calculating final result.")
        return None

    try:
        results = Result.objects.filter(
            student=student,
            academic_year=academic_year,
            exam_type__subject=subject
        )

        if academic_class:
            results = results.filter(exam_type__subject__academic_class=academic_class)
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
        print("❌ Error in calculate_and_create_final_result:", e)
        return None
















def aggregate_student_data(student, academic_year, academic_class, section, language_type):   
    total_marks = Result.objects.filter(
        student=student, academic_year=academic_year, student__enrolled_students__academic_class=academic_class,
        student__enrolled_students__section=section, student__enrolled_students__student_class__language_version=language_type
    ).aggregate(total_marks=Sum('exam_type__exam_marks'))['total_marks'] or 0

    total_obtained = Result.objects.filter(
        student=student, academic_year=academic_year, student__enrolled_students__academic_class=academic_class,
        student__enrolled_students__section=section, student__enrolled_students__student_class__language_version=language_type
    ).aggregate(total_obtained=Sum('obtained_marks'))['total_obtained'] or 0
 
    total_highest = (
        Result.objects.filter(
            academic_year=academic_year, student__enrolled_students__academic_class=academic_class,
            student__enrolled_students__section=section, student__enrolled_students__student_class__language_version=language_type
        )
        .values('student')
        .annotate(total_obtained=Sum('obtained_marks')) 
        .aggregate(highest_total=Max('total_obtained'))['highest_total'] or 0  
    )

    final_result = StudentFinalResult.objects.filter(
        student=student, academic_year=academic_year, academic_class=academic_class,
        section=section, student__enrolled_students__student_class__language_version=language_type
    ).aggregate(total_grade_points=Sum('grade_point'))['total_grade_points'] or 0

    print(StudentFinalResult.objects.filter(
    student=student, academic_year=academic_year, academic_class=academic_class,
    section=section, student__enrolled_students__student_class__language_version=language_type
).values_list('grade_point', flat=True))

    num_subjects = StudentFinalResult.objects.filter(
        student=student, academic_year=academic_year, academic_class=academic_class,
        section=section, student__enrolled_students__student_class__language_version=language_type
    ).count()

    overall_gpa = final_result / num_subjects if num_subjects > 0 else 0
   

    return {
        'total_marks': total_marks,
        'total_obtained': total_obtained,
        'total_highest': total_highest,
        'overall_gpa': overall_gpa,
    }



def calculate_gpa_and_grade(obtained_marks, total_marks):  
    if total_marks == 0: 
        return 0.0, "N/A"
    percentage = (obtained_marks / total_marks) * 100
    grade = Grade.objects.filter(
        min_marks__lte=percentage, max_marks__gte=percentage
    ).first()
    
    if grade:
        return grade.grade_point, grade.name    
    return 0.0, "N/A"

