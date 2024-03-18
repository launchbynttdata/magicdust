import os
import sys
import traceback

from libs.jinja.jinja_utils import JinjaTemplate


class JinjaCommand:
    command = "jinja"

    def __init__(self, args):
        try:
            if not os.path.exists(args.template):
                raise FileNotFoundError(f"Template file not found: {args.template}")
            if not os.path.exists(args.values):
                raise FileNotFoundError(f"Input yaml file not found: {args.values}")
            JinjaTemplate(args.values, args.environment_type)(
                args.template, args.output
            )
        except Exception:
            traceback.print_exception(*sys.exc_info())
            sys.exit(1)

    @staticmethod
    def create_parser_in(parent_parser):
        parser = parent_parser.add_parser(JinjaCommand.command)
        parser.add_argument(
            "action", type=str, choices=["sprinkle"], help="Type of action"
        )
        parser.add_argument(
            "--values",
            "-f",
            required=True,
            type=str,
            help="Path to the input yaml values file",
        )
        parser.add_argument(
            "--environment-type",
            required=True,
            type=str,
            help="Deployment environment like qa|uat|prod",
        )
        parser.add_argument(
            "--template",
            "-t",
            required=True,
            type=str,
            help="Absolute or relative path to the template file. e.g. subnets.yaml.jinja2",
        )
        parser.add_argument(
            "--output",
            "-o",
            required=False,
            type=str,
            default="yaml",
            choices=["yaml", "json"],
            help="Format of the output. Either yaml or json",
        )
        parser.add_argument(
            "--env-prefix",
            "-p",
            required=False,
            type=str,
            default="AWS_ENV_VARS_",
            help="Environment variables prefix for auto discovery of dynamic "
            "variables during template rendering",
        )
        return parser
