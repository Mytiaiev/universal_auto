// SIDEBAR TOGGLE

let sidebarOpen = false;
let sidebar = document.getElementById("sidebar");

// Визначте змінну для стану бічного бару

function toggleSidebar() {
	const sidebar = document.getElementById("sidebar");

	if (sidebarOpen) {
		// Закрити бічний бар
		sidebar.classList.remove("sidebar-responsive");
		sidebarOpen = false;
	} else {
		// Відкрити бічний бар
		sidebar.classList.add("sidebar-responsive");
		sidebarOpen = true;
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
			$(".apply-filter-button").prop("disabled", false);
			let isAllValuesZero = true;
			for (let key in response.data[0]) {
				if (parseFloat(response.data[0][key]) !== 0) {
					isAllValuesZero = false;
					break;
				}
			}
			if (isAllValuesZero) {
				$("#noDataMessage-1").show();
				$('#bar-chart').hide();
			} else {
				$("#noDataMessage-1").hide();
				$('#bar-chart').show();
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

				if (period === 'yesterday') {
					$('.weekly-income-dates').text(startDate);
					$('.weekly-income-rent').text(totalRent + ' ' + gettext('км'));
					$('.weekly-income-amount').text(totalAmount + ' ' + gettext('грн'));
					$('.income-efficiency').text(efficiency + ' ' + gettext('грн/км'));
				} else {
					$('.weekly-income-dates').text(gettext('З ') + startDate + ' ' + gettext('по') + ' ' + endDate);
					$('.weekly-income-rent').text(totalRent + ' ' + gettext('км'));
					$('.weekly-income-amount').text(totalAmount + ' ' + gettext('грн'));
					$('.income-efficiency').text(efficiency + ' ' + gettext('грн/км'));
				}
			}
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
			$(".apply-filter-button").prop("disabled", false);
			let dataObject = response.data;
			if (Object.keys(response.data).length === 0) {
				$("#noDataMessage-2").show();
				$('#area-chart').hide();
			} else {
				$("#noDataMessage-2").hide();
				$('#area-chart').show();
				let carData = {};

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
			$(".apply-filter-button").prop("disabled", false);
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

				if (period === 'yesterday') {
					$('.income-drivers-date').text(startDate);
				} else {
					$('.income-drivers-date').text('З ' + startDate + ' ' + gettext('по') + ' ' + endDate);
				}
			});
			$('.driver-container').empty();

			response.data[0].forEach(function (driver) {
				let driverBlock = $('<div class="driver-block"></div>');
				let driverName = $('<div class="driver-name"></div>');
				let driverInfo = $('<div class="driver-info"></div>');

				driverName.append('<h3>' + driver.driver + '</h3>');
				driverName.append('<div class="arrow" onclick="toggleDriverInfo(this)">▼</div>');

				driverInfo.append('<p>Каса: ' + driver.total_kasa + ' грн' + '</p>');
				driverInfo.append('<p>Кількість замовлень: ' + driver.total_orders + '</p>');
				driverInfo.append('<p>Відсоток прийнятих замовлень: ' + driver.accept_percent + ' %</p>');
				driverInfo.append('<p>Середній чек, грн: ' + driver.average_price + '</p>');
				driverInfo.append('<p>Пробіг, км: ' + driver.mileage + '</p>');
				driverInfo.append('<p>Ефективність, грн/км: ' + driver.efficiency + '</p>');
				driverInfo.append('<p>Час в дорозі: ' + formatTime(driver.road_time) + '</p>');

				driverBlock.append(driverName);
				driverBlock.append(driverInfo);

				// Додати блок водія до контейнера
				$('.driver-container').append(driverBlock);
			});
		}
	});
}

const commonPeriodSelect = $('#period-common');
const periodSelect = $('#period');

commonPeriodSelect.on('change', function () {
	const selectedPeriod = commonPeriodSelect.val();
	if (selectedPeriod !== "custom") {
		loadDefaultKasa(selectedPeriod);
		loadEffectiveChart(selectedPeriod);
	}
	if (selectedPeriod === "custom") {
		$("#datePicker").css("display", "block");
	} else {
		$("#datePicker").css("display", "none");
	}
});

periodSelect.on('change', function () {
	const selectedPeriod = periodSelect.val();
	if (selectedPeriod !== "custom") {
		loadDefaultDriver(selectedPeriod);
	}
	if (selectedPeriod === "custom") {
		$("#datePickerDriver").css("display", "block");
	} else {
		$("#datePickerDriver").css("display", "none");
	}
});

loadDefaultKasa('yesterday');
loadEffectiveChart('yesterday');
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
	$(".apply-filter-button").prop("disabled", true);

	let startDate = $("#start_date").val();
	let endDate = $("#end_date").val();

	const selectedPeriod = periodSelect.val();
	loadDefaultDriver(selectedPeriod, startDate, endDate);
}

function applyCustomDateRange() {
$(".apply-filter-button").prop("disabled", true);

	let startDate = $("#start_date").val();
	let endDate = $("#end_date").val();

	const selectedPeriod = commonPeriodSelect.val();
	loadDefaultKasa(selectedPeriod, startDate, endDate);
	loadEffectiveChart(selectedPeriod, startDate, endDate);
}


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
		$('.payback-car').css('display', 'flex');
		$('.charts').hide();
		$('.main-cards').hide();
		$('.info-driver').hide();
		$('.common-period').hide();
		$('.driver-container').hide()
		$('#datePicker').hide()
		$('#sidebar').removeClass('sidebar-responsive');
	});

	$('#managerDriverBtnContainer').click(function () {
		$('.info-driver').show();
		$('.payback-car').hide();
		$('.charts').hide();
		$('.main-cards').hide();
		$('.common-period').hide();
		$('#datePicker').hide()
		$('#sidebar').removeClass('sidebar-responsive');
		if (window.innerWidth <= 900) {
			$('.driver-container').css('display', 'block');
		}
	});

	$(".close-btn").click(function () {
		$("#settingsWindow").fadeOut();
		sessionStorage.setItem('settings', 'false');
		location.reload();
	});

	const resetButton = $("#reset-button");

	resetButton.on("click", function () {
		areaChart.resetSeries();
	});
});

function toggleDriverInfo(arrow) {
	const driverBlock = $(arrow).closest('.driver-block');
	driverBlock.toggleClass('active');
}

function formatTime(time) {
	let parts = time.match(/(\d+) days?, (\d+):(\d+):(\d+)/);

	if (!parts) {
		return time;
	} else {
		let days = parseInt(parts[1]);
		let hours = parseInt(parts[2]);
		let minutes = parseInt(parts[3]);
		let seconds = parseInt(parts[4]);

		hours += days * 24;

		// Форматувати рядок у вигляді HH:mm:ss
		return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
	}
}
