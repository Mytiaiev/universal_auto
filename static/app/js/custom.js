let map, orderReject, orderGo, orderConfirm, orderData, markersTaxi,
	taxiMarkers = [];
let circle, intervalId, intervalTime, intervalTaxiMarker;

const FREE_DISPATCH = parseInt(parkSettings && parkSettings.FREE_CAR_SENDING_DISTANCE || 0);
const TARIFF_DISPATCH = parseInt(parkSettings && parkSettings.TARIFF_CAR_DISPATCH || 0);
const TARIFF_OUTSIDE_DISPATCH = parseInt(parkSettings && parkSettings.TARIFF_CAR_OUTSIDE_DISPATCH || 0);
const TARIFF_IN_THE_CITY = parseInt(parkSettings && parkSettings.TARIFF_IN_THE_CITY || 0);
const TARIFF_OUTSIDE_THE_CITY = parseInt(parkSettings && parkSettings.TARIFF_OUTSIDE_THE_CITY || 0);
const CENTRE_CITY_LAT = parseFloat(parkSettings && parkSettings.CENTRE_CITY_LAT || 0);
const CENTRE_CITY_LNG = parseFloat(parkSettings && parkSettings.CENTRE_CITY_LNG || 0);
const CENTRE_CITY_RADIUS = parseInt(parkSettings && parkSettings.CENTRE_CITY_RADIUS || 0);
const SEND_TIME_ORDER_MIN = parseInt(parkSettings && parkSettings.SEND_TIME_ORDER_MIN || 0);
const MINIMUM_PRICE_RADIUS = parseInt(parkSettings && parkSettings.MINIMUM_PRICE_RADIUS || 0);
const MAXIMUM_PRICE_RADIUS = parseInt(parkSettings && parkSettings.MAXIMUM_PRICE_RADIUS || 0);
const TIMER = parseInt(parkSettings && parkSettings.SEARCH_TIME || 0);
const userLanguage = navigator.language || navigator.userLanguage;

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
	].map(function ([lat, lng]) {
		return {
			lat, lng
		}
	});
};

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

function getAllPath(obj) {
	let allPaths = [];
	for (let i = 0; i < obj.length; i++) {
		let currentPath = obj[i].path;
		allPaths = allPaths.concat(currentPath);
	}
	return allPaths
}

function pathSeparation(obj) {
	let getCity = city_boundaries();
	let cityPolygon = new google.maps.Polygon({paths: getCity});

	let inCity = [], outOfCity = [];
	obj.forEach(function (path) {
		// Використовуємо метод containsLocation() для перевірки, чи точка входить у межі міста
		let isInCity = google.maps.geometry.poly.containsLocation(path, cityPolygon);
		// Якщо точка входить у межі міста, додаємо її до масиву inCity, інакше - до масиву outOfCity
		if (isInCity) {
			inCity.push(path);
		} else {
			outOfCity.push(path);
		}
	});
	return [inCity, outOfCity]
}

function getPathCoords(obj) {
	let coords = []
	for (let i = 0; i < obj.length; i++) {
		coords.push({lat: obj[i].lat(), lng: obj[i].lng()});
	}
	return coords
}

