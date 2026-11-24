DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def is_leap(y):
    return y % 4 == 0 and y % 100 != 0

def is_valid_date(y, m, d):
    if not 1 <= m <= 12:
        return False
    return 1 <= d <= DAYS[m - 1]
