import libs.boto3.ecs_fargate_infra as ecs_fargate
import os

class AWSCommand():
    command = "aws"

    def __init__(self, args, logger):
        if args.infra_name == "ecs-fargate":
            if not os.path.exists(args.templates_dir):
                raise FileNotFoundError(f"Template file not found: {args.templates_dir}")
            if not os.path.exists(args.values):
                raise FileNotFoundError(f"Input yaml file not found: {args.values}")
            logger.info("Will install/delete the ecs-fargate cluster")
            if args.action == "create":
                logger.info("Will create the infra structure")
                ecs_fargate.create(args.values, args.environment_type, args.templates_dir)
            elif args.action == "destroy":
                logger.info("Will delete the infrastructure")
                ecs_fargate.destroy(args.values, args.environment_type, args.templates_dir, args.dry_run)
            else:
                logger.info(f"invalid action: {args.action}")
        else:
            logger.error(f"Invalid argument: {args.infra_name}")

    @staticmethod
    def create_parser_in(parent_parser):
        parser = parent_parser.add_parser(AWSCommand.command)
        parser.add_argument("infra_name", type=str, choices=["ecs-fargate"],
                                help="Name of the infrastructure to install")
        parser.add_argument("action", type=str, choices=["create", "destroy"], help="Choose between create or destroy")
        parser.add_argument("--environment-type", required=True, type=str,
                                help="Deployment environment like qa|uat|prod")
        parser.add_argument("--values", "-f", required=True, type=str, help="Path to the input yaml values file")
        parser.add_argument("--templates-dir", "-d", required=True, type=str,
                                help="Root directory where the templates are located. "
                                    "Its sub-dirs should be ec2, ecs, etc.")
        parser.add_argument("--dry-run", required=False, action='store_true', help="Dry run for delete action")
        return parser
