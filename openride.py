from web3.auto import w3
from secp256k1 import PrivateKey, PublicKey
from eth_keys import keys
from eth_utils import keccak
from rlp.utils import decode_hex
import string
import random
from web3 import Web3, HTTPProvider, TestRPCProvider, IPCProvider
import time
from web3.middleware import geth_poa_middleware

import warnings


import json

LOG = 0

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_color(text):
    print(bcolors.BOLD  + text + bcolors.ENDC)

def log(a, *args, **kwargs):
    if not LOG:
        return None

    print(a, args, kwargs)

# we are assuming that contract is already deployed, if not deploy it somewhere else (geth) and put rides_address here

RIDES_ADDRESS ="0x75834b763a4ddccf67f9af8302427a1567613ff4"

RIDES_ABI_FILE = open('OpenRide_sol_Rides.abi')
USERS_ABI_FILE = open('OpenRide_sol_Users.abi')
USER_ABI_FILE = open('OpenRide_sol_User.abi')
RIDE_ABI_FILE = open('OpenRide_sol_Ride.abi')

WAIT_FOR_TRANSACTION_CONF = 1


def create_account(password):
    w3.eth.enable_unaudited_features()

    acct = w3.eth.account.create(password)

    return  acct.address, acct.privateKey.hex()


# this should be done first time
ACCOUNT_ADDRESS, ACCOUNT_PRIVATE_KEY = create_account("PASSWD")

# gas example
gas_limit = 250000
gas_price = 60



def generate_private_key():
    return PrivateKey().private_key.hex()

def send_transaction(transaction):
    txnCount = web3.eth.getTransactionCount(ACCOUNT_ADDRESS)
    transaction['nonce'] = web3.toHex(txnCount)

    #transaction['nonce']
    #transaction['gas'] = gas_limit,
    #transaction['gasPrice']  = int(gas_price * (10 ** 9)),
    signed = web3.eth.account.signTransaction(transaction, ACCOUNT_PRIVATE_KEY)

    return web3.eth.sendRawTransaction(signed.rawTransaction)

def to_32byte_hex(val):
    return Web3.toHex(Web3.toBytes(val).rjust(32, b'\0'))

def my_eth_sign_sha3(data):
    """
    eth_sign/recover compatible hasher
    Prefixes data with "\x19Ethereum Signed Message:\n<len(data)>"
    """
    prefix = "0x19457468657265756d205369676e6564204d6573736167653a0a000000000000"[2:]

    length = len(data)
    length = hex(length)[2:].zfill(64) # we need to fill it with zeros on the left up to maximum length == 64

    #length = "0x0000000000000000000000000000000000000000000000000000000000000004"
    #data = "0x3230313800000000000000000000000000000000000000000000000000000000"

    # text needs zeros on the right in soldity, don't ask me why, so we invert twice ...
    data = ''.join(r'{0:x}'.format(ord(c)) for c in data)[::-1].zfill(64)[::-1]


    #my_hash = decode_hex(prefix[2:].zfill(64)) + decode_hex(length[2:].zfill(64))
    concat = decode_hex(prefix) + decode_hex(length) + decode_hex(data)

    hash = "0x" + keccak(concat).hex()

    log("Data as stored in blockchain", "0x" + data)
    return hash

def get_public_key(priv_key):
    privkey = PrivateKey(bytes(bytearray.fromhex(priv_key)), raw=True)
    private_key = keys.PrivateKey(privkey.private_key)

    return private_key.public_key

def sign_message_preparing_for_ec_recover(msg, priv_key):
    privkey = PrivateKey(bytes(bytearray.fromhex(priv_key)), raw=True)
    private_key = keys.PrivateKey(privkey.private_key)

    address = private_key.public_key.to_checksum_address()

    #log("address", address)

    message_hash = my_eth_sign_sha3(msg)


    #log(Web3.toHex(message_hash))

    signed_message = web3.eth.account.signHash(message_hash, private_key=private_key)

    #log(signed_message)

    ec_recover_args = (msghash, v, r, s) = (
        Web3.toHex(signed_message.messageHash), signed_message.v, to_32byte_hex(signed_message.r),
        to_32byte_hex(signed_message.s))

    return ec_recover_args

def prepare_random_bytes32():
    msg = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))

    return msg

def sign_stuff():
    msg = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))
    log("Random generated is", msg)
    #msg = keccak(msg.1())
    #msg =  msg
    #log(msg)

    priv_key = "31a84594060e103f5a63eb742bd46cf5f5900d8406e2726dedfc61c7cf43ebad"
    public_key = get_public_key(priv_key)

    log(sign_message_preparing_for_ec_recover(msg, priv_key))
    log("public key", public_key)

