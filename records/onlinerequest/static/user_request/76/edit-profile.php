<?php
session_start();

// Redirect if subscription value is 0
if(isset($_SESSION["subscription"]) && $_SESSION["subscription"] == 0) {
    header("location: ../index.php");
    exit;
}

// Proceed with the rest of your script
require_once "../php/connection.php";
require_once "../php/functions.php";

// Check if the $_SESSION["subscription"] variable is set

$modal_display = "hidden";
$gender = "";
//barangay variable
$selectBarangayQuery = "SELECT name FROM barangays";
$selectBarangayResult = $mysqli->query($selectBarangayQuery);

$barangayOptions = array();

if ($selectBarangayResult) {
    if ($selectBarangayResult->num_rows > 0) {
        while ($row = $selectBarangayResult->fetch_assoc()) {
            $barangayOptions[] = $row["name"];
        }
    } else {
        $barangayOptions[] = "No Result";
    }
    $selectBarangayResult->free();
} else {
    $barangayOptions[] = "Error executing query: " . $mysqli->error;
}

//check for profile information
$getProfileQuery = "SELECT * FROM mechanic WHERE userID = ?";

if($getProfileStmt = $mysqli->prepare($getProfileQuery)){

    $getProfileStmt->bind_param("s",$param_id);

    $param_id = validate($_SESSION['userID']);

    if($getProfileStmt->execute()){ 

        $getProfileResult = $getProfileStmt->get_result();

            if($getProfileResult->num_rows === 1){
                $profileAction = "Update";

                $row = $getProfileResult->fetch_array(MYSQLI_ASSOC);
                $fname = $row["firstName"];
                $lname = $row["lastName"];
                $suffix = $row["suffix"];
                $gender = $row["gender"];
                $contact = substr($row["contactNumber"],3);
                $address = $row["address"];
                $barangay = $row["barangay"];
                $latitude = $row["latitude"];
                $longitude = $row["longitude"]; 
                $_SESSION['mechanicID'] = $row['mechanicID'];

            }else {
                $profileAction = "Create";
            }

        }else {
            $modal_display = "";
            $modal_status = "error";
            $modal_title = "Profile Information Error";
            $modal_message = "Profile cannot be retrieve";
            $modal_button = '<a href="dashboard.php">OK</a>';
        }

    $getProfileStmt->close();
}

