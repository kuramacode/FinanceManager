from dataclasses import dataclass
import datetime

@dataclass
class DateTime:
    FORMAT = "%y:%m:%d %H:%M:%S"
    
    dt: datetime
    
    @classmethod
    def now(cls):
        return cls(datetime.now())
    
    @classmethod
    def from_string(cls, date_str: str):
        dt = datetime.strptime(date_str, cls.FORMAT)
        return cls(dt)
    
    def __str__(self):
        return self.dt.strftime(self.FORMAT)
    
    def __repr__(self):
        return f"MyDateTime('{self}')"
    