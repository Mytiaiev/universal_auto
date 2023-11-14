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
		name: gettext("Заробіток "),
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
		"#89A632",
		"#FDCA10",
		"#18A64D",
		"#1858A6",
		"#79C8C5",
		"#EC6323",
		"#018B72"
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
	colors: [
		"#DCE43F",
		"#89A632",
		"#018B72",
		"#79C8C5",
		"#EC6323",
		"#1858A6",
		"#FDCA10"
	],
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
				show: false,
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
		size: 3,
		strokeColors: "#1b2635",
		strokeWidth: 1,
	},
	stroke: {
		curve: "smooth",
	},
	tooltip: {
		shared: true,
		intersect: false,
		theme: "dark",
	}
};

let areaChart = new ApexCharts(document.querySelector("#area-chart"), areaChartOptions);
areaChart.render();

function fetchSummaryReportData(period, start, end) {
	let apiUrl;
	if (period === 'custom') {
		apiUrl = `/api/reports/${start}&${end}/`;
	} else {
		apiUrl = `/api/reports/${period}/`;
	}
	;
	$.ajax({
		url: apiUrl,
		type: 'GET',
		dataType: 'json',
		success: function (data) {
			$(".apply-filter-button").prop("disabled", false);
			let startDate = data[0]['start'];
			let endDate = data[0]['end'];
			let totalDistance = data[0]['total_rent'];
			if (data[0]['drivers'].length !== 0) {
				$(".noDataMessage1").hide();
				$('#bar-chart').show();
				const driversData = data[0]['drivers'];
				const categories = driversData.map(driver => driver.full_name);
				const values = driversData.map(driver => driver.total_kasa);
				barChartOptions.series[0].data = values;
				barChartOptions.xaxis.categories = categories;
				barChart.updateOptions(barChartOptions);
			} else {
				$(".noDataMessage1").show();
				$('#bar-chart').hide();
			}
			;
			if (period === 'yesterday') {
				$('.weekly-income-dates').text(startDate);
			} else {
				$('.weekly-income-dates').text(gettext('З ') + startDate + ' ' + gettext('по') + ' ' + endDate);
			}
			;
			$('.weekly-income-rent').text(totalDistance + ' ' + gettext('км'));
		},
		error: function (error) {
			console.error(error);
		}
	});
}

function fetchCarEfficiencyData(period, start, end) {
	let apiUrl;
	if (period === 'custom') {
		apiUrl = `/api/car_efficiencies/${start}&${end}/`;
	} else {
		apiUrl = `/api/car_efficiencies/${period}/`;
	}
	;
	$.ajax({
		url: apiUrl,
		type: 'GET',
		dataType: 'json',
		success: function (data) {
			if (data['dates'].length !== 0) {
				$(".noDataMessage2").hide();
				$('#area-chart').show();
				let seriesData = data["vehicles"].map(item =>({
                    name: item.name,
                    data: item.efficiency
                }));
				areaChartOptions.series = seriesData;
				areaChartOptions.labels = data['dates'];
				areaChart.updateOptions(areaChartOptions);
			} else {
				$(".noDataMessage2").show();
				$('#area-chart').hide();
			}
			;
			$('.weekly-income-amount').text(data["kasa"] + ' ' + gettext('грн'));
			$('.income-efficiency').text(data["average_efficiency"].toFixed(2) + ' ' + gettext('грн/км'));
		},
		error: function (error) {
			console.error(error);
		}
	});
}


