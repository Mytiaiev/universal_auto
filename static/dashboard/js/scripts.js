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
		name: "Products",
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
		const selectedEffective = $(this).valconst
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

	// Обробка натискання на кнопку "Налаштування"

	$("#settingsBtn").click(function () {
		$("#settingsWindow").fadeIn();
	});


	$(".close-btn").click(function () {
		$("#settingsWindow").fadeOut();
	});

	$(function () {
		$(".showPassword").each(function (index, input) {
			let $input = $(input);
			$("<p class='opt'/>").append(
				$("<input type='checkbox' class='showPasswordCheckbox' id='showPassword' />").click(function () {
					let change = $(this).is(":checked") ? "text" : "password";
					let rep = $("<input placeholder='Password' type='" + change + "' />")
						.attr("id", $input.attr("id"))
						.attr("name", $input.attr("name"))
						.attr('class', $input.attr('class'))
						.val($input.val())
						.insertBefore($input);
					$input.remove();
					$input = rep;
				})
			).append($("<label for='showPassword'/>").text("Показати пароль")).insertAfter($input.parent());
		});
	});

	// Обробка натискання на кнопку "Увійти" в формі логіну Uber
	$("#uberForm button").click(function () {
		let uberLogin = $("#uberLogin").val();
		let uberPassword = $("#uberPassword").val();
		let action = 'Uber';
		sendLoginDataToServer(action, uberLogin, uberPassword);
	});

	// Обробка натискання на кнопку "Увійти" в формі логіну Uklon
	$("#uklonForm button").click(function () {
		let uklonLogin = $("#uklonLogin").val();
		let uklonPassword = $("#uklonPassword").val();
		let action = 'Uklon';
		sendLoginDataToServer(action, uklonLogin, uklonPassword);
	});

	// Обробка натискання на кнопку "Увійти" в формі логіну Bolt
	$("#boltForm button").click(function () {
		let boltLogin = $("#boltLogin").val();
		let boltPassword = $("#boltPassword").val();
		let action = 'Bolt';
		sendLoginDataToServer(action, boltLogin, boltPassword);
	});

	function sendLoginDataToServer(action, login, password) {
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
				console.log("Відповідь сервера:", response);
			}
		});
	}
});
