

from datetime import datetime, timedelta
from django.utils.timezone import now
from django.db.models import Min, Max
from school_management.models import Schedule




def get_dynamic_attendance_policy(student, date=None):
    if not date:
        date = now().date()
    weekday = date.strftime('%A')

    enrollment = student.enrolled_students.first()
    if not enrollment:
        return None
 
    assigned_policy = AttendancePolicy.objects.filter(user=student.user, is_dynamic=True).first()
    if not assigned_policy:
        return None  

    schedules = Schedule.objects.filter(
        subject_assignment__class_assignment__academic_class=enrollment.academic_class,
        subject_assignment__section=enrollment.section,
        day_of_week=weekday,
        gender=enrollment.section.class_gender,
        shift=enrollment.student_class.shift
    )

    if not schedules.exists():
        return None

    earliest_start = schedules.aggregate(Min('start_time'))['start_time__min']
    latest_end = schedules.aggregate(Max('end_time'))['end_time__max']

    dt_earliest = datetime.combine(date, earliest_start)
    dt_latest = datetime.combine(date, latest_end)

    check_in_threshold = (dt_earliest + timedelta(minutes=assigned_policy.check_in_buffer)).time()
    absent_threshold = (dt_earliest + timedelta(minutes=assigned_policy.absent_buffer)).time()
    check_out_threshold = (dt_latest - timedelta(minutes=assigned_policy.check_out_buffer)).time()

    return {
        "check_in_time": earliest_start,
        "check_out_time": latest_end,
        "check_in_threshold": check_in_threshold,
        "absent_threshold": absent_threshold,
        "check_out_threshold": check_out_threshold,
    }




#Usage Logic (Smart Fallback)
from attendance.models import AttendancePolicy

def get_attendance_policy_for_student(student, date=None):
    policy = AttendancePolicy.objects.filter(user=student.user).first()
    if not policy:
        return None

    if policy.is_dynamic:
        return get_dynamic_attendance_policy(student, date)
    else:
        return {
            "check_in_time": policy.check_in_time,
            "check_out_time": policy.check_out_time,
            "check_in_threshold": policy.check_in_threshold,
            "check_out_threshold": policy.check_out_threshold,
        }

