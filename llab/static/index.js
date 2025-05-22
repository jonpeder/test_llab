// JS

// Get image landmark from click

function FindPosition(oElement)
{
  if(typeof( oElement.offsetParent ) != "undefined")
  {
    for(var posX = 0, posY = 0; oElement; oElement = oElement.offsetParent)
    {
      posX += oElement.offsetLeft;
      posY += oElement.offsetTop;
    }
      return [ posX, posY ];
    }
    else
    {
      return [ oElement.x, oElement.y ];
    }
}
function GetCoordinates(e)
{
  var PosX = 0;
  var PosY = 0;
  var ImgPos;
  ImgPos = FindPosition(myImg);
  if (!e) var e = window.event;
  if (e.pageX || e.pageY)
  {
    PosX = e.pageX;
    PosY = e.pageY;
  }
  else if (e.clientX || e.clientY)
    {
      PosX = e.clientX + document.body.scrollLeft
        + document.documentElement.scrollLeft;
      PosY = e.clientY + document.body.scrollTop
        + document.documentElement.scrollTop;
    }
  PosX = PosX - ImgPos[0];
  PosY = PosY - ImgPos[1];
  document.getElementById("x").innerHTML = PosX;
  document.getElementById("y").innerHTML = PosY;
}


// Function to make any api call
async function api_call(gbif_url) {
    const response = await fetch(gbif_url);
    const myJson = await response.json(); //extract JSON from the http response
    // do something with myJson
    return myJson;
}

// Transform gbif-id to api-url, make api-call and return gbif-data
async function gbif_call() {
    // get taxon-id from input
    let gbif_id = document.getElementById('taxonID').value;
    // transform taxon-id into url for api call
    const gbif_url = gbif_id.replace("https://www.gbif.org/", "https://api.gbif.org/v1/");
    // Make api call
    const gbif_out = await api_call(gbif_url);
    // Add gbif-data to fields
    if (typeof gbif_out.order !== 'undefined') {document.getElementById("order").value = gbif_out.order};
    if (typeof gbif_out.family !== 'undefined') {document.getElementById("family").value = gbif_out.family};
    if (typeof gbif_out.genus !== 'undefined') {document.getElementById("genus").value = gbif_out.genus};
    if (typeof gbif_out.rank !== 'undefined') {document.getElementById("rank").value = gbif_out.rank.toLowerCase()};
    if (typeof gbif_out.authorship !== 'undefined') {document.getElementById("scientificNameAuthorship").value = gbif_out.authorship};
    if (typeof gbif_out.canonicalName !== 'undefined') {document.getElementById("taxonName").value = gbif_out.canonicalName};
    if (typeof gbif_out.publishedIn !== 'undefined') {document.getElementById("publishedIn").value = gbif_out.publishedIn};

}

//
async function stedsnavn_call() {
    // Get longitude and latitude from input form
    let lat = document.getElementById('Latitude').value;
    let lon = document.getElementById('Longitude').value;
    // Prepare url for api call
    const stedsnavn_url = 'https://ws.geonorge.no/stedsnavn/v1/punkt?nord='+lat+'&ost='+lon+'&koordsys=4326&radius=2000&utkoordsys=4326&treffPerSide=200&side=1';
    const administReg_url = 'https://ws.geonorge.no/kommuneinfo/v1/punkt?koordsys=4326&ost='+lon+'&nord='+lat
    // Make api calls
    const stedsnavn_out = await api_call(stedsnavn_url);
    const administReg_out = await api_call(administReg_url);
    // Sort locality name by distance from point and pick the closest one
    const stedsnavn_sorted = stedsnavn_out.navn;
    stedsnavn_sorted.sort((a,b) => a.meterFraPunkt - b.meterFraPunkt);
    // Add locality, county and municipality names to fields
    if (typeof stedsnavn_sorted[0].stedsnavn[0].skrivemåte !== 'undefined') {document.getElementById("Locality_2").value = stedsnavn_sorted[0].stedsnavn[0].skrivemåte};
    if (typeof administReg_out.fylkesnavn !== 'undefined') {document.getElementById("County").value = administReg_out.fylkesnavn};
    if (typeof administReg_out.kommunenavn !== 'undefined') {document.getElementById("Municipality").value = administReg_out.kommunenavn};
}

// Selectpicker
//$('#ScientificName').selectpicker();

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

/*
// Find document variable
const output = document.querySelector("#result");

// Get input images and loop over each image
function loadFiles(event) {
    output.innerHTML = ""
    for (let i = 0; i < event.target.files.length; i++) {
        var img_item = document.createElement("div"); // Create new div element
        img_item.className = "img_item";
        img_item.appendChild(imageAppend(event.target.files[i])); // Append element to img_item
        output.appendChild(img_item);
    }
}

function clearFiles() {
    output.innerHTML = ""
    document.getElementById("imgInp").value = ""
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

// Dark mode
function myFunction() {
  var element = document.body;
  element.classList.toggle("dark-mode");
}
*/

