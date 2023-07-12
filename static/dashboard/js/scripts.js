// SIDEBAR TOGGLE

var sidebarOpen = false;
var sidebar = document.getElementById("sidebar");

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
var barChartOptions = {
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

var barChart = new ApexCharts(document.querySelector("#bar-chart"), barChartOptions);
barChart.render();


// AREA CHART
var areaChartOptions = {
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

var areaChart = new ApexCharts(document.querySelector("#area-chart"), areaChartOptions);
areaChart.render();

$(document).ready(function () {
  function loadDefaultData() {
    let period = 'day';

    $.ajax({
      type: "GET",
      url: ajaxGetUrl,
      data: {
        action: 'get_drivers_cash',
        period: period
      },
      success: function (response) {
        let data = response.data[0];
        let totalAmount = response.data[1].toFixed(2);
        let startDate = response.data[2];
        let endDate = response.data[3];
        let formattedData = {};

        Object.keys(data).forEach(function (key) {
          let value = parseFloat(data[key].toFixed(2));
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

  loadDefaultData();

  $('input[name="effective-period"]').change(function () {
    let selectedValue = $(this).val();

    let period;
    switch (selectedValue) {
      case '1':
        period = 'day';
        break;
      case '2':
        period = 'week';
        break;
      case '3':
        period = 'month';
        break;
      case '4':
        period = 'quarter';
        break;
      default:
        period = 'day';
    }

    $.ajax({
      type: "GET",
      url: ajaxGetUrl,
      data: {
        action: 'get_drivers_cash',
        period: period
      },
      success: function (response) {
        let data = response.data[0];
        let totalAmount = response.data[1].toFixed(2);
        let startDate = response.data[2];
        let endDate = response.data[3];
        let formattedData = {};

        Object.keys(data).forEach(function (key) {
          let value = parseFloat(data[key].toFixed(2));
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
  });

  $('#vehicle-select').change(function () {
    let vehicleId = $(this).val();
    $.ajax({
      type: "GET",
      url: ajaxGetUrl,
      data: {
        action: 'effective_vehicle',
        period: 'week',
        vehicle_id: vehicleId
      },
      success: function (response) {
        // Отримати дані з відповіді
        let dataArray = response.data.data;
        let uniqueNames = Array.from(new Set(dataArray.map(item => item.name)));
        let driverData = {};
        uniqueNames.forEach((name, index) => {
          let driverIndex = index + 1;
          let driverNameKey = `name${driverIndex}`;
          let effectiveKey = `effective${driverIndex}`;

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
          let driverNameKey = `name${driverIndex}`;
          let effectiveKey = `effective${driverIndex}`;

          driverData[driverNameKey] = "Водій відсутній";
          driverData[effectiveKey] = "0";
        }
        driverData.date_effective = dataArray
          .map(item => {
            let date = new Date(item.date_effective);
            return `${date.getDate()}-${date.getMonth() + 1}-${date.getFullYear()}`;
          })
          .join(', ');

        areaChartOptions.series[0].name = driverData.name1;
        areaChartOptions.series[0].data = driverData.effective1.split(', ');
        areaChartOptions.series[1].name = driverData.name2;
        areaChartOptions.series[1].data = driverData.effective2.split(', ');
        areaChartOptions.xaxis.categories = driverData.date_effective.split(', ');
        areaChart.updateOptions(areaChartOptions);
      }
    });
  });
});
