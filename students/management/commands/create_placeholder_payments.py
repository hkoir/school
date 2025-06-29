from django.core.management.base import BaseCommand
from payments.models import Payment
from students.models import Student
from datetime import date

class Command(BaseCommand):
    help = 'Create placeholder payment records for all students for the current academic year.'

    def handle(self, *args, **kwargs):
        # Get the current academic year (assuming academic year starts in August)
        current_year = date.today().year
        # Get all students
        students = Student.objects.all()
        print(students)

        for student in students:
            # Create payment records for each month of the current academic year
            for month in range(1, 13):  # Iterate through all months (January to December)
                # If a payment record doesn't exist for the student in this month
                if not Payment.objects.filter(student=student, academic_year=current_year, month=month).exists():
                    Payment.objects.create(
                        student=student,
                        academic_year=current_year,
                        month=month,
                        payment_status='due',  # Initially marked as due
                        due_date=date(current_year, month, 25),  # Assuming payment due date is 25th of each month
                        monthly_tuition_fee_paid=0.00,  # No payment made initially
                        total_paid=0.00,
                        remaining_due=student.feestructure.monthly_tuition_fee,  # Assuming student fee structure is linked
                    )
                    self.stdout.write(f'Created placeholder payment record for student {student.id} for {date(current_year, month, 1).strftime("%B")}.')
