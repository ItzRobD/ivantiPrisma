import pandas as pd
import argparse
import json
from datetime import datetime, timezone, timedelta
from openpyxl.styles import Border, Side

import requests


class PrismaInventory:
    def __init__(self, user_input):
        self.auth_token = ''
        self.refresh_time = None
        self.api_url = 'https://api.prismacloud.io/'
        self.headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Accept': 'application/json; charset=UTF-8',
            'x-redlock-auth': self.auth_token,
        }
        self.resources = []
        self.inventory = None
        self.output_file = user_input.output_file
        self.highlight_threshold = user_input.threshold
        # self.login(user_input.access_key, user_input.secret_key, user_input.refresh_time)

    def test_load_json(self):
        data = None
        with open('test_data.json', 'r') as f:
            data = json.load(f)

        return data

    def test(self):
        self.inventory = self.test_load_json()['resources']
        if self.inventory:
            # pprint(self.inventory)
            res, alerts, vulns = self.get_parsed_inventory()
            summary = {
                'resources': res,
                'total_alerts': alerts,
                'total_vulns': vulns,
            }

            self.export_resource_summary(self.output_file, self.highlight_threshold, summary)
        else:
            print('No inventory found')

    def run(self):
        if self.auth_token == '':
            self.login(args.access_key, args.secret_key, args.refresh_time)
        self.inventory = self.get_inventory()
        if self.inventory:
            res, alerts, vulns = self.get_parsed_inventory()
            summary = {
                'resources': res,
                'total_alerts': alerts,
                'total_vulns': vulns,
            }
            self.export_resource_summary(self.output_file, self.highlight_threshold, summary)

    def login(self, access_key, secret_key, refresh_time=9):
        """
        Obtains auth token and sets a time to refresh the token

        :param access_key: to be used as username in request
        :param secret_key: to be used as password in request
        :param refresh_time: how frequently, in minutes, to refresh this token, default 9
        :return: None
        """
        if access_key == "" or secret_key == "":
            raise ValueError('Access key and secret key must be set')
        if refresh_time > 10:
            raise ValueError(f'Invalid refresh time, exceeds 10 minutes: {refresh_time}')
        payload = json.dumps({
            'username': access_key,
            'password': secret_key,
        })
        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Accept': 'application/json; charset=UTF-8'
        }
        resp = requests.post(f'{self.api_url}login', headers=headers, data=payload)
        if resp.status_code == 200:
            self.auth_token = resp.json()['token']
            self.set_new_refresh_time(refresh_time)
        if resp.status_code == 401:
            raise Exception('token expired')

    def extend_token(self):
        """
            Obtains a refreshed auth token and resets the refresh time
        :return: None
        """
        url = f'{self.api_url}auth_token/extend'
        resp = requests.get(url, headers=self.headers)
        if resp.status_code == 200:
            self.auth_token = resp.json()['token']
        if resp.status_code == 401:
            raise ValueError('invalid credentials')
        if resp.status_code == 429:
            raise Exception('too many requests')

    def set_new_refresh_time(self, delta_time_minutes):
        """
        Sets the refresh time to the current time + delta time
        :param delta_time_minutes: number of minutes to add to current time
        :return: None
        """
        self.refresh_time = datetime.now(timezone.utc) + timedelta(minutes=delta_time_minutes)

    def check_token_timer(self, should_update=True):
        """
        Checks if the current time exceeds the life of the auth token
        and extends if necessary, if should_update is true
        :param should_update: True if should extend token life
        :return: None
        """
        if should_update:
            curr_time = datetime.now(timezone.utc)
            if curr_time > self.refresh_time:
                self.extend_token()

    def get_inventory(self) -> list:
        """
        Returns list of resources in inventory
        :return: resources
        :rtype: list
        """
        self.check_token_timer()
        resp = requests.get(f'{self.api_url}v3/inventory', headers=self.headers)
        if resp.status_code == 400:
            raise Exception('bad request')
        if resp.status_code == 200:
            pass
        return resp.json()['resources']

    def get_parsed_inventory(self) -> tuple:
        """
        Uses the currently set inventory list.
        Totals alerts and vulnerabilities by category
        Creates a list of resources with selected fields for export
        :return: resource list, alerts dict, vuln dict
        :rtype: tuple(list, dict, dict)
        """
        resources = []
        total_alerts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'informational': 0
        }
        total_vulns = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }

        for r in self.inventory:
            # Assuming the result is the number of alerts and vulns
            # add these to the total tracker
            total_alerts['critical'] += r['alertStatus']['critical']
            total_alerts['high'] += r['alertStatus']['high']
            total_alerts['medium'] += r['alertStatus']['medium']
            total_alerts['low'] += r['alertStatus']['low']
            total_alerts['informational'] += r['alertStatus']['informational']

            total_vulns['critical'] += r['vulnerabilityStatus']['critical']
            total_vulns['high'] += r['vulnerabilityStatus']['high']
            total_vulns['medium'] += r['vulnerabilityStatus']['medium']
            total_vulns['low'] += r['vulnerabilityStatus']['low']

            res = {
                'accountId': r['accountId'],
                'accountName': r['accountName'],
                'id': r['id'],
                'name': r['name'],
                'overallPassed': r['overallPassed'],
                'regionName': r['regionName'],
                'critical_alerts': r['alertStatus']['critical'],
                'high_alerts': r['alertStatus']['high'],
                'med_alerts': r['alertStatus']['medium'],
                'low_alerts': r['alertStatus']['low'],
                'info_alerts': r['alertStatus']['informational'],
                'high_vulns': r['vulnerabilityStatus']['high'],
                'med_vulns': r['vulnerabilityStatus']['medium'],
                'low_vulns': r['vulnerabilityStatus']['low'],
            }
            resources.append(res)
        return resources, total_alerts, total_vulns

    def export_resource_summary(self, output_file, highlight_threshold, inventory_summary):
        """
        Creates an excel workbook containing the inventory summary. A sheet for each key in the dict.
        The resources sheet is highlighted based on highest number of alerts using the threshold.
        :param output_file: name of the output file
        :param highlight_threshold: used to determine highlight color
        :param inventory_summary: resources, alerts, vulns
        :return: None
        """
        resources_df = pd.DataFrame(inventory_summary['resources'])
        alerts_df = pd.DataFrame([inventory_summary['total_alerts']])
        vulns_df = pd.DataFrame([inventory_summary['total_vulns']])

        resources_df = resources_df.sort_values(by='id')

        # Used to apply coloring styles to the output
        def highlight_rows(row):
            color = ''
            col_purple = '#F2DBF2'
            col_red = '#F2DCDB'
            col_yellow = '#FFFFCC'
            col_green = '#DBE6C4'
            if row['critical_alerts'] > highlight_threshold:
                color = col_purple
            elif row['high_alerts'] > highlight_threshold:
                color = col_red
            elif row['med_alerts'] > highlight_threshold:
                color = col_yellow
            elif row['low_alerts'] > highlight_threshold:
                color = col_green
            else:
                color = 'white'
            return ['background-color: %s' % color]*len(row.values)

        output_file = output_file
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            resources_df.style.apply(highlight_rows, axis=1).to_excel(writer, sheet_name='Resources', index=False)
            workbook = writer.book
            worksheet = workbook.active
            thin_border = Border(left=Side(style='thin'),
                                 right=Side(style='thin'),
                                 top=Side(style='thin'),
                                 bottom=Side(style='thin'))
            for row in worksheet:
                for cell in row:
                    cell.border = thin_border
            alerts_df.to_excel(writer, sheet_name='Alerts', index=False)
            vulns_df.to_excel(writer, sheet_name='Vulns', index=False)


def main(args):
    if args.refresh_time is None:
        refresh_time = 9
    else:
        refresh_time = args.refresh_time
    user_input = {
        'access_key': args.access_key,
        'secret_key': args.secret_key,
        'refresh_time': refresh_time,
    }
    inventory = PrismaInventory(args)
    # inventory.login()
    # inventory.run()
    inventory.test()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Prisma Inventory')
    parser.add_argument('--access_key', '--a', type=str, help='Access Key', required=True)
    parser.add_argument('--secret_key', '--s', type=str, help='Secret Key', required=True)
    parser.add_argument('--refresh_time', '--t', type=int, help='Refresh Time in Minutes', required=False)
    parser.add_argument('--threshold', '--h', type=int, help='Number to increase highlight color',
                        required=True)
    parser.add_argument('--output_file', '--o', type=str, help='Output filename', required=True)
    args = parser.parse_args()

    main(args)