function calculateDistance(obj) {
	let Distance = 0;
	for (let i = 0; i < obj.length - 1; i++) {
		const {lat: lat1, lng: lon1} = obj[i];
		const {lat: lat2, lng: lon2} = obj[i + 1];
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
	if (Array.isArray(markersTaxi)) {
		markersTaxi.push(marker);
	} else {
		markersTaxi = [marker];
	}
	return marker;
}

function setAutoCenter(map) {
	let bounds = new google.maps.LatLngBounds();
	markersTaxi.forEach(marker => {
		bounds.extend(marker.getPosition());
	});
	map.fitBounds(bounds);
}

function getMarkerIcon(type) {
	return {
		url: 'static/app/images/icon_' + type + '.webp',
		scaledSize: new google.maps.Size(32, 32),
	};
}

function createMap(address, to_address) {
	let modal = document.createElement('div');
	modal.id = 'order-modal';
	modal.innerHTML = '<div id="map"></div>';

	document.body.appendChild(modal);

	let mapCanvas = document.getElementById("map");
	let mapOpts = {
		zoom: 10,
		center: new google.maps.LatLng(50.4546600, 30.5238000)
	};
	map = new google.maps.Map(mapCanvas, mapOpts);

	// Додати from_address маркер
	addMarker({
		position: address[0].geometry.location,
		map,
		title: address[0].formatted_address,
		icon: getMarkerIcon('address'),
		animation: google.maps.Animation.DROP
	});

	// Додати to_address маркер
	addMarker({
		position: to_address[0].geometry.location,
		map,
		title: to_address[0].formatted_address,
		icon: getMarkerIcon('to_address'),
		animation: google.maps.Animation.DROP
	});

	let directionsService = new google.maps.DirectionsService();
	let request = {
		origin: address[0].formatted_address,
		destination: to_address[0].formatted_address,
		travelMode: google.maps.TravelMode.DRIVING
	};
	directionsService.route(request, function (result, status) {
		if (status == google.maps.DirectionsStatus.OK) {
			// Отримати відстань між точками
			let distanceInMeters = result.routes[0].legs[0]['steps'];

			let allPathsAddress = getAllPath(distanceInMeters)

			let inCitOrOutCityAddress = pathSeparation(allPathsAddress)
			let inCity = inCitOrOutCityAddress[0]
			let outOfCity = inCitOrOutCityAddress[1]

			let inCityCoords = getPathCoords(inCity)
			let outOfCityCoords = getPathCoords(outOfCity)


			let inCityDistance = parseInt(calculateDistance(inCityCoords));
			let outOfCityDistance = parseInt(calculateDistance(outOfCityCoords));
			let totalDistance = inCityDistance + outOfCityDistance;

			let tripAmount = Math.ceil((inCityDistance * TARIFF_IN_THE_CITY) + (outOfCityDistance * TARIFF_OUTSIDE_THE_CITY));
			setCookie('sumOder', tripAmount, 1)
			setCookie('distanceGoogle', totalDistance, 1)
			setAutoCenter(map);

			// Додати текст та таймер до елементу costDiv
			let costText = gettext("Оберіть метод оплати.");
			let costDiv = document.createElement('div');
			costDiv.innerHTML = '<div class="alert alert-primary mt-2" role="alert">' +
				'<h6 class="alert-heading alert-message mb-0">' + costText + '</h6><div id="timer"></div></div>';
			map.controls[google.maps.ControlPosition.TOP_CENTER].push(costDiv);

			// Додати кнопки оплати на карту
			let paymentDiv = document.createElement('div');
			let button1 = gettext('Готівка');
			let button2 = gettext('Картка');
			let button3 = gettext('Відмовитись');
			paymentDiv.innerHTML =
				"<div class='mb-3'>" +
				"<button class='order-confirm btn btn-primary'>" + button1 + "</button>" +
				// "<button class='order-confirm btn btn-primary ml-3'>" + button2 + "</button>" +
				"<button class='order-reject btn btn-danger ml-3'>" + button3 + "</button>" +
				"</div>";

			map.controls[google.maps.ControlPosition.BOTTOM_CENTER].push(paymentDiv);

			if (getCookie('idOrder') != null) {
				orderConfirm = paymentDiv.getElementsByClassName('order-confirm')[0];
				let Text = gettext("Зачекайте поки ми підберемо вам автомобіль. Ваша ціна складає ") + tripAmount + gettext(" грн.");
				costDiv = document.createElement('div');
				costDiv.innerHTML = '<div class="alert alert-primary mt-2" role="alert">' +
					'<h6 class="alert-heading alert-message mb-0">' + Text + '</h6><div id="timer"></div></div>';
				map.controls[google.maps.ControlPosition.TOP_CENTER].clear();
				map.controls[google.maps.ControlPosition.TOP_CENTER].push(costDiv);
				intervalTaxiMarker = setInterval(updateTaxiMarkers, 10000);
				orderConfirm.remove()
				startTimer();

				// Додати обробник події для кнопки "Відмовитись" для перенаправлення на домашню сторінку
				orderReject = paymentDiv.getElementsByClassName('order-reject')[0];
				orderReject.addEventListener("click", onOrderReject);
			} else {
				// Додати обробник події для кнопки "Готівка" для відправлення POST-запиту до views.py
				orderConfirm = paymentDiv.getElementsByClassName('order-confirm')[0];
				orderConfirm.addEventListener("click", function () {
					costText = gettext("Заждіть поки ми підберемо вам автомобіль. Ваша ціна складає ") + tripAmount + gettext(" грн.");
					costDiv.innerHTML = '<div class="alert alert-primary mt-2" role="alert">' +
						'<h6 class="alert-heading alert-message mb-0">' + costText + '</h6><div id="timer"></div></div>';
					map.controls[google.maps.ControlPosition.TOP_CENTER].clear();
					map.controls[google.maps.ControlPosition.TOP_CENTER].push(costDiv);
					map.controls[google.maps.ControlPosition.BOTTOM_CENTER].clear();
					map.controls[google.maps.ControlPosition.BOTTOM_CENTER].push(paymentDiv);
					onOrderPayment('Готівка');
					hidePaymentButtons();
					startTimer();
				});

				// Додати обробник події для кнопки "Відмовитись" для перенаправлення на домашню сторінку
				orderReject = paymentDiv.getElementsByClassName('order-reject')[0];
				orderReject.addEventListener("click", onOrderReject);
			}
		}
	});
}

function orderUpdate(id_order) {
	intervalId = setInterval(function () {
		$.ajax({
			url: ajaxGetUrl,
			method: 'GET',
			data: {
				"action": "order_confirm",
				"id_order": id_order
			},
			success: function (response) {
				let driverOrder = JSON.parse(response.data)
				if (driverOrder.vehicle_gps) {
					clearInterval(intervalId);
					clearInterval(intervalTime);
					clearInterval(intervalTaxiMarker);

					clearTaxiMarkers();
					$('#timer').remove();

					const driverMarker = addMarker({
						position: new google.maps.LatLng(driverOrder.vehicle_gps[0].lat, driverOrder.vehicle_gps[0].lon),
						map,
						title: driverOrder.vehicle_gps[0].vehicle__licence_plate,
						icon: getMarkerIcon('taxi1'),
						animation: google.maps.Animation.DROP
					});

					let from = JSON.parse(getCookie('address'));
					let to = JSON.parse(getCookie('to_address'));

					const clientMarker = addMarker({
						position: from[0].geometry.location,
						map,
						title: from[0].formatted_address,
						icon: getMarkerIcon('address'),
						animation: google.maps.Animation.DROP
					});
					const destinationMarker = addMarker({
						position: to[0].geometry.location,
						map,
						title: to[0].formatted_address,
						icon: getMarkerIcon('to_address'),
						animation: google.maps.Animation.DROP
					});

					// Create a directions service object to get the route
					let directionsService = new google.maps.DirectionsService();

					// Create a directions renderer object to display the route
					let directionsRenderer = new google.maps.DirectionsRenderer();

					// Bind the directions renderer to the map
					directionsRenderer.setMap(map);
					directionsRenderer.setOptions({suppressMarkers: true})

					// Set the options for the route
					let routeOptions = {
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
						language: userLanguage,
					};

					// Call the directions service to get the route
					directionsService.route(routeOptions, function (result, status) {
						if (status == google.maps.DirectionsStatus.OK) {
							directionsRenderer.setDirections(result);

							let tripAmount = parseInt(getCookie('sumOder'));
							let cost = parseInt(driverOrder.car_delivery_price) + tripAmount;
							cost = Math.ceil(cost);

							let durationToA = result.routes[0].legs[0].duration.text;

							$('.alert-message').html(gettext('Ціна поїздки: ') + cost + gettext(' грн. Приблизний час прибуття авто: ') + durationToA);
							$('.order-confirm').remove();
							$('.order-reject').before('<button class="order-go btn btn-primary ml-3" onclick="consentTrip()">' + gettext("Погодитись") + '</button>');

							google.maps.event.trigger(map, 'resize');
						}
					});
				}
			}
		});
	}, 5000);
}


function onOrderPayment(paymentMethod) {
	let savedOrderData = getCookie('orderData');
	if (!savedOrderData) {
		alert('Помилка: дані замовлення не знайдені.');
		return;
	}

	let orderData = JSON.parse(savedOrderData);
	orderData.sum = getCookie('sumOder');
	orderData.distance_google = getCookie('distanceGoogle');
	orderData.latitude = getCookie('fromLat');
	orderData.longitude = getCookie('fromLon');
	orderData.to_latitude = getCookie('toLat');
	orderData.to_longitude = getCookie('toLon');
	orderData.payment_method = paymentMethod;
	orderData.status_order = 'Очікується';

	return new Promise((resolve, reject) => {
		$.ajax({
			url: ajaxPostUrl,
			method: 'POST',
			data: orderData,
			headers: {
				'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
			},
			success: function (response) {
				let idOrder = JSON.parse(response.data)
				setCookie("idOrder", idOrder.id, 1);
				orderUpdate(idOrder.id);
				resolve(idOrder)
			},
			error: function (error) {
				// Handle the error
				console.log("Сталася помилка при відправленні замовлення:", error);
				reject(error);
			}
		});
	});
}


function onOrderReject() {
	let idOrder = getCookie('idOrder')
	clearInterval(intervalTaxiMarker);
	destroyMap()
	$('#timer').remove();

	if (idOrder)
		$.ajax({
			url: ajaxPostUrl,
			method: 'POST',
			data: {
				csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
				action: 'user_opt_out',
				idOrder: idOrder,
			},
		})

	// Create an HTML window element with a comment form
	let modalText = gettext("Коментар про відмову від поїздки")
	let modalButton = gettext("Відправити")
	let commentForm = document.createElement("div");
	commentForm.innerHTML = `
    <div class="modal">
      <div class="modal-content">
        <span class="close">&times;</span>
        <h3>${modalText}</h3>
        <div class="form-group">
          <label for="reject_comment">${gettext("Залишіть, будь ласка, відгук")}</label>
          <textarea class="form-control" id="reject_comment" name="reject_comment" rows="3"></textarea>
        </div>
        <button class="btn btn-block btn-primary" onclick="sendComment()">${modalButton}</button>
      </div>
    </div>
  `;

	// Add a window to the page
	document.body.appendChild(commentForm);
	deleteCookie("address")

	// We attach an event to close the window when the cross is clicked
	let closeButton = commentForm.querySelector(".close");
	closeButton.addEventListener("click", function () {
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
			csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
			action: 'send_comment',
			comment: $('[name="reject_comment"]').val()
		},
		success: function (response) {
			// Process the response from the server
			$('.modal').remove();
			deleteAllCookies();
			location.reload();
		},
		error: function (error) {
			// Handle the error
			console.log("Сталася помилка при відправленні коментаря:", error);
		}
	});
}

