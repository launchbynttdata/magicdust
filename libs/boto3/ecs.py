import json
import os
import time

from libs.boto3.common import *

AWS_RESOURCE_TYPE = "ecs"


class BotoEcs(BotoAws):
    """
    Class containing methods to get|create|destroy|find  all ECS resources
    """

    def __init__(
        self, jinja_template, templates_base_dir, resource_type=AWS_RESOURCE_TYPE
    ):
        super().__init__(jinja_template, templates_base_dir, resource_type)
        self.logger = get_logger(__name__)

    # public functions

    def create_ecs_fargate_cluster(self, template_file=None):
        if not template_file:
            template_file = os.path.join(
                self.templates_base_dir,
                AWS_RESOURCE_TYPE,
                "ecs_fargate_cluster.yaml.jinja2",
            )
        request_string = self.jinja_template.generate_from_template(
            template_file, output_format="json", print_output=False
        )
        request_dict = json.loads(request_string)
        try:
            response = self.client.create_cluster(**request_dict)
            cluster_arn = response["cluster"]["clusterArn"]
            self.logger.info(f"Fargate Cluster with ARN: {cluster_arn} created")
            return cluster_arn
        except (ClientError, KeyError) as e:
            raise Exception(e)

    def delete_ecs_fargate_cluster(self, dry_run=True):
        """
        Destroys the Fargate Cluster
        :param dry_run: If set, will not delete the resources, only self.logger.info the resources to be deleted
        :return: None
        """
        arns = self.find_ecs_cluster_by_tag()
        self.logger.info(
            f"The following ECS resources will be deleted\n"
            f"\tFargate ECS Clusters: {arns}"
        )
        if not dry_run:
            for arn in arns:
                self.logger.info(f"Deleting ECS cluster: {arn}")
                self.delete_ecs_cluster_by_arn(arn)
        else:
            self.logger.warn(
                f"No resources are deleted since the --dry-run flag is set."
            )

    def find_ecs_cluster_by_tag(self):
        filtered_arns = []
        try:
            tag_key = self.input_values_dict.get("tags").get("key")
            tag_value = self.input_values_dict.get("tags").get("name")
            clusters_list = self.client.list_clusters()
            cluster_arns = clusters_list.get("clusterArns")
            clusters = self.client.describe_clusters(
                clusters=cluster_arns, include=["TAGS"]
            )
            for row in clusters.get("clusters"):
                for tag in row.get("tags"):
                    if tag.get("key") == tag_key and tag.get("value") == tag_value:
                        filtered_arns.append(row.get("clusterArn"))
        except (ClientError, KeyError) as e:
            raise Exception(f"An error occurred while finding ECS Cluster by tag: {e}")

        return filtered_arns

    # Private functions

    @retry
    def delete_ecs_cluster_by_arn(
        self, ecs_arn, max_retries=MAX_RETRIES, delay=RETRY_DELAY
    ):
        response = self.client.delete_cluster(cluster=ecs_arn)
        self.logger.debug(
            f"Response from API: {response.get('ResponseMetadata').get('HTTPStatusCode')}"
        )
