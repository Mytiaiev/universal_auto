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
		data: [],
		name: gettext("Заробіток: "),
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
		"#c51162",
		"#00bfa5",
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
		categories: [],
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
			rotate: -45,
		},
	},
	yaxis: {
		title: {
			text: gettext("Каса"),
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
		name: "",
		data: [''],
	}, {
		name: "",
		data: [''],
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
	colors: ["#00ab57", "#d50000", "#2e7d32", "#ff6d00", "#583cb3", "#c51162", "#00bfa5",],
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
					text: gettext("Дохід грн/км"),
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
					text: gettext("Дохід грн/км"),
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


// Обробка графіків
function loadDefaultKasa(period, startDate, endDate) {
	$.ajax({
		type: "GET",
		url: ajaxGetUrl,
		data: {
			action: 'get_cash_manager',
			period: period,
			start_date: startDate,
			end_date: endDate
		},
		success: function (response) {
			let data = response.data[0];
			let totalAmount = parseFloat(response.data[1]).toFixed(2);
			let totalRent = parseFloat(response.data[2]).toFixed(2);
			let startDate = response.data[3];
			let endDate = response.data[4];
			let efficiency = parseFloat(response.data[5]).toFixed(2);
			let formattedData = {};

			Object.keys(data).forEach(function (key) {
				let value = parseFloat(data[key]).toFixed(2);
				if (value > 0) {
					formattedData[key] = value;
				}
			});

			let sortedKeys = Object.keys(formattedData).sort();
			let sortedFormattedData = {};
			sortedKeys.forEach(function (key) {
				sortedFormattedData[key] = formattedData[key];
			});

			barChartOptions.series[0].data = Object.values(formattedData);
			barChartOptions.xaxis.categories = Object.keys(formattedData);
			barChart.updateOptions(barChartOptions);

			$('.weekly-income-dates').text(gettext('З ') + startDate + gettext(' по ') + endDate);
			$('.weekly-income-amount').text(totalAmount + gettext(' грн'));
			$('.weekly-income-rent').text(totalRent + gettext(' км'));
			$('.income-efficiency').text(efficiency + ' ' + gettext('грн/км'));
		}
	});
}

function loadEffectiveChart(period, startDate, endDate) {
	$.ajax({
		type: "GET",
		url: ajaxGetUrl,
		data: {
			action: 'manager',
			period: period,
			start_date: startDate,
			end_date: endDate
		},
		success: function (response) {
			let dataObject = response.data;

			let carData = {}; // Об'єкт для зберігання даних кожного автомобіля

			// Проходимося по кожному ідентифікатору автомобіля
			Object.keys(dataObject).forEach(function (carNumber) {
				carData[carNumber] = dataObject[carNumber].map(function (item) {
					return {
						date: new Date(item.date_effective),
						efficiency: parseFloat(item.efficiency)
					};
				});
			});

			let efficiencySeries = Object.keys(carData).map(function (carNumber) {
				return {
					name: carNumber,
					data: carData[carNumber].map(function (entry) {
						return entry.efficiency;
					})
				};
			});

			let dates = carData[Object.keys(carData)[0]].map(function (entry) {
				return `${entry.date.getDate()}-${entry.date.getMonth() + 1}-${entry.date.getFullYear()}`;
			});

			// Оновити опції графіка з новими даними
			areaChartOptions.series = efficiencySeries;
			areaChartOptions.labels = dates;

			areaChart.updateOptions(areaChartOptions);
		}
	});
}

function loadDefaultDriver(period, startDate, endDate) {
	$.ajax({
		type: "GET",
		url: ajaxGetUrl,
		data: {
			action: 'get_drivers_manager',
			period: period,
			start_date: startDate,
			end_date: endDate,

		},
		success: function (response) {
			let table = $('.info-driver table');
			let startDate = response.data[1];
			let endDate = response.data[2];
			table.find('tr:gt(0)').remove();

			response.data[0].forEach(function (item) {
				let row = $('<tr></tr>');
				let time = item.road_time
				let parts = time.match(/(\d+) days?, (\d+):(\d+):(\d+)/);

				if (!parts) {
					time = time
				} else {
					let days = parseInt(parts[1]);
					let hours = parseInt(parts[2]);
					let minutes = parseInt(parts[3]);
					let seconds = parseInt(parts[4]);

					hours += days * 24;

					// Форматувати рядок у вигляді HH:mm:ss
					let formattedTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

					time = formattedTime
				}

				row.append('<td>' + item.driver + '</td>');
				row.append('<td>' + item.total_kasa + '</td>');
				row.append('<td>' + item.total_orders + '</td>');
				row.append('<td>' + item.accept_percent + " %" + '</td>');
				row.append('<td>' + item.average_price + '</td>');
				row.append('<td>' + item.mileage + '</td>');
				row.append('<td>' + item.efficiency + '</td>');
				row.append('<td>' + time + '</td>');

				table.append(row);

				$('.income-drivers-date').text(gettext('З ') + startDate + ' ' + gettext('по') + ' ' + endDate);
			});
		}
	});
}

const commonPeriodSelect = $('#period-common');
const showCommonButton = $('#common-show-button');
const periodSelect = $('#period');
const showButton = $('#show-button');
showCommonButton.on('click', function (event) {
	event.preventDefault();

	const selectedPeriod = commonPeriodSelect.val();
	loadDefaultKasa(selectedPeriod);
	loadEffectiveChart(selectedPeriod);
});

showButton.on('click', function (event) {
	event.preventDefault();

	const selectedPeriod = periodSelect.val();
	loadDefaultDriver(selectedPeriod);
});

loadDefaultKasa('yesterday');
loadEffectiveChart('current_week');
loadDefaultDriver('yesterday');

function showDatePicker(periodSelectId, datePickerId) {
	let periodSelect = $("#" + periodSelectId);
	let datePicker = $("#" + datePickerId);

	if (periodSelect.val() === "custom") {
		datePicker.css("display", "block");
	} else {
		datePicker.css("display", "none");
	}
}

function customDateRange() {
	let startDate = $("#datePickerDriver #start_date").val();
	let endDate = $("#datePickerDriver #end_date").val();

	const selectedPeriod = periodSelect.val();
	loadDefaultDriver(selectedPeriod, startDate, endDate);
}

function applyCustomDateRange() {
	let startDate = $("#start_date").val();
	let endDate = $("#end_date").val();

	const selectedPeriod = commonPeriodSelect.val();
	loadDefaultKasa(selectedPeriod, startDate, endDate);
	loadEffectiveChart(selectedPeriod, startDate, endDate);
}

$(document).ready(function () {

	const partnerForm = $("#partnerForm");
	const partnerLoginField = $("#partnerLogin");
	const partnerRadioButtons = $("input[name='partner']");

	partnerRadioButtons.change(function () {
		const selectedPartner = $("input[name='partner']:checked").val();
		updateLoginField(selectedPartner);
	});

	function updateLoginField(partner) {
		if (partner === 'uklon') {
			partnerLoginField.val('+380');
		} else {
			partnerLoginField.val('');
			$("#partnerPassword").val("");
		}
	}

	if (sessionStorage.getItem('settings') === 'true') {
		$("#settingsWindow").fadeIn();
	}

	if (localStorage.getItem('uber')) {
		$("#partnerLogin").hide()
		$("#partnerPassword").hide()
		$(".opt-partnerForm").hide()
		$(".login-ok").show()
		$("#loginErrorMessage").hide()
	}

	$("#settingBtn").click(function () {
		sessionStorage.setItem('settings', 'true');
		$("#settingsWindow").fadeIn();
	});

	$(".close-btn").click(function () {
		$("#settingsWindow").fadeOut();
		sessionStorage.setItem('settings', 'false');
		location.reload();
	});

	$(".login-btn").click(function () {
		const selectedPartner = partnerForm.find("input[name='partner']:checked").val();
		const partnerLogin = partnerForm.find("#partnerLogin").val();
		const partnerPassword = partnerForm.find("#partnerPassword").val();

		if (partnerForm[0].checkValidity() && selectedPartner) {
			showLoader(partnerForm);
			sendLoginDataToServer(selectedPartner, partnerLogin, partnerPassword);
		}
	});

	$(".logout-btn").click(function () {
		const selectedPartner = partnerForm.find("input[name='partner']:checked").val();
		sendLogautDataToServer(selectedPartner);
		localStorage.removeItem(selectedPartner);
		$("#partnerLogin").show()
		$("#partnerPassword").show()
		$(".opt-partnerForm").show()
		$(".login-ok").hide()
		$("#loginErrorMessage").hide()
	});

	// Show/hide password functionality
	$("#showPasswordPartner").click(function () {
		let $checkbox = $(this);
		let $passwordField = $checkbox.closest('.settings-content').find('.partnerPassword');
		let change = $checkbox.is(":checked") ? "text" : "password";
		$passwordField.prop('type', change);
	});

	function showLoader(form) {
		$(".opt-partnerForm").hide();
		form.find(".loader-login").show();
		$("input[name='partner']").prop("disabled", true);
	}

	function hideLoader(form) {
		form.find(".loader-login").hide();
		$("input[name='partner']").prop("disabled", false);
	}


	$('[name="partner"]').change(function () {
		let partner = $(this).val()
		let login = localStorage.getItem(partner)

		if (login === "success") {
			$("#partnerLogin").hide()
			$("#partnerPassword").hide()
			$(".opt-partnerForm").hide()
			$(".login-ok").show()
			$("#loginErrorMessage").hide()
		} else {
			$("#partnerLogin").show()
			$("#partnerPassword").show()
			$(".opt-partnerForm").show()
			$(".login-ok").hide()
			$("#loginErrorMessage").hide()
		}
	})

	function sendLoginDataToServer(partner, login, password) {
		$.ajax({
			type: "POST",
			url: ajaxPostUrl,
			data: {
				csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
				action: partner,
				login: login,
				password: password,
			},
			success: function (response) {
				if (response.data === true) {
					localStorage.setItem(partner, 'success');
					$("#partnerLogin").hide()
					$("#partnerPassword").hide()
					$(".opt-partnerForm").hide()
					$(".login-ok").show()
					$("#loginErrorMessage").hide()
				} else {
					$(".opt-partnerForm").show();
					$("#loginErrorMessage").show()
					$("#partnerLogin").val("").addClass("error-border");
					$("#partnerPassword").val("").addClass("error-border");
				}
				hideLoader(partnerForm);
			}
		});
	}

	function sendLogautDataToServer(partner) {
		console.log(partner + "_logout")
		$("#partnerLogin").val("")
		$("#partnerPassword").val("")
		$.ajax({
			type: "POST",
			url: ajaxPostUrl,
			data: {
				csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
				action: partner + "_logout",
			},
			success: function (response) {
				if (response.data === true) {
					localStorage.setItem(partner, 'false');
					$("#partnerLogin").show()
					$("#partnerPassword").show()
					$(".opt-partnerForm").show()
					$(".login-ok").hide()
				}
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

		if (newPassword !== confirmPassword) {
			$("#ChangeErrorMessage").show();
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
					if (response.data['success'] === true) {
						$("#passwordChangeForm").hide();
						window.location.href = "/";
					} else {
						$("#oldPasswordMessage").show();
					}
				}
			});
		}
	});
	// burger-menu

	$('.burger-menu').click(function () {
		$('.burger-menu').toggleClass('open');
	});

	$('#managerVehicleBtnContainer').click(function () {
		$('.payback-car').show();
		$('.payback-car').css('display', 'flex');
		$('.charts').hide();
		$('.main-cards').hide();
		$('.info-driver').hide();
		$('.common-period').hide();
		$('#datePicker').hide()
	});

	$('#managerDriverBtnContainer').click(function () {
		$('.info-driver').show();
		$('.payback-car').hide();
		$('.charts').hide();
		$('.main-cards').hide();
		$('.common-period').hide();
		$('#datePicker').hide()
	});

	$(".sidebar-list-item.admin").on("click", function () {

		let adminPanelURL = $(this).data("url");

		if (adminPanelURL) {
			window.open(adminPanelURL, "_blank");
		}
	});

	$(".close-btn").click(function () {
		$("#settingsWindow").fadeOut();
		sessionStorage.setItem('settings', 'false');
		location.reload();
	});
});
