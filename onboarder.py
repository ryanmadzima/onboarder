#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
title: onboarder.py
description: Quickly onboard a large amount of EX switches to the Mist cloud using a CSV file.
author: Ryan M. Adzima <radzima@juniper.net>
date: 20200413
version: 1.0
notes: This script was tested using Python 3.8.1 and assumes existing SSH access and a super-user account that can apply a configuration.
    CSV file example:
        ip,username,password
        192.168.0.2,super_user,MyPassw0rd!
        192.168.0.3,super_user,MyPassw0rd!
python_version: 3.8.1
"""

import argparse
import csv
import requests
from netmiko import ConnectHandler
import logging


# SCRIPT FUNCTIONS

log = logging.getLogger('onboarder')
log_cmds = logging.getLogger('onboarder-commands')


def parse_arguments() -> dict:
    """
    Parses the CLI arguments and returns a dictionary containing the data.

    :return dict: Dictionary containing the CLI arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--token',
                        type=str,
                        required=True,
                        help="Mist API token.")
    parser.add_argument('-o', '--org_id',
                        type=str,
                        required=True,
                        help="Mist organization ID.")
    parser.add_argument('-c', '--csv',
                        type=str,
                        required=True,
                        help="CSV file containing switches to be onboarded.")
    parser.add_argument('-l', '--log_level',
                        type=str,
                        choices=['ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        default='DEBUG',
                        help="Set the logging verbosity.")
    arguments = parser.parse_args()
    create_logger(level=arguments.log_level)
    cfg = {
        'mist': {
            'api_token': arguments.token,
            'org_id': arguments.org_id,
        },
        'devices': list()
    }
    with open(arguments.csv, 'r') as devices_file:
        reader = csv.DictReader(devices_file)
        for row in reader:
            row['device_type'] = 'juniper'
            cfg['devices'].append(row)
    return cfg


def create_logger(level: str):
    """
    Configure script logging object.

    :param str level: Logging level (ERROR, WARNING, INFO, DEBUG)
    """
    log.setLevel(level=level)
    log_cmds.setLevel(level=logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(levelname)-7s][%(name)s] %(message)s')
    formatter.datefmt = "%Y-%m-%d %H:%M:%S %Z"

    # Create onboarder.log file handler
    fh = logging.FileHandler('onboarder.log')
    fh.formatter = formatter
    fh.setLevel(level=level)
    log.addHandler(fh)

    # Create onboarder stream handler
    sh = logging.StreamHandler()
    sh.formatter = formatter
    sh.setLevel(level=level)
    log.addHandler(sh)

    # Create onboarder-commands.log file handler
    fh = logging.FileHandler('onboarder-commands.log')
    fh.formatter = formatter
    fh.setLevel(logging.DEBUG)
    log_cmds.addHandler(fh)


# MIST FUNCTIONS


def get_mist_commands(api_token: str, org_id: str):
    """
    Get Juniper switch onboarding commands from Mist API.

    :param str api_token: Mist API token
    :param str org_id: Mist organization ID
    # :return list: The response containing commands from the Mist API
    """
    url = f"https://api.mist.com/api/v1/orgs/{org_id}/ocdevices/outbound_ssh_cmd"
    headers = {
        "Authorization": f"Token {api_token}",
        "Content-type": "application/json"
    }
    log.info("Connecting to Mist API...")
    try:
        res = requests.get(url=url, headers=headers)
        log.debug("Reading response from Mist API...")
        if res.status_code == 200:
            cmds = res.json()['cmd'].split('\n')
            log.info("Got onboarding commands from Mist API...")
            log_cmds.debug(f"Commands: {cmds}")
            return cmds
        else:
            log.error("Could not get commands from Mist API...")
            log.error(f"Mist API status code: {res.status_code}")
            raise ConnectionError(f"Status code: {res.status_code}")
    except Exception as e:
        log.error("Could not get commands from Mist API...")
        log.error(f"Error connecting to Mist API: {e}")
        raise e


# JUNIPER SWITCH FUNCTIONS


def send_commands(devices: list, cmds: str) -> list:
    """
    Send commands to specified device.

    :param list devices: List of dictionaries representing each device
    :param str cmds: String containing the commands to send
    :return list: List containing the status of each device configured
    """
    log.info("Preparing to send onboarding commands to devices...")
    statuses = list()
    for device in devices:
        status = {
            "device": device['ip'],
            "status": "pending",
            "error": None
        }
        log.info(f"Sending commands to {device['ip']}...")
        try:
            net_connect = ConnectHandler(**device)
            net_connect.find_prompt()
            o = net_connect.send_config_set(config_commands=cmds, exit_config_mode=False)
            log_cmds.debug(f"Output for {device['ip']} config: {o}")
            o = net_connect.commit(and_quit=True)
            log_cmds.debug(f"Output for {device['ip']} commit: {o}")
            log.info(f"Successfully sent commands to {device['ip']}!")
            status['status'] = "success"
        except Exception as e:
            log.error(f"Failed sending commands to {device['ip']}!")
            log.error(f"Error sending commands: {e}")
            status['status'] = "failed"
            status['error'] = str(e)
            continue
        statuses.append(status)
    return statuses


if __name__ == '__main__':
    config = parse_arguments()
    log.info("Starting onboarding...")
    commands = get_mist_commands(**config['mist'])
    stats = send_commands(devices=config['devices'], cmds=commands)
    successful = [o for o in stats if o['status'] == 'success']
    failed = [o for o in stats if o['status'] == 'failed']
    log.info(f"Successful: {len(successful)}")
    log.info(f"Successful devices: {', '.join([o['device'] for o in successful])}")
    log.info(f"Failed: {len(failed)}")
    log.info(f"Failed devices: {', '.join([o['device'] for o in failed])}")
