import sys
import traceback

from libs import get_logger
from libs.boto3.ec2 import BotoEc2
from libs.boto3.ecs import BotoEcs
from libs.boto3.elbv2 import BotoElbv2
from libs.boto3.route53 import BotoRoute53
from libs.jinja.jinja_utils import JinjaTemplate

logger = get_logger(__name__)


def create(values_input_file, environment_type, templates_root_dir):
    """
    Creates all the AWS infrastructure resources for the ECS Fargate Cluster
    :param values_input_file: The absolute path of values input file template
    :param environment_type: The environment type of deployment qa|uat|prod
    :param templates_root_dir: The root directory where the jinja templates are placed
    :return: None
    """
    try:
        jinja_template = JinjaTemplate(values_input_file, environment_type)
        boto_ec2 = BotoEc2(jinja_template, templates_root_dir)
        boto_ecs = BotoEcs(jinja_template, templates_root_dir)
        boto_elbv2 = BotoElbv2(jinja_template, templates_root_dir)
        boto_route53 = BotoRoute53(jinja_template, templates_root_dir)

        boto_ec2.create_and_configure_vpc()
        boto_elbv2.create_elbv2()
        boto_elbv2.create_elbv2_target_group()
        boto_elbv2.create_elbv2_listeners()
        boto_ecs.create_ecs_fargate_cluster()
        boto_route53.change_record_set_elbv2("CREATE")
        logger.info("Infrastructure creation successful")
    except Exception as e:
        logger.error(f"Exception occurred while creating infrastructure: {e}")
        traceback.print_exception(*sys.exc_info())


def destroy(values_input_file, environment_type, templates_root_dir, dry_run=True):
    """
    Destroys all the AWS infrastructure resources for the ECS Fargate Cluster
    :param values_input_file: The absolute path of values input file template
    :param environment_type: The environment type of deployment qa|uat|prod
    :param templates_root_dir: The root directory where the jinja templates are placed
    :param dry_run: If dry-run flag is set, the infrastructure to be deleted is only printed and not deleted
    :return:
    """
    try:
        jinja_template = JinjaTemplate(values_input_file, environment_type)
        boto_ec2 = BotoEc2(jinja_template, templates_root_dir)
        boto_ecs = BotoEcs(jinja_template, templates_root_dir)
        boto_elbv2 = BotoElbv2(jinja_template, templates_root_dir)
        boto_route53 = BotoRoute53(jinja_template, templates_root_dir)

        boto_route53.change_record_set_elbv2("DELETE", dry_run=dry_run)
        boto_ecs.delete_ecs_fargate_cluster(dry_run=dry_run)
        boto_elbv2.delete_elbv2_resources(dry_run=dry_run)
        boto_ec2.delete_vpc(dry_run=dry_run)
        logger.info("Destroy infrastructure successful")
    except Exception as e:
        logger.error(f"Exception occurred while destroying infrastructure: {e}")
        traceback.print_exception(*sys.exc_info())