function consentTrip() {
	destroyMap();
	let text1 = gettext('Ваша заявка прийнята. Очікуйте на автомобіль!');
	let applicationAccepted = document.createElement("div");
	applicationAccepted.innerHTML = `
    <div class="modal">
      <div class="modal-content">
        <h3>${text1}</h3>
      </div>
    </div>
  `;
	document.body.appendChild(applicationAccepted);
	deleteAllCookies();

	let modal = applicationAccepted.querySelector(".modal");

	setTimeout(function () {
		modal.parentNode.removeChild(modal);
		deleteAllCookies();
		location.reload();
	}, 5000);
}

function startTimer() {
	let duration = TIMER * 1000; // 3 хвилини
	// let duration = 10 * 1000; // 3 хвилини

	// Отримати збережений час початку таймера
	let startTime = getCookie('timerStartTime');
	if (startTime) {
		startTime = parseInt(startTime);
	} else {
		startTime = Date.now();
		// Зберегти час початку таймера в куках
		setCookie('timerStartTime', startTime, 1);
	}

	document.addEventListener('DOMContentLoaded', function () {
		let timer = document.createElement('div');
		timer.id = 'timer';

		let costDiv = document.getElementsByClassName('alert alert-primary mt-2')[0];
		costDiv.appendChild(timer);
	});

	// Зупинити попередній таймер, якщо він вже запущений
	clearInterval(intervalTime);

	let intervalTime = setInterval(function () {
		let elapsedTime = Date.now() - startTime;
		let remainingTime = duration - elapsedTime;

		// Перевірити, чи таймер закінчився
		if (remainingTime <= 0) {
			deleteCookie('timerStartTime');
			clearInterval(intervalTime);
			// let timerElement = document.getElementById('timer');
			// if (timerElement) {
			//   timerElement.remove();
			// }

			let modalContent = document.createElement('div');
			let text = gettext('Зараз спостерігається підвищений попит бажаєте збільшити ціну для прискорення пошуку?');
			let buttonTextIncrease = gettext('Підвищити');
			let buttonTextSearch = gettext('Шукати далі');
			let buttonTextDecline = gettext('Відмовитись');
			modalContent.innerHTML = '<div id="timer-modal" class="modal">\n' +
				'  <div class="modal-content">\n' +
				'    <p>' + text + '</p>\n' +
				'    <div class="slider-container">\n' +
				'      <input type="range" id="price-range" min="' + MINIMUM_PRICE_RADIUS + '" max="' + MAXIMUM_PRICE_RADIUS + '" step="1" value="' + MINIMUM_PRICE_RADIUS + '" class="price-range">\n' +
				'      <span id="slider-value">30 ₴</span>\n' +
				'    </div>\n' +
				'    <div class="button-group">\n' +
				'      <button class="btn btn-primary">' + buttonTextIncrease + '</button>\n' +
				'      <button class="btn btn-primary">' + buttonTextSearch + '</button>\n' +
				'      <button class="btn btn-danger">' + buttonTextDecline + '</button>\n' +
				'    </div>\n' +
				'  </div>\n' +
				'</div>';
			let modal = document.createElement('div');
			modal.id = 'timer-modal';
			modal.classList.add('modal');
			modal.appendChild(modalContent);
			document.body.appendChild(modal);

			let increasePrice = modal.getElementsByClassName('btn-primary')[0];
			let continueSearch = modal.getElementsByClassName('btn-primary')[1];
			let rejectSearch = modal.getElementsByClassName('btn-danger')[0];

			increasePrice.addEventListener('click', function () {
				setCookie("car_delivery_price", sliderElement.value, 1);
				onIncreasePrice();
				modal.remove();
			});
			continueSearch.addEventListener('click', function () {
				onContinueSearch();
				modal.remove();
			});
			rejectSearch.addEventListener('click', function () {
				onOrderReject();
				modal.remove();
			});

			let sliderElement = document.getElementById('price-range');
			let sliderValueElement = document.getElementById('slider-value');
			sliderElement.addEventListener('input', function () {
				sliderValueElement.textContent = sliderElement.value + '₴';
			});
		}

		// Обчислити хвилини та секунди
		let minutes = Math.floor(remainingTime / 60000);
		let seconds = Math.floor((remainingTime % 60000) / 1000);

		let timerElements = document.getElementById('timer');
		let timerText = gettext('Приблизний час пошуку: ') + minutes + gettext(' хв ') + seconds + gettext(' сек');
		if (timerElements) {
			timerElements.innerHTML = timerText;
		}
	}, 1000);
}


