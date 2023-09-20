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
	colors: ["#00ab57", "#d50000", "#ff6d00", "#583cb3", "#c51162", "#00bfa5"],
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
					text: gettext("пробіг км"),
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
					text: gettext("пробіг км"),
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
			action: 'get_cash_investor',
			period: period,
			start_date: startDate,
			end_date: endDate,
		},
		success: function (response) {
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

			$('.weekly-income-dates').text(gettext('З ') + startDate + gettext(' по ') + endDate);
			$('.weekly-income-amount').text(totalAmount + gettext(' грн'));
			$('.spending-all').text(spending + gettext(' грн'));
			$('.income-km').text(totalKm + gettext(' км'));
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
			startDate: startDate,
			endDate: endDate,
		},
		success: function (response) {
			let dataObject = response.data;

			let carData = {}; // Об'єкт для зберігання даних кожного автомобіля

			// Проходимося по кожному ідентифікатору автомобіля
			Object.keys(dataObject).forEach(function (carNumber) {
				carData[carNumber] = dataObject[carNumber].map(function (item) {
					return {
						date: new Date(item.date_effective),
						mileage: parseFloat(item.mileage)
					};
				});
			});

			let mileageSeries = Object.keys(carData).map(function (carNumber) {
				return {
					name: carNumber,
					data: carData[carNumber].map(function (entry) {
						return entry.mileage;
					})
				};
			});

			let dates = carData[Object.keys(carData)[0]].map(function (entry) {
				return `${entry.date.getDate()}-${entry.date.getMonth() + 1}-${entry.date.getFullYear()}`;
			});

			// Оновити опції графіка з новими даними
			areaChartOptions.series = mileageSeries;
			areaChartOptions.labels = dates;

			areaChart.updateOptions(areaChartOptions);
		}
	});
}


const commonPeriodSelect = $('#period-common');
const showCommonButton = $('#common-show-button');

showCommonButton.on('click', function (event) {
	event.preventDefault();

	const selectedPeriod = commonPeriodSelect.val();
	loadDefaultKasa(selectedPeriod);
	loadEffectiveChart(selectedPeriod);
});

loadDefaultKasa('yesterday');
loadEffectiveChart('current_week');

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
	let startDate = $("#datePicker #start_date").val();
	let endDate = $("#datePicker #end_date").val();

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
		$('.payback-car').show();
		$('.payback-car').css('display', 'flex');
		$('.charts').hide();
		$('.main-cards').hide();
		$('.common-period').hide();
		$('#datePicker').hide();
	});

	$(".close-btn").click(function () {
		$("#settingsWindow").fadeOut();
		sessionStorage.setItem('settings', 'false');
		location.reload();
	});
});
