import argparse

from libs import get_logger
from libs.aws_command import AWSCommand
from libs.j2props_command import J2PropsCommand
from libs.jinja_command import JinjaCommand

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Automation Helper", add_help=True, prog="magicdust"
    )
    command_parsers = parser.add_subparsers(
        dest="command", title="command", help="Sub commands for the main cli"
    )

    # Load jinja parser
    JinjaCommand.create_parser_in(command_parsers)

    # Load aws parser
    AWSCommand.create_parser_in(command_parsers)

    # Load j2props parser
    J2PropsCommand.create_parser_in(command_parsers)

    args = parser.parse_args()
    if args.command == AWSCommand.command:
        AWSCommand(args, logger)
    elif args.command == JinjaCommand.command:
        JinjaCommand(args)
    elif args.command == J2PropsCommand.command:
        J2PropsCommand(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
