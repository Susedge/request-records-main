function showToast(options) {
    let toast = Toastify({
        text: options.message,
        duration: 2000,
        newWindow: true,
        close: true,
        gravity: "top",
        position: "right",
        stopOnFocus: true,
        style: {
            background: options.color || "#007bff",
        },
    });

    toast.showToast();
}

$(document).ready(function() {
    // Events
    $('#btnCreate').click(function() {
        // Clear any existing error messages first
        $("#container").empty();
        
        let selectedRequest = document.querySelector("#request");
        if (!selectedRequest || !selectedRequest.value) {
            showToast({message: "Please select a request type", color: "#FF0000"});
            return;
        }

        // Get selected request text directly
        const selectedRequestText = selectedRequest.options[selectedRequest.selectedIndex].text;
        
        // Show loading message
        showToast({message: "Creating request form for " + selectedRequestText + ", please wait..."});
        
        try {
            // Get the request data and create form dynamically
            getRequest(selectedRequest.value, function(data) {
                // Ensure we're using the data from the response
                createRequestForm(data);
            });
        } catch (error) {
            console.error("Error handling request creation:", error);
            showToast({message: "An error occurred. Please try again.", color: "#FF0000"});
        }
    });

    // Web services
    function getRequest(id, successCallBack, errorCallBack){
        console.log("Fetching request details for ID:", id);
        
        $.ajax({
            type: 'GET',
            url: '/request/' + id + '/',
            success: function(response) {
                console.log("Server response for request ID", id, ":", response);
                
                // Clear any previous error messages
                const container = document.getElementById("container");
                if (container) {
                    // Check if there's an error message in the container
                    const errorMessage = container.querySelector('.alert-danger');
                    if (errorMessage) {
                        errorMessage.remove();
                    }
                }
                
                successCallBack(response);
            },
            error: function(xhr, errmsg, err) {
                console.error("Error getting request:", xhr.status, errmsg);
                
                // Get the container
                const container = document.getElementById("container");
                if (!container) return;
                
                // Clear any existing content
                container.innerHTML = "";
                
                // Default error message
                let errorMessage = "The selected request type is no longer available. Please choose another.";
                
                // Try to parse the response for a more specific error
                try {
                    if (xhr.responseText) {
                        const response = JSON.parse(xhr.responseText);
                        if (response.error) {
                            errorMessage = response.error;
                        }
                    }
                } catch (e) {
                    console.error("Error parsing error response:", e);
                }
                
                // Create and display error message
                const errorDiv = document.createElement("div");
                errorDiv.classList.add("alert", "alert-danger", "mt-3");
                errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${errorMessage}`;
                container.appendChild(errorDiv);
                
                // Refresh the dropdown to get the latest active requests
                if (typeof window.refreshActiveRequests === 'function') {
                    window.refreshActiveRequests();
                }
                
                // Call error callback if provided
                if (typeof errorCallBack === 'function') {
                    errorCallBack(xhr, errmsg, err);
                }
            }
        });
    }
    
    function createRequestForm(response) {
        try {
            let data = response;
            let requestID = data.id;
            
            // Completely clear the container first
            const container = document.getElementById("container");
            if (!container) {
                console.error("Container element not found");
                return;
            }
            
            container.innerHTML = "";
            
            // Extract document title from response
            const documentTitle = data.document || "Unknown Document";
            
            // Create the form header
            const h2ForRequiredFiles = document.createElement("h5");
            h2ForRequiredFiles.textContent = documentTitle; // Use textContent for safety
            h2ForRequiredFiles.classList.add("mb-3");

            const price = document.createElement("span");
            price.textContent = "₱" + data.price;
            price.classList.add("mx-2", "badge", "bg-primary");
            h2ForRequiredFiles.appendChild(price);
            container.appendChild(h2ForRequiredFiles);
            
            // Log what was rendered
            console.log("Rendered document title:", h2ForRequiredFiles.textContent);

            // Create textarea for description
            const descriptionTextarea = document.createElement("p");
            descriptionTextarea.id = "description";
            descriptionTextarea.name = "description";
            descriptionTextarea.textContent = data.description;
            container.appendChild(descriptionTextarea);

            // Purpose
            const lblPurpose = document.createElement("h5");
            lblPurpose.innerHTML = "Purpose:";
            container.appendChild(lblPurpose);

            // Purpose dropdown
            const drpPurpose = document.createElement("select");
            drpPurpose.classList.add("form-select"); 
            drpPurpose.setAttribute("id", "drpPurpose")
            drpPurpose.classList.add("mb-3") // Add margin left 3
            drpPurpose.name = "purpose";

            const purposes = data.purpose;
            purposes.forEach((purpose) => {
                const optPurpose = document.createElement("option");
                optPurpose.value = purpose.description;
                optPurpose.textContent = purpose.description;
                drpPurpose.appendChild(optPurpose);
            })

            // Add "Others" option
            const optOthers = document.createElement("option");
            optOthers.value = "Others";
            optOthers.textContent = "Others";
            drpPurpose.appendChild(optOthers);
            
            // Add event listener for when purpose changes
            drpPurpose.addEventListener("change", function() {
                // Remove existing custom purpose input if it exists
                const existingCustomInput = document.getElementById("customPurposeContainer");
                if (existingCustomInput) {
                    existingCustomInput.remove();
                }
                
                // If "Others" is selected, show the custom input field
                if (this.value === "Others") {
                    const customPurposeContainer = document.createElement("div");
                    customPurposeContainer.id = "customPurposeContainer";
                    customPurposeContainer.classList.add("mb-3");
                    
                    const customPurposeLabel = document.createElement("label");
                    customPurposeLabel.textContent = "Please specify your purpose:";
                    customPurposeLabel.classList.add("form-label");
                    
                    const customPurposeInput = document.createElement("input");
                    customPurposeInput.type = "text";
                    customPurposeInput.id = "customPurpose";
                    customPurposeInput.classList.add("form-control");
                    customPurposeInput.required = true;
                    customPurposeInput.placeholder = "Enter your purpose here";
                    
                    customPurposeContainer.appendChild(customPurposeLabel);
                    customPurposeContainer.appendChild(customPurposeInput);
                    
                    // Insert after the dropdown
                    drpPurpose.parentNode.insertBefore(customPurposeContainer, drpPurpose.nextSibling);
                }
            });

            container.appendChild(drpPurpose);

            // Create note about additional requirements
            const noteDiv = document.createElement("div");
            noteDiv.classList.add("alert", "alert-info", "mt-3", "mb-3");
            noteDiv.innerHTML = "<strong>Note:</strong> Additional document requirements may be requested after your request is reviewed and approved.";
            container.appendChild(noteDiv);

            // Create submit button
            const btnSubmitRequest = document.createElement("button");
            btnSubmitRequest.id = "btnSubmitRequest";
            btnSubmitRequest.textContent = "Submit Request";
            btnSubmitRequest.addEventListener("click", () => {
                submitRequest(requestID, data);
            })
            btnSubmitRequest.type = "button";
            btnSubmitRequest.classList.add("btn", "btn-primary"); // Add Bootstrap classes
            container.appendChild(btnSubmitRequest);
        } catch (e) {
            console.error("Error creating request form:", e);
            showToast({message: 'An error occurred. Please try again.', color: '#FF0000'});
        }
    }
});

// Function to submit the user request directly
function submitUserRequest(requestId) {
    // Validate purpose
    const purposeElement = document.querySelector("#drpPurpose");
    if (purposeElement && purposeElement.value === "Others") {
        const customPurposeInput = document.querySelector("#customPurpose");
        if (!customPurposeInput || !customPurposeInput.value.trim()) {
            showToast({ message: 'Please specify your purpose.', color: '#FF0000' });
            if (customPurposeInput) {
                customPurposeInput.classList.add('is-invalid');
            }
            return;
        } else {
            customPurposeInput.classList.remove('is-invalid');
        }
    }

    var csrftoken = getCookie('csrftoken');

    // Create form data
    var formData = new FormData();
    formData.append("request", requestId);

    // Add authorization letter if provided
    const authLetterInput = document.getElementById('authorization_letter');
    if (authLetterInput && authLetterInput.files.length > 0) {
        if (!validateFileSize([authLetterInput])) {
            return;
        }
        formData.append('authorization_letter', authLetterInput.files[0]);
    }

    // Add purpose
    if (purposeElement) {
        if (purposeElement.value === "Others") {
            const customPurposeInput = document.querySelector("#customPurpose");
            if (customPurposeInput && customPurposeInput.value.trim()) {
                formData.append('purpose', "Other: " + customPurposeInput.value.trim());
            }
        } else {
            formData.append('purpose', purposeElement.value);
        }
    } else {
        formData.append('purpose', 'General Purpose');
    }
    
    // Get number_of_copies
    const numberOfCopiesElement = document.querySelector("#number_of_copies");
    if (numberOfCopiesElement) {
        formData.append('number_of_copies', numberOfCopiesElement.value);
    } else {
        formData.append('number_of_copies', '1');
    }
    
    // Add profile info if exists
    if (document.getElementById('profile-form')) {
        const profileForm = document.getElementById('profile-form');
        const temp_user_info = {
            first_name: profileForm.querySelector('#first-name').value,
            last_name: profileForm.querySelector('#last-name').value,
            middle_name: profileForm.querySelector('#middle-name').value || '',
            user_type: profileForm.querySelector('#user-type').value,
            contact_no: profileForm.querySelector('#contact-no').value,
            course: profileForm.querySelector('#course').value,
            entry_year_from: profileForm.querySelector('#entry-year-from').value,
            entry_year_to: profileForm.querySelector('#entry-year-to').value,
            timestamp: new Date().toISOString()
        };
        
        formData.append('temp_user_info', JSON.stringify(temp_user_info));
        formData.append('user_type', profileForm.querySelector('#user-type').value);
    }

    // Show submission message
    showToast({
        message: 'Submitting your request...',
        color: '#007bff'
    });
    
    // Disable the submit button
    const submitBtn = document.getElementById('btnSubmitRequest');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Submitting...';
    }

    // Send request
    $.ajax({
        type: 'POST',
        url: '/request/user/create/',
        data: formData,
        processData: false,
        contentType: false,
        headers: {
            'X-CSRFToken': csrftoken
        },
        success: function(response) {
            showToast({
                'message': response.message,
                'duration': 3000
            });

            if (response.status) {
                setTimeout(function() {
                    window.location.href = '/request/user/';
                }, 2000);
            } else {
                // Re-enable button on error
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Submit Request';
                }
            }
        },
        error: function(xhr, errmsg, err) {
            console.error("Error submitting request:", err);
            
            showToast({
                message: 'An error occurred. Please try again.',
                color: '#FF0000'
            });
            
            // Re-enable button
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Submit Request';
            }
        }
    });
}

function validateFileSize(files) {
    const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB in bytes
    let isValid = true;
    
    files.forEach(file => {
        if (file.files[0] && file.files[0].size > MAX_FILE_SIZE) {
            showToast({
                message: `File ${file.files[0].name} exceeds 25MB limit`,
                color: '#FF0000'
            });
            isValid = false;
        }
    });
    
    // Check authorization letter size if provided
    const authLetterInput = document.getElementById('authorization_letter');
    if (authLetterInput && authLetterInput.files.length > 0 && authLetterInput.files[0].size > MAX_FILE_SIZE) {
        showToast({
            message: `Authorization letter exceeds 25MB limit`,
            color: '#FF0000'
        });
        isValid = false;
    }
    
    return isValid;
}

function getDocumentDescription(docCode, callback) {
    $.ajax({
        type: 'GET',
        url: '/get-document-description/' + docCode + '/',
        success: function(response) {
            callback(response.description);
        },
        error: function(xhr, errmsg, err) {
            console.log(errmsg);
        }
    });
}

// Function to get CSRF cookie value
function getCookie(name) {
    var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
    return cookieValue;
}

function validateForm() {
    let isValid = true;

    // Validate custom purpose if "Others" is selected
    const purposeElement = document.querySelector("#drpPurpose");
    if (purposeElement && purposeElement.value === "Others") {
        const customPurposeInput = document.querySelector("#customPurpose");
        if (!customPurposeInput || !customPurposeInput.value.trim()) {
            isValid = false;
            if (customPurposeInput) {
                customPurposeInput.classList.add('is-invalid');
            }
        } else if (customPurposeInput) {
            customPurposeInput.classList.remove('is-invalid');
        }
    }

    // Validate profile form if it exists
    if (document.getElementById('profile-form')) {
        const requiredFields = document.getElementById('profile-form').querySelectorAll('[required]');
        requiredFields.forEach(field => {
            if (!field.value) {
                isValid = false;
                field.classList.add('is-invalid');
            } else {
                field.classList.remove('is-invalid');
            }
        });
    }

    return isValid;
}

function validateFileSize(files) {
    const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB in bytes
    let isValid = true;
    
    files.forEach(file => {
        if (file.files[0] && file.files[0].size > MAX_FILE_SIZE) {
            showToast({
                message: `File ${file.files[0].name} exceeds 25MB limit`,
                color: '#FF0000'
            });
            isValid = false;
        }
    });
    
    return isValid;
}

// Add these functions
function showRequirements(requestId) {
    // Set the form action directly
    const form = document.getElementById('requirementsForm');
    form.action = `/request/user/${requestId}/upload-requirements/`;
    
    // Set the request ID
    document.getElementById('requestId').value = requestId;
    
    // Clear previous fields
    document.getElementById('requirementFields').innerHTML = '';
    
    // Create a test file input just to make sure the form works
    let testContainer = document.createElement('div');
    testContainer.classList.add('mb-3');
    
    let testLabel = document.createElement('label');
    testLabel.textContent = 'Test Document Upload';
    testLabel.classList.add('form-label');
    
    let testInput = document.createElement('input');
    testInput.setAttribute('type', 'file');
    testInput.setAttribute('name', 'test_document');
    testInput.classList.add('form-control');
    testInput.required = true;
    
    testContainer.appendChild(testLabel);
    testContainer.appendChild(testInput);
    document.getElementById('requirementFields').appendChild(testContainer);
    
    // Show the modal
    let modal = new bootstrap.Modal(document.getElementById('requirementsModal'));
    modal.show();
}

function loadRequirements(requestId) {
    // Clear previous fields
    document.getElementById('requirementFields').innerHTML = '';
    document.getElementById('requestId').value = requestId;
    
    // Get requirements for this request
    $.ajax({
        type: 'GET',
        url: '/request/user/' + requestId + '/requirements/',
        success: function(response) {
            if (response.requirements && response.requirements.length > 0) {
                response.requirements.forEach(req => {
                    let fileInputContainer = document.createElement("div");
                    fileInputContainer.classList.add("mb-3");
                    
                    let fileLabel = document.createElement("label");
                    fileLabel.setAttribute("for", req.code);
                    fileLabel.textContent = req.description;
                    fileLabel.classList.add("form-label");
                    
                    let fileInput = document.createElement("input");
                    fileInput.setAttribute("type", "file");
                    fileInput.setAttribute("id", req.code);
                    fileInput.setAttribute("name", req.code);
                    fileInput.classList.add("form-control");
                    fileInput.required = true;
                    
                    fileInputContainer.appendChild(fileLabel);
                    fileInputContainer.appendChild(fileInput);
                    document.getElementById('requirementFields').appendChild(fileInputContainer);
                });
                
                // Show the modal
                let modal = new bootstrap.Modal(document.getElementById('requirementsModal'));
                modal.show();
            } else {
                showToast({
                    message: 'No requirements found for this request.',
                    color: '#FF0000'
                });
            }
        },
        error: function(xhr, errmsg, err) {
            console.log(errmsg);
            showToast({
                message: 'Error loading requirements. Please try again.',
                color: '#FF0000'
            });
        }
    });
}

function submitRequirements() {
    const reqForm = document.getElementById('requirementsForm');
    const files = reqForm.querySelectorAll('input[type="file"]');
    const requestId = document.getElementById('requestId').value;
    
    console.log("Submitting requirements for request ID:", requestId);
    console.log("File inputs found:", files.length);
    
    // Debug check on files
    let hasFiles = false;
    files.forEach(fileInput => {
        console.log(`Input ${fileInput.id}:`, 
                   fileInput.files.length > 0 ? fileInput.files[0].name : "no file selected");
        if (fileInput.files.length > 0) {
            hasFiles = true;
        }
    });
    
    if (!hasFiles) {
        showToast({
            message: 'Please select at least one file to upload.',
            color: '#FF0000'
        });
        return;
    }
    
    // Create form data - simpler approach
    var formData = new FormData();
    
    // Add the request ID
    formData.append("request_id", requestId);
    
    // Add all files
    files.forEach(fileInput => {
        if (fileInput.files[0]) {
            // Use name attribute instead of id to be consistent
            console.log(`Adding file: ${fileInput.name} = ${fileInput.files[0].name}`);
            formData.append(fileInput.name, fileInput.files[0]);
        }
    });
    
    // Show submitting message
    showToast({
        message: 'Uploading files...',
        color: '#007bff'
    });
    
    var csrftoken = getCookie('csrftoken');
    
    $.ajax({
        type: 'POST',
        url: '/request/user/' + requestId + '/upload-requirements/',
        data: formData,
        processData: false,
        contentType: false,
        headers: {
            'X-CSRFToken': csrftoken
        },
        success: function(response) {
            console.log("Upload response:", response);
            if (response.status) {
                showToast({
                    message: response.message,
                    color: '#28a745'
                });
                
                // Close modal and refresh page
                let modal = bootstrap.Modal.getInstance(document.getElementById('requirementsModal'));
                modal.hide();
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                showToast({
                    message: response.message || 'Error uploading files',
                    color: '#FF0000'
                });
            }
        },
        error: function(xhr, errmsg, err) {
            console.error("Upload error:", err);
            console.error("Server response:", xhr.responseText);
            showToast({
                message: 'Server error. Please try again.',
                color: '#FF0000'
            });
        }
    });
}

function validateFileInputs(files) {
    let valid = true;
    files.forEach(file => {
        if (!file.files || file.files.length === 0) {
            valid = false;
            file.classList.add('is-invalid');
        } else {
            file.classList.remove('is-invalid');
        }
    });
    return valid;
}

// Add this function at the end of the file
function refreshActiveRequests() {
    const requestDropdown = document.getElementById('request');
    if (!requestDropdown) return;
    
    // Show loading indicator
    requestDropdown.disabled = true;
    
    // Fetch active requests
    fetch('/request/active-list/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Clear existing options
            requestDropdown.innerHTML = '';
            
            // Add new options
            if (data && data.length > 0) {
                data.forEach(req => {
                    const option = document.createElement('option');
                    option.value = req.id;
                    option.textContent = req.document;
                    requestDropdown.appendChild(option);
                });
                
                // Clear any error messages
                const errorBanner = document.querySelector('.alert-danger');
                if (errorBanner) {
                    errorBanner.remove();
                }
            } else {
                // No active requests
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No active request types available';
                requestDropdown.appendChild(option);
                
                // Show a message to the user that no request types are available
                const container = document.getElementById('container');
                if (container) {
                    container.innerHTML = '<div class="alert alert-warning">No active request types are available. Please try again later.</div>';
                }
            }
            
            // Re-enable dropdown
            requestDropdown.disabled = false;
        })
        .catch(error => {
            console.error('Error refreshing requests:', error);
            requestDropdown.disabled = false;
            
            // Add an error option
            requestDropdown.innerHTML = '';
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Error loading request types';
            requestDropdown.appendChild(option);
            
            showToast({
                message: 'Error refreshing request types. Please try again.',
                color: '#dc3545'
            });
        });
}

// Add this function to show error messages
function showErrorBanner(message) {
    // Get the container element
    const container = document.getElementById("container");
    if (!container) return;
    
    // Clear existing content
    container.innerHTML = "";
    
    // Create error banner
    const errorDiv = document.createElement("div");
    errorDiv.classList.add("alert", "alert-danger");
    errorDiv.setAttribute("role", "alert");
    
    // Create dismiss button
    const dismissButton = document.createElement("button");
    dismissButton.type = "button";
    dismissButton.classList.add("btn-close");
    dismissButton.setAttribute("data-bs-dismiss", "alert");
    dismissButton.setAttribute("aria-label", "Close");
    
    // Add error message
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle me-2"></i> ${message} `;
    errorDiv.appendChild(dismissButton);
    
    // Add to container
    container.appendChild(errorDiv);
    
    // Refresh request list
    refreshActiveRequests();
}

function clearErrorMessages() {
    // Remove any existing error messages
    const errorMessages = document.querySelectorAll(".alert-danger");
    errorMessages.forEach(element => {
        element.remove();
    });
}


