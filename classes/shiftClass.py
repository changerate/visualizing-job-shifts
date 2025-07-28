from utilities.rates import PAY_RATE_TABLE
from datetime import datetime, time, date




class WorkShift:
    def __init__(
        self, 
        date: date,
        clock_in: time, 
        clock_out: time, 
        lunch_in: time = time(1), 
        lunch_out: time = time(1),
        rate_type: str = 'staples copy center', 
        notes: str = "", 
    ):
        # variables
        self._date = date
        self._clock_in = clock_in
        self._clock_out = clock_out
        self._lunch_in = lunch_in
        self._lunch_out = lunch_out
        self._rate_type = rate_type
        self._notes = notes



    @property
    def date(self):
        return self._date

    @property
    def clock_in(self):
        return self._clock_in

    @property
    def clock_out(self):
        return self._clock_out

    @property
    def lunch_in(self):
        return self._lunch_in

    @property
    def lunch_out(self):
        return self._lunch_out

    @property
    def rate_type(self):
        return self._rate_type

    @property
    def notes(self):
        return self._notes


    
    @property
    def view(self):
        """
        EXAMPLE: 
        DATE: 		Tue Jun 17
        IN: 		1:55 PM
        OUT: 		8:33 PM
        Lunch start: 	6:21 PM
        Lunch end: 	6:54 PM
        Shift length: 	6.08
        Payrate: 	staples copy center
        Payrate: 	$18.50 per hour
        Pre-tax: 	$112.54
        """
        print()
        print(f"DATE: \t\t{self.date.strftime("%a %b %d")}")
        print(f"IN: \t\t{self.clock_in.strftime("%-I:%M %p")}")
        print(f"OUT: \t\t{self.clock_out.strftime("%-I:%M %p")}")
        if self.lunch_in == time(1): 
            print("Skipped lunch this shift.")
        else: 
            print(f"Lunch start: \t{self.lunch_in.strftime("%-I:%M %p")}")
            print(f"Lunch end: \t{self.lunch_out.strftime("%-I:%M %p")}")

        print(f"Shift length: \t{self.hours_worked():.2f}")
        print(f"Payrate: \t{self.rate_type}")
        print(f"Payrate: \t${self.hourly_rate:.2f} per hour")
        print(f"Pre-tax: \t${self.before_tax_earnings():.2f}")
        print()
        

    @property
    def hourly_rate(self) -> float:
        return PAY_RATE_TABLE.get(self.rate_type, 0.0)


    def hours_worked(self) -> float:
        shiftLength = datetime.combine(self.date, self.clock_out) - datetime.combine(self.date, self.clock_in)
        lunch = datetime.combine(self.date, self.lunch_out) - datetime.combine(self.date, self.lunch_in)
        # net = (self.clock_out - self.clock_in) - (self.lunch_out - self.lunch_in)
        net = shiftLength - lunch
        return net.total_seconds() / 3600


    def before_tax_earnings(self) -> float:
        return round(self.hours_worked() * self.hourly_rate, 2)


    @staticmethod
    def from_row(row):
        """
        Helps with loading shifts from a SQL database
        """
        print(f"from_row got: {row}")
        return WorkShift(
            date=date.fromisoformat(row[0]),
            clock_in=time.fromisoformat(row[1]),
            clock_out=time.fromisoformat(row[2]),
            lunch_in=time.fromisoformat(row[3]) if row[3] else time(1),
            lunch_out=time.fromisoformat(row[4]) if row[4] else time(1),
            rate_type=row[5],
            notes=row[6]
        )


    def __repr__(self):
        return (f"<WorkShift {self.clock_in.strftime('%-I:%M %p')} - {self.clock_out.strftime('%-I:%M %p')}, "
                f"{self.hours_worked():.2f} hrs, ${self.before_tax_earnings():.2f}, Note: {self.notes}>")