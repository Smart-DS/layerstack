from __future__ import print_function, division, absolute_import

import argparse
from builtins import super
import imp
import logging
import os
import sys

from enum import Enum
from jinja2 import Environment, FileSystemLoader

from .args import ArgList, KwargDict
from layerstack import start_console_log, LayerStackError


logger = logging.getLogger(__name__)


class Layer(object):

    def __init__(self, layer_dir):
        self.layer_dir = layer_dir
        # load the layer.py module and find the LayerBase class
        # self._layer = the layer base class we found
        self._layer = self.load_layer(layer_dir)
        self._name = self._layer.name
        self._args = self._layer.args()
        self._args.mode = ArgMode.DESC
        self._kwargs = self._layer.kwargs()
        self._kwargs.mode = ArgMode.DESC

    @classmethod
    def create(cls, name, parent_dir, desc=None, layer_base_class=LayerBase):
        """
        Creates a new Layer on the file system under parent_dir.

        Arguments:
            - name (str) - Concise, human readable name for the new layer
            - parent_dir (str) - Path to the parent directory for the new Layer
            - desc (optional str) - Description string to drop into the new layer
            - layer_base_class (issubclass(layer_base_class,LayerBase)) - 
                  Class from which the new layer should be derived. If 
                  issubclass(layer_base_class,ModelLayerBase) then the new layer
                  will conform to that structure (i.e. assume that a model of
                  a particular type is being operated on).
        """

        # Create the directory
        if not os.path.exists(parent_dir):
            raise ValueError("The parent_dir {} does not exist."
                             .format(parent_dir))
        dir_name = name.lower().replace(" ", "_")
        dir_path = os.path.join(parent_dir, dir_name)
        if os.path.exists(dir_path):
            raise ValueError("The new directory to be created, {}, already exists."
                             .format(dir_path))
        os.mkdir(dir_path)

        # Create the layer.py file
        j2env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        template = j2env.get_template('layer.template')
        with open(os.path.join(dir_path, 'layer.py'), 'w') as f:
            f.write(template.render(**cls._template_kwargs(name, model_type, desc)))
        return dir_path

    @classmethod
    def _template_kwargs(cls, name, model_type, desc):
        kwargs = {}
        kwargs['name'] = name

        def class_name(name):
            result = name.title()
            replacements = [(" ", ""),
                            ("-", "")]
            for old, new in replacements:
                result = result.replace(old, new)
            return result

        kwargs['class_name'] = class_name(name)
        kwargs['model_type'] = model_type

        if desc is not None:
            kwargs['desc'] = desc

        main_opts = ""
        lead = None
        for ln in LayerBase.main.__doc__.split("\n"):
            if not lead and not ln:
                continue
            if not lead:
                lead = " " * (len(ln) - len(ln.lstrip(' ')))
            else:
                main_opts += "\n"
            main_opts += ln.replace(lead, "    # ", 1)
        kwargs['main_opts'] = main_opts
        return kwargs

    @staticmethod
    def load_layer(layer_dir):
        module = imp.load_source('layer', os.path.join(layer_dir, 'layer.py'))
        for item in dir(module):
            try:
                if issubclass(getattr(module, item), ModelLayerBase):
                    if item is not 'ModelLayerBase':
                        return getattr(module, item)
            except:
                continue

    @property
    def layer(self):
        return self._layer

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, args):
        self._args.mode = ArgMode.USE
        for i, arg in enumerate(args):
            self._args[i] = arg

    @property
    def kwargs(self):
        return self._kwargs

    @kwargs.setter
    def kwargs(self, kwargs):
        self._kwargs.mode = ArgMode.USE
        for name, value in kwargs.items():
            self._kwargs[name] = value

    @property
    def name(self):
        return self._name

    @classmethod
    def load(cls, layer_dir, model=None):
        return Layer(layer_dir)

    @classmethod
    def run(cls, layer_dir, stack, model, *args, **kwargs):
        layer = Layer(layer_dir)
        layer.args.mode = ArgMode.USE
        for i, arg in enumerate(args):
            layer.args[i] = arg

        layer.kwargs.mode = ArgMode.USE
        for name, value in kwargs.items():
            layer.kwargs[name] = value

        layer.run_layer(stack, model)

    @property
    def runnable(self):
        return self._args.set

    def run_layer(self, stack, model):
        assert self.runnable
        self._args.mode = ArgMode.USE
        self._kwargs.mode = ArgMode.USE
        kwargs = dict(self._kwargs.items())
        self._layer.apply(stack, model, *self._args, **kwargs)


