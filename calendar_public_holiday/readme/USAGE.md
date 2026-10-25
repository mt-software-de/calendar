For adding public holidays:

1.  Go to the menu *Calendar \> Public Holidays \> Public Holidays*.
2.  Create your public holidays.

For generating public holidays from a template:

1.  Go to the menu *Calendar \> Public Holidays \> Public Holiday Templates*.
2.  Create a template for a country and add its holidays. The "Date
    Type" of a holiday defines how its date is determined:
    - *Fixed Date*: the day and month of "Date" are used every year
      (the year of the date is ignored).
    - *Easter Sunday*: the date of Easter Sunday of the year.
    - *Calculated (Python Code)*: the date is calculated by the python
      code in "Python Code", which must assign the date to `result`,
      e.g. the Wednesday before November 23rd:
      `result = datetime.date(year, 11, 22) + relativedelta.relativedelta(weekday=relativedelta.WE(-1))`.
      The variables `year`, `datetime` (module), `relativedelta`
      (module `dateutil.relativedelta`) and `easter(year)` are
      available.

    The number of days in "Day Offset" is added to the date, use a
    negative value to subtract days (e.g. Good Friday is Easter Sunday
    with an offset of -2).
3.  Set the year and press "Generate Holidays". The public holidays of
    that year and country are created, existing ones are replaced.
