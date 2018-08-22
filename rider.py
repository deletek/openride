import openride
import time
from openride import print_color

# let's get users and rides
Users, Rides = openride.ethereum_load_Users_Rides()


print_color ("!!! We are about to create new rider")
rider_username = input("Rider username: ")

print_color ("!!! we are genearing private key for you Mr ({})".format(rider_username))
rider_priv_key = openride.generate_private_key()


print_color("!!! your private key that you _MUST_ ride down: " + rider_priv_key)
print_color('Adding user to blockchain, pls wait.')
rider_address = openride.add_user(Users, rider_username, rider_priv_key, driver=False)

if not rider_address:
    print_color ("user could not be created")
    exit(1)

print_color ("!!! your user is created and it's address is: " + rider_address)
print_color(" !!! let's order you a ride")

'''
rider_priv_key = "d5038d7a02053d8b3434f4c73432d1a732a2dcbb1085ec7698077dca93e4358d"
rider_address = "0xcf66C2e8a5Df42Ab5184A9D56D96FF983E2a73Dd"
#ride_address = "0xfec794b978E3d1d1A78f7A3dFDDf8C97e466396C"
'''

location = input("! Your location: ")
print_color('Adding ride to blockchain, pls wait.')
ride_address = openride.add_ride(Rides, rider_address, rider_priv_key, location, "onion_address.onion" )

print_color("!!! taxi has been ordered and ride_address is " + ride_address)

print_color("!!! now we are waiting for driver to pick us up :-)")
while (not openride.is_driver_set(ride_address)):
    time.sleep(1)


driver_address = openride.get_ride_driver(ride_address)
driver_username = openride.get_username(driver_address)

print_color('!!! taxi driver {} picked it up'.format(driver_username))

input("Let me know when you are finished: ")
print_color('Finishing ride in the blockchain, pls wait.')


openride.finish_ride(ride_address, rider_priv_key)


review = input("What is your review for the guy (0-100): ")
review = int(review)
openride.review_driver(ride_address, review, rider_priv_key)
print_color('Adding review to blockchain, pls wait.')

print_color('Thank you for using OpenRide!')



