#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from .decimal_encoder import DecimalEncoder
from .timer import Timer, TimerNotStartedException
import requests
import logging
from datetime import datetime
import os
import json
import copy
import math
import typing

logger = logging.getLogger(__name__)

class SolutionMetricsHelper:
    """Submit anonymous solution usage metrics. Call `start_timer` before `report_metrics`."""
    def __init__(self, stack_parameters: dict) -> None:
        self._timer: Timer = Timer()
        self._stack_parameters = copy.deepcopy(stack_parameters)
        # Do not collect the bucket name, since that would de-anonymize the metrics
        self._stack_parameters.pop('BucketName')

    def start_timer(self) -> None:
        """Start the timer for reporting execution time metrics."""
        self._timer.start()

    def report_metrics(self, workspaces: typing.List[dict], workspaces_count: int, directory_count: int, region_count: int) -> None:
        """Report execution metrics if enabled."""
        if not get_solution_metrics_enabled():
            return

        try:
            try:
                execution_time: int = math.ceil(self._timer.get_elapsed_time())
            except TimerNotStartedException:
                logger.error('Timer not started for execution time metrics.')
                execution_time: int = -1

            solution_version = get_solution_version()

            metrics_data = {
                'List_of_Workspaces': workspaces,
                'Total_Workspaces': workspaces_count,
                'Total_Directories': directory_count,
                'Total_Regions': region_count,
                'Stack_Parameters': self._stack_parameters,
                'ECS_Task_Execution_Time': execution_time,
                'SolutionVersion': solution_version
            }

            solution_id = get_solution_id()
            url = get_metrics_endpoint()

            logger.debug("Sending metrics with data {}, solution_is {} and url {}".format(metrics_data, solution_id, url))

            reported_metrics_data = {
                'TimeStamp': str(datetime.utcnow().isoformat()),
                'Solution': solution_id,
                'UUID': get_uuid(),
                'Data': metrics_data
            }

            json_data = json.dumps(reported_metrics_data, cls=DecimalEncoder)
            response = requests.post(url, data=json_data, headers={'content-type': 'application/json'})
            logger.debug("The return code for the metrics request is {}".format(response.status_code))
        except Exception as e:
            logger.warning("Unexpected error submitting solution metrics: {}".format(e))

def get_solution_metrics_enabled() -> bool:
    return os.getenv('SendAnonymousData', 'false').lower() == 'true'

def get_solution_id() -> str:
    return os.getenv('SolutionID', 'Unknown')

def get_metrics_endpoint() -> typing.Union[str, None]:
    return os.getenv('MetricsEndpoint')

def get_uuid() -> str:
    return os.getenv('UUID', 'Unknown')

def get_solution_version() -> str:
    return os.getenv('SolutionVersion', 'Unknown')
