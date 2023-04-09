function getCookie (key){
    var cDecoded = decodeURIComponent(document.cookie)
    var cArray = cDecoded.split("; ")

    var result = null
    cArray.forEach((el) => {
        if (el.indexOf(key) === 0){
            result = el.substring(key.length + 1)
        }
    })
    return result;
}

function setCookie(key, value, daysToLive){
    var date = new Date()
    date.setTime(date.getTime() + (daysToLive * 24 * 60 * 60 * 1000))
    var expires = `expires=${date.toUTCString()}`
    document.cookie = `${key}=${value}; ${expires}`
}

function checkCookies(){
    var address = getCookie('address');
    var phone = getCookie('phone');
    if (address && phone) {
        $.ajax({
            url: ajaxPostUrl,
            method: 'GET',
            data: {
                "action": "active_vehicles_locations"
            },
             success: function(response){
                var taxiArr = JSON.parse(response.data)
                createMap(address, taxiArr);
             }
        })
    }
}

function deleteAllCookies() {
  var cookies = document.cookie.split(";");
  for (var i = 0; i < cookies.length; i++) {
    var cookieName = cookies[i].split("=")[0].trim();
    document.cookie = cookieName + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  }
}

// to get current year
(function() {
    var currentDate = new Date();
    var currentYear = currentDate.getFullYear();
    document.querySelector("#displayYear").innerHTML = currentYear;
})();

// add Google Maps script
var script = document.createElement("script");
script.setAttribute("src", `https://maps.googleapis.com/maps/api/js?key=${apiGoogle}&libraries=geometry`);
document.body.appendChild(script);

var map, orderReject, orderConfirm, orderData;

