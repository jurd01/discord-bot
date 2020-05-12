import yaml
import os
import re


def parse_config(config_path):
    if not config_path:
        return {}

    if not os.path.exists(config_path):
        raise IOError(f'The config path "{config_path}" is not a valid path. '
                      'Please check that the path is correct and that the file exists.')

    try:
        pattern = re.compile('.*?{(\\w+)}.*?')
        tag = None

        def environ_var_builder(loader, node):
            value = loader.construct_scalar(node)
            match = pattern.findall(value)
            if match:
                _all = value
                for m in match:
                    if not os.getenv(m):
                        raise ValueError(f"Required environment variable {m} not set.")
                    _all = _all.replace(f"${{{m}}}", os.getenv(m))
                return _all
            return value

        yaml.SafeLoader.add_implicit_resolver(tag, pattern, None)
        yaml.SafeLoader.add_constructor(tag, environ_var_builder)

        with open(config_path, 'r') as stream:
            config = yaml.load(stream, Loader=yaml.SafeLoader)

    except yaml.YAMLError as ex:
        error_message = f'Cannot parse YAML file {os.path.basename(config_path)}'
        if hasattr(ex, 'problem_mark'):
            mark = ex.problem_mark
            error_message += (', Error position: ({0}:{1})'
                              .format(mark.line + 1, mark.column + 1))
        raise ValueError(error_message)

    return config