if ($_SERVER["REQUEST_METHOD"] == "POST") {

    $errors = [];
    //FIRST NAME
    $fname = validate($_POST["fname"]);
    if(empty($fname)){
        $errors["fname"] = "Enter First Name";
    } elseif(!preg_match("/^[a-zA-Z- ]*$/", $fname)){
        $errors["fname"] = "Only Letters and Spaces are allowed";
    } else{
            $fname = ucwords(strtolower($fname));
    }
    //LAST NAME
    $lname = validate($_POST["lname"]);
    if(empty($lname)){
        $errors["lname"] = "Enter Suffix";
    } elseif(!preg_match("/^[a-zA-Z- ]*$/", $lname)){
        $errors["lname"] = "Only Letters and Spaces are allowed";
    } else{
            $lname = ucwords(strtolower($lname));
    }
    //SUFFIX
    $suffix = validate($_POST["suffix"]);
    if(!empty($suffix)){
        if(!preg_match("/^[a-zA-Z]*$/", $suffix)){
            $errors["suffix"] = "Only Letters are allowed";
        }else{
            $suffix = ucwords(strtolower($suffix));
        }
    }else{
        $suffix = null;
    }
    //gender
    $gender = isset($_POST['gender']) ? validate($_POST['gender']) : '';
    if(empty($gender)){
        $errors["gender"] = "Select Gender";
    }
    // contact number
    $contact = validate($_POST['contact']);
    if(empty($contact)){
        $errors["contact"] = "Enter Contact Number";
    } elseif(!preg_match('/^[0-9]{10}$/',$contact)){
        $errors["contact"] = "Only Numbers are allowed";
    }
    // address
    $address = $_POST['address'];
    if(empty($address)){
        $errors["address"] = "Enter Address";
    }elseif(!preg_match("/^[a-zA-Z 0-9&*@#().\/~-]*$/", $address)){
        $errors["address"] = "Invalid Address";
    } else{
        $address = ucwords(strtolower($address));
    }
    //barangay
    $barangay = isset($_POST['barangay']) ? validate($_POST['barangay']) : '';
    if(empty($barangay)){
        $errors["barangay"]  = "Select Barangay";
    }
    //location
    $latitude = validate($_POST["latitude"]);
    $longitude = validate($_POST["longitude"]);
    if(empty($latitude) || empty($longitude)){
        $errors["location"]  = "Please pin your location";
    }

    // Profile Picture Upload
    if (isset($_FILES['profile_picture']) && $_FILES['profile_picture']['error'] === UPLOAD_ERR_OK) {
        $profile_picture_tmp = $_FILES['profile_picture']['tmp_name'];
        $profile_picture_name = $_FILES['profile_picture']['name'];
        $profile_picture_extension = pathinfo($profile_picture_name, PATHINFO_EXTENSION);
        $profile_picture_new_name = uniqid('profile_', true) . '.' . $profile_picture_extension;
        $profile_picture_destination = 'profile/' . $profile_picture_new_name;

        if (move_uploaded_file($profile_picture_tmp, $profile_picture_destination)) {
            // File uploaded successfully, update the profilePicture column in the database
            $update_profile_picture_query = "UPDATE mechanic SET profile_picture = ? WHERE userID = ?";
            if ($update_profile_picture_stmt = $mysqli->prepare($update_profile_picture_query)) {
                $update_profile_picture_stmt->bind_param("ss", $profile_picture_new_name, $_SESSION['userID']);
                if ($update_profile_picture_stmt->execute()) {
                    // Profile picture updated successfully
                } else {
                    // Failed to update profile picture in the database
                    $errors["profile_picture"] = "Failed to update profile picture";
                }
                $update_profile_picture_stmt->close();
            } else {
                // Error preparing the SQL statement to update profile picture
                $errors["profile_picture"] = "Error preparing SQL statement to update profile picture";
            }
        } else {
            // Failed to move uploaded profile picture to destination
            $errors["profile_picture"] = "Failed to move uploaded profile picture";
        }
    }

    // Valid ID Upload
    if (isset($_FILES['valid_id']) && $_FILES['valid_id']['error'] === UPLOAD_ERR_OK) {
        $valid_id_tmp = $_FILES['valid_id']['tmp_name'];
        $valid_id_name = $_FILES['valid_id']['name'];
        $valid_id_extension = pathinfo($valid_id_name, PATHINFO_EXTENSION);
        $valid_id_new_name = uniqid('valid_id_', true) . '.' . $valid_id_extension;
        $valid_id_destination = 'valid_ids/' . $valid_id_new_name;

        if (move_uploaded_file($valid_id_tmp, $valid_id_destination)) {
            // File uploaded successfully, update the validID column in the database
            $update_valid_id_query = "UPDATE mechanic SET valid_id_path = ? WHERE userID = ?";
            if ($update_valid_id_stmt = $mysqli->prepare($update_valid_id_query)) {
                $update_valid_id_stmt->bind_param("ss", $valid_id_new_name, $_SESSION['userID']);
                if ($update_valid_id_stmt->execute()) {
                    // Valid ID updated successfully
                } else {
                    // Failed to update valid ID in the database
                    $errors["valid_id"] = "Failed to update valid ID";
                }
                $update_valid_id_stmt->close();
            } else {
                // Error preparing the SQL statement to update valid ID
                $errors["valid_id"] = "Error preparing SQL statement to update valid ID";
            }
        } else {
            // Failed to move uploaded valid ID to destination
            $errors["valid_id"] = "Failed to move uploaded valid ID";
        }
    }

    //insert to database
    if(empty($errors)){ 

        if($profileAction === "Update"){

            $insertProfileQuery = "UPDATE mechanic SET firstName = ?, lastName = ?, suffix = ?, gender = ?, contactNumber = ?, address = ?, barangay = ?, latitude = ?, longitude = ? WHERE mechanicID = ?";

        }else {

            $getLastIdQuery = "SELECT mechanicID as maxID FROM mechanic ORDER BY mechanicID DESC LIMIT 1";

            if($lastIDstmt = $mysqli->prepare($getLastIdQuery)) {

                if($lastIDstmt->execute()){  

                    $lastIDstmt->bind_result($maxID);

                    if($lastIDstmt->fetch()) {
                        $lastID = $maxID;
                    }
                }

                $lastIDstmt->close();

            }

            $currentYear = date('Y');

            if(!empty($lastID)) {
                $year = substr($lastID, 2, 4);
                $countDash = substr($lastID, 7);
                $count = str_replace("-","",$countDash);

                if($year === $currentYear) {
                    $count += 1;
                } else {
                    $count = 0;
                }
            } else {
                $count = 0;
            }

            $count = str_pad($count, 6, '0', STR_PAD_LEFT);
            $countDash = substr_replace($count, "-", 3, 0);
            $mechanicID = "M-" . $currentYear . "-" . $countDash; 

            if($profileAction === "Update"){
                // Prepare the UPDATE query
                $insertProfileQuery = "UPDATE mechanic SET firstName = ?, lastName = ?, suffix = ?, gender = ?, contactNumber = ?, address = ?, barangay = ?, latitude = ?, longitude = ? WHERE mechanicID = ?";
            } else {
                // Prepare the INSERT query
                $insertProfileQuery = "INSERT INTO mechanic (userID, mechanicID, firstName, lastName, suffix, gender, contactNumber, address, barangay, latitude, longitude, profile_picture, validID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";
            }
        
            // Attempt to prepare the SQL statement
            if($insertProfileStmt = $mysqli->prepare($insertProfileQuery)){
                // Bind parameters
                if($profileAction === "Update"){
                    $insertProfileStmt->bind_param("ssssssssdds", $param_UserID, $param_mechanicID, $param_fname, $param_lname, $param_suffix, $param_gender, $param_contact, $param_address, $param_barangay, $param_latitude, $param_longitude);
                    $param_mechanicID = validate($_SESSION['mechanicID']);
                } else {
                    $insertProfileStmt->bind_param("sssssssssddss", $param_UserID, $param_mechanicID, $param_fname, $param_lname, $param_suffix, $param_gender, $param_contact, $param_address, $param_barangay, $param_latitude, $param_longitude, $profile_picture_new_name, $valid_id_new_name);
                    $param_mechanicID = $mechanicID;
                    $param_UserID = validate($_SESSION['userID']);
                }
        
                // Set parameter values
                $param_fname = $fname;
                $param_lname = $lname;
                $param_suffix = $suffix;
                $param_gender = $gender;
                $param_contact = "+63".$contact;
                $param_address = $address;
                $param_barangay = $barangay;
                $param_latitude = $latitude;
                $param_longitude = $longitude;
                            
                // Execute the statement
                if($insertProfileStmt->execute()){
                } else {
                }
                $modal_display = "";
                $modal_status = "success";

                if($profileAction === "Update"){

                    $modal_title = "Profile Information Updated";
                    $modal_message = "Your Profile has been updated";

                }else{

                    $_SESSION['mechanicID'] = $mechanicID;
                    $modal_title = "Profile Creation Success";
                    $modal_message = "Good Work!";

                }

                $modal_button = '<a href="dashboard.php">Dashboard</a>';

            }else{
                $modal_display = "";
                $modal_status = "error";
                $modal_title = "Profile Information Error";
                $modal_message = "Try again later";
                $modal_button = '<a href="../index.php">OK</a>';
            }

            $insertProfileStmt->close();
        }
    } 
}

