from libs.j2props.j2props_utils import J2PropsTemplate
import os
import sys
import traceback

class J2PropsCommand():
    command = "j2props"

    def __init__(self, args):
        try:
            if not os.path.exists(args.template):
                raise FileNotFoundError(f"Template file not found: {args.template}")
            if not os.path.exists(args.values):
                raise FileNotFoundError(f"Input yaml file not found: {args.values}")
            J2PropsTemplate(args.region).generate_from_template(args.values, args.template)
        except Exception:
            traceback.print_exception(*sys.exc_info())
            sys.exit(1)

    @staticmethod
    def create_parser_in(parent_parser):
        parser = parent_parser.add_parser(J2PropsCommand.command,
                                          description="A Jinja2 template processor that adds a filter to replace keys in the input with values from AWS Secrets Manager")
        parser.add_argument("action", type=str, choices=["sprinkle"], help="Type of action")
        parser.add_argument("--values", "-f", required=True, type=str, help="Path to the input yaml values file.  Ex: uat/application/input.yml")
        parser.add_argument("--template", "-t", required=True, type=str,
                                help="Absolute or relative path to the template file.  Ex: templates/application.properties")
        parser.add_argument("--region", "-r", type=str, default="us-east-2", help="AWS Region for secret retrieval")
        return parser
