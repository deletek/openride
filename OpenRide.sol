pragma solidity ^0.4.0;

library ECVerify {
    function ecr (bytes32 msgh, uint8 v, bytes32 r, bytes32 s) internal returns (address sender) {
            return ecrecover(msgh, v, r, s);
    }


    function verify(address _user, bytes32 msgh, uint8 v, bytes32 r, bytes32 s, bytes32 random_used) internal returns (bool) {
        bytes32  prefix = "\x19Ethereum Signed Message:\n";
        bytes32  length = 32;
        bytes32  data = random_used;
        bytes32 prefixedHash = sha3(prefix, length, data);
        
        // TODO: random used should be stored in DB to avoid anti-replays
        // here we should verify if random was not used in the past already

        if (msgh != prefixedHash) {
            return false;
        }
        //log1("1", toBytes(message.length));

        address result = ecr(msgh, v, r, s);
        
        User user = User(_user);

        if (user.get_public_key_address() != result) {
            return false;
        }
        
        
        return true;
    }
}

contract User {
    /* Define variable owner of the type address */
    bytes32 internal username;
    address internal owner = msg.sender;
    address internal rides_address;

    bool internal is_driver_bool;
    address [] internal HistoricalRides;
    
    /*struct Image{
      bytes32 imageHash;
      string ipfsInfo; // we need string since this can be long
    }*/
    
    //Image internal photo;
    
    uint internal creationTime = now;

    bytes internal public_key;
    address internal public_key_address;

    /* This function is executed at initialization and sets the owner of the contract */
    function User(bytes32 _username, bytes _public_key, bool _is_driver, address _rides_address) public { 
        owner = msg.sender;
        public_key = _public_key;
        username = _username;
        
        public_key_address =  address(keccak256(public_key));
        is_driver_bool = _is_driver;
        
        rides_address = _rides_address;
        
        //photo.imageHash = _imageHash;
        //photo.ipfsInfo = _ipfsInfo;
        
    }

    function get_username()  returns (bytes32) {
        return username;
    }
    
    function get_public_key()  returns (bytes) {
        return public_key;
    }
    
    /*function get_photo_hash() constant returns (bytes32) {
        return photo.imageHash;
    }
    
    function get_photo_url() constant returns (string) {
        return photo.ipfsInfo;
    }*/
    
    // authentication required
    function add_historical_ride(address _ride) public {
        require(
            msg.sender == rides_address,
            "Sender not authorized."
        );
        HistoricalRides.push(_ride);
    }
    
    function get_historical_rides() public returns (address []) {
        return HistoricalRides;
    }
    
    function get_public_key_address() public returns (address) {
        return public_key_address;
    }
    
    function is_driver() public returns (bool) {
        return is_driver_bool;
    }
    
    function get_creation_time() public returns (uint) {
        return creationTime;
    }
    
    function get_review() public returns (uint) {
        uint sum = 0;
        uint rides_with_review = 0;
        for (uint i = 0; i < HistoricalRides.length; i++) {
            Ride ride = Ride(HistoricalRides[i]);
            uint review_score = ride.get_review(is_driver_bool);
            
            if (review_score !=0 ) {
                sum += ride.get_review(is_driver_bool);
                rides_with_review += 1;
            }
            
            
        }
        if (rides_with_review == 0) {
            return 0;
        }
        return sum/rides_with_review;
    }
    
    /* TODO functions that change public_key, image etc. */
}

/* We will use one user for now
contract Driver is User {
    function Driver(bytes32 _username, bytes _public_key, bytes32 _imageHash, string _ipfsInfo) 
        User(_username, _public_key, _imageHash, _ipfsInfo) {}

}
*/

/*
contract Rider is User {
    function Rider(bytes32 _username, bytes _public_key, bytes32 _imageHash, string _ipfsInfo) 
          User(_username, _public_key, _imageHash, _ipfsInfo) { }
}*/

contract Users {
    address internal owner = msg.sender;
    address internal rides_address;

    /* this should be created only by riders */
    function Users() public {
        rides_address = msg.sender;
    }

    mapping(bytes32 => address) internal ReturnValue;

    // Drivers
    mapping(bytes32 => User) internal DriversMapping;
    address[] internal DriversArray;
    

    function add_driver(bytes32 _username, bytes _public_key) public returns (address) {
        // let's first make sure that driver does not exist
        require(
            !is_user_used(_username, DriversArray),
            "Username exists."
        );
        
        User driver = new User(_username, _public_key,  true, rides_address);
        
        DriversMapping[_username] = driver;
        DriversArray.push(driver);
        
        ReturnValue[_username] = driver;
        return driver;
        
    }
    
    function get_return_address(bytes32 _unique_id) public returns (address) {
        
        return ReturnValue[_unique_id];
    }

 
    function get_driver(bytes32 _username) public returns (User) {
        return DriversMapping[_username];
    }
    
    function is_user_used(bytes32 _username, address [] UsersArray) public returns (bool) {
        for (uint i = 0; i < UsersArray.length; i++) {
            User user = User(UsersArray[i]);
            if (user.get_username() == _username) {
                return true;
            }
        }
        
        return false;
    }

    
    // Riders
    mapping(bytes32 => User) internal RidersMapping;
    address[] internal RidersArray;


    function add_rider(bytes32 _username, bytes _public_key) public returns (address) {
        // let's first make sure that driver does not exist
        require(
            !is_user_used(_username, RidersArray),
            "Username exists."
        );
        
        User rider = new User(_username, _public_key, false, rides_address);
        
        RidersMapping[_username] = rider;
        RidersArray.push(rider);
        
        ReturnValue[_username] = rider;
        return rider;
    }

    
    function get_rider(bytes32 _username) public returns (User) {
        return RidersMapping[_username];
    }
    
}

