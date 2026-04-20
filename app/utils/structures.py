from dataclasses import dataclass
import datetime

@dataclass
class DateTime:
    FORMAT = "%y:%m:%d %H:%M:%S"
    
    dt: datetime
    
    @classmethod
    def now(cls):
        """Повертає поточне значення дати часу."""
        return cls(datetime.now())
    
    @classmethod
    def from_string(cls, date_str: str):
        """Створює об’єкт з рядкового значення."""
        dt = datetime.strptime(date_str, cls.FORMAT)
        return cls(dt)
    
    def __str__(self):
        """Повертає рядкове подання об’єкта."""
        return self.dt.strftime(self.FORMAT)
    
    def __repr__(self):
        """Повертає технічне подання об’єкта."""
        return f"MyDateTime('{self}')"
    
