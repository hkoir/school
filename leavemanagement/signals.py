
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Employee
from leavemanagement.models import LeaveType, EmployeeLeaveBalance
from django.utils import timezone

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Employee)
def create_leave_balances_for_new_employee(sender, instance, created, **kwargs):
    if created:
        logger.info(f"Signal fired: Creating leave balances for employee {instance}")
        print(f"Signal fired: Creating leave balances for employee {instance}")

        current_year = timezone.now().year
        leave_types = LeaveType.objects.all()

        if not leave_types:
            logger.warning("No LeaveTypes found. Please add LeaveType instances.")
            print("No LeaveTypes found. Please add LeaveType instances.")
            return

        for leave_type in leave_types:
            elb, created_elb = EmployeeLeaveBalance.objects.get_or_create(
                employee=instance,
                leave_type=leave_type,
                year=current_year,
                defaults={
                    'balance': leave_type.annual_allowance,
                    'carry_forward': 0,
                }
            )
            if created_elb:
                logger.info(f"Created leave balance for {instance} - {leave_type}")
                print(f"Created leave balance for {instance} - {leave_type}")
            else:
                logger.info(f"Leave balance already exists for {instance} - {leave_type}")
                print(f"Leave balance already exists for {instance} - {leave_type}")
