<?php 
session_start();

error_reporting(E_ALL);
ini_set('display_errors', 1);

require_once "php/functions.php";

if (!isset($_SESSION["role"])) {
    $_SESSION["role"] = '';
}

$dashboardLink = ''; // Initialize the dashboard link variable

switch ($_SESSION["role"]) {
    case 'client':
        $dashboardLink = '<a href="client/dashboard.php">Dashboard</a>';
        break;
    case 'mechanic':
        // Check if the subscription value is 0
        if ($_SESSION["subscription"] === 0) {
            // If subscription is 0, hide the dashboard link
            $dashboardLink = '';
        } else {
            // If subscription is not 0, show the dashboard link
            $dashboardLink = '<a href="mechanic/dashboard.php">Dashboard</a>';
        }
        break;
}

// Generate the logout link
$logoutLink = '<a href="php/logout.php">Logout</a>';

// If the role is not client or mechanic, generate login and register links
if ($_SESSION["role"] !== 'client' && $_SESSION["role"] !== 'mechanic') {
    $links = '
        <a href="login.php">Login</a>
        <a href="register.php">Register</a>
    ';
} else {
    // If the role is client or mechanic, combine the dashboard and logout links
    $links = $dashboardLink . $logoutLink;
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="shortcut icon" href="img/hammer.jpg" type="image/x-icon">
    <link rel="icon" href="img/hammer.jpg" type="image/x-icon">
    <link rel="stylesheet" href="css/style.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
    crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
    crossorigin=""></script>
    <script src="js/script.js" defer></script>
    <script src="js/map.js" defer></script>

    <title>Mekanik</title>
</head>
<body>

<nav>
    <div class="logo">
    <img src="img/hammer.jpg" alt="Hammer" class="logo" style="border-radius: 50%; width: 15%; height: auto;">
        <p>Mechanic Services</p>
    </div>
    <div class="toggle-menu">
        <img src="img/navbar-toggle.svg" alt="Toggle Menu">
    </div>
    <div class="link-group">
        <?= $links ?>
    </div>
</nav>

<main>
    <div class="map-container">
        <map id="map"></map>
    </div>
</main>
    
    <?php
    require_once "php/connection.php";

    $sql = "SELECT firstName, lastName, suffix, contactNumber, longitude, latitude FROM mechanic";

    if ($stmt = $mysqli->prepare($sql)) {
        if ($stmt->execute()) {
            $stmt->bind_result($fname, $lname, $suffix, $contact, $longitude, $latitude);

            $coordinates = array();

            while ($stmt->fetch()) {
                $coordinates[] = array(
                    'name' => $fname . " " . $lname . " " . $suffix,
                    'contact' => $contact,
                    'longitude' => $longitude,
                    'latitude' => $latitude
                );
            }
            $coordinatesJson = json_encode($coordinates);
        } else {
            $coordinatesJson = "Error retrieving data";
        }
        $stmt->close();
    }
    $mysqli->close();
    ?>

    <script>
    let coordinates = JSON.parse('<?php echo $coordinatesJson; ?>');

    coordinates.forEach(mechanic => {
        let latitude = mechanic.latitude;
        let longitude = mechanic.longitude;
        let name = mechanic.name;
        let contact = mechanic.contact;
        let location = L.latLng(latitude, longitude);
        let marker = L.marker(location).addTo(map);
        marker.bindPopup(name + '</br>' + contact);
    });
    </script>

</body>
</html>
