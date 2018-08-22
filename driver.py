import openride
import time
from openride import print_color

# let's get users and rides
Users, Rides = openride.ethereum_load_Users_Rides()

print_color ("!!! We are about to create new driver")
driver_username = input("Driver username: ")

print_color ("!!! we are genearing private key for you Mr ({})".format(driver_username))
driver_priv_key = openride.generate_private_key()

print_color("!!! your private key that you _MUST_ ride down: " + driver_priv_key)
print_color('Adding user to blockchain, pls wait.')

driver_address = openride.add_user(Users, driver_username, driver_priv_key, driver=False)

if not driver_address:
    print_color ("user could not be created")
    exit(1)

print_color ("!!! your user is created and it's address is: " + driver_address)


#driver_address = "0xDeB4B3cF91fc6cdECBd583a5A6726b25DCeebF2C"


while(True):
    print_color ('!!! lets check if there are any rides close to me')

    current_location = "Krakow"

    rides_close = openride.get_rides_near_me(Rides, current_location)

    if rides_close:
        print_color("!!! there are couple of rides for you available, here is the list")
        for i, ride in enumerate(rides_close):
            ride_user = openride.get_rider(ride)
            username = openride.get_username(ride_user)
            review = openride.get_user_review(ride_user)
            location = openride.get_ride_location(ride)

            print_color ("{}) username ({}) location ({}) review ({})".format(i, username, location, review))

        choice = input("Which ride would you like to accept: ")
        choice = int(choice)

        ride = rides_close[choice]

        print_color("!!! Acceping ride by signing accept_ride() with my private key. Please wait.")

        openride.accept_ride(Rides, ride, driver_address, driver_priv_key)

        print_color("!!! You accepted a Ride, now there should be P2P TOR connection and you should go to fetch CU and than deliver her/him to final location")

        print_color("!!! Let's wait for user to confirm that you finished the ride")

        while(not openride.is_ride_finished(ride)):
            time.sleep(1)


        review = input("!!! Rider confirmed you are guys over with it, how was the ride (0-100): ")
        review = int(review)

        openride.review_rider(ride, review, driver_priv_key)
        print_color('Adding review to blockchain, pls wait.')

    else:
        print_color ("no rides at the moment, let's wait 5 seconds")
        time.sleep(5)