def convert_string_to_bytes32(msg):
    return ''.join(r'{0:x}'.format(ord(c)) for c in msg)

def ethereum_load_Users_Rides():
    RIDES_ABI_FILE.seek(0)
    USERS_ABI_FILE.seek(0)

    rides_abi = json.load(RIDES_ABI_FILE)
    users_abi = json.load(USERS_ABI_FILE)

    # let's fetch Rides 0x972a1b41266a7d55e8bf0fa19464af497bde0cd2
    rides_address = web3.toChecksumAddress(RIDES_ADDRESS)
    Rides = web3.eth.contract(address=rides_address, abi=rides_abi)

    log("Adress of Rides", rides_address)

    # let's fetch Users now, call() is for free, transaction() is paid
    # https://ethereum.stackexchange.com/questions/765/what-is-the-difference-between-a-transaction-and-a-call

    users_address = Rides.functions.get_users_address().call()
    users_address = web3.toChecksumAddress(users_address)

    log("Address of Users", users_address)

    Users = web3.eth.contract(address=users_address, abi=users_abi)

    return Users, Rides

def get_returned_address(contract, unique_id, ttl=255):
    # we don't want to use events, since events are not supported on most of the public nodes
    if ttl == 0: # ttl
        return None

    result = contract.functions.get_return_address(unique_id).call()

    if result and result != '0x0000000000000000000000000000000000000000':
        return result;

    log ("there is no returned address yet in the events, let's try again")
    # if we found nothing, let's wait a little and try again
    time.sleep(2)
    return get_returned_address(contract, unique_id, ttl-1)

def get_user_detail(address_of_user):
    USER_ABI_FILE.seek(0)

    user_abi = json.load(USER_ABI_FILE)

    # let's fetch Rides
    user = web3.eth.contract(address=address_of_user, abi=user_abi)

    return(user.functions.get_public_key().call())


def get_username(address_of_user):
    USER_ABI_FILE.seek(0)

    user_abi = json.load(USER_ABI_FILE)

    # let's fetch Rides
    user = web3.eth.contract(address=address_of_user, abi=user_abi)

    return(user.functions.get_username().call()).split(b'\0', 1)[0]

def wait_for_transaction(tx):
    if not WAIT_FOR_TRANSACTION_CONF:
        return None

    log("Waiting for transaction {} to be mined".format(tx.hex()))
    while(True):
        receipt = web3.eth.getTransactionReceipt(tx)

        if receipt:
            log("Transaction {} has been mined in block: {}".format(tx.hex(), receipt.blockNumber))

            return receipt

        time.sleep(0.1)

def add_user(Users, username, priv_key, driver=False):
    # let's add first rider
    public_key = str(get_public_key(priv_key))
    log("public_key of the user {}: {}".format(username, get_public_key(priv_key)))
    username = "0x" + convert_string_to_bytes32(username)

    #log(username, public_key)

    # this needs to be transaction
    if driver:
        transaction = Users.functions.add_driver(username, public_key).buildTransaction()
    else:
        transaction = Users.functions.add_rider(username, public_key).buildTransaction()

    user_tx = send_transaction(transaction)

    role = { 0: "rider", 1 : "driver"}

    log("User with role ({}) added in transaction {}".format(role[driver], user_tx.hex()))

    #wait_for_transaction(user_tx)
    # i don't like this way
    user_address = get_returned_address(Users, username)

    #log(web3.eth.getTransactionReceipt(user1_tx))
    return user_address
    #receipt = web3.eth.waitForTransactionReceipt(user1)

def get_rider(username, Users):
    username = "0x" + convert_string_to_bytes32(username)
    return Users.functions.get_rider(username).call()

def get_driver(username, Users):
    username = "0x" + convert_string_to_bytes32(username)
    return Users.functions.get_driver(username).call()

def convert_to_address(address):
    if not address.startswith("0x"):
        return "0x" + address

def convert_to_bytes32(data):
    return convert_to_address(data)