function onIncreasePrice() {
	let idOrder = getCookie('idOrder');
	let carDeliveryPrice = getCookie('car_delivery_price');

	// Розрахунок нового радіуса
	let newRadius = (FREE_DISPATCH * 1000) + (carDeliveryPrice / TARIFF_DISPATCH) * 1000;

	$.ajax({
		url: ajaxPostUrl,
		method: 'POST',
		data: {
			csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
			action: 'increase_price',
			idOrder: idOrder,
			carDeliveryPrice: carDeliveryPrice
		},
		success: function (response) {
			// Оновлення радіуса на карті
			updateCircleRadius(newRadius);
			startTimer();
		}
	});
}

function updateCircleRadius(radius) {
	// Перевірити, чи коло вже існує
	if (circle) {
		// Оновити радіус кола
		circle.setRadius(radius);
	}
}


function onContinueSearch() {
	let idOrder = getCookie('idOrder');

	$.ajax({
		url: ajaxPostUrl,
		method: 'POST',
		data: {
			csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
			action: 'continue_search',
			idOrder: idOrder
		},
		success: function (response) {
			startTimer()
		}
	});
}

function destroyMap() {
	map = null;
	orderData = null
	orderConfirm.removeEventListener('click', onOrderPayment)
	orderReject.removeEventListener('click', onOrderReject)
	document.getElementById('order-modal').remove()
}

