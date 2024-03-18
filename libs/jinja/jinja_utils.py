import json
import os
import re

import benedict
from jinja2 import Template

DYNAMIC_VARS_PLACEHOLDER = "%%"


class JinjaTemplate:
    def __init__(self, values_input_file, environment, env_vars_prefix="AWS_ENV_VARS_"):
        # generate the input values file from the jinja template
        if not os.path.isfile(values_input_file):
            raise FileExistsError(f"Not a valid file: {values_input_file}")
        self.__generate_values_file(values_input_file, environment)
        self.env = environment
        self.input_values_dict = {}
        self.env_prefix = env_vars_prefix
        self.template = None

    def __call__(self, template_file, output_format="yaml", print_output=True):
        return self.generate_from_template(template_file, output_format, print_output)

    # Public methods

    def generate_from_template(
        self, template_file, output_format="yaml", print_output=True
    ):
        """
        Renders the AWS resource yaml files from its respective jinja templates
        :param template_file: Full path of the jinja template file
        :param output_format: The format of the output. yaml or json
        :param print_output: Flag whether to print the output to the console
        :return: Rendered template
        """
        try:
            with open(template_file, "r") as f:
                self.template = Template(f.read())
            self.process_input_yaml()
            result = self.template.render(inputs=self.input_values_dict)
            return self.__process_output_text(result, output_format, print_output)
        except Exception as e:
            raise Exception(e)

    def process_input_yaml(self):
        """
        Performs dynamic env vars substitution and returns the text input values as a python dictionary

        :return: Dictionary of values
        """
        # Substitutes the environment variables
        input_values_text = self.__populate_environment_variables(
            self.input_values_text
        )
        # Loads the values in yaml format
        input_values_dict = benedict.load_yaml_str(input_values_text)
        # returns the yaml for the common environment
        self.input_values_dict = input_values_dict["common"]

    # Private methods

    def __generate_values_file(self, input_values_file, environment):
        """
        Generate the input yaml values file from the jinja template by substituting the
        deployment environment
        :param input_values_file: Path of the input values file jinja template
        :param environment: The deployment environment-type
        :return: the input values file as a text string
        """
        with open(input_values_file, "r") as f:
            template = Template(f.read())
        self.input_values_text = template.render(env=environment)

    def __populate_environment_variables(self, input_values_text):
        """
        Read all the environment variables of the OS and replace the place-holders in the input-yaml file
        if the place-holder variable name matches a certain prefix
        :param input_values_text: input-yaml file in raw string format
        :return: env vars substituted input-yaml string
        """
        # replaces the placeholders with blank string
        input_values_text = re.sub(DYNAMIC_VARS_PLACEHOLDER, "", input_values_text)
        env_var_dict = dict(os.environ)
        for k, v in env_var_dict.items():
            if str(k).startswith(self.env_prefix):
                input_values_text = re.sub(k, v, input_values_text)
        return input_values_text

    @staticmethod
    def __process_output_text(rendered_text, output_format, print_output):
        """
        Converts the rendered template text to desired output
        :param rendered_text: text rendered by jinja
        :param output_format: The format of the output text
        :return: The rendered template as a formatted yaml or json string
        """
        if output_format in {"yaml", "yml"}:
            # the rendered text is already in yaml format
            if print_output:
                print(rendered_text)
            return rendered_text
        elif output_format == "json":
            # convert to json
            output_dict = benedict.load_yaml_str(rendered_text)
            if print_output:
                print(json.dumps(output_dict, indent=4))
            return json.dumps(output_dict, indent=4)
        else:
            raise TypeError(f"Invalid Output format: {output_format}")
        return None
