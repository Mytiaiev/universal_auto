function getCookie(key) {
  var cDecoded = decodeURIComponent(document.cookie);
  var cArray = cDecoded.split("; ");

  var result = null;
  cArray.forEach((el) => {
    if (el.indexOf(key) === 0) {
      result = el.substring(key.length + 1);
    }
  });
  return result;
}


function setCookie(key, value, daysToLive) {
  var date = new Date()
  date.setTime(date.getTime() + (daysToLive * 24 * 60 * 60 * 1000))
  var expires = `expires=${date.toUTCString()}`
  document.cookie = `${key}=${value}; ${expires}`
}

function checkCookies() {
  var idOrder = getCookie('idOrder');
  var address = JSON.parse(getCookie('address'));
  var to_address = JSON.parse(getCookie('to_address'));
  var phone = getCookie('phone');

  if (idOrder) {
    $.ajax({
      url: ajaxGetUrl,
      method: 'GET',
      data: {
        "action": "active_vehicles_locations"
      },
      success: function (response) {
        var taxiArr = JSON.parse(response.data);
        createMap(address, to_address, taxiArr);
      }
    });
    orderUpdate(idOrder);
  } else {
    if (address && to_address && phone) {
      $.ajax({
        url: ajaxGetUrl,
        method: 'GET',
        data: {
          "action": "active_vehicles_locations"
        },
        success: function (response) {
          console.log(response.data)
          var taxiArr = JSON.parse(response.data);
          createMap(address, to_address, taxiArr);
        }
      });
    }
  }
}


function deleteAllCookies() {
  var cookies = document.cookie.split(";");
  for (var i = 0; i < cookies.length; i++) {
    var cookieName = cookies[i].split("=")[0].trim();
    document.cookie = cookieName + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  }
}

function deleteCookie(key) {
  document.cookie = key + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
}

document.cookie = "LAST_RESULT_ENTRY_KEY=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=.www.youtube.com; SameSite=None; Secure";
document.cookie = "TESTCOOKIESENABLED=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/embed; domain=www.youtube.com; SameSite=None; Secure";
document.cookie = "remote_sid=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=.youtube.com; SameSite=Lax";
document.cookie = "PREF=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=.youtube.com; SameSite=Lax";
document.cookie = "requests=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=.www.youtube.com; SameSite=Lax";
