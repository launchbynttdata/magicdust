# magicdust

This project contains all the python helpers to be used for Nexient designed:
TerraForm Modules and TerraGrunt Templates
AWS cloud resource provisioning in json or yaml data structures
Could be extended to support dynamically generating any data structure type describing a deployment to some API.

User can install this repo as a python module and use it in their code. This could also be used as a CLI.
<br>[GitHub] https://github.com/launchbynttdata/magicdust

## Usage
* Lists down all the commands:
`magicdust -h`
* List down all the parameters of the command __jinja__:
`magicdust jinja -h`
* Render a jinja template for subnets

```buildoutcfg
magicdust jinja sprinkle -f aws_infra_values.yaml --environment-type qa -o json -t subnets.yaml.jinja2
```

### Parameters Description:
```buildoutcfg
magicdust jinja -h
```
```buildoutcfg

usage: magicdust jinja [-h] --values VALUES --environment-type ENVIRONMENT_TYPE
                --template TEMPLATE [--output {yaml,json}]
                [--env-prefix ENV_PREFIX]
                {sprinkle}

positional arguments:
  {sprinkle}              Type of action

optional arguments:
  -h, --help            show this help message and exit
  --values VALUES, -f VALUES
                        Path to the input yaml values file
  --environment-type ENVIRONMENT_TYPE
                        Deployment environment like qa|uat|prod
  --template TEMPLATE, -t TEMPLATE
                        Absolute or relative path to the template file. e.g.
                        subnets.yaml.jinja2
  --output {yaml,json}, -o {yaml,json}
                        Format of the output. Either yaml or json
  --env-prefix ENV_PREFIX, -p ENV_PREFIX
                        Environment variables prefix for auto discovery of
                        dynamic variables during template rendering
```

```buildoutcfg
magicdust aws -h
```
```buildoutcfg
usage: magicdust aws [-h] --environment-type ENVIRONMENT_TYPE --values VALUES
              --templates-dir TEMPLATES_DIR [--dry-run]
              {ecs-fargate} {create,destroy}

positional arguments:
  {ecs-fargate}         Name of the infrastructure to install
  {create,destroy}      Choose between create or destroy

optional arguments:
  -h, --help            show this help message and exit
  --environment-type ENVIRONMENT_TYPE
                        Deployment environment like qa|uat|prod
  --values VALUES, -f VALUES
                        Path to the input yaml values file
  --templates-dir TEMPLATES_DIR, -d TEMPLATES_DIR
                        Root directory where the templates are located. Its
                        sub-dirs should be ec2, ecs, etc.
  --dry-run             Dry run for delete action
```

## Installation

### Create a virtual environment
```buildoutcfg
python -m venv <path_to_venv>
# Example will create a virtual env in the directory venv in home dir of the user
python -m venv ~/venv

# Activate a virtual env
source venv/bin/activate

# Deactivate a virtual env
deactivate
```

This module could be installed as a pip package.
```buildoutcfg
# Clone the repository
git clone https://github.com/launchbynttdata/magicdust
# cd into the repo
cd magicdust
# install the module
python setup.py install
# alternate installation
pip install .
```

__Note:__ in case of using python inside asdf, perform a `asdf reshim`<br>
Use `pip list` to find the installed package by the name: _magicdust_

### Testing

- Ensure that all tests is prefixed `test_*.py`
- Run `pytest` to run all python unit tests
- To run a specific test run the command `pytest -q file_directory`

### Linting

- `pylint`: outputs a list of arguments that can be run with this command
- `pylint [filename].py`: lints specific python file
- `pylint *`: runs linting for the entire project
