import os
import time

import boto3
from botocore.exceptions import ClientError, ParamValidationError

from libs import get_logger

MAX_RETRIES = 5
RETRY_DELAY = 5

logger = get_logger(__name__)


def retry(function_name):
    """
    This function is used as a decorator around any function which would implement retry logic
    The target function would simply annotate itself with @retry annotation
    :param function_name: Name of the function which is annotated with @retry
    :return: The return value of the annotating function
    """

    def inner(*args, **kwargs):
        max_retries = kwargs.get("max_retries") or MAX_RETRIES
        delay = kwargs.get("delay") or RETRY_DELAY
        for num_retry in range(MAX_RETRIES):
            try:
                return function_name(*args)
            except ClientError as e:
                logger.warn(
                    f"Attempt: {num_retry + 2}: Resources might be busy. Trying again after {delay} seconds"
                )
                time.sleep(delay)
                if num_retry == max_retries - 1:
                    raise Exception(f"Maximum retries exceeded: {e}")

    return inner


class BotoAws:
    def __init__(self, jinja_template, templates_base_dir, resource_type):
        self.client = boto3.client(resource_type)
        self.jinja_template = jinja_template
        self.jinja_template.process_input_yaml()
        self.input_values_dict = self.jinja_template.input_values_dict
        self.templates_base_dir = templates_base_dir
        self.resource_type = resource_type

    def get_template(self, template_file_path, template_name):
        if not template_file_path:
            template_file_path = os.path.join(
                self.templates_base_dir, self.resource_type, template_name
            )
        return template_file_path
