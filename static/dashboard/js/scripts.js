// SIDEBAR TOGGLE

let sidebarOpen = false;
let sidebar = document.getElementById("sidebar");

function openSidebar() {
	if (!sidebarOpen) {
		sidebar.classList.add("sidebar-responsive");
		sidebarOpen = true;
	}
}

function closeSidebar() {
	if (sidebarOpen) {
		sidebar.classList.remove("sidebar-responsive");
		sidebarOpen = false;
	}
}


// ---------- CHARTS ----------

// BAR CHART
let barChartOptions = {
	series: [{
		data: [10, 8, 6, 4, 2],
		name: "Заробіток: ",
	}],
	chart: {
		type: "bar",
		background: "transparent",
		height: 350,
		toolbar: {
			show: false,
		},
	},
	colors: [
		"#2962ff",
		"#d50000",
		"#2e7d32",
		"#ff6d00",
		"#583cb3",
	],
	plotOptions: {
		bar: {
			distributed: true,
			borderRadius: 4,
			horizontal: false,
			columnWidth: "40%",
		}
	},
	dataLabels: {
		enabled: false,
	},
	fill: {
		opacity: 1,
	},
	grid: {
		borderColor: "#55596e",
		yaxis: {
			lines: {
				show: true,
			},
		},
		xaxis: {
			lines: {
				show: true,
			},
		},
	},
	legend: {
		labels: {
			colors: "#f5f7ff",
		},
		show: false,
		position: "top",
	},
	stroke: {
		colors: ["transparent"],
		show: true,
		width: 2
	},
	tooltip: {
		shared: true,
		intersect: false,
		theme: "dark",
	},
	xaxis: {
		categories: ["Laptop", "Phone", "Monitor", "Headphones", "Camera"],
		title: {
			style: {
				color: "#f5f7ff",
			},
		},
		axisBorder: {
			show: true,
			color: "#55596e",
		},
		axisTicks: {
			show: true,
			color: "#55596e",
		},
		labels: {
			style: {
				colors: "#f5f7ff",
			},
		},
	},
	yaxis: {
		title: {
			text: "Каса",
			style: {
				color: "#f5f7ff",
			},
		},
		axisBorder: {
			color: "#55596e",
			show: true,
		},
		axisTicks: {
			color: "#55596e",
			show: true,
		},
		labels: {
			style: {
				colors: "#f5f7ff",
			},
		},
	}
};

let barChart = new ApexCharts(document.querySelector("#bar-chart"), barChartOptions);
barChart.render();


// AREA CHART
let areaChartOptions = {
	series: [{
		name: "Василь",
		data: [31, 40, 28, 51, 42, 60, 76],
	}, {
		name: "Іван",
		data: [11, 32, 45, 32, 34, 52, 41],
	}],
	chart: {
		type: "area",
		background: "transparent",
		height: 350,
		stacked: false,
		toolbar: {
			show: false,
		},
	},
	colors: ["#00ab57", "#d50000"],
	labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
	dataLabels: {
		enabled: false,
	},
	fill: {
		gradient: {
			opacityFrom: 0.4,
			opacityTo: 0.1,
			shadeIntensity: 1,
			stops: [0, 100],
			type: "vertical",
		},
		type: "gradient",
	},
	grid: {
		borderColor: "#55596e",
		yaxis: {
			lines: {
				show: true,
			},
		},
		xaxis: {
			lines: {
				show: true,
			},
		},
	},
	legend: {
		labels: {
			colors: "#f5f7ff",
		},
		show: true,
		position: "top",
		horizontalAlign: 'left',
	},
	markers: {
		size: 6,
		strokeColors: "#1b2635",
		strokeWidth: 3,
	},
	stroke: {
		curve: "smooth",
	},
	xAxis: {
		axisBorder: {
			color: "#55596e",
			show: true,
		},
		axisTicks: {
			color: "#55596e",
			show: true,
		},
		labels: {
			offsetY: 5,
			style: {
				colors: "#f5f7ff",
			},
		},
	},
	yAxis:
		[
			{
				title: {
					text: "Дохід грн/км",
					style: {
						color: "#f5f7ff",
					},
				},
				labels: {
					style: {
						colors: ["#f5f7ff"],
					},
				},
			},
			{
				opposite: true,
				title: {
					text: "Дохід грн/км",
					style: {
						color: "#f5f7ff",
					},
				},
				labels: {
					style: {
						colors: ["#f5f7ff"],
					},
				},
			},
		],
	tooltip: {
		shared: true,
		intersect: false,
		theme: "dark",
	}
};