$mysqli->close();

?>
<!DOCTYPE html>
<html lang="en">
<head>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="shortcut icon" href="../img/hammer.jpg" type="image/x-icon">
    <link rel="icon" href="../img/hammer.jpg" type="image/x-icon">
    <link rel="stylesheet" href="../css/style.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
    crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
    crossorigin=""></script>
    
    <title>Edit Profile</title>
</head>
<body>

<modal class="<?= $modal_display ?>">
    <div class="content <?= $modal_status ?>">
        <p class="title"><?= $modal_title ?></p>
        <p class="message"><?= $modal_message ?></p>
        <div class="link-group">
            <?= $modal_button ?>
        </div>
    </div>
</modal>

<nav>
    <div class="logo">
    <img src="../img/hammer.jpg" alt="Hammer" class="logo" style="border-radius: 50%; width: 15%; height: auto;">
        <p>Mechanic Services</p>  
    </div>
    <div class="toggle-menu">
        <img src="../img/navbar-toggle.svg" alt="Toggle Menu">
    </div>
    <div class="link-group">
        <a href="dashboard.php">Dashboard</a>
        <a class="current" href="edit-profile.php">Profile</a>
        <a href="../php/logout.php">Logout</a>
    </div>
</nav>
<style>
.profile-picture-container {
    width: 150px;
    height: 150px;
    border-radius: 50%; /* Pabilog na border */
    overflow: hidden; /* Itago ang labas ng larawan */
    border: 2px solid #ccc; /* Kulay ng border */
    display: flex; /* Gawing flex container */
    align-items: center; /* I-align ang mga item sa gitna */
    justify-content: center; /* I-align ang mga item sa gitna */
}

.profile-picture {
    width: 100%;
    height: 100%;
    object-fit: cover; /* Pataasan o pababain ang larawan para punan ang bilog na border */
}

.no-profile-picture {
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 16px;
    color: #888;
}