class LayerBase(object):
    name = None
    desc = None

    @classmethod
    def args(cls, **kwargs):
        return ArgList()

    @classmethod
    def kwargs(cls, **kwargs):
        return KwargDict()

    @classmethod
    def apply(cls, stack, *args, **kwargs):
        pass

    # TODO: Split main into parser and execution. Should be able to re-use
    # parser-part for workflows.
    @classmethod
    def main(cls, log_format='%(asctime)s|%(levelname)s|%(name)s|\n    %(message)s'):
        """
        Arguments:
            - log_format (str) - set this to override the format of the default
                  console logging output
        """
        # Create argument parser
        desc = cls._cli_desc()
        parser = argparse.ArgumentParser(description=desc)
        cls._add_positional_arguments(parser)
        parser.add_argument('-r', '--run_dir', help="Run directory",
                            default='.')
        parser.add_argument('-d', '--debug', help="Display debug messages",
                            action='store_true')
        arg_list = cls.args()
        arg_list.add_arguments(parser)
        kwarg_dict = cls.kwargs()
        kwarg_dict.add_arguments(parser, short_names=['r', 'd'])

        # Parse args and set values
        cli_args = parser.parse_args()
        arg_list.set_args(cli_args)
        kwarg_dict.set_kwargs(cli_args)

        log_level = logging.DEBUG if cli_args.debug else logging.INFO
        start_console_log(log_level=log_level, log_format=log_format)

        if not os.path.isdir(cli_args.run_dir):
            # TODO: Make this a DiTTo Exception
            raise ValueError("The run directory '{}' does not exist."
                             .format(os.path.abspath(cli_args.run_dir)))
        cls._main_apply(cli_args, arg_list, kwarg_dict)
        sys.exit()

    @classmethod
    def _cli_desc(cls):
        return cls.desc if cls.desc is not None else "Apply Layer '{}'".format(cls.name)

    @classmethod
    def _add_positional_arguments(cls, parser):
        pass

    @classmethod
    def _main_apply(cls, cli_args, arg_list, kwarg_dict):
        # HERE -- Why doesn't *arg_list, **kwarg_dict work? (Must be bypassing __getitem__)
        assert arg_list.mode == ArgMode.USE
        assert kwarg_dict.mode == ArgMode.USE
        from ditto.layers.stack import Stack
        return cls.apply(Stack(), *arg_list, **kwarg_dict)
        #if len(arg_list) > 0:
        #    assert not isinstance(arg_list[0],Arg)
        #
        #if len(kwarg_dict.keys()) > 0:
        #    assert not isinstance(kwarg_dict[kwarg_dict.keys()[0]],Kwarg)
        #return cls.apply(Stack(),
        #                 *[arg_val.value for arg_val in arg_list],
        #                 **{kwarg_name: kwarg_val for kwarg_name, kwarg_val in kwarg_dict.items()})


class ModelLayerBase(LayerBase):
    model_type = ModelType.DiTTo

    @classmethod
    def args(cls, model=None, **kwargs):
        return super().args(**kwargs)

    @classmethod
    def kwargs(cls, model=None, **kwargs):
        return super().kwargs(**kwargs)

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        if isinstance(model,str):
            model = cls._load_model(model)
        cls._check_model_type(model)
        return model

    @classmethod
    def _cli_desc(cls):
        return cls.desc if cls.desc is not None else "Apply Layer '{}' to {} model".format(cls.name,cls.model_type.name)

    @classmethod
    def _add_positional_arguments(cls, parser):
        parser.add_argument('model', help="Path to {} model".format(cls.model_type.name))

    @classmethod
    def _main_apply(cls, cli_args, arg_list, kwarg_dict):
        model = cls._load_model(cli_args.model)
        from ditto.layers.stack import Stack
        return cls.apply(Stack(), model, *arg_list, **kwarg_dict)

    @classmethod
    def _load_model(cls, model_path):
        if cls.model_type == ModelType.GridLABD:
            from ditto.readers.gridlabd.read import Reader
            from ditto.store import Store
            m = Store()
            Reader().parse(m, model_path)
            return m
        raise DiTToNotImplementedError("Cannot yet load {} models.".format(cls.model_type))
