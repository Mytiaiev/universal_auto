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
let investorBarChartOptions = {
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

let investorBarChart = new ApexCharts(document.querySelector("#investor-bar-chart"), investorBarChartOptions);
investorBarChart.render();


// AREA CHART
let investorAreaChartOptions = {
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

let investorAreaChart = new ApexCharts(document.querySelector("#investor-area-chart"), investorAreaChartOptions);
investorAreaChart.render();

function fetchInvestorData(period, start, end) {
		let apiUrl;
		if (period === 'custom') {
		apiUrl = `/api/investor_info/${start}&${end}/`;
		} else {
    	apiUrl = `/api/investor_info/${period}/`;
    	};
    $.ajax({
        url: apiUrl,
        type: 'GET',
        dataType: 'json',
        success: function (data) {
            $(".apply-filter-button").prop("disabled", false);
            let totalEarnings = data[0]['totals']['total_earnings'];
            let totalMileage = data[0]['totals']['total_mileage'];
            let totalSpending = data[0]['totals']['total_spending'];
            let startDate = data[0]['start'];
            let endDate = data[0]['end'];
            const vehiclesData = data[0]['car_earnings'];
			const categories = vehiclesData.map(vehicle => vehicle.licence_plate);
        if (totalEarnings !== "0.00") {
        	$(".noDataMessage1").hide();
			$('#investor-bar-chart').show();

            const values = vehiclesData.map(vehicle => vehicle.earnings);
            investorBarChartOptions.series[0].data = values;
            investorBarChartOptions.xaxis.categories = categories;
            investorBarChart.updateOptions(investorBarChartOptions);

        } else {
        	$(".noDataMessage1").show();
			$('#investor-bar-chart').hide()
        };
        if (totalMileage !== "0.00"){
            $(".noDataMessage2").hide();
            $('#investor-area-chart').show();

            const carValue = vehiclesData.map(vehicle => vehicle.mileage);
            investorAreaChartOptions.series[0].data = carValue;
			investorAreaChartOptions.xaxis.categories = categories;
			investorAreaChart.updateOptions(investorAreaChartOptions);
        } else {
            $(".noDataMessage2").show();
		    $('#investor-area-chart').hide();
        };
        if (period === 'yesterday') {
			$('.weekly-income-dates').text(startDate);
		} else {
			$('.weekly-income-dates').text(gettext('З ') + startDate + ' ' + gettext('по') + ' ' + endDate);
			};
		$('.weekly-income-amount').text(totalEarnings + gettext(' грн'));
		$('.spending-all').text(totalSpending + gettext(' грн'));
		$('.income-km').text(totalMileage + gettext(' км'));
        },
        error: function (error) {
            console.error(error);
        }
		});
}

const commonPeriodSelect = $('#period-common');

commonPeriodSelect.on('change', function () {
	const selectedPeriod = commonPeriodSelect.val();
	if (selectedPeriod !== "custom") {
		fetchInvestorData(selectedPeriod);
	}
	if (selectedPeriod === "custom") {
		$("#datePicker").css("display", "block");
	} else {
		$("#datePicker").css("display", "none");
	}
});

fetchInvestorData('yesterday');


function showDatePicker(periodSelectId, datePickerId) {
	let periodSelect = $("#" + periodSelectId);
	let datePicker = $("#" + datePickerId);

	if (periodSelect.val() === "custom") {
		datePicker.css("display", "block");
	} else {
		datePicker.css("display", "none");
	}
}

function applyCustomDateRange() {
	$(".apply-filter-button").prop("disabled", true);

	let startDate = $("#start_report").val();
	let endDate = $("#end_report").val();

	const selectedPeriod = commonPeriodSelect.val();
	fetchInvestorData(selectedPeriod, startDate, endDate);
}

$(document).ready(function () {

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
})