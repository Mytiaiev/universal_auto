from datetime import datetime, timedelta
import requests
from django.db import models

from app.models import Payments, UberSession, Fleets_drivers_vehicles_rate, Partner, FleetOrder, Fleet, UberService
from auto_bot.handlers.order.utils import check_vehicle
from selenium_ninja.driver import SeleniumTools
from selenium_ninja.synchronizer import Synchronizer


class UberRequest(Fleet, Synchronizer):
    base_url = models.URLField(default=UberService.get_value('REQUEST_UBER_BASE_URL'))
    # def __init__(self, partner_id=None, fleet="Uber"):
    #     super().__init__(partner_id, fleet)
    #     self.base_url = UberService.get_value('REQUEST_UBER_BASE_URL')

    def get_header(self):
        obj_session = UberSession.objects.filter(partner=self.partner).latest('created_at')
        headers = {
            "content-type": "application/json",
            "x-csrf-token": "x",
            "cookie": f"sid={obj_session.session}; csid={obj_session.cook_session}"
        }
        return headers

    def get_uuid(self):
        obj_session = UberSession.objects.filter(partner=self.partner__id).latest('created_at')
        return str(obj_session.uber_uuid)

    @staticmethod
    def create_session(partner, login, password):
        SeleniumTools(partner).create_uber_session(login, password)

    @staticmethod
    def remove_dup(text):
        if 'DUP' in text:
            text = text[:-3]
        return text

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
                pictureUrl
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
                    "orgUUID": self.get_uuid(),
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
            phone = driver['member']['user']['phone']
            drivers.append({'fleet_name': self.name,
                            'name': self.remove_dup(driver['member']['user']['name']['firstName']),
                            'second_name': self.remove_dup(driver['member']['user']['name']['lastName']),
                            'email': driver['member']['user']['email'],
                            'phone_number': phone['countryCode'] + phone['nationalPhoneNumber'],
                            'driver_external_id': driver['member']['user']['uuid'],
                            'licence_plate': licence_plate,
                            'pay_cash': True,
                            'photo': driver['member']['user']['pictureUrl'],
                            'vehicle_name': vehicle_name,
                            'vin_code': vin_code,
                            'worked': True})
        return drivers

    def save_report(self, day):
        reports = Payments.objects.filter(report_from=day, vendor_name=self.name, partner=self.partner)
        if reports:
            return list(reports)
        start = self.report_interval(day, True) * 1000
        end = self.report_interval(day) * 1000
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
        uber_drivers = Fleets_drivers_vehicles_rate.objects.filter(partner=self.partner,
                                                                   fleet__name=self.name)
        drivers_id = [obj.driver_external_id for obj in uber_drivers]
        variables = {
                      "performanceReportRequest": {
                        "orgUUID": self.get_uuid(),
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
        if uber_drivers:
            data = self.get_payload(query, variables)
            response = requests.post(self.base_url, headers=self.get_header(), json=data)
            if response.status_code == 200 and response.json()['data']:
                for report in response.json()['data']['getPerformanceReport']:
                    if report['totalEarnings']:
                        driver = Fleets_drivers_vehicles_rate.objects.get(driver_external_id=report['uuid'],
                                                                          partner=self.partner).driver
                        vehicle = check_vehicle(driver, day, max_time=True)[0]
                        order = Payments(
                            report_from=day,
                            vendor_name=self.name,
                            driver_id=report['uuid'],
                            full_name=str(driver),
                            total_amount=round(report['totalEarnings'], 2),
                            total_amount_without_fee=round(report['totalEarnings'], 2),
                            total_amount_cash=round(report['cashEarnings'], 2),
                            total_rides=report['totalTrips'],
                            partner=Partner.get_partner(self.partner),
                            vehicle=vehicle)
                        order.save()
            else:
                self.logger.error(f"Failed save uber report {self.partner} {response}")

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
                    "orgUUID": self.get_uuid()
                     }
        with_client = []
        wait = []
        data = self.get_payload(query, variables)
        response = requests.post(self.base_url, headers=self.get_header(), json=data)
        if response.status_code == 200:
            drivers = response.json()['data']['getDriverEvents']['driverEvents']
            if drivers:
                for rider in drivers:
                    rate = Fleets_drivers_vehicles_rate.objects.filter(driver_external_id=rider['driverUUID']).first()
                    if rate:
                        name, second_name = rate.driver.name, rate.driver.second_name
                        if rider["driverStatus"] == "online":
                            wait.append((name, second_name))
                            wait.append((second_name, name))
                        elif rider["driverStatus"] in ("accepted", "in_progress"):
                            with_client.append((name, second_name))
                            with_client.append((second_name, name))
        return {'wait': wait,
                'with_client': with_client}

    def get_vehicles(self):
        query = '''query vehiclesTableVehicles($orgUUID: String, $pageSize: Int) {
                      getSupplierVehicles(
                        orgUUID: $orgUUID
                        pageSize: $pageSize
                      ) {
                        vehicles {
                          ...VehicleDetailsFields
                        }
                      }
                    }
                    fragment VehicleDetailsFields on Vehicle {
                      make
                      model
                      licensePlate
                      vin
                    }'''
        variables = {
            "orgUUID": self.get_uuid(),
            "pageSize": 25
        }
        data = self.get_payload(query, variables)
        response = requests.post(self.base_url, headers=self.get_header(), json=data)
        if response.status_code == 200:
            vehicles_list = []
            vehicles = response.json()["data"]["getSupplierVehicles"]["vehicles"]
            for vehicle in vehicles:
                vehicles_list.append({
                    'licence_plate': vehicle['licensePlate'],
                    'vehicle_name': f'{vehicle["make"]} {vehicle["model"]}',
                    'vin_code': vehicle['vin']})
            return vehicles_list

    def get_fleet_orders(self, day):
        if not FleetOrder.objects.filter(fleet="Uber", accepted_time__date=day):
            uber_driver = SeleniumTools(self.partner)
            uber_driver.download_payments_order(day)
            uber_driver.save_trips_report(day)
            uber_driver.quit()

    def disable_cash(self, driver_id, enable):
        date = datetime.now() + timedelta(weeks=1)
        period = date.isoformat() + "Z"
        block_query = '''mutation EnableCashBlocks($supplierUuid: UberDataSchemasBasicProtoUuidInput!,
         $earnerUuid: UberDataSchemasBasicProtoUuidInput!) {
                    enableCashBlock(
                        supplierUuid: $supplierUuid
                        earnerUuid: $earnerUuid
                      ) { 
                      cashBlockOverride {
                        earnerUuid {
                        value
                        __typename
                        }
                      }
                      __typename
                    }
        }'''
        unblock_query = '''mutation DisableCashBlocks(
                            $supplierUuid: UberDataSchemasBasicProtoUuidInput!,
                             $earnerUuid: UberDataSchemasBasicProtoUuidInput!,
                              $effectiveAt: UberDataSchemasTimeProtoDateTimeInput!) {
                              disableCashBlock(
                                supplierUuid: $supplierUuid
                                earnerUuid: $earnerUuid
                                effectiveAt: $effectiveAt
                              ) {
                                cashBlockOverride {
                                  earnerUuid {
                                    value
                                    __typename
                                  }
                                }
                                __typename
                              }
                            }'''
        variables = {
                    "supplierUuid":  self.get_uuid(),
                    "earnerUuid": driver_id,
                    "effectiveAt": period
        }
        query = unblock_query if enable == 'true' else block_query
        data = self.get_payload(query, variables)
        requests.post(self.base_url, headers=self.get_header(), json=data)
