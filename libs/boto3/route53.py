import json

from libs.boto3.common import *
from libs.boto3.elbv2 import BotoElbv2

CHANGE_RECORD_SET_TEMPLATE_FILE = "route53_elbv2_mapping.yaml.jinja2"
AWS_RESOURCE_TYPE = "route53"


class BotoRoute53(BotoAws):
    """
    Class containing methods to get|create|destroy|modify|find  all Route53 resources
    """

    def __init__(
        self, jinja_template, templates_base_dir, resource_type=AWS_RESOURCE_TYPE
    ):
        super().__init__(jinja_template, templates_base_dir, resource_type)
        self.logger = get_logger(__name__)

    # Public functions

    def change_record_set_elbv2(
        self, action, elb_dns=None, template_file=None, dry_run=False
    ):
        record_set_domain = (
            self.input_values_dict.get("fargate_route_53")
            .get("change_batch")
            .get("changes")[0]
            .get("resource_record_set")
            .get("name")
        )
        if dry_run:
            self.logger.info(
                f"The Route53 record set: {record_set_domain} will not be deleted "
                "as the --dry-run flag is set"
            )
        if action not in {"CREATE", "DELETE"}:
            raise ValueError(f"The action should either be CREATE or DELETE")
        template_file = self.get_template(
            template_file, CHANGE_RECORD_SET_TEMPLATE_FILE
        )
        if not elb_dns:
            boto_elbv2 = BotoElbv2(self.jinja_template, self.templates_base_dir)
            # at most one elb will be found
            elbv2_arns = boto_elbv2.find_elbv2_by_tag()
            if not elbv2_arns:
                raise Exception("Could not file ELB instances matching the tag")
            elb_dns = boto_elbv2.get_elb_dns_by_arn(elbv2_arns[0])
        os.environ["AWS_ENV_VARS_LOAD_BALANCER_DNS"] = elb_dns
        os.environ["AWS_ENV_VARS_ROUTE53_ACTION_TYPE"] = action
        request_string = self.jinja_template.generate_from_template(
            template_file, output_format="json", print_output=False
        )
        request_dict = json.loads(request_string)
        try:
            self.client.change_resource_record_sets(**request_dict)
            self.logger.info(
                f"Performed action: {action} for record-set: {record_set_domain}"
            )
        except (ClientError, KeyError) as e:
            raise Exception(e)