</style>
<main>
    <div class="form-container">  

        <p class="title">Mechanic Profile</p>

        <form autocomplete="off" method="post" action="<?= htmlspecialchars($_SERVER["PHP_SELF"]);?>" enctype="multipart/form-data">
        <div class="form-group" >
            <label for="profile_picture" >Profile Picture</label>
            <div class="profile-picture-container" >
                <?php if(isset($row['profile_picture']) && !empty($row['profile_picture'])): ?>
                    <!-- Display the saved profile picture -->
                    <img src="profile/<?php echo $row['profile_picture']; ?>" alt="Profile Picture" class="profile-picture">
                <?php else: ?>
                    <!-- If no profile picture is saved, display default placeholder or no image -->
                    <div class="no-profile-picture">No Profile Picture</div>
                <?php endif; ?>
            </div><br>
            <input type="file" id="profile_picture" name="profile_picture">
            <div class="error-msg"><?= isset($errors["profile_picture"]) ? $errors["profile_picture"] : ''; ?></div>
        </div>

        <div class="form-group" style="text-align: center;">
    <label for="valid_id" style="text-align: left;">Valid ID</label>

    <!-- Display valid ID as an image if it exists -->
    <?php if (isset($row['valid_id_path']) && !empty($row['valid_id_path'])): ?>
        <div class="valid-id-image-container">
            <img src="valid_ids/<?php echo $row['valid_id_path']; ?>" alt="Valid ID" style="max-width: 200px;">
        </div>
    <?php endif; ?>

    <input type="file" id="valid_id" name="valid_id">
    <div class="error-msg"><?= isset($errors["valid_id"]) ? $errors["valid_id"] : ''; ?></div>
</div>


        <div class="form-group">
            <label for="fname">First Name</label>
            <input type="text" id="fname" name="fname" placeholder="First Name" value="<?= isset($fname) ? $fname : '';   ?>">
            <div class="error-msg"><?= isset($errors["fname"]) ? $errors["fname"] : ''; ?></div>
        </div>

        <div class="form-group">
            <label for="lname">Last Name</label>
            <input type="text" id="lname" name="lname" placeholder="Last Name" value="<?= isset($lname) ? $lname : ''; ?>">
            <div class="error-msg"><?= isset($errors["lname"]) ? $errors["lname"] : ''; ?></div>
        </div>

        <div class="form-group">
            <label for="suffix">Suffix</label>
            <input type="text" id="suffix" name="suffix" placeholder="Suffix (e.g., Jr., III)" value="<?= isset($suffix) ? $suffix : ''; ?>">
            <div class="error-msg"><?= isset($errors["suffix"]) ? $errors["suffix"] : ''; ?></div>
        </div>

        <div class="form-group">
            <label for="gender">Gender</label>
            <select id="gender" name="gender">
                <option value="" disabled <?php if(empty($gender)) { echo "selected"; } ?>>Select Gender</option>
                <option value="Male" <?php if($gender === "Male") { echo "selected"; } ?>>Male</option>
                <option value="Female" <?php if($gender === "Female") { echo "selected"; } ?>>Female</option>
                <option value="Other" <?php if($gender === "Other") { echo "selected"; } ?>>Other</option>
            </select>
            <div class="error-msg"><?= isset($errors["gender"]) ? $errors["gender"] : ''; ?></div>
        </div>

        <div class="form-group">
            <label for="contact">Contact Number</label>
            <div class="input-container">
                <div class="pre-input">+63</div>
                <input type="text" id="contact" name="contact" placeholder="Contact Number" maxlength="10" value="<?= isset($contact) ? $contact : '';   ?>">
            </div>
            <div class="error-msg"><?= isset($errors["contact"]) ? $errors["contact"] : ''; ?></div>
        </div>

        <div class="form-group">
            <label for="address">Address</label>
            <input type="text" id="address" name="address" placeholder="Address" value="<?= isset($address) ? $address : ''; ?>">
            <div class="error-msg"><?= isset($errors["address"]) ? $errors["address"] : ''; ?></div>
        </div>

        <div class="form-group">
            <label for="barangay">Barangay</label>
            <select id="barangay" name="barangay">
                <option value="" disabled <?php if(empty($barangay)) { echo "selected"; } ?>>Select Barangay</option>
                <?php foreach($barangayOptions as $option): ?>
                    <option value="<?= $option ?>" <?php if($barangay === $option) { echo "selected"; } ?>><?= $option ?></option>
                <?php endforeach; ?>
            </select>
            <div class="error-msg"><?= isset($errors["barangay"]) ? $errors["barangay"] : ''; ?></div>
        </div>

        <div class="map-group">
                <p class="label">Pin Location</p>
                <map id="map"></map>
                <input type="text" id="latitude" name="latitude" value="<?= isset($latitude) ? $latitude : '';   ?>" hidden> 
                <input type="text" id="longitude" name="longitude" value="<?= isset($longitude) ? $longitude : '';   ?>" hidden>
                <div class="error-msg"><?= isset($errors["location"]) ? $errors["location"] : ''; ?></div>
            </div>

        <input type="submit" value="<?= $profileAction ?>">

    </form>

    </div>
</main>

    <script src="../js/script.js" defer></script>
    <script src="../js/map.js" defer></script>
    <script src="../js/pin-location.js" defer></script>
</body>
</html>
