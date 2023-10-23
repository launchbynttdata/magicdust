import yaml
from jinja2 import Template, Environment, FileSystemLoader
import os
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

class J2PropsTemplate:

    def __init__(self, region="us-east-2"):
        self.region = region
        self._aws_client = None

    # Public methods

    def generate_from_template(self, input_file, template_file):
        """
        Performs a jinja2 template expansion from the given input and template files.  Adds functionality to
        replace secrets from AWS Secrets Manager using the awssecrets filter:
        mysecretvalue={{ some.yaml.path | awssecret }}

        This will lookup the value of the secret defined at some.yaml.path in AWS Secrets Manager, where value in the
        input file contains a key into AWS SM (example: myapp/dev/oracle/password).

        mysecretvalue={{ some.yaml.path | awssecretarn }}

        This will lookup the ARN of the secret defined at some.yaml.path in AWS Secrets Manager, where value in the
        input file contains a key into AWS SM (example: myapp/dev/oracle/password).

        :param input_file: path to the input values yaml file
        :param template_file: path to the jinja2 template file to expand
        :return: None - writes to stdout
        """
        self.__validate_paths(input_file, template_file)

        template_dir = Path(template_file).parent
        template_file = Path(template_file).name
        jinja_env = Environment(loader=FileSystemLoader(template_dir))
        jinja_env.filters['awssecret'] = self.__lookup_aws_secret_filter
        jinja_env.filters['awssecretarn'] = self.__lookup_aws_secret_arn_filter

        # Load YAML input
        with open(input_file, 'r') as file:
            input_data = yaml.safe_load(file)

        # Load Jinja2 template
        template = jinja_env.get_template(template_file)

        # Render template with YAML data and environment variables
        rendered_data = template.render(input_data)

        # Write rendered data to stdout
        print(rendered_data)

    # Private methods

    def __validate_paths(self, values_input_file, template_file):
        # validate paths
        if not os.path.isfile(values_input_file):
            raise FileExistsError(f"Not a valid file: {values_input_file}")
        if not os.path.isfile(template_file):
            raise FileExistsError(f"Not a valid file: {template_file}")

    def __get_client(self):
        """
        Return an AWS boto3 client using lazy initialization.
        :return: boto3 client
        """
        if self._aws_client is None:
            # Create a Secrets Manager client
            session = boto3.session.Session()
            self._aws_client = session.client(service_name='secretsmanager', region_name=self.region)
        return self._aws_client

    def __lookup_aws_secret_filter(self, secret_name):
        """
        Expand a reference to a secret pulling from AWS Secrets Manager
        :param secret_name: name of the secret to retrieve
        :return: Secret value from AWS
        """
        client = self.__get_client()
        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name)
        except ClientError as e:
            # For a list of exceptions thrown, see
            # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
            raise e

        # Decrypts secret using the associated KMS key.
        secret = get_secret_value_response['SecretString']
        return secret

    def __lookup_aws_secret_arn_filter(self, secret_name):
        """
        Expand a reference to a secret pulling from AWS Secrets Manager
        :param secret_name: name of the secret to retrieve
        :return: Secret value from AWS
        """
        client = self.__get_client()
        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name)
        except ClientError as e:
            # For a list of exceptions thrown, see
            # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
            raise e

        # Decrypts secret using the associated KMS key.
        secret = get_secret_value_response['ARN']
        return secret
