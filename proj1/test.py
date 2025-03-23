"""
This file has nothing to do with an agent. 
I just test solutions here.
"""

from datetime import datetime

# Get the current date and time
now = datetime.now()

# Format the date as day-month-year
date_str = now.strftime("%d-%m-%Y")

# Get the exact time
time_str = now.strftime("%H:%M:%S")

# Get the day of the week
day_of_week = now.strftime("%A")

result = f"""
Current date: {date_str} (day-month-year)
Current time: {time_str}
Day of the week: {day_of_week}"""

print(result)