let areaChart = new ApexCharts(document.querySelector("#area-chart"), areaChartOptions);
areaChart.render();

$(document).ready(function () {

	// Обробка графіків
	function loadDefaultKasa(period) {
		$.ajax({
			type: "GET",
			url: ajaxGetUrl,
			data: {
				action: 'get_drivers_cash',
				period: period
			},
			success: function (response) {
				let data = response.data[0];
				let totalAmount = response.data[1];
				let startDate = response.data[2];
				let endDate = response.data[3];
				let formattedData = {};

				Object.keys(data).forEach(function (key) {
					let value = parseFloat(data[key]);
					if (value !== 0) {
						formattedData[key] = value;
					}
				});

				barChartOptions.series[0].data = Object.values(formattedData);
				barChartOptions.xaxis.categories = Object.keys(formattedData);
				barChart.updateOptions(barChartOptions);

				$('#weekly-income-dates').text(startDate + ' по ' + endDate);
				$('#weekly-income-amount').text(totalAmount + ' грн');
			}
		});
	}

	function loadEffectiveChart(period, vehicleId) {
		$.ajax({
			type: "GET",
			url: ajaxGetUrl,
			data: {
				action: 'effective_vehicle',
				period: period,
				vehicle_id: vehicleId
			},
			success: function (response) {
				let dataArray = response.data.data;
				let uniqueNames = Array.from(new Set(dataArray.map(item => item.name)));
				let driverData = {};

				uniqueNames.forEach(function (name, index) {
					let driverIndex = index + 1;
					let driverNameKey = 'name' + driverIndex;
					let effectiveKey = 'effective' + driverIndex;

					driverData[driverNameKey] = name;
					driverData[effectiveKey] = dataArray
						.filter(item => item.name === name)
						.map(item => item.effective)
						.join(', ');

					if (driverData[effectiveKey] === '') {
						driverData[effectiveKey] = 0;
					}
				});

				if (uniqueNames.length === 1) {
					let driverIndex = 2;
					let driverNameKey = 'name' + driverIndex;
					let effectiveKey = 'effective' + driverIndex;

					driverData[driverNameKey] = "Водій відсутній";
					driverData[effectiveKey] = "0";
				}

				driverData.date_effective = dataArray
					.map(function (item) {
						let date = new Date(item.date_effective);
						return `${date.getDate()}-${date.getMonth() + 1}-${date.getFullYear()}`;
					})
					.join(', ');

				let dataPairs = [];
				let dates = driverData.date_effective.split(', ');
				let effective1 = driverData.effective1.split(', ');
				let effective2 = driverData.effective2.split(', ');

				for (let i = 0; i < dates.length; i++) {
					let pair = {
						date: dates[i],
						effective1: parseFloat(effective1[i]),
						effective2: parseFloat(effective2[i])
					};
					dataPairs.push(pair);
				}

				// Сортування масиву за датами
				dataPairs.sort(function (a, b) {
					let dateA = new Date(a.date);
					let dateB = new Date(b.date);
					return dateA - dateB;
				});

				// Оновлення графіка з новими даними
				areaChartOptions.series[0].name = driverData.name1;
				areaChartOptions.series[0].data = dataPairs.map(pair => pair.effective1);
				areaChartOptions.series[1].name = driverData.name2;
				areaChartOptions.series[1].data = dataPairs.map(pair => pair.effective2);
				areaChartOptions.labels = dataPairs.map(pair => pair.date);

				areaChart.updateOptions(areaChartOptions);
			}
		});
	}

	function updateEffectiveChart(vehicleId, period) {
		loadEffectiveChart(period, vehicleId);
	}

	loadDefaultKasa('day');
	loadEffectiveChart('week', $('#vehicle-select').val());

	$('input[name="effective-amount"]').change(function () {
		const selectedKasa = $(this).val();
		const period = getPeriod(selectedKasa);

		loadDefaultKasa(period);
	});

	$('input[name="effective-period"]').change(function () {
		const selectedEffective = $(this).val();
		const vehicleId = $('#vehicle-select').val();
		const period = getPeriod(selectedEffective);

		updateEffectiveChart(vehicleId, period);
	});

	$('#vehicle-select').change(function () {
		const vehicleId = $(this).val();
		const selectedEffective = $('input[name="effective-period"]:checked').val();
		const period = getPeriod(selectedEffective);

		updateEffectiveChart(vehicleId, period);
	});

	function getPeriod(val) {
		return {
			d: 'day',
			w: 'week',
			m: 'month',
			q: 'quarter'
		}[val];
	}
});