def add_ride(Rides, rider_address, priv_key, location, onion_address):
    log("add_ride()")
    ride_address = ""

    #rider_address = rider_address.encode().hex() # address
    rider_adderss = convert_to_address(rider_address)
    location = convert_to_bytes32(location.encode().hex()) # bytes32
    onion_address = convert_to_bytes32(onion_address.encode().hex()) # string


    msgh = "" # bytes32
    v = "" # uint
    r = "" # bytes32
    s = "" # bytes32
    random_used = "" # bytes32

    # preparing authentication data
    random_used = prepare_random_bytes32()
    (msgh, v, r, s) = sign_message_preparing_for_ec_recover(random_used, priv_key)
    random_used = "0x" + random_used.encode().hex()

    # convert stuff
    '''random_used = random_used.encode().hex()
    msgh = msgh.encode().hex()
    r = r.encode().hex()
    s = s.encode().hex()
    location = location.encode().hex()
    '''
    #(rider_address, location, onion_address, msgh, r, s, random_used) = ("", "", "", "", "", "", '"')
    # = 0

    try:
        transaction = Rides.functions.add_ride(rider_address, location, onion_address, msgh, v, r, s, random_used).buildTransaction()
        tx_hash = send_transaction(transaction)
    except ValueError:
        log("CRASH!!! It looks like something went wrong while checking signature")
        return None

    wait_for_transaction(tx_hash)
    # argument 3
    #v=11
    #random_used = '0x585538534b345451484e4843594b353434573354435555554f4456453654444b'
    ride_address = get_returned_address(Rides, random_used) # TODO I don't like this that much, I think if we do it by events, when we post even we should be able to corealte input with event without a doubt (state)

    log("Ride address", ride_address)

    return ride_address

def get_rides_near_me(Rides, current_location):
    current_location = convert_to_bytes32(current_location.encode().hex())
    rides_close = Rides.functions.get_ride_near_me(current_location).call()

    #log("rides_close", rides_close)

    return rides_close

def get_ride_location(ride_address):
    RIDE_ABI_FILE.seek(0)
    ride_abi = json.load(RIDE_ABI_FILE)
    ride_address = web3.toChecksumAddress(ride_address)

    Ride = web3.eth.contract(address=ride_address, abi=ride_abi)

    return Ride.functions.get_ordering_location().call().split(b'\0', 1)[0].decode('utf-8')

def review_driver(ride_address, review, rider_priv_key):
    RIDE_ABI_FILE.seek(0)
    ride_abi = json.load(RIDE_ABI_FILE)
    ride_address = web3.toChecksumAddress(ride_address)

    Ride = web3.eth.contract(address=ride_address, abi=ride_abi)

    # preparing authentication data
    random_used = prepare_random_bytes32()
    (msgh, v, r, s) = sign_message_preparing_for_ec_recover(random_used, rider_priv_key)
    random_used = "0x" + random_used.encode().hex()

    transaction =  Ride.functions.review_driver(review, msgh, v, r, s, random_used).buildTransaction()
    tx_hash = send_transaction(transaction)

    wait_for_transaction(tx_hash)

def review_rider(ride_address, review, driver_priv_key):
    RIDE_ABI_FILE.seek(0)
    ride_abi = json.load(RIDE_ABI_FILE)
    ride_address = web3.toChecksumAddress(ride_address)

    Ride = web3.eth.contract(address=ride_address, abi=ride_abi)

    # preparing authentication data
    random_used = prepare_random_bytes32()
    (msgh, v, r, s) = sign_message_preparing_for_ec_recover(random_used, driver_priv_key)
    random_used = "0x" + random_used.encode().hex()

    transaction =  Ride.functions.review_rider(review, msgh, v, r, s, random_used).buildTransaction()
    tx_hash = send_transaction(transaction)

    wait_for_transaction(tx_hash)

def is_ride_finished(ride_address):
    RIDE_ABI_FILE.seek(0)
    ride_abi = json.load(RIDE_ABI_FILE)
    ride_address = web3.toChecksumAddress(ride_address)

    Ride = web3.eth.contract(address=ride_address, abi=ride_abi)

    return Ride.functions.is_finished().call()

def finish_ride(ride_address, rider_priv_key):
    RIDE_ABI_FILE.seek(0)
    ride_abi = json.load(RIDE_ABI_FILE)
    ride_address = web3.toChecksumAddress(ride_address)

    Ride = web3.eth.contract(address=ride_address, abi=ride_abi)

    # preparing authentication data
    random_used = prepare_random_bytes32()
    (msgh, v, r, s) = sign_message_preparing_for_ec_recover(random_used, rider_priv_key)
    random_used = "0x" + random_used.encode().hex()

    transaction = Ride.functions.finish_ride(msgh, v, r, s, random_used).buildTransaction()
    tx_hash = send_transaction(transaction)

    wait_for_transaction(tx_hash)

