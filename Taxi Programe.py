## TAXI ##
print("Welcome to Uber")
print("1-> WagonR")
print("2-> Dzire")
print("3-> Swift")
print("4-> Ciaz")
c=int(input("Choose Your Car Model: "))

if c==1:
    s=int(input("Meter Reading at Starting of trip"))
    e=int(input("Meter Reading at End of trip"))
    t=int(input("Total time taken (in minutes)"))
    d=e-s
    print("Your Car Model is WagonR:(AP 05 AE 8887)")
    print("Total kilometeres driven today:=", d)
    print("Duration of Trip:=")
    Base_fare=100
    cost_per_kilometer=9
    cost_per_minute=2.5
    minimum_fare=20
#
    total_km = (cost_per_kilometer*d)+Base_fare
    total_tm = (cost_per_minute*t)
    total_fare = (cost_per_kilometer*d)+Base_fare+(cost_per_minute*t)
    if total_fare < minimum_fare:
        total_fare = minimum_fare
    print("Total fare:Rs.", total_fare)
elif c==2:
    s=int(input("Meter Reading at Starting of trip"))
    e=int(input("Meter Reading at End of trip"))
    t=int(input("Total time taken (in minutes)"))
    d=e-s
    print("Your Car Model is Dzire:(AP 05 HU 2356)")
    print("Total kilometeres driven today:=", d)
    print("Duration of Trip:=")
    Base_fare=100
    cost_per_kilometer=12
    cost_per_minute=2.5
    minimum_fare=20
#
    total_km = (cost_per_kilometer*d)+Base_fare
    total_tm = (cost_per_minute*t)
    total_fare = (cost_per_kilometer*d)+Base_fare+(cost_per_minute*t)
    if total_fare < minimum_fare:
        total_fare = minimum_fare
    print("Total fare:Rs.", total_fare)
elif c==3:
    s=int(input("Meter Reading at Starting of trip"))
    e=int(input("Meter Reading at End of trip"))
    t=int(input("Total time taken (in minutes)"))
    d=e-s
    print("Your Car Model is Swift:(HR 55 CV 8927)")
    print("Total kilometeres driven today:=", d)
    print("Duration of Trip:=")
    Base_fare=100
    cost_per_kilometer=12
    cost_per_minute=2.5
    minimum_fare=20
#
    total_km = (cost_per_kilometer*d)+Base_fare
    total_tm = (cost_per_minute*t)
    total_fare = (cost_per_kilometer*d)+Base_fare+(cost_per_minute*t)
    if total_fare < minimum_fare:
        total_fare = minimum_fare
    print("Total fare:Rs.", total_fare)
elif c==4:
    s=int(input("Meter Reading at Starting of trip"))
    e=int(input("Meter Reading at End of trip"))
    t=int(input("Total time taken (in minutes)"))
    d=e-s
    print("Your Car Model is Ciaz:(HR 26 AX 6789)")
    print("Total kilometeres driven today:=", d)
    print("Duration of Trip:=")
    Base_fare=150
    cost_per_kilometer=15
    cost_per_minute=2.5
    minimum_fare=50
#
    total_km = (cost_per_kilometer*d)+Base_fare
    total_tm = (cost_per_minute*t)
    total_fare = (cost_per_kilometer*d)+Base_fare+(cost_per_minute*t)
    if total_fare < minimum_fare:
        total_fare = minimum_fare
    print("Total fare:Rs.", total_fare)