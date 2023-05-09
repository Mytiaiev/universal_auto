// to get current year
(function() {
  var currentDate = new Date();
  var currentYear = currentDate.getFullYear();
  document.querySelector("#displayYear").innerHTML = currentYear;
})();

function toRadians(degrees) {
  return degrees * Math.PI / 180;
}

function haversine(lat1, lon1, lat2, lon2) {
  const earthRadiusKm = 6371;

  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);

  lat1 = toRadians(lat1);
  lat2 = toRadians(lat2);

  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.sin(dLon / 2) * Math.sin(dLon / 2) * Math.cos(lat1) * Math.cos(lat2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return earthRadiusKm * c;
}

function getAllPath(obj){
  var allPaths = [];
    for (var i = 0; i < obj.length; i++) {
      var currentPath = obj[i].path;
      allPaths = allPaths.concat(currentPath);
   }
    return allPaths
}

function pathSeparation(obj){
  var getCity = city_boundaries();
  var cityPolygon = new google.maps.Polygon({ paths: getCity });

  var inCity = [], outOfCity = [];
  obj.forEach(function(path) {
    // Використовуємо метод containsLocation() для перевірки, чи точка входить у межі міста
    var isInCity = google.maps.geometry.poly.containsLocation(path, cityPolygon);
    // Якщо точка входить у межі міста, додаємо її до масиву inCity, інакше - до масиву outOfCity
    if (isInCity) {
      inCity.push(path);
    } else {
      outOfCity.push(path);
    }
  });
   return [inCity, outOfCity]
}

function getPathCoords(obj){
  var coords = []
  for (var i = 0; i < obj.length; i++) {
    coords.push({ lat: obj[i].lat(), lng: obj[i].lng() });
  }
  return coords
}

function calculateDistance(obj) {
  let Distance = 0;
  for (let i = 0; i < obj.length - 1; i++) {
    const { lat: lat1, lng: lon1 } = obj[i];
    const { lat: lat2, lng: lon2 } = obj[i + 1];
    const distance = haversine(lat1, lon1, lat2, lon2);
    Distance += distance;
  }
  return Distance;
}

function hidePaymentButtons() {
  $(".order-confirm").remove()
}

function addMarker(obj) {
  const marker = new google.maps.Marker(obj);
  markersTaxi.push(marker)
    return marker;
}
function removeAllMarkers() {
  for(const m in markersTaxi) {
    markersTaxi[m].setMap(null);
  }
  markersTaxi = [];
}

function setAutoCenter(map) {
  var bounds = new google.maps.LatLngBounds();
  markersTaxi.forEach(marker => {
    bounds.extend(marker.getPosition());
  });
  map.fitBounds(bounds);
}

var map, orderReject, orderGo, orderConfirm, orderData, markersTaxi = [];