const decodedData = tariff.replace(/&#x(\w+);/g, (match, hex) => String.fromCharCode(parseInt(hex, 16)));
const parsedData = JSON.parse(decodedData.replace(/'/g, '"'));
const kmCost = parsedData["TARIFF_IN_THE_CITY"]
const KM_COST = parseInt(kmCost);


function getMarkerIcon (type) {
    return {
        url: 'static/app/images/icon_' + type + '.png',
        scaledSize: new google.maps.Size(32, 32),
    };
}

 function onOrderConfirm(){
  var savedOrderData = getCookie('orderData');
  if (!savedOrderData) {
    alert('Помилка: дані замовлення не знайдені.');
    return;
  }

  var orderData = JSON.parse(savedOrderData);

    $.ajax({
        url: ajaxPostUrl,
        method: 'POST',
        data: orderData,
        headers: {
        'X-CSRF-Token': getCookie("csrfToken")
    },
    })
     destroyMap();
    alert('Ваше замовлення прийнято!');
    deleteAllCookies();
 }

function onOrderReject() {
  // Destroy the map
  destroyMap();

  // Create an HTML window element with a comment form
  var commentForm = document.createElement("div");
  commentForm.innerHTML = `
    <div class="modal">
      <div class="modal-content">
        <span class="close">&times;</span>
        <h3>Коментар про відмову від поїздки</h3>
        <div class="form-group">
            <label for="reject_comment">Залишіть будьласка відгук</label>
            <textarea class="form-control" id="reject_comment" name="reject_comment" rows="3"></textarea>
        </div>
        <button class="btn btn-block btn-primary" onclick="sendComment()">Відправити</button>
      </div>
    </div>
  `;

  // Add a window to the page
  document.body.appendChild(commentForm);

  // We attach an event to close the window when the cross is clicked
  var closeButton = commentForm.querySelector(".close");
  closeButton.addEventListener("click", function() {
    commentForm.parentNode.removeChild(commentForm);
    deleteAllCookies();
  });
}

function sendComment() {
  // Send the comment to the server
  $.ajax({
    url: ajaxPostUrl,
    method: 'POST',
    data: {
        csrfmiddlewaretoken: getCookie("csrfToken"),
        action: 'send_comment',
        comment: $('[name="reject_comment"]').val()
    },
    success: function(response) {
        // Process the response from the server
        console.log("Коментар успішно відправлено!");
        $('.modal').remove()
        deleteAllCookies();
    },
    error: function(error) {
        // Handle the error
        console.log("Сталася помилка при відправленні коментаря:", error);
    }
  });
}


function createMap(address, taxiArr) {
   var modal = document.createElement('div');
        modal.id = 'order-modal';
        modal.innerHTML = '<div id="map"></div>';

        document.body.appendChild(modal);

    var mapCanvas = document.getElementById("map");
    var mapOpts = {
        zoom: 10,
        center: new google.maps.LatLng(50.4546600, 30.5238000)
    };
    map = new google.maps.Map(mapCanvas, mapOpts);

    // Create a geocoder object to convert the address to coordinates
    var geocoder = new google.maps.Geocoder();

    geocoder.geocode({ address }, function (results, status) {
        if (status == google.maps.GeocoderStatus.OK) {
            // Get the coordinates of the address
            var latLng = results[0].geometry.location;

            // Create a marker for the address
            var marker = new google.maps.Marker({
                position: latLng,
                map: map,
                title: address,
                icon: getMarkerIcon('address'),
                animation: google.maps.Animation.DROP
            });

            var markers = [];
            taxiArr.forEach(taxi => {
                // Create a marker for the taxi with the custom icon
                var taxiLatLng = new google.maps.LatLng(taxi.lat, taxi.lon);
                var taxiMarker = new google.maps.Marker({
                  position: taxiLatLng,
                  map: map,
                  title: taxi.vehicle__licence_plate,
                  icon: getMarkerIcon('taxi'),
                  animation: google.maps.Animation.DROP
                });
                // Add the marker to the markers array
                markers.push(taxiMarker);
            });
            var bounds = new google.maps.LatLngBounds();
            markers.forEach(marker => {
                bounds.extend(marker.getPosition());
            });
            map.fitBounds(bounds);

            // Create a directions service object to get the route
            var directionsService = new google.maps.DirectionsService();

            // Create a directions renderer object to display the route
            var directionsRenderer = new google.maps.DirectionsRenderer();

            // Bind the directions renderer to the map
            directionsRenderer.setMap(map);
            directionsRenderer.setOptions( { suppressMarkers: true })

            var closestMarker;
            var closestDistance = Infinity;
            markers.forEach(function (marker) {
                var distance = google.maps.geometry.spherical.computeDistanceBetween(latLng, marker.position);
                if (distance < closestDistance) {
                    closestMarker = marker;
                    closestDistance = distance;
                }
            });
            // Set the options for the route
            var routeOptions = {
                origin: closestMarker.position,
                destination: latLng,
                travelMode: google.maps.TravelMode.DRIVING,
            };

            // Call the directions service to get the route
            directionsService.route(routeOptions, function (result, status) {
                if (status == google.maps.DirectionsStatus.OK) {
                    // Display the route on the map
                    directionsRenderer.setDirections(result);

                    // Calculate the distance between the taxi and the address in kilometers
                    var distanceInMeters = result.routes[0].legs[0].distance.value;
                    var distanceInKm = distanceInMeters / 1000;

                    // Calculate the cost of the taxi ride
                    var cost = distanceInKm * KM_COST;

                    // Add the cost text to the map
                    var costText = "Подача автомобіля буде коштувати " + cost.toFixed(2) + " грн";
                    var costDiv = document.createElement('div');
                    costDiv.innerHTML = '<div class="alert alert-primary mt-2" role="alert"><h6 class="alert-heading mb-0">' + costText + '</h6></div>';
                    map.controls[google.maps.ControlPosition.TOP_CENTER].push(costDiv);

                    // Add the payment buttons to the map
                    var paymentDiv = document.createElement('div');
                    paymentDiv.innerHTML =
                        "<div class='mb-3'>" +
                            "<button class='order-confirm btn btn-primary'>Оплатити</button>" +
                            "<button class='order-reject btn btn-danger ml-3'>Відмовитись</button>" +
                        "</div>";

                    map.controls[google.maps.ControlPosition.BOTTOM_CENTER].push(paymentDiv);

                     // Add event listener to the "Оплатити" button to send a post request to views.py with the address and phone number
                    orderConfirm = paymentDiv.getElementsByClassName('order-confirm')[0];
                    orderConfirm.addEventListener("click", onOrderConfirm);

                    // Add event listener to the "Відмовитись" button to redirect to the homepage
                    orderReject = paymentDiv.getElementsByClassName('order-reject')[0]
                    orderReject.addEventListener("click", onOrderReject);

                    google.maps.event.trigger(map, 'resize');
                }
            });
        }
    });
}

function destroyMap(){
     map = null;
     orderData = null
     orderConfirm.removeEventListener('click', onOrderConfirm)
     orderReject.removeEventListener('click', onOrderReject)
     document.getElementById('order-modal').remove()
}

$(document).ready(function(){
    setCookie("csrfToken", $.parseHTML(csrfToken)[0].value)
    checkCookies();
  $('#order-form').on('submit', function(event){
    event.preventDefault();
    var form = new FormData(this);
    var fields = form.keys()
    var errorFields = 0;
    var errorMsgs = {
        'phone_number': "Номер телефону обов'язковий",
        'from_address': "Адреса обов'язкова"
    }

    for(const field of fields) {
        const err = $(`#${field}-error`);
        if(form.get(field).length === 0) {
            errorFields++;
            err.html(errorMsgs[field]);
        } else {
            err.html('');
        }
    }

    if(!errorFields) {
        form.append('action', 'order')
        orderData = Object.fromEntries(form)
         $.ajax({
            url: ajaxPostUrl,
            method: 'GET',
            data: {
                "action": "active_vehicles_locations"
            },
             success: function(response){
                var taxiArr = JSON.parse(response.data)
                createMap(form.get('from_address'), taxiArr)
             }
        })
        setCookie("address", form.get('from_address'), 1)
        setCookie("phone", form.get('phone_number'), 1)
        setCookie('orderData', JSON.stringify(orderData), 1);
    }
  });
});

$(document).ready(function(){
  $('[id^="sub-form-"]').on('submit', function(event){
    event.preventDefault();
    const form = this;
    $.ajax({
      type: "POST",
      url: ajaxPostUrl,
      data: {
        'email': $(event.target).find('#sub_email').val(),
        'action': 'subscribe',
        'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
      },
      success: function(data){
        $('#email-error-1, #email-error-2').html('');
        this.reset();
      },

      error: function(data){
       $('#email-error-1, #email-error-2').html('');
        var errors = data.responseJSON;
        $.each(errors, function(key, value) {
          $('#' + key + '-error-1').html(value);
          $('#' + key + '-error-2').html(value);
        });
      }
    });
  });
});