function fetchDriverEfficiencyData(period, start, end) {
	let apiUrl;
	if (period === 'custom') {
		apiUrl = `/api/drivers_info/${start}&${end}/`;
	} else {
		apiUrl = `/api/drivers_info/${period}/`;
	}
	;
	$.ajax({
		url: apiUrl,
		type: 'GET',
		dataType: 'json',
		success: function (data) {
			$(".apply-filter-button").prop("disabled", false);
			let table = $('.info-driver table');
			let driverBlock = $('.driver-block');
			let startDate = data[0]['start'];
			let endDate = data[0]['end'];
			table.find('tr:gt(0)').remove();
			if (data[0]['drivers_efficiency'].length !== 0) {
				data[0]['drivers_efficiency'].forEach(function (item) {
					let row = $('<tr></tr>');
					let time = item.road_time
					let parts = time.match(/(\d+) (\d+):(\d+):(\d+)/);
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

					row.append('<td class="driver">' + item.full_name + '</td>');
					row.append('<td class="kasa">' + item.total_kasa + '</td>');
					row.append('<td class="orders">' + item.orders + '</td>');
					row.append('<td class="accept">' + item.accept_percent + " %" + '</td>');
					row.append('<td class="price">' + item.average_price + '</td>');
					row.append('<td class="mileage">' + item.mileage + '</td>');
					row.append('<td class="efficiency">' + item.efficiency + '</td>');
					row.append('<td class="road">' + time + '</td>');

					table.append(row);

				});

				$('.driver-container').empty();

				data[0]['drivers_efficiency'].forEach(function (driver) {
					let driverBlock = $('<div class="driver-block"></div>');
					let driverName = $('<div class="driver-name"></div>');
					let driverInfo = $('<div class="driver-info"></div>');

					driverName.append('<h3>' + driver.full_name + '</h3>');
					driverName.append('<div class="arrow">▼</div>');

					driverName.on('click', function () {
						if (driverInfo.is(':hidden')) {
							driverInfo.slideDown();
						} else {
							driverInfo.slideUp();
						}
					});

					driverInfo.append('<p>' + gettext("Каса: ") + driver.total_kasa + gettext(" грн") + '</p>');
					driverInfo.append('<p>' + gettext("Кількість замовлень: ") + driver.orders + '</p>');
					driverInfo.append('<p>' + gettext("Відсоток прийнятих замовлень: ") + driver.accept_percent + '%' + '</p>');
					driverInfo.append('<p>' + gettext("Середній чек, грн: ") + driver.average_price + '</p>');
					driverInfo.append('<p>' + gettext("Пробіг, км: ") + driver.mileage + '</p>');
					driverInfo.append('<p>' + gettext("Ефективність, грн/км: ") + driver.efficiency + '</p>');
					driverInfo.append('<p>' + gettext("Час в дорозі: ") + formatTime(driver.road_time) + '</p>');

					driverBlock.append(driverName);
					driverBlock.append(driverInfo);

					// Додати блок водія до контейнера
					$('.driver-container').append(driverBlock);
				});
			}
			if (period === 'yesterday') {
				$('.income-drivers-date').text(startDate);
			} else {
				$('.income-drivers-date').text('З ' + startDate + ' ' + gettext('по') + ' ' + endDate);
			}
		},
		error: function (error) {
			console.error(error);
		}
	});
}

const commonPeriodSelect = $('#period-common');
const periodSelect = $('#period');

commonPeriodSelect.on('change', function () {
	const selectedPeriod = commonPeriodSelect.val();
	if (selectedPeriod !== "custom") {
		fetchSummaryReportData(selectedPeriod);
		fetchCarEfficiencyData(selectedPeriod);
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
		fetchDriverEfficiencyData(selectedPeriod);
	}
	if (selectedPeriod === "custom") {
		$("#datePickerDriver").css("display", "block");
	} else {
		$("#datePickerDriver").css("display", "none");
	}
});

fetchSummaryReportData('yesterday');
fetchCarEfficiencyData('yesterday');
fetchDriverEfficiencyData('yesterday');


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
	fetchDriverEfficiencyData(selectedPeriod, startDate, endDate);
}

