$.scrollTop = () => Math.max(document.documentElement.scrollTop, document.body.scrollTop);
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

//$(window).on('load', function () {
//	$('.loader').remove();
//});

$(document).ready(function () {

	// js for header

	$("#loginBtn").click(function () {
		$("#loginForm").fadeIn();
		$("#loginRadio").hide();
		$("label[for='loginRadio']").hide();
	});

	$("#loginBtn2").click(function () {
		$("#loginForm").fadeIn();
		$("#loginRadio").hide();
		$("label[for='loginRadio']").hide();
	});

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

	$('.stripes').click(function () {
		$('.sub-menu').slideToggle();
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

	$(".close-btn").click(function () {
		$("#loginForm").fadeOut();
		$(".forgot-password-form").fadeOut();
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
				if (response.data['success'] === true) {
					$("#loginBtn").hide();
					window.location.href = "/dashboard/";
					$("#loginForm").fadeOut();

					if (response.data['role'] === 'Partner') {
						localStorage.setItem('role', 'partner');
					}

				} else {
					$("#loginErrorMessage").show();
					$("#login").val("")
					$("#password").val("");
				}
			}
		});
	});

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
		modalText.innerHTML = gettext('Вхід не вдався:') + '<br>' +
    '<ol><li>' + gettext('Будь ласка, перевірте, чи ви використовуєте електронну адресу, яку вказували під час реєстрації.') + '</li>' +
    '<li>' + gettext('Також, переконайтеся, що ви є партнером компанії Ninja Taxi.') + '</li>' +
    '<li>' + gettext('Якщо ви впевнені в правильності введених даних, але не можете увійти в систему, зверніться до нашого менеджера для отримання допомоги.') + '</li>' +
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
				$('#passwordError').text(gettext('Паролі не співпадають')).addClass('error-message').show();
			} else {
				$('#passwordError').hide()
			}

			if (activeCode !== resetCode) {
				$('#activationError').text(gettext('Невірний код активації')).addClass('error-message').show();
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

	$(window).scroll(function () {
		var h = $(".header_section")
		if ($.scrollTop() > 32) {
			h.addClass("fx");
		} else {
			h.removeClass("fx");
		}
	});

	// js for park page

	const openButtonsFree = $(".free-access-button");
	const openButtonsConnect = $(".connect-button");
	const openButtonsConsult = $(".consult-button");
	const formSectionFree = $("#free-access-form");
	const closeButtonAccess = $("#close-form-access");
	const accessForm = $("#access-form");
	const thankYouMessage = $("#thank-you-message");
	const existingYouMessage = $("#existing-you-message")

	function hideFormAndShowThankYou(success) {
    formSectionFree.hide();

    if (success) {
			thankYouMessage.show();
			$(".header_section").show();
			setTimeout(function () {
				thankYouMessage.hide();
			}, 5000);
    } else {
			existingYouMessage.show();
			$(".header_section").show();
			setTimeout(function () {
				existingYouMessage.hide();
			}, 5000);
    }
  }


	function submitForm(formData) {
    formData += "&action=free_access_or_consult";
    $.ajax({
			type: "POST",
			url: ajaxPostUrl,
			data: formData,
			success: function(response) {
				hideFormAndShowThankYou(response.success);
			},
			error: function () {
				console.log("Помилка під час відправки форми.");
			}
    });
  }


	openButtonsFree.on("click", function () {
		$("#free-access-form h2").text(gettext("Отримати безкоштовний доступ на місяць"));
		$("#access-form input[type='submit']").val(gettext("Отримати безкоштовний доступ"));
		formSectionFree.show();
		$(".header_section").hide();
		thankYouMessage.hide();
	});

	openButtonsConnect.on("click", function () {
		$("#free-access-form h2").text(gettext("Зв’язатися з нами"));
    $("#access-form input[type='submit']").val(gettext("Зв’язатися з нами"));
		formSectionFree.show();
		$(".header_section").hide();
		thankYouMessage.hide();
	});

	openButtonsConsult.on("click", function () {
		$("#free-access-form h2").text(gettext("Проконсультуватися"));
		$("#access-form input[type='submit']").val(gettext("Проконсультуватися"));
		formSectionFree.show();
		$(".header_section").hide();
		thankYouMessage.hide();
	});

	closeButtonAccess.on("click", function () {
		formSectionFree.hide();
		$(".header_section").show();
	});

	accessForm.on("submit", function (e) {
    e.preventDefault();
    let formData = accessForm.serialize();
    let phoneInput = accessForm.find('#phone').val();
    let nameInput = accessForm.find('#name').val();
    $(".error-message").hide();
    $(".error-name").hide();

    if (!/^\+\d{1,3} \d{2,3} \d{2,3}-\d{2,3}-\d{2,3}$/.test(phoneInput)) {
			$(".error-message").show();
			return;
		}

		if (nameInput.trim() === "") {
			$(".error-name").show();
			return;
    }

    submitForm(formData);
	});
});

$.mask.definitions['9'] = '';
$.mask.definitions['d'] = '[0-9]';

function intlTelInit(phoneEl) {
	let phoneSelector = $(phoneEl);

	if (phoneSelector.length) {
		phoneSelector.mask("+380 dd ddd-dd-dd");
	}
}

$(document).ready(function() {
  intlTelInit('#phone');

//  js investment page

	var investmentSlider = new Splide( '.investment-slider', {
		type    : 'loop',
		perPage : 1,
		autoplay: true,
	} );

	investmentSlider.mount();
});
