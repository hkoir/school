from datetime import timedelta, datetime
from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from datetime import date

from teachers.models import Teacher
from students.models import Student
from.models import Attendance,AttendanceLog




@shared_task
def daily_attendance_update_task(attendance_date=None):
    try:
        if attendance_date is None:
            attendance_date = date.today()

        # Process Teacher Attendance
        teachers = Teacher.objects.all()
        for teacher in teachers:
            logs = AttendanceLog.objects.filter(teacher=teacher, date=attendance_date).order_by("check_in_time")
            if logs.exists():
                first_check_in = logs.first().check_in_time
                last_check_out = logs.last().check_out_time if logs.last().check_out_time else None

                is_late = first_check_in > teacher.attendance_policy.check_in_time # Assuming teachers have a fixed start time
                is_early_out = last_check_out and last_check_out < teacher.attendance_policy.check_out_time

                total_worked_time = timedelta()
                for log in logs:
                    if log.check_out_time:
                        worked_time = datetime.combine(attendance_date, log.check_out_time) - datetime.combine(attendance_date, log.check_in_time)
                        total_worked_time += worked_time

                # Create or update teacher attendance record
                attendance, created = Attendance.objects.update_or_create(
                    teacher=teacher,
                    date=attendance_date,
                    defaults={
                        "first_check_in": first_check_in,
                        "last_check_out": last_check_out,
                        "is_late": is_late,
                        "is_early_out": is_early_out,
                        "remarks": "Teacher attendance updated",
                    }
                )

        # Process Student Attendance
        students = Student.objects.all()
        for student in students:
            logs = AttendanceLog.objects.filter(student=student, date=attendance_date).order_by("check_in_time")
            if logs.exists():
                first_check_in = logs.first().check_in_time
                last_check_out = logs.last().check_out_time if logs.last().check_out_time else None

                # Assuming students have a defined class schedule
                is_late = first_check_in > student.attendance_policy.check_in_time  # Each student might have different class start time
                is_early_out = last_check_out and last_check_out < student.attendance_policy.check_out_time

                total_class_time = timedelta()
                for log in logs:
                    if log.check_out_time:
                        class_time = datetime.combine(attendance_date, log.check_out_time) - datetime.combine(attendance_date, log.check_in_time)
                        total_class_time += class_time

                # Create or update student attendance record
                attendance, created = Attendance.objects.update_or_create(
                    student=student,
                    date=attendance_date,
                    defaults={
                        "first_check_in": first_check_in,
                        "last_check_out": last_check_out,
                        "is_late": is_late,
                        "is_early_out": is_early_out,
                        "remarks": "Student attendance updated",
                    }
                )

        return f"Attendance processed for all teachers and students on {attendance_date}"

    except ObjectDoesNotExist:
        return "Error: One or more records not found or invalid data."

    except Exception as e:
        return f"An error occurred: {str(e)}"