contract Ride {
    address internal rider;
    bytes32 internal riders_ordering_location;
    string internal riders_onion_address;
    
    address internal owner = msg.sender;
    uint internal creationTime = now;
    bool internal finished = false; // is Ride finished

    
    address internal driver;
    
    uint rider_review;
    uint driver_review;
    
    function Ride(address _rider, bytes32 _location, string _onion_address) public {
        rider = _rider;
        
        riders_ordering_location = _location;
        riders_onion_address = _onion_address;
    }
    
    function is_driver_set() public returns (bool) {
        if (driver == address(0)) {
            return false;
        }
        return true;
    }
    
    function set_driver(address _driver) {
        require(
            msg.sender == owner,
            "Sender not authorized."
        );
        
        driver = _driver;
    }
    
    function get_creation_time() public returns (uint) {
        return creationTime;
    }
    
    
    function get_ordering_location() public returns (bytes32) {
        return riders_ordering_location;
    }
    
    
    function get_riders_onion_addrses() public returns (string) {
        return riders_onion_address;
    }
    
    function finish_ride(bytes32 msgh, uint8 v, bytes32 r, bytes32 s, bytes32 random_used) public {
        require(
            (ECVerify.verify(rider, msgh, v, r, s, random_used) == true),
            "Only rider can finish a ride"
        );
        
        finished = true;
    }
    
    function is_finished() public returns (bool) {
        return finished;
    }
    
    function review_driver(uint review, bytes32 msgh, uint8 v, bytes32 r, bytes32 s, bytes32 random_used) public { // yes it is possible to change review later on
        require(
            review >= 0 && review <= 100, "review must be between 0 and 100"
            );
        
        require(
            (ECVerify.verify(rider, msgh, v, r, s, random_used) == true),
            "only rider can review a driver"
        );
            
        driver_review = review;
    }
    
    function review_rider(uint review, bytes32 msgh, uint8 v, bytes32 r, bytes32 s, bytes32 random_used) public {
        require(
            review >= 0 && review <= 100, "review must be between 0 and 100"
            );
        require(
            (ECVerify.verify(driver, msgh, v, r, s, random_used) == true),
            "only driver can review a rider."
        );
        rider_review = review;            
    }
    
    function get_review(bool is_driver) public returns (uint) {
        if (is_driver){
            require(
                msg.sender == driver, 'only driver can get driver review'
                );
            return driver_review;
        }
        if (!is_driver){
            require(
                msg.sender == rider, 'only driver can get driver review'
                );
            return rider_review;       
        }
    }
    
    function get_rider() public returns (address) {
        return rider;
    }
    
    function get_driver() public returns (address) {
        return rider;
    }
}

contract Rides {
    
    mapping(bytes32 => address) internal ReturnValue;

    address[] internal RidesArray;
    address[] internal RidesWithoutADriverArray;
    
    Users internal users;
    
    function Rides() public {
        users = new Users();
    }
    
    function add_ride(address _rider, bytes32 _location, string _onion_address, bytes32 msgh, uint8 v, bytes32 r, bytes32 s, bytes32 random_used) returns (address) {
        
        require(
            (ECVerify.verify(_rider, msgh, v, r, s, random_used) == true),
            "you don't have proper private key my friend."
        );

        User rider = User(_rider);

        Ride ride = new Ride(_rider, _location, _onion_address);
        rider.add_historical_ride(ride);

        RidesWithoutADriverArray.push(ride);

        ReturnValue[random_used] = ride;
        
        return ride;
    }
    
    function get_return_address(bytes32 _unique_id) public returns (address) {
        
        return ReturnValue[_unique_id];
    }
    
    function accept_ride(address _ride, address _driver, bytes32 msgh, uint8 v, bytes32 r, bytes32 s, bytes32 random_used) public returns (bool) {
        Ride ride = Ride(_ride);

        if (ride.is_driver_set() == true)
            return false;
            
        require(
            (ECVerify.verify(_driver, msgh, v, r, s, random_used) == true),
            "you don't have proper private key my friend."
        );
        
        
        for (uint i = 0; i<RidesWithoutADriverArray.length; i++){
            if (_ride == RidesWithoutADriverArray[i]) {
                // just copy the last element instead of this one and remove last one
                RidesWithoutADriverArray[i] = RidesWithoutADriverArray[RidesWithoutADriverArray.length - 1];
                delete RidesWithoutADriverArray[RidesWithoutADriverArray.length - 1];
                RidesWithoutADriverArray.length--;
                break; // we found a ride already, we should not continue this loop
            }
        }
        
        User driver = User(_driver);
        
        driver.add_historical_ride(ride);
        ride.set_driver(_driver);
        
        return true;
    } 
    
    function get_ride_near_me(bytes32 _current_location) public returns (address []) {
        // TODO: probably we should take into consideartion current_location ;-)
        return RidesWithoutADriverArray;
        
    }
    
    function get_users_address() public returns(address) {
        return users;
    }
}



