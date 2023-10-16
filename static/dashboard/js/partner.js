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
})