const decodedData = parkSettings.replace(/&#x(\w+);/g, (match, hex) => String.fromCharCode(parseInt(hex, 16)));
const parsedData = JSON.parse(decodedData.replace(/'/g, '"'));
const FREE_DISPATCH = parseInt(parsedData["FREE_CAR_SENDING_DISTANCE"]);
const TARIFF_DISPATCH = parseInt(parsedData["TARIFF_CAR_DISPATCH"]);
const TARIFF_OUTSIDE_DISPATCH = parseInt(parsedData["TARIFF_CAR_OUTSIDE_DISPATCH"]);
const TARIFF_IN_THE_CITY = parseInt(parsedData["TARIFF_IN_THE_CITY"]);
const TARIFF_OUTSIDE_THE_CITY = parseInt(parsedData["TARIFF_OUTSIDE_THE_CITY"]);
const CENTRE_CITY_LAT = parseFloat(parsedData["CENTRE_CITY_LAT"]);
const CENTRE_CITY_LNG = parseFloat(parsedData["CENTRE_CITY_LNG"]);
const CENTRE_CITY_RADIUS = parseInt(parsedData["CENTRE_CITY_RADIUS"]);
const SEND_TIME_ORDER_MIN = parseInt(parsedData["SEND_TIME_ORDER_MIN"]);

const city_boundaries = function () {
  return [
    [50.482433, 30.758250], [50.491685, 30.742045], [50.517374, 30.753721], [50.529704, 30.795370],
    [50.537806, 30.824810], [50.557504, 30.816837], [50.579778, 30.783808], [50.583684, 30.766494],
    [50.590833, 30.717995], [50.585827, 30.721184], [50.575221, 30.709590], [50.555702, 30.713665],
    [50.534572, 30.653589], [50.572107, 30.472565], [50.571557, 30.464734], [50.584574, 30.464120],
    [50.586367, 30.373054], [50.573406, 30.373049], [50.570661, 30.307423], [50.557272, 30.342127],
    [50.554324, 30.298128], [50.533394, 30.302445], [50.423057, 30.244148], [50.446055, 30.348753],
    [50.381271, 30.442675], [50.372075, 30.430830], [50.356963, 30.438040], [50.360358, 30.468252],
    [50.333520, 30.475291], [50.302393, 30.532814], [50.213270, 30.593929], [50.226755, 30.642478],
    [50.291609, 30.590369], [50.335279, 30.628839], [50.389522, 30.775925], [50.394966, 30.776293],
    [50.397798, 30.790669], [50.392594, 30.806395], [50.404878, 30.825881], [50.458385, 30.742751],
    [50.481657, 30.748158], [50.482454, 30.758345]
  ].map(function([lat, lng]){
    return {
      lat, lng
    }
  });
}
function getMarkerIcon(type) {
  return {
    url: 'static/app/images/icon_' + type + '.png',
    scaledSize: new google.maps.Size(32, 32),
  };
}

function orderUpdate(id_order) {
  var intervalId = setInterval(function() {
    $.ajax({
      url: ajaxPostUrl,
      method: 'GET',
      data: {
        "action": "order_confirm",
        "id_order": id_order
      },
      success: function(response) {
        var driverOrder = JSON.parse(response.data)
        if (driverOrder.length > 0) {
          clearInterval(intervalId);

          removeAllMarkers();

           const driverMarker = addMarker({
            position: new google.maps.LatLng(driverOrder[0].lat, driverOrder[0].lon),
            map,
            title: driverOrder[0].vehicle__licence_plate,
            icon: getMarkerIcon('taxi1'),
            animation: google.maps.Animation.DROP
          });
          var from = JSON.parse(getCookie('address'));
          var to = JSON.parse(getCookie('to_address'));

          const clientMarker = addMarker({
            position: from[0].geometry.location,
            map,
            title: from[0].formatted_address,
            icon: getMarkerIcon('address'),
            animation: google.maps.Animation.DROP
          });
          const destinationMarker =  addMarker({
            position: to[0].geometry.location,
            map,
            title: to[0].formatted_address,
            icon: getMarkerIcon('to_address'),
            animation: google.maps.Animation.DROP
          });

          // Create a directions service object to get the route
          var directionsService = new google.maps.DirectionsService();

          // Create a directions renderer object to display the route
          var directionsRenderer = new google.maps.DirectionsRenderer();

          // Bind the directions renderer to the map
          directionsRenderer.setMap(map);
          directionsRenderer.setOptions({suppressMarkers: true})

          // Set the options for the route
          var routeOptions = {
            origin: driverMarker.position,
            waypoints: [
              {
                location: clientMarker.position,
                stopover: true,
              },
              {
                location: destinationMarker.position,
                stopover: true,
              },
            ],
            destination: destinationMarker.position,
            travelMode: google.maps.TravelMode.DRIVING,
          };

          // Call the directions service to get the route
          directionsService.route(routeOptions, function (result, status) {
            if (status == google.maps.DirectionsStatus.OK) {
              // Display the route on the map
              directionsRenderer.setDirections(result);

              var pickupDistanceInMeters = result.routes[0].legs[0]['steps'];
              var finalDistanceInMeters = result.routes[0].legs[1]['steps'];

              var allPathsAddress = getAllPath(finalDistanceInMeters)
              var allPathsServing = getAllPath(pickupDistanceInMeters)

              var inCitOrOutCityAddress = pathSeparation(allPathsAddress)
              var inCitOrOutCityServing = pathSeparation(allPathsServing)
              var inCity = inCitOrOutCityAddress[0]
              var outOfCity = inCitOrOutCityAddress[1]
              var inCityServing = inCitOrOutCityServing[0]
              var outOfCityServing = inCitOrOutCityServing[1]

              var inCityCoords = getPathCoords(inCity)
              var outOfCityCoords = getPathCoords(outOfCity)
              var inCityCoordsServing = getPathCoords(inCityServing)
              var outOfCityCoordsServing = getPathCoords(outOfCityServing)


              let inCityDistance = calculateDistance(inCityCoords)
              let outOfCityDistance = calculateDistance(outOfCityCoords)
              let inCityDistanceServing = calculateDistance(inCityCoordsServing)
              let outOfCityDistanceServing = calculateDistance(outOfCityCoordsServing)

              var servingTaxi;
              if (inCityDistanceServing <= FREE_DISPATCH){
                servingTaxi = 0;
              } else {
                servingTaxi = ((inCityDistanceServing - FREE_DISPATCH) * TARIFF_DISPATCH) + (outOfCityDistanceServing * TARIFF_OUTSIDE_DISPATCH);
              }

              var tripAmount = (inCityDistance * TARIFF_IN_THE_CITY) + (outOfCityDistance * TARIFF_OUTSIDE_THE_CITY);

              var cost = servingTaxi + tripAmount;
              cost = Math.ceil(cost);
              setCookie('sum', cost, 1)

                $('.alert-message').html('Ціна поїздки:' +cost+ 'грн.');
              $('.order-confirm').remove();
              $('.order-reject').before('<button class="order-go btn btn-primary ml-3" onclick="consentTrip()">Погодитись</button>');

              google.maps.event.trigger(map, 'resize');
            }
          });
        }
      }
    });
  }, 5000);
}



function onOrderPayment(paymentMethod) {
  var savedOrderData = getCookie('orderData');
  if (!savedOrderData) {
    alert('Помилка: дані замовлення не знайдені.');
    return;
  }

  var orderData = JSON.parse(savedOrderData);
  orderData.latitude = getCookie('fromLat')
  orderData.longitude = getCookie('fromLon')
  orderData.to_latitude = getCookie('toLat')
  orderData.to_longitude = getCookie('toLon')
  orderData.payment_method = paymentMethod;

  return new Promise((resolve, reject) => {
    $.ajax({
      url: ajaxPostUrl,
      method: 'POST',
      data: orderData,
      headers: {
        'X-CSRF-Token': getCookie("csrfToken")
      },
      success: function(response) {
        var idOrder = JSON.parse(response.data)
        setCookie("idOrder", idOrder.id, 1);
        orderUpdate(idOrder.id);
        resolve(idOrder)
      },
      error: function(error) {
        // Handle the error
        console.log("Сталася помилка при відправленні замовлення:", error);
        reject(error);
      }
    });
  });
}


function onOrderReject() {
  var idOrder = getCookie('idOrder')
  var sum = getCookie('sum')
  destroyMap()

  if (idOrder)
    $.ajax({
      url: ajaxPostUrl,
      method: 'POST',
      data: {
        csrfmiddlewaretoken: getCookie("csrfToken"),
        action: 'user_opt_out',
        idOrder: idOrder,
        sum: sum,
      },
    })

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
  deleteCookie("address")

  // We attach an event to close the window when the cross is clicked
  var closeButton = commentForm.querySelector(".close");
  closeButton.addEventListener("click", function() {
    commentForm.parentNode.removeChild(commentForm);
    deleteAllCookies();
    location.reload();
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
      $('.modal').remove();
      deleteAllCookies();
      location.reload();
    },
    error: function(error) {
      // Handle the error
      console.log("Сталася помилка при відправленні коментаря:", error);
    }
  });
}

function consentTrip(){
  var idOrder = getCookie('idOrder')
  var sum = getCookie('sum')
  $.ajax({
    url: ajaxPostUrl,
    method: 'POST',
    data: {
      csrfmiddlewaretoken: getCookie("csrfToken"),
      action: 'order_sum',
      idOrder: idOrder,
      sum: sum,
    },
    success: function(response) {
      destroyMap();
      var applicationAccepted = document.createElement("div");
      applicationAccepted.innerHTML = `
        <div class="modal">
          <div class="modal-content">
            <span class="close">&times;</span>
            <h3>Ваша заявка прийнята. Очікуйте на автомобіль!</h3>
          </div>
        </div>
      `;
      document.body.appendChild(applicationAccepted);
      deleteAllCookies();

      // We attach an event to close the window when the cross is clicked
      var closeButton = applicationAccepted.querySelector(".close");
      closeButton.addEventListener("click", function() {
        applicationAccepted.parentNode.removeChild(applicationAccepted);
        deleteAllCookies();
        location.reload();
      });
    },
  })
}



function createMap(address, to_address, taxiArr) {
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
      // Add from_address marker
    addMarker({
      position: address[0].geometry.location,
      map,
      title: address[0].formatted_address,
      icon: getMarkerIcon('address'),
      animation: google.maps.Animation.DROP
    });

    addMarker({
      position:  to_address[0].geometry.location,
      map,
      title: to_address[0].formatted_address,
      icon: getMarkerIcon('to_address'),
      animation: google.maps.Animation.DROP
    });

    taxiArr.forEach(taxi => {
      // Create a marker for the taxi with the custom icon
      addMarker({
        position: new google.maps.LatLng(taxi.lat, taxi.lon),
        map,
        title: taxi.vehicle__licence_plate,
        icon: getMarkerIcon('taxi1'),
        animation: google.maps.Animation.DROP
      });
    });

    setAutoCenter(map);


    // Add the cost text to the map
    var costText = "Оберіть будь ласка метод оплати та заждіть поки ми підберемо вам автомобіль.";
    var costDiv = document.createElement('div');
    costDiv.innerHTML = '<div class="alert alert-primary mt-2" role="alert"><h6 class="alert-heading alert-message mb-0">' + costText + '</h6></div>';
    map.controls[google.maps.ControlPosition.TOP_CENTER].push(costDiv);

    // Add the payment buttons to the map
    var paymentDiv = document.createElement('div');
    paymentDiv.innerHTML =
      "<div class='mb-3'>" +
      "<button class='order-confirm btn btn-primary'>Готівка</button>" +
      // "<button class='order-confirm btn btn-primary ml-3'>Картка</button>" +
      "<button class='order-reject btn btn-danger ml-3'>Відмовитись</button>" +
      "</div>";

    map.controls[google.maps.ControlPosition.BOTTOM_CENTER].push(paymentDiv);

    // Add event listener to the "Готівка" button to send a post request to views.py
    orderConfirm = paymentDiv.getElementsByClassName('order-confirm')[0];
    orderConfirm.addEventListener("click", function (){
      onOrderPayment('Готівка')
      hidePaymentButtons();
    });

    // Add event listener to the "Картка" button to send a post request to views.py
    // orderConfirm = paymentDiv.getElementsByClassName('order-confirm')[1];
    // orderConfirm.addEventListener("click", function () {
    //   onOrderPayment('Картка')
    //   hidePaymentButtons();
    // });

    // Add event listener to the "Відмовитись" button to redirect to the homepage
    orderReject = paymentDiv.getElementsByClassName('order-reject')[0]
    orderReject.addEventListener("click", onOrderReject);
}

function destroyMap(){
     map = null;
     orderData = null
     orderConfirm.removeEventListener('click', onOrderPayment)
     orderReject.removeEventListener('click', onOrderReject)
     document.getElementById('order-modal').remove()
}

$.mask.definitions['9'] = '';
$.mask.definitions['d'] = '[0-9]';

function intlTelInit(phoneEl) {
  var phoneSelector = $(phoneEl);

  if (phoneSelector.length) {
    phoneSelector.mask("+380 dd ddd-dd-dd");
  }
}

$(document).ready(function(){
  setCookie("csrfToken", $.parseHTML(csrfToken)[0].value);

  $('#delivery_time').mask("dd:dd", {placeholder: "00:00 (Вкажіть час)"});
  intlTelInit('#phone');

  $('#order-form').on('submit', function(event){
    event.preventDefault();

    var isLateOrder = event.originalEvent.submitter.id === 'later-order';
    var form = new FormData(this);
    var timeWrapper = $('#order-time-field');
    var noTime = timeWrapper.hasClass('hidden');

    if (isLateOrder && noTime) {
      timeWrapper.removeClass('hidden').next().html('');
      return;
    }

    if(!isLateOrder) {
       timeWrapper.addClass('hidden').next().html('');
       form.delete('order_time')
    }

    var fields = form.keys()
    var errorFields = 0;
    var errorMsgs = {
      'phone_number': "Номер телефону обов'язковий",
      'from_address': "Адреса обов'язкова",
      'to_the_address': "Адреса обов'язкова",
      'order_time': "Час замовлення обов'язково"
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

    if (!errorFields && form.has('order_time')){
      const formattedDeliveryTime = moment(form.get('order_time'), 'HH:mm').format('YYYY-MM-DD HH:mm:ss');
      const currentTime = moment();
      const minCurrentTime = moment(currentTime).add(SEND_TIME_ORDER_MIN, 'minutes');
      if (moment(formattedDeliveryTime, 'YYYY-MM-DD HH:mm:ss').isSameOrAfter(minCurrentTime)){
        form.set('order_time', formattedDeliveryTime);
      }else {
        errorFields++;
        $('#order_time-error').html('Виберіть час не менше ніж через ' + SEND_TIME_ORDER_MIN + ' хвилин')
      }
    }

    if(!errorFields) {
      // Додаємо перевірку валідності адрес
      var fromAddress = form.get('from_address');
      var toAddress = form.get('to_the_address');

      var geocoder = new google.maps.Geocoder();
      geocoder.geocode({ 'address': fromAddress }, function(fromGeocoded, status) {
        if (status !== 'OK') {
          $('#from_address-error').html('Некоректна адреса');
          return;
        }
        geocoder.geocode({ 'address': toAddress }, function(toGeocoded, status) {
          if (status !== 'OK') {
            $('#to_the_address-error').html('Некоректна адреса');
            return;
          }
          form.append('action', 'order');
          orderData = Object.fromEntries(form);
          orderData.phone_number = orderData.phone_number.replace(/[^+0-9]/gi, '');
          var fromGeocode = fromGeocoded[0].geometry.location
          var toGeocode = toGeocoded[0].geometry.location
          setCookie("fromLat", fromGeocode.lat().toFixed(6), 1);
          setCookie("fromLon", fromGeocode.lng().toFixed(6), 1);
          setCookie("toLat", toGeocode.lat().toFixed(6), 1);
          setCookie("toLon", toGeocode.lng().toFixed(6), 1);
          setCookie('orderData', JSON.stringify(orderData));

          if(form.has('order_time')) {
            $('body').prepend( `
              <div class="modal">
                <div class="modal-content">
                  <span class="close" onclick="$('.modal').remove(); window.location.reload();">&times;</span>
                  <h3>Дякую за замовлення. Очікуйте на автомобіль!</h3>
                </div>
              </div>
            `);

            onOrderPayment().then(function(){
                deleteAllCookies();
            })
          } else {
            $.ajax({
              url: ajaxPostUrl,
              method: 'GET',
              data: {
                "action": "active_vehicles_locations"
              },
              success: function (response) {
                var taxiArr = JSON.parse(response.data);

                if (taxiArr.length > 0) {
                  createMap(fromGeocoded, toGeocoded, taxiArr);
                } else {
                  var noTaxiArr = document.createElement("div");
                  noTaxiArr.innerHTML = `
                    <div class="modal-taxi">
                      <div class="modal-content-taxi">
                        <span class="close">&times;</span>
                        <h3>Вибачте але на жаль вільних водіїв нема. Скористайтеся нашою послугою пізніше!</h3>
                      </div>
                    </div>
                  `;
                  document.body.appendChild(noTaxiArr);
                  deleteCookie("address")

                  // We attach an event to close the window when the cross is clicked
                  var closeButton = noTaxiArr.querySelector(".close");
                  closeButton.addEventListener("click", function () {
                    noTaxiArr.parentNode.removeChild(noTaxiArr);
                  });
                }
              }
            });
            setCookie("address", JSON.stringify(fromGeocoded), 1);
            setCookie("to_address", JSON.stringify(toGeocoded), 1);
            setCookie("phone", form.get('phone_number'), 1);
          }
        });
      });
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

function initAutocomplete(inputID) {
  const inputField = document.getElementById(inputID);
  const autoComplete = new google.maps.places.Autocomplete(inputField, {
    bounds: new google.maps.Circle({
      center: { lat: CENTRE_CITY_LAT, lng: CENTRE_CITY_LNG },
      radius: CENTRE_CITY_RADIUS,
    }).getBounds(),
    strictBounds: true,
  });
  autoComplete.addListener('place_changed', function(){
    const place = autoComplete.getPlace();
    if (place && place.formatted_address) {
      inputField.value = place.formatted_address;
    } else {
      inputField.value = '';
      inputField.placeholder = "Будь ласка, введіть коректну адресу";
    }
  });
}

loadGoogleMaps( 3, apiGoogle, "uk",'','geometry,places').then(function() {
 initAutocomplete('address');
 initAutocomplete('to_address');
 checkCookies()
});
