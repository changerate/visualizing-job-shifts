from rates import PAY_RATE_TABLE
from datetime import datetime, timedelta

class WorkShift:
    def __init__(self, clock_in: datetime, clock_out: datetime, rate_type: str, notes: str = "", lunch_in: datetime = datetime(1, 1, 1, 1), lunch_out: datetime = datetime(1, 1, 1, 1)):
        self.clock_in = clock_in
        self.clock_out = clock_out
        self.lunch_in = lunch_in
        self.lunch_out = lunch_out
        self.rate_type = rate_type
        self.notes = notes


    @property
    def view(self):
        """
        EXAMPLE: 
        IN:     Wed Jul 23      8:00 AM
        OUT:    Wed Jul 23      4:00 PM
        Skipped lunch this shift.
        Shift length:   8.0
        Payrate:        copy center
        Payrate:        $18.50 per hour
        Pre-tax:        $148.00
        """
        print()
        print(f"IN: \t{self.clock_in.strftime("%a %b %d\t%-I:%M %p")}")
        print(f"OUT: \t{self.clock_out.strftime("%a %b %d\t%-I:%M %p")}")
        if self.lunch_in == datetime(1, 1, 1, 1): 
            print("Skipped lunch this shift.")
        else: 
            print(f"Lunch start: \t{self.lunch_in.strftime("%a %b %d\t%-I:%M %p")}")
            print(f"Lunch end: \t{self.lunch_out.strftime("%a %b %d\t%-I:%M %p")}")

        print(f"Shift length: \t{self.hours_worked()}")
        print(f"Payrate: \t{self.rate_type}")
        print(f"Payrate: \t${self.hourly_rate:.2f} per hour")
        print(f"Pre-tax: \t${self.before_tax_earnings():.2f}")
        print()
        

    @property
    def hourly_rate(self) -> float:
        return PAY_RATE_TABLE.get(self.rate_type, 0.0)


    def hours_worked(self) -> float:
        net = (self.clock_out - self.clock_in) - (self.lunch_out - self.lunch_in)
        return net.total_seconds() / 3600


    def before_tax_earnings(self) -> float:
        return round(self.hours_worked() * self.hourly_rate, 2)


    def __repr__(self):
        return (f"<WorkShift {self.clock_in.strftime('%Y-%m-%d %H:%M')} - {self.clock_out.strftime('%H:%M')}, "
                f"{self.hours_worked():.2f} hrs, ${self.before_tax_earnings():.2f}, Note: {self.notes}>")