$(document).ready(function () {
	const forms = ['uberForm', 'boltForm', 'uklonForm'];

	function showLoggedInUser(formName) {
		$("#" + formName + " input").hide();
		$("#" + formName + " .login-btn").remove();
		$(".opt-" + formName).remove();
		$("#" + formName).append("<span class='successful-message'>Вхід Успішний!</span>");
		$("#" + formName).append("<button class='logout-btn' data-form='" + formName + "'>Вийти</button>");
	}

	if (sessionStorage.getItem('settings') === 'true') {
		$("#settingsWindow").fadeIn();

		forms.forEach((formName) => {
			if (localStorage.getItem(formName.substring(0, formName.length - 4)) === 'true') {
				showLoggedInUser(formName);
			}
		});
	}

	$("#settingBtn").click(function () {
		sessionStorage.setItem('settings', 'true');
		$("#settingsWindow").fadeIn();

		forms.forEach((formName) => {
			if (localStorage.getItem(formName.substring(0, formName.length - 4)) === 'true') {
				showLoggedInUser(formName);
			}
		});
	});


	$(document).on("click", ".logout-btn", function () {
		let formName = $(this).data('form');
		localStorage.removeItem(formName.substring(0, formName.length - 4));
		location.reload();
	});

	$(".close-btn").click(function () {
		$("#settingsWindow").fadeOut();
		sessionStorage.setItem('settings', 'false');
		location.reload();
	});

	$(function () {
		$("#showPasswordBolt").click(function () {
			let $checkbox = $(this);
			let $passwordField = $checkbox.closest('.settings-content').find('.boltPassword');
			let change = $checkbox.is(":checked") ? "text" : "password";
			$passwordField.prop('type', change);
		});
	});

	$(function () {
		$("#showPasswordUklon").click(function () {
			let $checkbox = $(this);
			let $passwordField = $checkbox.closest('.settings-content').find('.uklonPassword');
			let change = $checkbox.is(":checked") ? "text" : "password";
			$passwordField.prop('type', change);
		});
	});

	$(function () {
		$("#showPasswordUber").click(function () {
			let $checkbox = $(this);
			let $passwordField = $checkbox.closest('.settings-content').find('.uberPassword');
			let change = $checkbox.is(":checked") ? "text" : "password";
			$passwordField.prop('type', change);
		});
	});

	function handlerLoginClick(formName, action) {
		let form = $("#" + formName + "Form");
		let loginField = $("#" + formName + "Login")
		let passwordField = $("#" + formName + "Password")
		let login = loginField.val();
		let password = passwordField.val();

		if (form[0].checkValidity()) {
			showLoader(form);
			sendLoginDataToServer(action, login, password, formName);
		} else {
			if (login === "") {
				loginField.attr("placeholder", "Обов'язково до заповнення");
			}
			if (password === "") {
				passwordField.attr("placeholder", "Обов'язково до заповнення");
			}

			loginField.addClass("error-message");
			passwordField.addClass("error-message");
		}
	}

	$("#uberForm .login-btn").click(function () {
		handlerLoginClick('uber', 'Uber_login');
	});

	$("#boltForm .login-btn").click(function () {
		handlerLoginClick('bolt', 'Bolt_login');
	});

	$("#uklonForm .login-btn").click(function () {
		handlerLoginClick('uklon', 'Uklon_login');
	});

	function showLoader(form) {
		form.find(".login-btn").hide();
		form.find(".loader-login").show();
	}

	function hideLoader(form) {
		form.find(".loader-login").hide();
	}


	function sendLoginDataToServer(action, login, password, form) {

		$.ajax({
			type: "POST",
			url: ajaxPostUrl,
			data: {
				csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
				action: action,
				login: login,
				password: password,
			},
			success: function (response) {
				if (response.data === true) {
					localStorage.setItem(form, 'true');
					if (action === 'Bolt_login') {
						$("#boltForm input").hide();
						$("#boltForm .login-btn").remove();
						$(".opt-boltForm").hide();
						$("#boltForm").append("<span class='successful-message'>Вхід Успішний!</span>");
						$("#boltForm").append("<button class='logout-btn' data-form='Uklon_logout'>Вийти</button>");
					}
					if (action === "Uber_login") {
						$("#uberForm input").hide();
						$("#uberForm .login-btn").remove();
						$(".opt-uberForm").hide();
						$("#uberForm").append("<span class='successful-message'>Вхід Успішний!</span>");
						$("#uberForm").append("<button class='logout-btn' data-form='Uklon_logout'>Вийти</button>");
					}
					if (action === "Uklon_login") {
						$("#uklonForm input").hide();
						$("#uklonForm .login-btn").remove();
						$(".opt-uklonForm").hide();
						$("#uklonForm").append("<span class='successful-message'>Вхід Успішний!</span>");
						$("#uklonForm").append("<button class='logout-btn' data-form='Uklon_logout'>Вийти</button>");
					}
				} else {
					if (action === "Bolt_login") {
						$("#boltLogin").val("Вказано неправильний логін або пароль").addClass("error-message");
						$("#boltPassword").val("Вказано неправильний логін або пароль").addClass("error-message");
						$("#boltForm .login-btn").show();
					} else if (action === "Uber_login") {
						$("#uberLogin").val("Вказано неправильний логін або пароль").addClass("error-message");
						$("#uberPassword").val("Вказано неправильний логін або пароль").addClass("error-message");
						$("#uberForm .login-btn").show();
					} else if (action === "Uklon_login") {
						$("#uklonLogin").val("Вказано неправильний логін або пароль").addClass("error-message");
						$("#uklonPassword").val("Вказано неправильний логін або пароль").addClass("error-message");
						$("#uklonForm .login-btn").show();
					}
				}
				hideLoader($("#" + form + "Form"));
			}
		});
	}
});

