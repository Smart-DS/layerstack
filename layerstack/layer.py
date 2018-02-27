from __future__ import print_function, division, absolute_import

import argparse
from builtins import super
import imp
import logging
import os
import sys
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader
from layerstack.args import ArgList, KwargDict, ArgMode
from layerstack import checksum, LayerStackError, start_console_log


logger = logging.getLogger(__name__)


class LayerBase(object):
    """
    Abstract base class for user-defined layers.

    Attributes
    ----------
    name : 'str'
        Layer name
    desc : 'str'
        Layer description
    """
    name = None
    desc = None

    @classmethod
    def args(cls, **kwargs):
        """
        Create ArgList

        Parameters
        ----------
        **kwargs
            Internal kwargs

        Returns
        -------
        'ArgList'
            ArgList class instance containing list of layer's args
        """
        return ArgList()

    @classmethod
    def kwargs(cls, **kwargs):
        """
        Create KwargDict

        Parameters
        ----------
        **kwargs
            Internal kwargs

        Returns
        -------
        'KwargDict'
            KwargDict class instance containing dict of layer's kwargs
        """
        return KwargDict()

    @classmethod
    def apply(cls, stack, *args, **kwargs):
        """
        Run layer

        Parameters
        ----------
        stack : 'Stack'
            Stack class instance in which the layer is being run
        *args
            The layer's args
        **kwargs
            The layer's kwargs
        """
        pass

    # TODO: Split main into parser and execution. Should be able to re-use
    # parser-part for workflows.
    @classmethod
    def main(cls,
             log_format='%(asctime)s|%(levelname)s|%(name)s|\n\t%(message)s'):
        """
        cli entry point

        Parameters
        ----------
        log_format : 'str'
            Custom logging format
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
        arg_list.mode = ArgMode.USE
        arg_list.set_args(cli_args)
        kwarg_dict.mode = ArgMode.USE
        kwarg_dict.set_kwargs(cli_args)

        log_level = logging.DEBUG if cli_args.debug else logging.INFO
        start_console_log(log_level=log_level, log_format=log_format)

        if not os.path.isdir(cli_args.run_dir):
            # TODO: Make this a DiTTo Exception
            raise LayerStackError("The run directory '{}' does not exist."
                                  .format(os.path.abspath(cli_args.run_dir)))
        cls._main_apply(cli_args, arg_list, kwarg_dict)
        sys.exit()

    @classmethod
    def _cli_desc(cls):
        """
        Get layer description

        Returns
        -------
        'str'
            Layer description
        """
        return cls.desc if cls.desc is not None else "Apply Layer \
'{}'".format(cls.name)

    @classmethod
    def _add_positional_arguments(cls, parser):
        """
        Add argument to parser

        Parameters
        ----------
        parser : 'argparser'
            Add arg to parser
        """
        pass

    @classmethod
    def _main_apply(cls, cli_args, arg_list, kwarg_dict):
        """
        Run layer from cli

        Parameters
        ----------
        cli_args : 'list'
            list of args from the cli
        arg_list : 'list'
            list of layer args
        kwargs_dict : 'dict'
            dict of layer kwargs

        Returns
        -------
            Layer output
        """
        assert arg_list.mode == ArgMode.USE
        assert kwarg_dict.mode == ArgMode.USE
        from layerstack.stack import Stack
        return cls.apply(Stack(), *arg_list, **kwarg_dict)


class ModelLayerBase(LayerBase):
    """
    Abstract base class for user-defined layers that operate on a model.

    Attributes
    ----------
    name : 'str'
        Layer name
    desc : 'str'
        Layer description
    """

    @classmethod
    def args(cls, model=None, **kwargs):
        """
        Create ArgList

        Parameters
        ----------
        model
            model to be operated on
        **kwargs
            Internal kwargs

        Returns
        -------
        'ArgList'
            ArgList class instance containing list of layer's args
        """
        return super().args(**kwargs)

    @classmethod
    def kwargs(cls, model=None, **kwargs):
        """
        Create KwargDict

        Parameters
        ----------
        model
            model to be operated on
        **kwargs
            Internal kwargs

        Returns
        -------
        'KwargDict'
            KwargDict class instance containing dict of layer's kwargs
        """
        return super().kwargs(**kwargs)

    @classmethod
    def _check_model_type(cls, model):
        """
        Check model type to ensure it is operable

        Parameters
        ----------
        model
            model to be operated on
        """
        # Check to make sure model is of the proper type
        pass

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        """
        Run layer

        Parameters
        ----------
        stack : 'Stack'
            Stack class instance in which the layer is being run
        model
            model to be operated on
        *args
            The layer's args
        **kwargs
            The layer's kwargs

        Returns
        -------
        model
            Updated model
        """
        if isinstance(model, str):
            model = cls._load_model(model)
        cls._check_model_type(model)
        return model

    @classmethod
    def _cli_desc(cls):
        """
        Get layer description

        Returns
        -------
        'str'
            Layer description
        """
        return cls.desc if cls.desc is not None else "Apply Layer '{}' to \
model".format(cls.name)

    @classmethod
    def _add_positional_arguments(cls, parser):
        """
        Add arg for model to parser

        Parameters
        ----------
        parser : 'argparser'
            Add arg to parser
        """
        parser.add_argument('model', help="Path to model")

    @classmethod
    def _main_apply(cls, cli_args, arg_list, kwarg_dict):
        """
        Run layer from cli

        Parameters
        ----------
        cli_args : 'list'
            list of args from the cli
        arg_list : 'list'
            list of layer args
        kwargs_dict : 'dict'
            dict of layer kwargs

        Returns
        -------
            updated model
        """
        model = cls._load_model(cli_args.model)
        from .stack import Stack
        return cls.apply(Stack(), model, *arg_list, **kwarg_dict)

    @classmethod
    def _load_model(cls, model_path):
        """
        Load model from cli

        Parameters
        ----------
        model_path : 'str'
            Path from which to load model
        """
        # Method to load model
        pass

    @classmethod
    def _save_model(cls, model_path):
        """
        Save model from cli

        Parameters
        ----------
        model_path : 'str'
            Path to save model to
        """
        # Method to save model
        pass


class Layer(object):
    """
    Base class to interact with layers:
    - Create
    - Load
    - Run

    Attributes
    ----------
    layer_dir : 'str'
        Directory containing the layer
    _layer : 'LayerBase|ModelLayerBase'
        Layer object
    _checksum : 'str'
        Checksum for layer
    _name : 'str'
        Layer name
    _args : 'ArgList'
        Layer's args
    _kwargs : 'KwargDict'
        Layer's kwargs

    Parameters
    ----------
    layer_dir : 'str'
        Directory from which to load the layer
    """

    def __init__(self, layer_dir):
        self.layer_dir = layer_dir
        # load the layer.py module and find the LayerBase class
        # self._layer = the LayerBase class we found
        logger.debug("Loading layer from {}".format(layer_dir))
        self._layer = self.load_layer(layer_dir)
        self._checksum = checksum(self.layer_filename(layer_dir))
        self._name = self._layer.name
        self._args = self._layer.args()
        self._args.mode = ArgMode.DESC
        self._kwargs = self._layer.kwargs()
        self._kwargs.mode = ArgMode.DESC

    @classmethod
    def create(cls, name, parent_dir, desc=None, layer_base_class=LayerBase):
        """
        Create new layer

        Parameters
        ----------
        name : 'str'
            Layer name
        parent_dir : 'str'
            Parent directory for layer
        desc : 'str'
            Layer description
        layer_base_class : 'LayerBase|ModelLayerBase'
            Base class on which to build layer

        Returns
        -------
        dir_path : 'str'
            Directory containing new layer
        """
        # Create the directory
        if not os.path.exists(parent_dir):
            raise LayerStackError("The parent_dir {} does not exist."
                                  .format(parent_dir))
        dir_name = name.lower().replace(" ", "_")
        dir_path = os.path.join(parent_dir, dir_name)
        if os.path.exists(dir_path):
            raise LayerStackError("The new directory to be created, {}, \
already exists."
                                  .format(dir_path))
        os.mkdir(dir_path)

        # Create the layer.py file
        j2env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        template = j2env.get_template('layer.template')
        with open(os.path.join(dir_path, 'layer.py'), 'w') as f:
            f.write(template.render(**cls._template_kwargs(name,
                                                           layer_base_class,
                                                           desc)))
        return dir_path

    @classmethod
    def _template_kwargs(cls, name, layer_base_class, desc):
        """
        Kwargs for layer template

        Parameters
        ----------
        name : 'str'
            Layer name
        layer_base_class : 'LayerBase|ModelLayerBase'
            Base class on which to build layer
        desc : 'str'
            Layer description

        Returns
        -------
        kwargs : 'dict'
            kwargs to pass to layer template
        """
        def class_name(name):
            result = name.title()
            replacements = [(" ", ""),
                            ("-", "")]
            for old, new in replacements:
                result = result.replace(old, new)
            return result

        kwargs = {}
        kwargs['name'] = name
        kwargs['uuid'] = uuid4()
        kwargs['class_name'] = class_name(name)
        kwargs['layer_base_class_module'] = layer_base_class.__module__
        kwargs['layer_base_class'] = layer_base_class.__name__
        kwargs['is_model_layer'] = issubclass(layer_base_class, ModelLayerBase)

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
    def layer_filename(layer_dir):
        """
        Create file path for layer

        Parameters
        ----------
        layer_dir : 'str'
            Parent directory for layer

        Returns
        -------
        'str'
            Path to layer.py file
        """
        return os.path.join(layer_dir, 'layer.py')

    @staticmethod
    def load_layer(layer_dir):
        """
        Load layer

        Parameters
        ----------
        layer_dir : 'str'
            Parent directory for layer

        Returns
        -------
        'Layer'
            Layer class object
        """
        module = imp.load_source('loaded_layer_{}'.format(uuid4()),
                                 Layer.layer_filename(layer_dir))
        candidate = None
        base_classes = [LayerBase, ModelLayerBase]
        for item in dir(module):
            try:
                temp = getattr(module, item)
                if issubclass(temp, LayerBase):
                    if item not in [x.__name__ for x in base_classes]:
                        if (candidate is not None) and (candidate != temp):
                            if issubclass(temp, candidate):
                                base_classes.append(candidate)
                                candidate = temp
                            else:
                                assert issubclass(candidate, temp), "Layer in \
{!r} contains LayerBase classes on different branches of the inheritance \
hierarchy tree.".format(layer_dir)
                                base_classes.append(temp)
                        else:
                            candidate = temp
            except:
                continue
        if candidate is not None:
            return candidate
        raise LayerStackError("No LayerBase subclass found in {!r}. Module \
dir:\n{}".format(layer_dir, dir(module)))

    @property
    def name(self):
        """
        Get layer name

        Returns
        -------
        'str'
            layer name
        """
        return self._name

    @property
    def layer(self):
        """
        Get layer class

        Returns
        -------
        'Layer'
            layer class object
        """
        return self._layer

    @property
    def checksum(self):
        """
        Get layer checksum

        Returns
        -------
        'str'
            layer checksum
        """
        return self._checksum

    @property
    def args(self):
        """
        Get layer args

        Returns
        -------
        'ArgList'
            Layer ArgList
        """
        return self._args

    @args.setter
    def args(self, args):
        """
        Set args

        Parameters
        ----------
        args : 'list'
            layer arg values
        """
        self._args.mode = ArgMode.USE
        for i, arg in enumerate(args):
            self._args[i] = arg

    @property
    def kwargs(self):
        """
        Get layer kwargs

        Returns
        -------
        'KwargDict'
            Layer KwargDict
        """
        return self._kwargs

    @kwargs.setter
    def kwargs(self, kwargs):
        """
        Set kwargs

        Parameters
        ----------
        kwargs : 'dict'
            layer kwargs
        """
        self._kwargs.mode = ArgMode.USE
        for name, value in kwargs.items():
            self._kwargs[name] = value

    @classmethod
    def run(cls, layer_dir, stack, model, *args, **kwargs):
        """
        Run layer

        Parameters
        ----------
        layer_dir : 'str'
            Parent directory for layer
        stack : 'Stack'
            Stack class instance that is handling the layer
        model
            Model to be operated on
        *args
            layer args
        **kwargs
            layer kwargs

        Returns
        -------
            updated model
        """
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
        """
        Check if layer is runnable (i.e. all args are set)

        Returns
        -------
        'bool'
            Layer args are set and layer can be run
        """
        return self._args.set

    def run_layer(self, stack, model=None):
        """
        Run layer

        Parameters
        ----------
        stack : 'Stack'
            Stack class instance that is handling the layer
        model
            Model to be operated on

        Returns
        -------
            updated model
        """
        assert self.runnable
        self._args.mode = ArgMode.USE
        self._kwargs.mode = ArgMode.USE
        kwargs = dict(self._kwargs.items())
        if model is None:
            return self._layer.apply(stack, *self._args, **kwargs)
        return self._layer.apply(stack, model, *self._args, **kwargs)
