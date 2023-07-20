import requests
from app.models import UberService, Payments, UberSession, Fleets_drivers_vehicles_rate, Partner
from selenium_ninja.synchronizer import Synchronizer


class UberRequest(Synchronizer):

    def __init__(self, partner_id=None, fleet="Uber"):
        super().__init__(partner_id, fleet)
        self.base_url = UberService.get_value('REQUEST_UBER_BASE_URL')

    def get_header(self):
        obj_session = UberSession.objects.filter(partner=self.partner_id).latest('created_at')
        headers = {
            "content-type": "application/json",
            "x-csrf-token": "x",
            "cookie": f"sid={obj_session.session}; csid={obj_session.cook_session}"
        }
        return headers

    @staticmethod
    def get_payload(query, variables):
        data = {
            'query': query,
            'variables': variables
        }
        return data

    def get_drivers_table(self):
        query = '''
          query GetDrivers(
            $orgUUID: ID!,
            $pagingOptions: PagingOptionsInput!,
            $filters: GetDriversFiltersInput
          ) {
            getDrivers(
              orgUUID: $orgUUID,
              pagingOptions: $pagingOptions,
              filters: $filters
            ) {
              orgUUID
              drivers {
                ...DriversTableRowFields
              }
              pagingResult {
                nextPageToken
              }
            }
          }

          fragment DriversTableRowFields on Driver {
            member {
              user {
                uuid
                name {
                  firstName
                  lastName
                }
                email
                phone {
                  countryCode
                  nationalPhoneNumber
                }
              }
            }
            associatedVehicles {
              uuid
              make
              model
              vin
              year
              licensePlate
            }
          }
        '''
        variables = {
                    "orgUUID": "49dffc54-e8d9-47bd-a1e5-52ce16241cb6",
                    "pagingOptions": {
                        "pageSize": 25
                                    },
                    "filters": {
                                "complianceStatuses": [],
                                "vehicleAssignmentStatuses": [],
                                "documentStatuses": []
                                }
                    }
        drivers = []
        data = self.get_payload(query, variables)
        response = requests.post(self.base_url, headers=self.get_header(), json=data)
        drivers_data = response.json()['data']['getDrivers']['drivers']
        for driver in drivers_data:
            licence_plate = ''
            vehicle_name = ''
            vin_code = ''
            if driver['associatedVehicles']:
                licence_plate = driver['associatedVehicles'][0]['licensePlate']
                vehicle_name = driver['associatedVehicles'][0]['make']
                vin_code = driver['associatedVehicles'][0]['vin']
            phone = driver['member']['user']['phone']['countryCode'] + driver['member']['user']['phone']['nationalPhoneNumber']
            drivers.append({'fleet_name': self.fleet,
                            'name': driver['member']['user']['name']['firstName'],
                            'second_name': driver['member']['user']['name']['lastName'],
                            'email': driver['member']['user']['email'],
                            'phone_number': phone,
                            'driver_external_id': driver['member']['user']['uuid'],
                            'licence_plate': licence_plate,
                            'pay_cash': True,
                            'vehicle_name': vehicle_name,
                            'vin_code': vin_code})
        return drivers

    def save_report(self, day):
        reports = Payments.objects.filter(report_from=day, vendor_name=self.fleet, partner=self.partner_id)
        if reports:
            return list(reports)
        start = int(self.start_report_interval(day).timestamp() * 1000)
        end = int(self.end_report_interval(day).timestamp() * 1000)
        query = '''query GetPerformanceReport($performanceReportRequest: PerformanceReportRequest__Input!) {
                  getPerformanceReport(performanceReportRequest: $performanceReportRequest) {
                    uuid
                    totalEarnings
                    hoursOnline
                    totalTrips
                    ... on DriverPerformanceDetail {
                      cashEarnings
                      driverAcceptanceRate
                      driverCancellationRate
                    }
                    ... on VehiclePerformanceDetail {
                      utilization
                      vehicleIncentiveTarget
                      vehicleIncentiveCompleted
                      vehicleIncentiveEnrollmentStatus
                      vehicleIncentiveUnit
                    }
                  }
                }'''
        uber_drivers = Fleets_drivers_vehicles_rate.objects.filter(partner=self.partner_id,
                                                                   fleet__name=self.fleet)
        drivers_id = [obj.driver_external_id for obj in uber_drivers]
        variables = {
                      "performanceReportRequest": {
                        "orgUUID": "49dffc54-e8d9-47bd-a1e5-52ce16241cb6",
                        "dimensions": [
                          "vs:driver"
                        ],
                        "dimensionFilterClause": [
                          {
                            "dimensionName": "vs:driver",
                            "operator": "OPERATOR_IN",
                            "expressions": drivers_id
                          }
                        ],
                        "metrics": [
                          "vs:TotalEarnings",
                          "vs:HoursOnline",
                          "vs:TotalTrips",
                          "vs:CashEarnings",
                          "vs:DriverAcceptanceRate",
                          "vs:DriverCancellationRate"
                        ],
                        "timeRange": {
                          "startsAt": {
                            "value": start
                          },
                          "endsAt": {
                            "value": end
                          }
                        }
                      }
                    }
        data = self.get_payload(query, variables)
        response = requests.post(self.base_url, headers=self.get_header(), json=data)
        if response.status_code == 200:
            for report in response.json()['data']['getPerformanceReport']:
                if report['totalEarnings']:
                    driver = Fleets_drivers_vehicles_rate.objects.get(driver_external_id=report['uuid']).driver
                    order = Payments(
                        report_from=day,
                        vendor_name=self.fleet,
                        driver_id=report['uuid'],
                        full_name=str(driver),
                        total_amount=round(report['totalEarnings'], 2),
                        total_amount_without_fee=round(report['totalEarnings'], 2),
                        total_amount_cash=round(report['cashEarnings'], 2),
                        total_rides=report['totalTrips'],
                        partner=Partner.get_partner(self.partner_id))
                    order.save()
        else:
            self.logger.error(f"Failed save uber report {self.partner_id} {response}")

    def get_drivers_status(self):
        query = '''query GetDriverEvents($orgUUID: String!) {
                      getDriverEvents(orgUUID: $orgUUID) {
                        driverEvents {
                          driverUUID
                          driverStatus
                        }
                      }
                    }'''
        variables = {
                    "orgUUID": "49dffc54-e8d9-47bd-a1e5-52ce16241cb6"
                     }
        with_client = []
        wait = []
        data = self.get_payload(query, variables)
        response = requests.post(self.base_url, headers=self.get_header(), json=data)
        if response.status_code == 200:
            drivers = response.json()['data']['getDriverEvents']['driverEvents']
            if drivers:
                for rider in drivers:
                    driver = Fleets_drivers_vehicles_rate.objects.get(driver_external_id=rider['driverUUID']).driver
                    name, second_name = driver.name, driver.second_name
                    if rider["driverStatus"] == "online":
                        wait.append((name, second_name))
                        wait.append((second_name, name))
                    elif rider["driverStatus"] in ("accepted", "in_progress"):
                        with_client.append((name, second_name))
                        with_client.append((second_name, name))
        return {'wait': wait,
                'with_client': with_client}