$(document).ready(function () {

	$.ajax({
		url: ajaxGetUrl,
		type: "GET",
		data: {
			action: "is_logged_in"
		},
		success: function (data) {
			if (data.is_logged_in === true) {
				let userName = data.user_name;
				$("#account_circle").text(userName).show();
				$("#logout-dashboard").show();
			}
		}
	})

	$("#logout-dashboard").click(function () {
		$.ajax({
			type: "POST",
			url: ajaxPostUrl,
			data: {
				csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
				action: "logout_invest",
			},
			success: function (response) {
				if (response.logged_out === true) {
					window.location.href = "/";
				}
			}
		});
	});

	// change-password

	$("#changePassword").click(function () {
		$("#passwordChangeForm").toggle();
	});


	$("#submitPassword").click(function () {
		let password = $("#oldPassword").val();
		let newPassword = $("#newPassword").val();
		let confirmPassword = $("#confirmPassword").val();

		console.log(password, newPassword, confirmPassword);

		if (newPassword !== confirmPassword) {
			$("#newPassword").val("Пароль не співпадає").addClass("error-message");
			$("#confirmPassword").val("Пароль не співпадає").addClass("error-message");
		} else {
			$.ajax({
				url: ajaxPostUrl,
				type: 'POST',
				data: {
					action: 'change_password',
					password: password,
					newPassword: newPassword,
					csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
				},
				success: function (response) {
					console.log(response);
					// if (data.data['success'] === true) {
					// 	$("#loginBtn").hide();
					// 	$("#loggedInUser").text('Кабінет Інвестора').show();
					// 	$("#loginForm").fadeOut();
					// } else {
					// 	$("#login").val("Невірний логін або пароль").addClass("error-message");
					// 	$("#password").val("Невірний логін або пароль").addClass("error-message");
					// }
				}
			});
		}
	});
	// burger-menu

	$('.burger-icon').click(function () {
		$('.burger-menu').toggleClass('open');
	});
});
