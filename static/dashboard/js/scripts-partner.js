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

function fetchSummaryReportData(period, start, end) {
		let apiUrl;
		if (period === 'custom') {
		apiUrl = `/api/reports/${start}&${end}/`;
		} else {
    	apiUrl = `/api/reports/${period}/`;
    	};
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
        			$("#noDataMessage-1").hide();
							$('#bar-chart').show();
							const driversData = data[0]['drivers'];
							const categories = driversData.map(driver => driver.full_name);
              const values = driversData.map(driver => driver.total_kasa);

							barChartOptions.series[0].data = values;
              barChartOptions.xaxis.categories = categories;
              barChart.updateOptions(barChartOptions);
						} else {
								$("#noDataMessage-1").show();
								$('#bar-chart').hide();
						};
						if (period === 'yesterday') {
							$('.weekly-income-dates').text(startDate);
						} else {
							$('.weekly-income-dates').text(gettext('З ') + startDate + ' ' + gettext('по') + ' ' + endDate);
						};
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
    	};
    $.ajax({
        url: apiUrl,
        type: 'GET',
        dataType: 'json',
        success: function (data) {
        let totalAmount = data['kasa'];
        let mileage = data['total_mileage'];
        let efficiency;
        if (mileage !== 0) {
        	 efficiency = parseFloat(totalAmount/mileage).toFixed(2);
        } else {
        	efficiency = 0
         };

        if (data['efficiency'].length !== 0) {
        	$("#noDataMessage-2").hide();
					$('#area-chart').show();
					const seriesData = [];
					const dates = [];
					data.efficiency.forEach(dateData => {
                    const date = Object.keys(dateData)[0];
                    const vehicleEfficiencies = dateData[date];
                    vehicleEfficiencies.forEach(entry => {
                        const vehicleName = entry.licence_plate;
                        const efficiencyValue = parseFloat(entry.efficiency);
                        let series = seriesData.find(series => series.name === vehicleName);
                        if (!series) {
                            series = {
                                name: vehicleName,
                                data: [],
                            };
                            seriesData.push(series);
                        }
                        series.data.push(efficiencyValue);
                    });
                    dates.push(date);
                });
					areaChartOptions.series = seriesData;
					areaChartOptions.labels = dates;
					areaChart.updateOptions(areaChartOptions);
        } else {
        	$("#noDataMessage-2").show();
					$('#area-chart').hide();
        };
				$('.weekly-income-amount').text(totalAmount + ' ' + gettext('грн'));
				$('.income-efficiency').text(efficiency + ' ' + gettext('грн/км'));
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
    	};
    $.ajax({
        url: apiUrl,
        type: 'GET',
        dataType: 'json',
        success: function (data) {
        console.log(data)
        console.log(data[0])
					$(".apply-filter-button").prop("disabled", false);
					let table = $('.info-driver table');
					let driverBlock = $('.driver-block');
					let startDate = data[0]['start'];
					let endDate = data[0]['end'];
					table.find('tr:gt(0)').remove();
					if (data[0]['drivers_efficiency'].length !== 0){
						data[0]['drivers_efficiency'].forEach(function (item) {
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

							row.append('<td>' + item.full_name + '</td>');
							row.append('<td>' + item.total_kasa + '</td>');
							row.append('<td>' + item.orders + '</td>');
							row.append('<td>' + item.accept_percent + " %" + '</td>');
							row.append('<td>' + item.average_price + '</td>');
							row.append('<td>' + item.mileage + '</td>');
							row.append('<td>' + item.efficiency + '</td>');
							row.append('<td>' + time + '</td>');

							table.append(row);

						});

						$('.driver-container').empty();

						data[0]['drivers_efficiency'].forEach(function (driver) {
							let driverBlock = $('<div class="driver-block"></div>');
							let driverName = $('<div class="driver-name"></div>');
							let driverInfo = $('<div class="driver-info"></div>');

							driverName.append('<h3>' + driver.full_name + '</h3>');
							driverName.append('<div class="arrow" onclick="toggleDriverInfo(this)">▼</div>');

							driverInfo.append('<p>Каса: ' + driver.total_kasa + ' грн' + '</p>');
							driverInfo.append('<p>Кількість замовлень: ' + driver.orders + '</p>');
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


function loadDefaultDriver(period, startDate, endDate) {
	$.ajax({
		type: "GET",
		url: ajaxGetUrl,
		data: {
			action: 'get_drivers_partner',
			period: period,
			start_date: startDate,
			end_date: endDate,

		},
		success: function (response) {
			$(".apply-filter-button").prop("disabled", false);
			let table = $('.info-driver table');
			let driverBlock = $('.driver-block');
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
	$.ajax({
		url: ajaxGetUrl,
		type: "GET",
		data: {
			action: "aggregators"
		},
		success: function (response) {
			let aggregators = response.data;

			for (let aggregator in aggregators) {
				if (aggregators.hasOwnProperty(aggregator)) {
					localStorage.setItem(aggregator, aggregators[aggregator] ? 'success' : 'false');
				}
			}
		}
	});

	const partnerForm = $("#partnerForm");
	const partnerLoginField = $("#partnerLogin");
	const partnerRadioButtons = $("input[name='partner']");

	let uklonStatus = localStorage.getItem('uklon');
	let boltStatus = localStorage.getItem('bolt');
	let uberStatus = localStorage.getItem('uber');

	// Перевірка умови, коли показувати або ховати елемент
	if ((uklonStatus === 'success' || boltStatus === 'success' || uberStatus === 'success')) {
		// Показуємо елемент
		$("#updateDatabaseContainer").show();
	} else {
		// Ховаємо елемент
		$("#updateDatabaseContainer").hide();
	}

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

	$("#settingBtnContainer").click(function () {
		sessionStorage.setItem('settings', 'true');
		$("#settingsWindow").fadeIn();
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
				let task_id = response.task_id;
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
								localStorage.setItem(partner, 'success');
								$("#partnerLogin").hide();
								$("#partnerPassword").hide().val('');
								$(".opt-partnerForm").hide();
								$(".login-ok").show();
								$("#loginErrorMessage").hide();
								hideLoader(partnerForm);
								clearInterval(interval); // Очистити інтервал після отримання "true"
							}
							if (response.data === false) {
								$(".opt-partnerForm").show();
								$("#loginErrorMessage").show();
								$("#partnerLogin").val("").addClass("error-border");
								$("#partnerPassword").val("").addClass("error-border");
								hideLoader(partnerForm);
								clearInterval(interval); // Очистити інтервал після отримання "false"
							}
						},
					});
				}, 5000);
			},
		});
	}


	function sendLogautDataToServer(partner) {
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
							}
						}
					});
				}, 5000);
			}
		});
	});
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

	$('#partnerVehicleBtnContainer').click(function () {
		$('.payback-car').css('display', 'flex');
		$('.charts').hide();
		$('.main-cards').hide();
		$('.info-driver').hide();
		$('.common-period').hide();
		$('#datePicker').hide()
		$('.driver-container').hide()
		$('#sidebar').removeClass('sidebar-responsive');
	});

	$('#partnerDriverBtnContainer').click(function () {
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