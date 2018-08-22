# Disclaimer

This code is really MVP version, it does not cover payments (which is probably really easy to be implemented), it does not cover TOR implementation.
Use it at your own risk, modify it as you want. If you found it useful, you might add positive comments at yasb.it (our blog).

# How to use it ?

First part of the application is Soldity source code that should be deployed in Ethereum.
It's already deployed in Rinkeby Testnet at the address: 
RIDES_ADDRESS ="0x75834b763a4ddccf67f9af8302427a1567613ff4"

# How to configure ride and driver ?
You need to have Account in the Ethereum mainnet/testnet which has some Ether on it, so you can pay transaction fees (with gas).

in OpenRide you can generate Account address and private key by using:

ACCOUNT_ADDRESS, ACCOUNT_PRIVATE_KEY = create_account("PASSWD")

# Connect to the node
You need to configure node that you will connect to, you can do it by modyfing
    web3 = Web3(HTTPProvider('https://rinkeby.infura.io'))

# rider and driver
there are two python3 modules, rider.py and driver.py that you can use. both are depending on openride.py and requirements.txt covert the requirements
