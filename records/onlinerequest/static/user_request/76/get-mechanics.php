<?php 
require_once "connection.php";

$sql = "SELECT firstName, lastName, suffix, contactNumber, longitude, latitude FROM mechanic";

if ($stmt = $mysqli->prepare($sql)) {

    if ($stmt->execute()) {
        $stmt->bind_result($fname, $lname, $suffix, $contact, $longitude, $latitude);

        $coordinates = array();

        while ($stmt->fetch()) {

            $coordinates[] = 
            array(
                'name' => $fname . " " . $lname . " " . $suffix,
                'contact' => $contact,    
                'longitude' => $longitude, 
                'latitude' => $latitude);
        }
        $coordinatesJson = json_encode($coordinates);

        echo $coordinatesJson;

    } else {

        echo "Error retrieving data";

    }
    $stmt->close();
}
$mysqli->close();
?>