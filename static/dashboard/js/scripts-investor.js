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
		name: gettext("Дохід: "),
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
			text: gettext("Дохід (грн.)"),
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
		data: [],
		name: gettext("Пробіг (км): "),
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
		"#2e7d32",
	],
	plotOptions: {
		bar: {
			distributed: true,
			borderRadius: 4,
			horizontal: true,
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
			text: gettext("Пробіг (км.)"),
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

let areaChart = new ApexCharts(document.querySelector("#area-chart"), areaChartOptions);
areaChart.render();

// Обробка графіків
function loadDefaultKasa(period, startDate, endDate) {
	$.ajax({
		type: "GET",
		url: ajaxGetUrl,
		data: {
			action: 'get_cash_investor',
			period: period,
			start_date: startDate,
			end_date: endDate,
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
				let totalKm = parseFloat(response.data[2]).toFixed(2);
				let spending = response.data[3];
				let startDate = response.data[4];
				let endDate = response.data[5];
				let formattedData = {};

				Object.keys(data).forEach(function (key) {
					let value = parseFloat(data[key]).toFixed(2);
					if (value !== 0) {
						let formattedKey = key;
						formattedData[formattedKey] = value;
					}
				});

				let sortedKeys = Object.keys(formattedData).sort();
				let sortedFormattedData = {};
				sortedKeys.forEach(function (key) {
					sortedFormattedData[key] = formattedData[key];
				});

				barChartOptions.series[0].data = Object.values(sortedFormattedData);
				barChartOptions.xaxis.categories = Object.keys(sortedFormattedData);
				barChart.updateOptions(barChartOptions);

				if (period === 'yesterday') {
					$('.weekly-income-dates').text(startDate);
					$('.weekly-income-amount').text(totalAmount + gettext(' грн'));
					$('.spending-all').text(spending + gettext(' грн'));
					$('.income-km').text(totalKm + gettext(' км'));
				} else {
					$('.weekly-income-dates').text(gettext('З ') + startDate + ' ' + gettext('по') + ' ' + endDate);
					$('.weekly-income-amount').text(totalAmount + gettext(' грн'));
					$('.spending-all').text(spending + gettext(' грн'));
					$('.income-km').text(totalKm + gettext(' км'));
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
			action: 'investor',
			period: period,
			start_date: startDate,
			end_date: endDate,
		},
		success: function (response) {
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
					carData[carNumber] = dataObject[carNumber].reduce(function (totalMileage, item) {
						return totalMileage + parseFloat(item.mileage);
					}, 0).toFixed(2);
				});

				// Сортуємо об'єкт за значеннями
				let sortedKeys = Object.keys(carData).sort(function (a, b) {
					return carData[a] - carData[b];
				});

				let sortedFormattedData = {};
				sortedKeys.forEach(function (key) {
					sortedFormattedData[key] = carData[key];
				});

				console.log(sortedFormattedData);


				areaChartOptions.series[0].data = Object.values(sortedFormattedData);
				areaChartOptions.xaxis.categories = Object.keys(sortedFormattedData);
				areaChart.updateOptions(areaChartOptions);
			}
		}
	});
}


const commonPeriodSelect = $('#period-common');

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

loadDefaultKasa('yesterday');
loadEffectiveChart('yesterday');

function showDatePicker(periodSelectId, datePickerId) {
	let periodSelect = $("#" + periodSelectId);
	let datePicker = $("#" + datePickerId);

	if (periodSelect.val() === "custom") {
		datePicker.css("display", "block");
	} else {
		datePicker.css("display", "none");
	}
}

function applyCustomDate() {
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

	$('#investorVehicleBtnContainer').click(function () {
		$('.payback-car').css('display', 'flex');
		$('.charts').hide();
		$('.main-cards').hide();
		$('.common-period').hide();
		$('#datePicker').hide();
		$('#sidebar').removeClass('sidebar-responsive');
	});

	$(".close-btn").click(function () {
		$("#settingsWindow").fadeOut();
		sessionStorage.setItem('settings', 'false');
		location.reload();
	});
});
