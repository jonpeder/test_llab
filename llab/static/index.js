// JS

// Delete notes function
function deleteNote(noteId) {
    fetch('/delete-note', {
        method: 'POST',
        body: JSON.stringify({ noteId: noteId }),
    }).then((_res) => {
        window.location.href = "/";
    });
}

// Delete print_events function
function deleteEvent(eventID) {
    fetch('/delete-event', {
        method: 'POST',
        body: JSON.stringify({ eventID: eventID }),
    }).then((_res) => {
        window.location.href = "/event_labels";
    });
}

// Use today as default date
Date.prototype.toDateInputValue = (function () {
    var local = new Date(this);
    local.setMinutes(this.getMinutes() - this.getTimezoneOffset());
    return local.toJSON().slice(0, 10);
})

document.getElementById('Date_1').defaultValue = new Date().toDateInputValue();

// get position
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition);
    } else {
        x.innerHTML = "Geolocation is not supported by this browser.";
    }
}

function showPosition(position) {
    document.getElementById("Latitude").value = position.coords.latitude
    document.getElementById("Longitude").value = position.coords.longitude
    document.getElementById("Radius").value = 25
}

// Find document variable
const output = document.querySelector("#result");

// Get input images and loop over each image
function loadFiles(event) {
    for (let i = 0; i < event.target.files.length; i++) {
        var img_item = document.createElement("div"); // Create new div element
        img_item.className = "img_item";
        img_item.appendChild(imageAppend(event.target.files[i])); // Append element to img_item
        output.appendChild(img_item);
    }
}

// Append image to output
function imageAppend(x) {
    var image = document.createElement("img"); // Create new image element
    image.src = URL.createObjectURL(x); // Add soure to image element
    image.id = x.name; // Add name to image element
    // free memory
    image.onload = function () {
        URL.revokeObjectURL(image.src); // free memory
    };
    // Return img element
    return (image);
}