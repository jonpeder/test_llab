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

/*
// Function to make any api call
async function api_call(gbif_url) {
    const response = await fetch(gbif_url);
    const myJson = await response.json(); //extract JSON from the http response
    // do something with myJson
    return myJson;
}
*/


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

/*
// Get political region names. First try to get names from  the Norwegian locality-name-service API. If this returns nothing, try to get the names from OpenStreetMap.
async function stedsnavn_call() {
    // Get longitude and latitude from input form
    let lat = document.getElementById('Latitude').value;
    let lon = document.getElementById('Longitude').value;
    // Prepare url for api call for  the Norwegian locality-name-service API
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
    // If no result use OpenStreetMap    
}
*/

async function stedsnavn_call() {
    // Get coordinates from input form
    const lat = document.getElementById('Latitude').value;
    const lon = document.getElementById('Longitude').value;

    // URLs for Norwegian APIs
    const stedsnavn_url = `https://ws.geonorge.no/stedsnavn/v1/punkt?nord=${lat}&ost=${lon}&koordsys=4326&radius=2000&utkoordsys=4326&treffPerSide=200&side=1`;
    const administReg_url = `https://ws.geonorge.no/kommuneinfo/v1/punkt?koordsys=4326&ost=${lon}&nord=${lat}`;

    // Try Norwegian APIs first
    try {
        const [stedsnavn_out, administReg_out] = await Promise.all([
            api_call(stedsnavn_url).catch(() => null),  // Return null if API fails
            api_call(administReg_url).catch(() => null)
        ]);

        // Process Norwegian API results if they exist
        let locality, county, municipality;

        // Get closest locality name (if available)
        if (stedsnavn_out?.navn) {
            const stedsnavn_sorted = [...stedsnavn_out.navn].sort((a, b) => a.meterFraPunkt - b.meterFraPunkt);
            locality = stedsnavn_sorted[0]?.stedsnavn[0]?.skrivemåte;
            if (locality) document.getElementById("Locality_2").value = locality;
        }

        // Get county/municipality (if available)
        if (administReg_out) {
            county = administReg_out.fylkesnavn;
            municipality = administReg_out.kommunenavn;
            if (county) document.getElementById("County").value = county;
            if (municipality) document.getElementById("Municipality").value = municipality;
        }

        // If all fields are filled, exit early (no need for OSM)
        if (locality && county && municipality) return;

    } catch (error) {
        console.error("Norwegian API error:", error);
    }

    // Fallback to OpenStreetMap if Norwegian APIs failed or returned incomplete data
    await getLocationFromOSM(lat, lon);
}

// Helper: Fetch data from OpenStreetMap (Nominatim)
async function getLocationFromOSM(lat, lon) {
    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=10&addressdetails=1`,
            { headers: { "User-Agent": "llab.no/1.0 (jonpeder.lindemann@gmail.com)" } } // Required by OSM
        );
        const data = await response.json();

        if (data.error) throw new Error(data.error);

        const address = data.address;
        
        // Fill fields
        document.getElementById("Country").value = address.country_code.toUpperCase();
        // locality
        const locality =  address.town || address.village || address.city;
        if (locality) document.getElementById("Locality_1").value = locality;
        // county
        const county = address.county || address.state_district;
        if (county) document.getElementById("County").value = county.replace(/\s(County)$/i, '');
        // municipality
        const municipality = address.municipality || address.city || address.town;
        if (municipality) document.getElementById("Municipality").value = municipality.replace(/\s(Municipality)$/i, '');

    } catch (error) {
        console.error("OpenStreetMap error:", error);
        alert("Could not fetch location details from any service.");
    }
}

// Generic API call function (assuming you already have this)
async function api_call(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`API request failed: ${response.status}`);
    return await response.json();
}


// Use today as default date
Date.prototype.toDateInputValue = (function () {
    var local = new Date(this);
    local.setMinutes(this.getMinutes() - this.getTimezoneOffset());
    return local.toJSON().slice(0, 10);
})

document.getElementById('Date_1').defaultValue = new Date().toDateInputValue();

// get position coordinates
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            showPosition, 
            function(error) {
                // Handle errors
                alert("Error getting location: " + error.message);
            },
            {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            }
        );
    } else {
        alert("Geolocation is not supported by this browser.");
    }
}

function showPosition(position) {
    document.getElementById("Latitude").value = position.coords.latitude;
    document.getElementById("Longitude").value = position.coords.longitude;
    document.getElementById("Radius").value = 25;
}