$.mask.definitions['9'] = '';
$.mask.definitions['d'] = '[0-9]';

function intlTelInit(phoneEl) {
	let phoneSelector = $(phoneEl);

	if (phoneSelector.length) {
		phoneSelector.mask("+380 dd ddd-dd-dd");
	}
}

$(document).ready(function () {

	$('#delivery_time').mask("dd:dd", {placeholder: gettext("00:00 (Вкажіть час)")});
	intlTelInit('#phone');

	$('input[name="radio"]').on('change', function () {
		let selectedValue = $('input[name="radio"]:checked').val();
		if (selectedValue === '2') {
			$('#order-time-field').removeClass('hidden');
			$('#order_time-error').removeClass('hidden');
		} else {
			$('#order-time-field').addClass('hidden');
		}

		if (selectedValue === '1') {
			$('#order_time-error').addClass('hidden');
		}
	});

	$('#order-form').on('submit', function (event) {
		event.preventDefault();

		let isLateOrder = $('input[name="radio"]:checked').val() === '2';
		let form = new FormData(this);
		let timeWrapper = $('#order-time-field');
		let noTime = timeWrapper.hasClass('hidden');

		if (isLateOrder && noTime) {
			timeWrapper.removeClass('hidden').next().html('');
			return;
		}

		if (!isLateOrder) {
			timeWrapper.addClass('hidden').next().html('');
			form.delete('order_time')
		}

		let fields = form.keys()
		let errorFields = 0;
		let errorMsgs = {
			'phone_number': gettext("Номер телефону обов'язковий"),
			'from_address': gettext("Адреса обов'язкова"),
			'to_the_address': gettext("Адреса обов'язкова"),
			'order_time': gettext("Час замовлення обов'язково")
		}

		for (const field of fields) {
			const err = $(`#${field}-error`);
			if (form.get(field).length === 0) {
				errorFields++;
				err.html(errorMsgs[field]);
			} else {
				err.html('');
			}
		}

		if (!errorFields && form.has('order_time')) {
			const formattedDeliveryTime = moment(form.get('order_time'), 'HH:mm').format('YYYY-MM-DD HH:mm:ss');
			const currentTime = moment();
			const minCurrentTime = moment(currentTime).add(SEND_TIME_ORDER_MIN, 'minutes');
			if (moment(formattedDeliveryTime, 'YYYY-MM-DD HH:mm:ss').isSameOrAfter(minCurrentTime)) {
				form.set('order_time', formattedDeliveryTime);
			} else {
				errorFields++;
				let orderTimeError1 = gettext('Виберіть час не менше ніж через ');
				let orderTimeError2 = gettext(' хвилин');
				$('#order_time-error').html(orderTimeError1 + SEND_TIME_ORDER_MIN + orderTimeError2)
			}
		}

		if (!errorFields) {
			// Додаємо перевірку валідності адрес
			let fromAddress = form.get('from_address');
			let toAddress = form.get('to_the_address');

			let geocoder = new google.maps.Geocoder();
			geocoder.geocode({'address': fromAddress}, function (fromGeocoded, status) {
				if (status !== 'OK') {
					$('#from_address-error').html(gettext('Некоректна адреса'));
					return;
				}
				geocoder.geocode({'address': toAddress}, function (toGeocoded, status) {
					if (status !== 'OK') {
						$('#to_the_address-error').html(gettext('Некоректна адреса'));
						return;
					}
					form.append('action', 'order');
					orderData = Object.fromEntries(form);
					orderData.phone_number = orderData.phone_number.replace(/[^+0-9]/gi, '');
					let fromGeocode = fromGeocoded[0].geometry.location
					let toGeocode = toGeocoded[0].geometry.location
					setCookie("fromLat", fromGeocode.lat().toFixed(6), 1);
					setCookie("fromLon", fromGeocode.lng().toFixed(6), 1);
					setCookie("toLat", toGeocode.lat().toFixed(6), 1);
					setCookie("toLon", toGeocode.lng().toFixed(6), 1);
					setCookie('orderData', JSON.stringify(orderData));

					if (form.has('order_time')) {
						// Отримання координат з куків
						let fromLat = parseFloat(getCookie("fromLat"));
						let fromLon = parseFloat(getCookie("fromLon"));
						let toLat = parseFloat(getCookie("toLat"));
						let toLon = parseFloat(getCookie("toLon"));

						// Створення об'єктів google.maps.LatLng на основі координат з куків
						let fromLocation = new google.maps.LatLng(fromLat, fromLon);
						let toLocation = new google.maps.LatLng(toLat, toLon);

						// Створення об'єкту запиту для DirectionsService
						let request = {
							origin: fromLocation,
							destination: toLocation,
							travelMode: google.maps.TravelMode.DRIVING
						};

						// Виклик DirectionsService для отримання маршруту та відстані
						let directionsService = new google.maps.DirectionsService();
						directionsService.route(request, function (result, status) {
							if (status === google.maps.DirectionsStatus.OK) {
								let distanceInMeters = result.routes[0].legs[0]['steps'];

								let allPathsAddress = getAllPath(distanceInMeters)

								let inCitOrOutCityAddress = pathSeparation(allPathsAddress)
								let inCity = inCitOrOutCityAddress[0]
								let outOfCity = inCitOrOutCityAddress[1]

								let inCityCoords = getPathCoords(inCity)
								let outOfCityCoords = getPathCoords(outOfCity)


								let inCityDistance = parseInt(calculateDistance(inCityCoords));
								let outOfCityDistance = parseInt(calculateDistance(outOfCityCoords));
								let totalDistance = inCityDistance + outOfCityDistance;


								let tripAmount = Math.ceil((inCityDistance * TARIFF_IN_THE_CITY) + (outOfCityDistance * TARIFF_OUTSIDE_THE_CITY));
								setCookie('sumOder', tripAmount, 1)
								setCookie('distanceGoogle', totalDistance, 1)


								let text2 = gettext('Дякуємо за замовлення. Очікуйте на автомобіль! Ваша вартість поїздки: ') +
									'<span class="trip-amount">' + tripAmount + '</span>' + gettext(' грн.');
								let modal = $('<div class="modal">' +
									'<div class="modal-content rounded">' +
									'<h3 class="modal-title">' + text2 + '</h3>' +
									'<div class="buttons-container">' +
									'<button class="order-confirm btn btn-primary">' + gettext('Погодитись') + '</button>' +
									'<button class="order-reject btn btn-danger">' + gettext('Відмовитись') + '</button>' +
									'</div>' +
									'</div>' +
									'</div>');

								$('body').prepend(modal);

								modal.find('.order-confirm').on('click', function () {
									onOrderPayment().then(function () {
										deleteAllCookies();
									});
									modal.remove();
									window.location.reload();
								});

								modal.find('.order-reject').on('click', function () {
									modal.remove();
									deleteAllCookies();
									window.location.reload();
								});
							}
						});
					} else {
						$.ajax({
							url: ajaxGetUrl,
							method: 'GET',
							data: {
								"action": "active_vehicles_locations"
							},
							success: function (response) {
								let taxiArr = JSON.parse(response.data);

								if (taxiArr.length > 0) {
									createMap(fromGeocoded, toGeocoded);
									intervalTaxiMarker = setInterval(updateTaxiMarkers, 10000);
								} else {
									let text3 = gettext('Вибачте але на жаль вільних водіїв нема. Скористайтеся нашою послугою замовлення на інший час!')
									let noTaxiArr = document.createElement("div");
									noTaxiArr.innerHTML = `
                    <div class="modal-taxi">
                    <div class="modal-content-taxi">
                    <span class="close">&times;</span>
                    <h3>${text3}</h3>
                    </div>
                    </div>`;
									document.body.appendChild(noTaxiArr);
									deleteCookie("address")

									// We attach an event to close the window when the cross is clicked
									let closeButton = noTaxiArr.querySelector(".close");
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

function updateTaxiMarkers() {
	$.ajax({
		url: ajaxGetUrl,
		method: 'GET',
		data: {
			"action": "active_vehicles_locations"
		},
		success: function (response) {
			let taxiArr = JSON.parse(response.data);
			// Clear previous taxi markers
			clearTaxiMarkers();
			// Add new taxi markers
			addTaxiMarkers(taxiArr);
		},
		error: function (error) {
			console.log("Error retrieving taxi data:", error);
		}
	});
}

function clearTaxiMarkers() {
	// Remove all taxi markers from the map
	taxiMarkers.forEach(function (marker) {
		marker.setMap(null);
	});
	// Clear the taxiMarkers array
	taxiMarkers = [];
}

function addTaxiMarkers(taxiArr) {
	taxiArr.forEach(taxi => {
		// Create a marker for each taxi with a custom icon
		let marker = new google.maps.Marker({
			position: new google.maps.LatLng(taxi.lat, taxi.lon),
			map: map,
			title: taxi.vehicle__licence_plate,
			icon: getMarkerIcon('taxi1'),
			animation: google.maps.Animation.SCALE
		});
		// Add the marker to the taxiMarkers array
		taxiMarkers.push(marker);
	});
}


$(document).ready(function () {
	$('[id^="sub-form-"]').on('submit', function (event) {
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
			success: function (data) {
				$('#email-error-1, #email-error-2').html('');
				form.reset();
			},
			error: function (xhr, textStatus, errorThrown) {
				if (xhr.status === 400) {
					let errors = xhr.responseJSON;
					$.each(errors, function (key, value) {
						$('#' + key + '-error-1, #' + key + '-error-2').html(value);
					});
				} else {
					console.error('Помилка запиту: ' + textStatus);
				}
			}
		});
	});
});

function initAutocomplete(inputID) {
	const inputField = document.getElementById(inputID);
	const autoComplete = new google.maps.places.Autocomplete(inputField, {
		bounds: new google.maps.Circle({
			center: {lat: CENTRE_CITY_LAT, lng: CENTRE_CITY_LNG},
			radius: CENTRE_CITY_RADIUS,
		}).getBounds(),
		strictBounds: true,
	});
	autoComplete.addListener('place_changed', function () {
		const place = autoComplete.getPlace();
		if (place && place.formatted_address) {
			inputField.value = place.formatted_address;
		} else {
			inputField.value = '';
			inputField.placeholder = gettext("Будь ласка, введіть коректну адресу");
		}
	});
}

$(document).ready(function () {

	if ($('#address').length || $('#to_address').length) {
		loadGoogleMaps(3, apiGoogle, userLanguage, '', 'geometry,places').then(function () {
			initAutocomplete('address');
			initAutocomplete('to_address');
			checkCookies()
		});
	}

	$(this).on('click', '.services-grid__item .btn', function () {
		let t = $(this);
		content = t.prev();

		if (content.hasClass('limited-lines')) {
			content.removeClass('limited-lines');
			t.text(gettext('Читайте менше <'));
		} else {
			content.addClass('limited-lines');
			t.text(gettext('Читати далі >'));
		}

		$('html, body').animate({scrollTop: $('.services-grid').offset().top}, 100);

		return false;
	});

	$("a[href='#order-now']").click(function () {
		$('html, body').animate({
			scrollTop: $("#order-now").offset().top
		}, 1000); // Час прокрутки в мілісекундах (1000 мс = 1 с)
	});

	if (userLanguage === "uk") {
		$(".img-box-en").addClass("hidden");
		$(".img-box-uk").removeClass("hidden");
	} else {
		$(".img-box-en").removeClass("hidden");
		$(".img-box-uk").addClass("hidden");
	}

	const $blocks = $('[data-block]');

	$blocks.on('mouseenter', function () {
		const $currentBlock = $(this);
		const initialHeight = $currentBlock.height();

		$currentBlock.animate({marginTop: -20}, 300);
	});

	$blocks.on('mouseleave', function () {
		const $currentBlock = $(this);
		$currentBlock.animate({marginTop: 0}, 300);
	});

	// video-youtube
	let videos = $('a[data-youtube]');
	videos.each(function () {
		let video = $(this);
		let href = video.attr('href');
		let id = new URL(href).searchParams.get('v');

		video.attr('data-youtube', id);
		video.attr('role', 'button');

		video.html(`
      <img alt="" src="https://img.youtube.com/vi/${id}/maxresdefault.jpg" style="border-radius: 25px" width="552" height="310" loading="lazy"><br>
      ${video.text()}
    `);
	});

	function clickHandler(event) {
		let link = $(event.target).closest('a[data-youtube]');
		if (!link) return;

		event.preventDefault();

		let id = link.attr('data-youtube');
		let player = $(`
      <div>
        <iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/${id}?autoplay=1" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
      </div>
    `);
		link.replaceWith(player);
	}

	$(document).on('click', 'a[data-youtube]', clickHandler);
});

$(window).on('load', function () {
	$('.loader').remove();
});


// login-invest

$(document).ready(function () {

	$.ajax({
		url: ajaxGetUrl,
		type: "GET",
		data: {
			action: "is_logged_in"
		},
		success: function (data) {
			if (data.is_logged_in === true) {
				$("#loginBtn").hide();
				$("#loggedInUser").text('Кабінет Інвестора').show();
			} else {
				$("#loginBtn").show();
				$("#loggedInUser").hide();
			}
		}
	})

	$("#loggedInUser").click(function () {
		window.location.href = "/dashboard/";
	});

	$("#loginBtn").click(function () {
		$("#loginForm").fadeIn();
		$("#loginRadio").hide();
		$("label[for='loginRadio']").hide();
	});

	$(".close-btn").click(function () {
		$("#loginForm").fadeOut();
		$(".forgot-password-form").fadeOut();
		window.location.reload();
	});

	$("#login-invest").click(function () {
		let login = $("#login").val();
		let password = $("#password").val();
		let action = 'login_invest';

		$.ajax({
			url: ajaxPostUrl,
			type: 'POST',
			data: {
				action: action,
				login: login,
				password: password,
				csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
			},
			success: function (data) {
				if (data.data['success'] === true) {
					$("#loginBtn").hide();
					$("#loggedInUser").text('Кабінет Інвестора').show();
					$("#loginForm").fadeOut();
					window.location.href = "/dashboard/";
				} else {
					$("#login").val("Невірний логін або пароль").addClass("error-message");
					$("#password").val("");
				}
			}
		});
	});

	let urlParams = new URLSearchParams(window.location.search);
	let signedIn = urlParams.get('signed_in');

	if (signedIn === 'false') {
		let modal = document.createElement('div');
		modal.id = 'modal-signed-in-false';
		modal.className = 'modal-signed-in-false';

		let modalContent = document.createElement('div');
		modalContent.className = 'modal-content-false';

		let closeBtn = document.createElement('span');
		closeBtn.className = 'close';
		closeBtn.innerHTML = '&times;';
		closeBtn.onclick = function () {
			document.body.removeChild(modal);
			window.location.href = '/';
		};

		let modalText = document.createElement('p');
		modalText.innerHTML = 'Вхід не вдався:<br>' +
			'<ol><li>Будь ласка, перевірте, чи ви використовуєте електронну адресу, яку вказували під час реєстрації.</li>' +
			'<li>Також, переконайтеся, що ви є партнером компанії Ninja Taxi.</li>' +
			'<li>Якщо ви впевнені в правильності введених даних, але не можете увійти в систему, зверніться до нашого менеджера для отримання допомоги.</li>' +
			'</ol>';

		modalContent.appendChild(closeBtn);
		modalContent.appendChild(modalText);
		modal.appendChild(modalContent);

		document.body.appendChild(modal);
	}

	const forgotPasswordForm = $('#forgotPasswordForm');
	const loginRadioForm = $('#loginForm');
	const sendResetCodeBtn = $('#sendResetCode');

	$('#forgotPasswordRadio').click(function () {
		forgotPasswordForm.show();
		loginRadioForm.hide();
	});

	sendResetCodeBtn.click(function () {
		const email = $('#forgotEmail').val();

		$.ajax({
			url: ajaxPostUrl,
			type: 'POST',
			data: {
				action: 'send_reset_code',
				email: email,
				csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
			},
			success: function (response) {
				console.log(response);
				if (response['success'] === true) {
					let resetCode = response['code'][1];
					console.log(resetCode);
					sendResetCodeBtn.data('resetCode', resetCode);
					forgotPasswordForm.hide();
					$('#resetPasswordForm').show();
				} else {
					$('#forgotEmail').val('Невірна електронна адреса').addClass('error-message');
				}
			}
		});
	});

	$('#updatePassword').click(function () {
		const email = $('#forgotEmail').val();
		const activeCode = $('#activationCode').val();
		const newPassword = $('#newPassword').val();
		const confirmPassword = $('#confirmPassword').val();
		const resetCode = sendResetCodeBtn.data('resetCode');

		if (newPassword !== confirmPassword || activeCode !== resetCode) {
			if (newPassword !== confirmPassword) {
				$('#passwordError').text('Паролі не співпадають').addClass('error-message');
			} else {
				$('#passwordError').text('').removeClass('error-message');
			}

			if (activeCode !== resetCode) {
				$('#activationError').text('Невірний код активації').addClass('error-message');
			} else {
				$('#activationError').text('').removeClass('error-message');
			}
		} else {

			$.ajax({
				url: ajaxPostUrl,
				type: 'POST',
				data: {
					action: 'update_password',
					email: email,
					newPassword: newPassword,
					csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
				},
				success: function (response) {
					if (response['success'] === true) {
						$('#resetPasswordForm').hide();
						$('#loginForm').show();
					}
				}
			});
		}
	});
});