def get_rider(ride_address):
    RIDE_ABI_FILE.seek(0)
    ride_abi = json.load(RIDE_ABI_FILE)
    ride_address = web3.toChecksumAddress(ride_address)

    Ride = web3.eth.contract(address=ride_address, abi=ride_abi)

    return Ride.functions.get_rider().call()

def get_ride_driver(ride_address):
    RIDE_ABI_FILE.seek(0)
    ride_abi = json.load(RIDE_ABI_FILE)
    ride_address = web3.toChecksumAddress(ride_address)

    Ride = web3.eth.contract(address=ride_address, abi=ride_abi)

    return Ride.functions.get_driver().call()


def get_user_review(user_address):
    USER_ABI_FILE.seek(0)

    user_abi = json.load(USER_ABI_FILE)

    # let's fetch Rides
    user = web3.eth.contract(address=user_address, abi=user_abi)

    return(user.functions.get_review().call())

def is_driver_set(ride_address):
    RIDE_ABI_FILE.seek(0)
    ride_abi = json.load(RIDE_ABI_FILE)
    ride_address = web3.toChecksumAddress(ride_address)

    Ride = web3.eth.contract(address=ride_address, abi=ride_abi)

    return Ride.functions.is_driver_set().call()

def accept_ride(Rides, ride_address, driver_address, priv_key):
    random_used = prepare_random_bytes32()
    (msgh, v, r, s) = sign_message_preparing_for_ec_recover(random_used, priv_key)
    random_used = "0x" + random_used.encode().hex()

    #tx_hash = Rides.functions.accept_ride(ride_address, driver_address, msgh, v, r, s, random_used).transact()
    transaction = Rides.functions.accept_ride(ride_address, driver_address, msgh, v, r, s, random_used).buildTransaction()

    tx_hash = send_transaction(transaction)

    wait_for_transaction(tx_hash)
    log('rides accepted (was it? probably we should have event here)', tx_hash.hex())

def web3_init():

    # probably we should go into https://infura.io/
    web3 = Web3(HTTPProvider('https://rinkeby.infura.io'))

    #web3 = Web3(IPCProvider("/Users/pkupisie/Library/Ethereum/rinkeby/geth.ipc"))

    #web3.eth.defaultAccount = w3.eth.accounts[0]

    web3.eth.enable_unaudited_features()

    # needed for rinkeby: https://ethereum.stackexchange.com/questions/44130/rinkeby-failure-with-web3-py-could-not-format-value-0x-as-field-extrada/44131#44131
    web3.middleware_stack.inject(geth_poa_middleware, layer=0)

    return web3

def test():
    web3 = web3_init()

    # let's get users and rides
    Users, Rides = ethereum_load_Users_Rides()

    # let's try to add test user
    priv_key = "31a84594060e103f5a63eb742bd46cf5f5900d8406e2726dedfc61c7cf43ebad"
    rider_username = "michal3"
    driver_username = "radek3"

    # ------- create user
    rider_address = add_user(Users, rider_username, priv_key, driver=False)
    driver_address = add_user(Users, driver_username, priv_key, driver=True)

    # ------- read existing user from DB
    #rider_address = get_rider(rider_username, Users)
    #driver_address = get_driver(driver_username, Users)

    # ------- CLIENT SIDE

    # ------- add ride
    #log("rider_address", rider_address)
    #ride_address = add_ride(Rides, rider_address, priv_key, "location", "onion_address.onion" )
    # ride address 0x5e3622e5E1783C9dE1A546A93710e5187bE9D76d


    # ------- DRIVER SIDE

    # ------- get rides without a driver close to me
    current_location = "0x6666"
    rides_close = get_rides_near_me(Rides, current_location)

    # ------- let's pick first one
    # ride address 0xc2edFF8D1AfEF9f577130F7eEa07ee6C904b791C

    if len(rides_close) == 0:
        log(" no rides anymore")
        exit(1)

    ride_address = rides_close[0]

    # ------- display location
    #ride_address = "0xc2edFF8D1AfEF9f577130F7eEa07ee6C904b791C"
    #location = get_ride_location(ride_address)

    log("is driver set: ", is_driver_set(ride_address))
    log("accepting the ride by driver", driver_address)
    # accept the ride
    accept_ride(Rides, ride_address, driver_address, priv_key)

    log("is driver set: ", is_driver_set(ride_address))

    # we probably should check, that this is really us who accepted it, since they might be hazard

    # check if it's accepted

    # do the tor magic
    # payment and review

web3 = web3_init()
