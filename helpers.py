
def toLitres(value):

    return f"{value / 33.814:.2f}"

def calculateSleep(age):
    if age in range (1, 2):
        return "11 to 14 hours"
    elif age in range (3, 5, 1):
        return "10 to 13 hours"
    elif age in range (6, 12, 1):
        return "9 to 12 hours"
    elif age in range (13, 18, 1):
        return "8 to 10 hours"
    elif age in range (18, 64, 1):
        return "7 to 9 hours"
    elif age >= 65:
        return "7 to 8 hours"

def cmToFeet(height):
    totalInches = float(height) / 2.54

    feet = int(totalInches / 12)
    inches = totalInches % 12

    return f"{feet} feet {inches:.2f} inches "

def KgToPounds(weight):
    
    return f"{weight * 2.205:.2f} pounds"

def numExtraction(string):
    for i in range(len(string) - 1):
        if string[i].isnumeric():
            if string[i + 1].isnumeric():
                return int((string[i] + string[i + 1]))
            return int((string[i]))