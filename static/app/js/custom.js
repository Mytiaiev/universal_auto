$(document).ready(function () {
	$('[id^="sub-form-"]').on('submit', function (event) {
		event.preventDefault();
		const form = this;
		$.ajax({
			type: "POST",
			url: ajaxPostUrl,
			data: {
				'email': $(event.target).find('#sub_email').val(),
				'action': 'subscribe',
				'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
			},
			success: function (data) {
				$('#email-error-1, #email-error-2').html('');
				form.reset();
			},
			error: function (xhr, textStatus, errorThrown) {
				if (xhr.status === 400) {
					let errors = xhr.responseJSON;
					$.each(errors, function (key, value) {
						$('#' + key + '-error-1, #' + key + '-error-2').html(value);
					});
				} else {
					console.error('Помилка запиту: ' + textStatus);
				}
			}
		});
	});
});

$(window).on('load', function () {
	$('.loader').remove();
});

$(document).ready(function () {

	// js for header

	$('.nav-item-social').click(function (event) {
		if ($('.social-icons').is(':visible')) {
			$('.social-icons').hide();
		} else {
			$('.social-icons').show();
		}
		event.stopPropagation();
	});

	$(document).click(function (event) {
		if (!$(event.target).closest('.nav-item-social').length) {
			$('.social-icons').hide();
		}
	});

	const subMenu = $('.sub-menu');

	$('.nav-item-adaptive').click(function (event) {
		event.stopPropagation();

		if (subMenu.is(':visible')) {
			subMenu.hide();
		} else {
			subMenu.show();
		}
	});

	$(document).click(function () {
		subMenu.hide();
	});

	subMenu.click(function (event) {
		event.stopPropagation();
	});

	let pagesLink = $("#pagesLink");
	let pagesList = $("#pagesList");

	pagesLink.click(function () {
		if (pagesList.is(":visible")) {
			pagesList.hide();
		} else {
			pagesList.show();
		}
	});

	$.ajax({
		url: ajaxGetUrl,
		type: "GET",
		data: {
			action: "is_logged_in"
		},
		success: function (data) {
			let userLink = $(".nav-link.fa.fa-user");

			if (data.is_logged_in === true) {
				userLink.css("background-color", "#A1E8B9");
				userLink.click(function () {
					getUserRoleAndRedirect();
				});
			} else {
				userLink.css("background-color", "#f0f0f0");
				userLink.click(function () {
					showLoginForm();
				});
			}
		}
	});

	function getUserRoleAndRedirect() {
		$.ajax({
			url: ajaxGetUrl,
			type: "GET",
			data: {
				action: "get_role"
			},
			success: function (response) {
				console.log(response.role);
				switch (response.role) {
					case 'Investor':
						window.location.href = "/dashboard-investor/";
						break;
					case 'Manager':
						window.location.href = "/dashboard-manager/";
						break;
					case 'Partner':
						window.location.href = "/dashboard-partner/";
						break;
					default:
						// Handle other roles or errors
						break;
				}
			}
		});
	}

	function showLoginForm() {
		$("#loginForm").fadeIn();
		$("#loginRadio").hide();
		$("label[for='loginRadio']").hide();
	}

	$(".close-btn").click(function () {
		$("#loginForm").fadeOut();
		$(".forgot-password-form").fadeOut();
		window.location.reload();
	});

	$("#showPassword").click(function () {
		let $checkbox = $(this);
		let $passwordField = $checkbox.closest('#loginForm').find('#password');
		let change = $checkbox.is(":checked") ? "text" : "password";
		$passwordField.prop('type', change);
	});

	$("#login-invest").click(function () {
		let login = $("#login").val();
		let password = $("#password").val();

		$.ajax({
			url: ajaxPostUrl,
			type: 'POST',
			data: {
				action: 'login_invest',
				login: login,
				password: password,
				csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
			},
			success: function (response) {
				console.log(response.data['role']);
				if (response.data['success'] === true) {
					handleSuccessfulLogin(response.data['role']);
				} else {
					handleFailedLogin();
				}
			}
		});
	});

	function handleSuccessfulLogin(role) {
		$("#loginBtn").hide();
		$("#loginForm").fadeOut();
		if (role === 'Investor') {
			$("#loggedInUser").text('Особистий кабінет').show();
			window.location.href = "/dashboard-investor/";
		} else if (role === 'Manager') {
			$("#loggedInUser").text('Кабінет Менеджера').show();
			localStorage.setItem('role', 'manager');
			window.location.href = "/dashboard-manager/";
		} else if (role === 'Partner') {
			$("#loggedInUser").text('Кабінет Партнера').show();
			localStorage.setItem('role', 'partner');
			window.location.href = "/dashboard-partner/";
		}
	}

	function handleFailedLogin() {
		$("#loginErrorMessage").show();
		$("#login").val("");
		$("#password").val("");
	}


	let urlParams = new URLSearchParams(window.location.search);
	let signedIn = urlParams.get('signed_in');

	if (signedIn === 'false') {
		let modal = document.createElement('div');
		modal.id = 'modal-signed-in-false';
		modal.className = 'modal-signed-in-false';

		let modalContent = document.createElement('div');
		modalContent.className = 'modal-content-false';

		let closeBtn = document.createElement('span');
		closeBtn.className = 'close';
		closeBtn.innerHTML = '&times;';
		closeBtn.onclick = function () {
			document.body.removeChild(modal);
			window.location.href = '/';
		};

		let modalText = document.createElement('p');
		modalText.innerHTML = 'Вхід не вдався:<br>' +
			'<ol><li>Будь ласка, перевірте, чи ви використовуєте електронну адресу, яку вказували під час реєстрації.</li>' +
			'<li>Також, переконайтеся, що ви є партнером компанії Ninja Taxi.</li>' +
			'<li>Якщо ви впевнені в правильності введених даних, але не можете увійти в систему, зверніться до нашого менеджера для отримання допомоги.</li>' +
			'</ol>';

		modalContent.appendChild(closeBtn);
		modalContent.appendChild(modalText);
		modal.appendChild(modalContent);

		document.body.appendChild(modal);
	}

	const forgotPasswordForm = $('#forgotPasswordForm');
	const loginRadioForm = $('#loginForm');
	const sendResetCodeBtn = $('#sendResetCode');

	$('#forgotPasswordRadio').click(function () {
		forgotPasswordForm.show();
		loginRadioForm.hide();
	});

	sendResetCodeBtn.click(function () {
		const email = $('#forgotEmail').val();

		$.ajax({
			url: ajaxPostUrl,
			type: 'POST',
			data: {
				action: 'send_reset_code',
				email: email,
				csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
			},
			success: function (response) {
				if (response['success'] === true) {
					let resetCode = response['code'][1];
					sendResetCodeBtn.data('resetCode', resetCode);
					forgotPasswordForm.hide();
					$('#resetPasswordForm').show();
				} else {
					$('#forgotPasswordError').show();
					$('#forgotEmail').val('');
				}
			}
		});
	});

	$('#updatePassword').click(function () {
		const email = $('#forgotEmail').val();
		const activeCode = $('#activationCode').val();
		const newPassword = $('#newPassword').val();
		const confirmPassword = $('#confirmPassword').val();
		const resetCode = sendResetCodeBtn.data('resetCode');

		if (newPassword !== confirmPassword || activeCode !== resetCode) {
			if (newPassword !== confirmPassword) {
				$('#passwordError').text('Паролі не співпадають').addClass('error-message').show();
			} else {
				$('#passwordError').hide()
			}

			if (activeCode !== resetCode) {
				$('#activationError').text('Невірний код активації').addClass('error-message').show();
			} else {
				$('#activationError').hide()
			}
		} else {

			$.ajax({
				url: ajaxPostUrl,
				type: 'POST',
				data: {
					action: 'update_password',
					email: email,
					newPassword: newPassword,
					csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
				},
				success: function (response) {
					if (response['success'] === true) {
						$('#resetPasswordForm').hide();
						$('#loginForm').show();
					}
				}
			});
		}
	});

	// js for index

	const detailsRadio = $('#detailsRadio');
	const howItWorksRadio = $('#howItWorksRadio');
	const detailRadio1 = $('#detail-radio-1');
	const detailRadio2 = $('#detail-radio-2');

	detailsRadio.change(function () {
		if (this.checked) {
			detailRadio1.show();
			detailRadio2.hide();
		}
	});

	howItWorksRadio.change(function () {
		if (this.checked) {
			detailRadio1.hide();
			detailRadio2.show();
		}
	});

	let videos = $('a[data-youtube]');
	videos.each(function () {
		let video = $(this);
		let href = video.attr('href');
		let id = new URL(href).searchParams.get('v');

		video.attr('data-youtube', id);
		video.attr('role', 'button');

		video.html(`
    <img alt="" src="https://img.youtube.com/vi/${id}/maxresdefault.jpg" style="border-radius: 25px" width="552" height="310" loading="lazy"><br>
    ${video.text()}
  `);
	});

	function clickHandler(event) {
		let link = $(event.target).closest('a[data-youtube]');
		if (!link) return;

		event.preventDefault();

		let id = link.attr('data-youtube');
		let player = $(`
      <div>
        <iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/${id}?autoplay=1" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
      </div>
    `);
		link.replaceWith(player);
	}

	$(document).on('click', 'a[data-youtube]', clickHandler);
});