function applyCustomDateRange() {
	$(".apply-filter-button").prop("disabled", true);

	let startDate = $("#start_report").val();
	let endDate = $("#end_report").val();

	const selectedPeriod = commonPeriodSelect.val();
	fetchSummaryReportData(selectedPeriod, startDate, endDate);
	fetchCarEfficiencyData(selectedPeriod, startDate, endDate);
}


$(document).ready(function () {
	let $table = $('.driver-table');
	let $tbody = $table.find('tbody');

	// Function to sort the table by a specific column
	function sortTable(column, order) {
		let rows = $tbody.find('tr').toArray();

		let collator = new Intl.Collator(undefined, {sensitivity: 'base'});

		rows.sort(function (a, b) {
			let valueA = $(a).find(`td.${column}`).text();
			let valueB = $(b).find(`td.${column}`).text();
			if (column === 'driver') {
				if (order === 'asc') {
					return collator.compare(valueA, valueB);
				} else {
					return collator.compare(valueB, valueA);
				}
				;
			} else {
				let floatA = parseFloat(valueA);
				let floatB = parseFloat(valueB);
				if (order === 'asc') {
					return floatA - floatB;
				} else {
					return floatB - floatA;
				}
				;
			}
		});

		$tbody.empty().append(rows);
	}

	// Attach click event handlers to the table headers for sorting
	$table.find('th.sortable').click(function () {

		let column = $(this).data('sort');
		let sortOrder = $(this).hasClass('sorted-asc') ? 'desc' : 'asc';

		// Reset sorting indicators
		$table.find('th.sortable').removeClass('sorted-asc sorted-desc');

		if (sortOrder === 'asc') {
			$(this).addClass('sorted-asc');
		} else {
			$(this).addClass('sorted-desc');
		}

		sortTable(column, sortOrder);
	});

	$(".sidebar-list-item.admin").on("click", function () {

		let adminPanelURL = $(this).data("url");

		if (adminPanelURL) {
			window.open(adminPanelURL, "_blank");
		}
	});

	$("#updateDatabaseContainer").click(function () {

		$("#loadingModal").css("display", "block")

		$.ajax({
			type: "POST",
			url: ajaxPostUrl,
			data: {
				csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
				action: "upd_database",
			},
			success: function (response) {
				let task_id = response.task_id
				let interval = setInterval(function () {
					$.ajax({
						type: "GET",
						url: ajaxGetUrl,
						data: {
							action: "check_task",
							task_id: task_id,
						},
						success: function (response) {
							if (response.data === true) {
								$("#loadingMessage").text(gettext("База даних оновлено"));
								$("#loader").css("display", "none");
								$("#checkmark").css("display", "block");
								setTimeout(function () {
									$("#loadingModal").css("display", "none");
									window.location.reload();
								}, 3000);
								clearInterval(interval);
							} if (response.data === false) {
							    $("#loadingMessage").text(gettext("Сталася помилка, спробуйте ще раз"));
							    $("#loader").css("display", "none");
							    setTimeout(function () {
									$("#loadingModal").css("display", "none");
									window.location.reload();
								}, 3000);
								clearInterval(interval);
							}

						}
					});
				}, 5000);
			}
		});
	});

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

	$(".close-btn").click(function () {
		$("#settingsWindow").fadeOut();
		sessionStorage.setItem('settings', 'false');
		location.reload();
	});

	// burger-menu
	$('.burger-menu').click(function () {
		$('.burger-menu').toggleClass('open');
	});

	$('#VehicleBtnContainer').click(function () {
		$('.payback-car').css('display', 'flex');
		$('.charts').hide();
		$('.main-cards').hide();
		$('.info-driver').hide();
		$('.common-period').hide();
		$('#datePicker').hide()
		$('.driver-container').hide()
		$('#sidebar').removeClass('sidebar-responsive');
	});

	$('#DriverBtnContainer').click(function () {
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

	const resetButton = $("#reset-button");

	resetButton.on("click", function () {
		areaChart.resetSeries();
	});
});

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