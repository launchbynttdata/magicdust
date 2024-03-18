import json
import os
import time

from libs.boto3.common import *
from libs.boto3.ec2 import BotoEc2

AWS_RESOURCE_TYPE = "elbv2"


class BotoElbv2(BotoAws):
    """
    Class containing methods to get|create|destroy|find  all ELBv2 resources
    """

    def __init__(
        self, jinja_template, templates_base_dir, resource_type=AWS_RESOURCE_TYPE
    ):
        super().__init__(jinja_template, templates_base_dir, resource_type)
        self.logger = get_logger(__name__)

    # Public functions

    def create_elbv2(self, subnet_ids=None, sg_id=None, template_file=None):
        if not template_file:
            template_file = os.path.join(
                self.templates_base_dir, AWS_RESOURCE_TYPE, "elbv2.yaml.jinja2"
            )
        if not (subnet_ids or sg_id):
            boto_ec2 = BotoEc2(self.jinja_template, self.templates_base_dir)
            vpc_ids = boto_ec2.find_vpcs_by_tag()
            if not vpc_ids:
                raise Exception(
                    f"No VPC Id found for the tag: {self.input_values_dict.get('tags').get('name')}"
                )
            # At most 1 VPC will be found
            vpc_id = vpc_ids[0]
            subnet_ids = boto_ec2.get_subnets_by_vpc_id(vpc_id)
            sg_ids = boto_ec2.get_security_groups_by_vpc_id(vpc_id)
            if not sg_ids:
                raise ValueError(f"No Target Group found for vpc: {vpc_id}")
            sg_id = sg_ids[0]
        # Set the env vars to be used by jinja template rendering
        for index, subnet_id in enumerate(subnet_ids):
            os.environ[f"AWS_ENV_VARS_SUBNET_ID_{index+1}"] = subnet_id
        os.environ["AWS_ENV_VARS_SG_ID"] = sg_id
        request_string = self.jinja_template.generate_from_template(
            template_file, output_format="json", print_output=False
        )
        request_dict = json.loads(request_string)
        try:
            response = self.client.create_load_balancer(**request_dict)
            # Array size will always be 1 upon successful creation
            elbv2_arn = response["LoadBalancers"][0]["LoadBalancerArn"]
            self.logger.info(f"ELBv2 with ARN: {elbv2_arn} created")
            return elbv2_arn
        except (ClientError, KeyError) as e:
            raise Exception(e)

    def create_elbv2_listeners(self, elbv2_arn=None, tg_arn=None, template_file=None):
        listener_arns = []
        if not template_file:
            template_file = os.path.join(
                self.templates_base_dir,
                AWS_RESOURCE_TYPE,
                "elbv2_listeners.yaml.jinja2",
            )
        if not (elbv2_arn or tg_arn):
            elbv2_arns = self.find_elbv2_by_tag()
            if not elbv2_arns:
                raise Exception(
                    f"No ELBv2 found for the tag: {self.input_values_dict.get('tags').get('name')}"
                )
            elbv2_arn = elbv2_arns[0]
            tg_arns = self.find_elbv2_target_group_by_tag()
            if not tg_arns:
                raise Exception(
                    f"No ELBv2 target group found for the tag: "
                    f"{self.input_values_dict.get('tags').get('name')}"
                )
            tg_arn = tg_arns[0]
        # Set env vars to be used by jinja template rendering
        os.environ["AWS_ENV_VARS_ELBV2_ARN"] = elbv2_arn
        os.environ["AWS_ENV_VARS_TARGET_GROUP_ARN"] = tg_arn

        request_string = self.jinja_template.generate_from_template(
            template_file, output_format="json", print_output=False
        )
        request_dict = json.loads(request_string)
        try:
            for listener_dict in request_dict:
                response = self.client.create_listener(**listener_dict)
                listener_arn = response["Listeners"][0]["ListenerArn"]
                self.logger.info(f"ELBv2 Listener with ARN: {listener_arn} created")
                listener_arns.append(listener_arn)
            return listener_arns
        except (ClientError, KeyError) as e:
            raise Exception(e)

    def create_elbv2_target_group(self, vpc_id=None, template_file=None):
        if not template_file:
            template_file = os.path.join(
                self.templates_base_dir,
                AWS_RESOURCE_TYPE,
                "elbv2_target_group.yaml.jinja2",
            )
        if not vpc_id:
            boto_ec2 = BotoEc2(self.jinja_template, self.templates_base_dir)
            vpc_ids = boto_ec2.find_vpcs_by_tag()
            if not vpc_ids:
                raise Exception(
                    f"No VPC Id found for the tag: {self.input_values_dict.get('tags').get('name')}"
                )
            # At most 1 VPC will be found
            vpc_id = vpc_ids[0]
        # Set env vars to be used by jinja template rendering
        os.environ["AWS_ENV_VARS_VPC_ID"] = vpc_id
        request_string = self.jinja_template.generate_from_template(
            template_file, output_format="json", print_output=False
        )
        request_dict = json.loads(request_string)
        try:
            response = self.client.create_target_group(**request_dict)
            tg_arn = response["TargetGroups"][0]["TargetGroupArn"]
            self.logger.info(f"ELBv2 Target group with ARN: {tg_arn} created")
            return tg_arn
        except (ClientError, KeyError) as e:
            raise Exception(e)

    def delete_elbv2_resources(self, dry_run=True):
        """
        Deletes all the ELBv2 resources including Load Balancers, Listeners, Target Groups
        :param dry_run: If set, will not delete the resources, only self.logger.info the resources to be deleted
        :return: None
        """
        elbv2_arns = self.find_elbv2_by_tag()
        tg_arns = self.find_elbv2_target_group_by_tag()
        self.logger.info(
            f"The following ELBv2 resources will be deleted\n"
            f"\tLoad Balancers: {elbv2_arns}\n"
            f"\tTarget Groups: {tg_arns}"
        )
        if not dry_run:
            for elbv2_arn in elbv2_arns:
                self.logger.info(f"Deleting LB with ARN: {elbv2_arn}")
                self.delete_elbv2_by_arn(elbv2_arn)
            for tg_arn in tg_arns:
                self.logger.info(f"Deleting Target Group with ARN: {tg_arn}")
                self.delete_tg_by_arn(tg_arn)
        else:
            self.logger.info(
                f"No resources are deleted since the --dry-run flag is set."
            )

    def get_elb_dns_by_arn(self, arn):
        try:
            load_balancer = self.client.describe_load_balancers(LoadBalancerArns=[arn])
            return load_balancer.get("LoadBalancers")[0].get("DNSName")
        except Exception as e:
            self.logger.info(f"Exception occurred: {e}")

    def find_elbv2_by_tag(self):
        filtered_arns = []
        tag_key = self.input_values_dict.get("tags").get("key")
        tag_value = self.input_values_dict.get("tags").get("name")
        try:
            # Work-around to find elb with tags, since describe_load_balancers() does not retrieve the tags
            elbs = self.client.describe_load_balancers()
            elb_arns = [elb.get("LoadBalancerArn") for elb in elbs.get("LoadBalancers")]
            tags = self.client.describe_tags(ResourceArns=elb_arns)
            for row in tags.get("TagDescriptions"):
                if row.get("Tags"):
                    for tag in row.get("Tags"):
                        if tag.get("Key") == tag_key and tag.get("Value") == tag_value:
                            filtered_arns.append(row.get("ResourceArn"))
        except (KeyError, ClientError) as e:
            self.logger.error(f"An error occurred while finding ELBv2 by tag: {e}")
        return filtered_arns

    def find_elbv2_target_group_by_tag(self):
        filtered_arns = []
        tag_key = self.input_values_dict.get("tags").get("key")
        tag_value = self.input_values_dict.get("tags").get("name")
        try:
            # Work-around to find TG with tags, since describe_target_groups() does not retrieve the tags
            all_tgs = self.client.describe_target_groups()
            all_tgs_arns = [
                tg.get("TargetGroupArn") for tg in all_tgs.get("TargetGroups")
            ]
            tags = self.client.describe_tags(ResourceArns=all_tgs_arns)
            for row in tags.get("TagDescriptions"):
                if row.get("Tags"):
                    for tag in row.get("Tags"):
                        if tag.get("Key") == tag_key and tag.get("Value") == tag_value:
                            filtered_arns.append(row.get("ResourceArn"))
        except (KeyError, ClientError) as e:
            self.logger.error(
                f"Exception occurred while finding Target Group by tag: {e}"
            )
        return filtered_arns

    # Private functions

    @retry
    def delete_elbv2_by_arn(
        self, elbv2_arn, max_retries=MAX_RETRIES, delay=RETRY_DELAY
    ):
        response = self.client.delete_load_balancer(LoadBalancerArn=elbv2_arn)
        self.logger.debug(
            f"Response from API: {response.get('ResponseMetadata').get('HTTPStatusCode')}"
        )

    @retry
    def delete_tg_by_arn(self, tg_arn, max_retries=MAX_RETRIES, delay=RETRY_DELAY):
        response = self.client.delete_target_group(TargetGroupArn=tg_arn)
        self.logger.debug(
            f"Response from API: {response.get('ResponseMetadata').get('HTTPStatusCode')}"
        )
