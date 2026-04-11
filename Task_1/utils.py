from datetime import datetime
import hashlib
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Select

# Hash the password by SHA256 algorithm to protect sensitive data
def hashPassword(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

class DatePicker(Horizontal):
    monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

    def __init__(self, id: str = None, classes: str = None, defaultDate: str = ""):
        super().__init__(id=id, classes=classes)
        if defaultDate:
            try:
                dateTimeValue = datetime.strptime(defaultDate, "%Y-%m-%d")
            except ValueError:
                dateTimeValue = datetime.now()
        else:
            dateTimeValue = datetime.now()

        self.defaultYear = str(dateTimeValue.year)
        self.defaultMonth = f"{dateTimeValue.month:02d}"
        self.defaultDay = f"{dateTimeValue.day:02d}"

    def yearOptions(self):
        currentYear = datetime.now().year
        return [(str(year), str(year)) for year in range(currentYear - 100, currentYear + 10)]

    def monthOptions(self):
        return [(f"{name}", f"{month:02d}") for month, name in enumerate(self.monthNames, start=1)]

    def isLeapYear(self, year: int) -> bool:
        return (year % 400 == 0) or (year % 4 == 0 and year % 100 != 0)

    def daysInMonth(self, year: int, month: int) -> int:
        if month in (1, 3, 5, 7, 8, 10, 12):
            return 31
        if month in (4, 6, 9, 11):
            return 30
        return 29 if self.isLeapYear(year) else 28

    def dayOptions(self, year: int, month: int):
        return [(f"{day:02d}", f"{day:02d}") for day in range(1, self.daysInMonth(year, month) + 1)]

    def selectedYearMonth(self) -> tuple[int, int]:
        yearSelect = self.query_one(".year-select", Select)
        monthSelect = self.query_one(".month-select", Select)

        yearValue = yearSelect.value
        monthValue = monthSelect.value

        year = int(yearValue) if yearValue != Select.BLANK else int(self.defaultYear)
        month = int(monthValue) if monthValue != Select.BLANK else int(self.defaultMonth)
        return year, month

    def updateDayOptions(self):
        daySelect = self.query_one(".day-select", Select)
        currentDay = daySelect.value
        year, month = self.selectedYearMonth()
        maxDay = self.daysInMonth(year, month)
        daySelect.set_options(self.dayOptions(year, month))

        if currentDay != Select.BLANK:
            clampedDay = min(int(currentDay), maxDay)
            daySelect.value = f"{clampedDay:02d}"

    def compose(self) -> ComposeResult:
        yield Select(self.yearOptions(), prompt="Year", classes="dob_picker year-select", allow_blank=False, value=self.defaultYear)
        yield Select(self.monthOptions(), prompt="Month", classes="dob_picker month-select", allow_blank=False, value=self.defaultMonth)
        yield Select(self.dayOptions(int(self.defaultYear), int(self.defaultMonth)), prompt="Day", classes="dob_picker day-select", allow_blank=False, value=self.defaultDay)

    def on_mount(self) -> None:
        self.updateDayOptions()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.has_class("year-select") or event.select.has_class("month-select"):
            self.updateDayOptions()

    @property
    def value(self):
        year = self.query_one(".year-select", Select).value
        month = self.query_one(".month-select", Select).value
        day = self.query_one(".day-select", Select).value
        if year == Select.BLANK or month == Select.BLANK or day == Select.BLANK:
            return None
        return f"{year}-{month}-{day}"
