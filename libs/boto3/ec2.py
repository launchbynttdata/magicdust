import json
import os
import time

from libs.boto3.common import *

AWS_RESOURCE_TYPE = "ec2"


class BotoEc2(BotoAws):
    """
    Class containing methods to get|create|destroy|find  all EC2 resources
    """

    def __init__(
        self, jinja_template, templates_base_dir, resource_type=AWS_RESOURCE_TYPE
    ):
        super().__init__(jinja_template, templates_base_dir, resource_type)
        self.logger = get_logger(__name__)

    # Public functions

    def create_and_configure_vpc(self):
        """
        Creates and configures VPC resources: Subnets, Route Table, Internet Gateway, Security Groups with
        Ingress Rules
        :return: None
        """
        vpc_id = self.create_vpc()
        subnet_ids = self.create_subnets_for_vpc(vpc_id)
        self.configure_vpc(vpc_id, subnet_ids)
        sg_id = self.create_security_group(vpc_id)
        self.create_security_group_ingress(sg_id)

    def delete_vpc(self, dry_run=True):
        """
        Deletes VPC along with all its resources like Subnets, Internet Gateways, Security Groups etc.
        :param dry_run: If set, will not delete the resources, only self.logger.info the resources to be deleted
        :return: None
        """
        try:
            vpc_ids = self.find_vpcs_by_tag()
            if not vpc_ids:
                raise ValueError("No VPC found for the provided tag")
            # At most 1 vpc will be found
            vpc_id = vpc_ids[0]
            subnet_ids = self.get_subnets_by_vpc_id(vpc_id)
            igt_ids = self.get_internet_gateways_by_vpc_id(vpc_id)
            sg_ids = self.get_security_groups_by_vpc_id(vpc_id)
            self.logger.info(
                f"Following resources are going to be deleted\n"
                f"\tSecurity Groups: {sg_ids}\n"
                f"\tInternet Gateways: {igt_ids}\n"
                f"\tSubnets: {subnet_ids}\n"
                f"\tVPC: {vpc_ids}\n"
            )
            if not dry_run:
                for sg_id in sg_ids:
                    self.logger.info(f"Deleting Security Group with ID: {sg_id}")
                    self.delete_security_group_by_id(sg_id)
                for subnet_id in subnet_ids:
                    self.logger.info(f"Deleting Subnet with ID: {subnet_id}")
                    self.delete_subnet_by_id(subnet_id)
                for igt_id in igt_ids:
                    self.client.detach_internet_gateway(
                        InternetGatewayId=igt_id, VpcId=vpc_id
                    )
                    self.logger.info(f"Deleting Internet Gateway with ID: {igt_id}")
                    self.delete_internet_gateway_by_id(igt_id, vpc_id)
                self.logger.info(f"Deleting VPC with ID: {vpc_id}")
                self.delete_vpc_by_id(vpc_id)
            else:
                self.logger.info(
                    f"No resources are deleted since the --dry-run flag is set."
                )
        except Exception as e:
            raise e

    def find_vpcs_by_tag(self):
        vpc_ids = []
        try:
            vpc_filter = {
                "Name": f"tag:{self.input_values_dict.get('tags').get('key')}",
                "Values": [self.input_values_dict.get("tags").get("name")],
            }
            vpcs = self.client.describe_vpcs(Filters=[vpc_filter])
            vpc_ids = [vpc.get("VpcId") for vpc in vpcs.get("Vpcs")]
        except (KeyError, ClientError) as e:
            self.logger.info(f"Exception occurred: {e}")
        return vpc_ids

    def get_internet_gateways_by_vpc_id(self, vpc_id):
        igt_ids = []
        if not vpc_id:
            return igt_ids
        try:
            vpc_filter = {"Name": "attachment.vpc-id", "Values": [vpc_id]}
            igts = self.client.describe_internet_gateways(Filters=[vpc_filter])
            igt_ids = [
                vpc.get("InternetGatewayId") for vpc in igts.get("InternetGateways")
            ]

        except (KeyError, ClientError) as e:
            self.logger.info(f"Exception occurred: {e}")
        return igt_ids

    def get_security_groups_by_vpc_id(self, vpc_id):
        sg_ids = []
        if not vpc_id:
            return sg_ids
        vpc_filter = {"Name": "vpc-id", "Values": [vpc_id]}
        try:
            security_groups = self.client.describe_security_groups(Filters=[vpc_filter])
            # Get all security groups except the default SG for the VPC
            sg_ids = [
                vpc.get("GroupId")
                for vpc in security_groups.get("SecurityGroups")
                if vpc.get("GroupName") != "default"
            ]
        except (KeyError, ClientError) as e:
            self.logger.info(f"Exception occurred while getting Security Groups: {e}")
        return sg_ids

    def get_subnets_by_vpc_id(self, vpc_id):
        subnet_ids = []
        if not vpc_id:
            return subnet_ids
        try:
            vpc_filter = {"Name": "vpc-id", "Values": [vpc_id]}
            subnets = self.client.describe_subnets(Filters=[vpc_filter])
            subnet_ids = [
                subnet_id.get("SubnetId") for subnet_id in subnets.get("Subnets")
            ]
        except (KeyError, ClientError) as e:
            self.logger.error(f"Exception while getting subnets: {e}")
        return subnet_ids

    # private functions

    def configure_vpc(self, vpc_id, subnet_ids):
        """
        Creates Internet Gateway, new routes and attaches with the subnets
        :param vpc_id: The VPC Id
        :param subnet_ids: The Subnet Ids
        :return: None
        """
        try:
            response = self.client.create_internet_gateway()
            igt_id = response["InternetGateway"]["InternetGatewayId"]
            self.logger.info(f"Internet Gateway: {igt_id} created")
            self.client.attach_internet_gateway(InternetGatewayId=igt_id, VpcId=vpc_id)
            self.logger.info(f"Internet gateway attached to VPC")
            # Get the default Route table of the VPC
            response = self.client.describe_route_tables(
                Filters=[
                    {"Name": "vpc-id", "Values": [vpc_id]},
                    {"Name": "association.main", "Values": ["true"]},
                ]
            )
            # There will be only 1 default route table
            route_table_id = response["RouteTables"][0]["RouteTableId"]
            self.logger.info(f"Default route table id: {route_table_id}")
            self.client.create_route(
                DestinationCidrBlock="0.0.0.0/0",
                GatewayId=igt_id,
                RouteTableId=route_table_id,
            )
            self.logger.info(f"New route created for RouteTable: {route_table_id}")
            for subnet_id in subnet_ids:
                self.client.associate_route_table(
                    RouteTableId=route_table_id, SubnetId=subnet_id
                )
                self.logger.info(f"Subnet: {subnet_id} associated with route table")
            for subnet_id in subnet_ids:
                self.client.modify_subnet_attribute(
                    MapPublicIpOnLaunch={"Value": True}, SubnetId=subnet_id
                )
        except (ClientError, KeyError) as e:
            raise Exception(e)

    def create_subnets_for_vpc(self, vpc_id, template_file=None):
        subnet_ids = []
        template_file = self.get_template(template_file, "subnets.yaml.jinja2")
        # Sets the env vars to be used in jinja template rendering
        os.environ["AWS_ENV_VARS_VPC_ID"] = vpc_id
        request_string = self.jinja_template.generate_from_template(
            template_file, output_format="json", print_output=False
        )
        request_dict = json.loads(request_string)
        try:
            for subnet_dict in request_dict:
                response = self.client.create_subnet(**subnet_dict)
                response_status = response.get("ResponseMetadata").get("HTTPStatusCode")
                if response_status != 200:
                    raise Exception(f"API returned status: {response_status}")
                subnet_id = response["Subnet"]["SubnetId"]
                self.logger.info(f"Subnet created successfully with ID: {subnet_id}")
                subnet_ids.append(subnet_id)
            return subnet_ids
        except (ClientError, KeyError) as e:
            raise Exception(e)

    def create_vpc(self, template_file=None):
        # Checks if any VPC exists with the given tag and raises exception if any
        existing_vpcs = self.find_vpcs_by_tag()
        if len(existing_vpcs) > 0:
            raise Exception(
                f"VPCs: {existing_vpcs} already exists with the tag: "
                f"{self.input_values_dict.get('tags').get('name')}. Please delete "
                f"them or select different tag"
            )
        if not template_file:
            template_file = os.path.join(
                self.templates_base_dir, AWS_RESOURCE_TYPE, "vpc.yaml.jinja2"
            )
        request_string = self.jinja_template.generate_from_template(
            template_file, output_format="json", print_output=False
        )
        request_dict = json.loads(request_string)
        try:
            response = self.client.create_vpc(**request_dict)
            response_status = response.get("ResponseMetadata").get("HTTPStatusCode")
            if response_status != 200:
                raise Exception(f"API returned status: {response_status}")
            vpc_id = response["Vpc"]["VpcId"]
            self.logger.info(f"VPC created successfully with ID: {vpc_id}")
            return vpc_id
        except (ClientError, KeyError) as e:
            raise Exception(e)

    def create_security_group(self, vpc_id, template_file=None):
        if not template_file:
            template_file = os.path.join(
                self.templates_base_dir, AWS_RESOURCE_TYPE, "security_group.yaml.jinja2"
            )
        # Sets the env var to be used in jinja template rendering
        os.environ["AWS_ENV_VARS_VPC_ID"] = vpc_id
        request_string = self.jinja_template.generate_from_template(
            template_file, output_format="json", print_output=False
        )
        request_dict = json.loads(request_string)
        try:
            response = self.client.create_security_group(**request_dict)
            security_group_id = response["GroupId"]
            return security_group_id
        except (ClientError, ParamValidationError, KeyError) as e:
            raise Exception(e)

    def create_security_group_ingress(self, sg_id, template_file=None):
        if not template_file:
            template_file = os.path.join(
                self.templates_base_dir,
                AWS_RESOURCE_TYPE,
                "security_group_ingress.yaml.jinja2",
            )
        os.environ["AWS_ENV_VARS_SG_ID"] = sg_id
        request_string = self.jinja_template.generate_from_template(
            template_file, output_format="json", print_output=False
        )
        request_dict = json.loads(request_string)
        try:
            self.client.authorize_security_group_ingress(**request_dict)
        except (ClientError, ParamValidationError, KeyError) as e:
            raise Exception(e)

    @retry
    def delete_internet_gateway_by_id(
        self, igt_id, vpc_id, max_retries=MAX_RETRIES, delay=RETRY_DELAY
    ):
        response = self.client.delete_internet_gateway(InternetGatewayId=igt_id)
        self.logger.debug(
            f"Response from API: {response.get('ResponseMetadata').get('HTTPStatusCode')}"
        )

    @retry
    def delete_security_group_by_id(
        self, sg_id, max_retries=MAX_RETRIES, delay=RETRY_DELAY
    ):
        response = self.client.delete_security_group(GroupId=sg_id)
        self.logger.debug(
            f"Response from API: {response.get('ResponseMetadata').get('HTTPStatusCode')}"
        )

    @retry
    def delete_subnet_by_id(
        self, subnet_id, max_retries=MAX_RETRIES, delay=RETRY_DELAY
    ):
        response = self.client.delete_subnet(SubnetId=subnet_id)
        self.logger.debug(
            f"Response from API: {response.get('ResponseMetadata').get('HTTPStatusCode')}"
        )

    @retry
    def delete_vpc_by_id(self, vpc_id, max_retries=MAX_RETRIES, delay=RETRY_DELAY):
        response = self.client.delete_vpc(VpcId=vpc_id)
        self.logger.debug(
            f"Response from API: {response.get('ResponseMetadata').get('HTTPStatusCode')}"
        )
