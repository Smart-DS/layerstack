'''
[LICENSE]
Copyright (c) 2020 Alliance for Sustainable Energy, LLC, All Rights Reserved

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

3. The entire corresponding source code of any redistribution, with or without modification, by a research entity, including but not limited to any contracting manager/operator of a United States National Laboratory, any institution of higher learning, and any non-profit organization, must be made publicly available under this license for as long as the redistribution is made available by the research entity.

4. Redistribution of this software, without modification, must refer to the software by the same designation. Redistribution of a modified version of this software (i) may not refer to the modified version by the same designation, or by any confusingly similar designation, and (ii) must refer to the underlying software originally provided by Alliance as "layerstack". Except to comply with the foregoing, the term "layerstack", or any confusingly similar designation may not be used to refer to any modified version of this software or any modified version of the underlying software originally provided by Alliance without the prior written consent of Alliance.

5. The name of the copyright holder(s), any contributors, the United States Government, the United States Department of Energy, or any of their employees may not be used to endorse or promote products derived from this software without specific prior written permission from the respective party.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE UNITED STATES GOVERNMENT, OR THE UNITED STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

[/LICENSE]
'''

from __future__ import print_function, division, absolute_import

import argparse
from builtins import super
import logging
from os import chdir

from pathlib import Path
import sys
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader
from layerstack.args import ArgList, KwargDict, ArgMode
from layerstack import (DEFAULT_LOG_FORMAT, LayerStackError, checksum, 
    load_module_from_file, start_console_log)


logger = logging.getLogger(__name__)


class LayerBase(object):
    """
    Abstract base class for user-defined layers. All attributes and methods are
    class level.
    """

    #: str: layer name, expected to be human-readable (spaces are okay and even 
    #: preferred)
    name = None

    #: uuid.uuid4: unique identifier for the layer
    uuid = None

    #: str: human readable version number for the layer (defaults to '0.1.0')
    version = None

    #: str: layer description
    desc = None

    @classmethod
    def args(cls, **kwargs):
        """
        Each layer must define its positional arguments by populating and 
        returning an ArgList object.

        Returns
        -------
        ArgList
            ArgList object describing the layer's positional arguments. Arg
            names should appear as positional arguments in the apply method in 
            the same order as they are defined here.
        """
        return ArgList()

    @classmethod
    def kwargs(cls, **kwargs):
        """
        Each layer must define its keyword arguments by populating and returning
        a KwargDict object.

        Returns
        -------
        KwargDict
            KwargDict object describing the layer's keyword arguments. Keyword
            argument specifications in the apply method should match what is 
            defined in this method (i.e., be equivalent to 
            Kwarg.name=Kwarg.default).
        """
        return KwargDict()

    @classmethod
    def apply(cls, stack, *args, **kwargs):
        r"""
        Run this layer in the context of the stack, with positional and keyword
        arguments. In general in user-defined layers (classes derived from 
        LayerBase), \*args and \*\*kwargs should be replaced by the actual 
        positional argument names (defined in the args method) and keyword 
        argument name, default value pairs (defined in the kwargs method).

        Parameters
        ----------
        stack : layerstack.stack.Stack
            Stack class instance in which the layer is being run
        *args
            the layer's positional arguments
        **kwargs
            the layer's keyword arguments
        """
        pass

    # TODO: Split main into parser and execution. Should be able to re-use
    # parser-part for workflows. Execution part should call Stack.run.
    @classmethod
    def main(cls, log_format=DEFAULT_LOG_FORMAT):
        """
        Single-layer command-line interface entry point.

        Parameters
        ----------
        log_format : str
            custom logging format to use with the logging package via 
            layerstack.start_console_log
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
        # *** issue 23, likely just need to add an h to this list
        kwarg_dict.add_arguments(parser, short_names=['r', 'd'])

        # Parse args and set values        
        cli_args = parser.parse_args()
        arg_list.mode = ArgMode.USE
        arg_list.set_args(cli_args)
        kwarg_dict.mode = ArgMode.USE
        kwarg_dict.set_kwargs(cli_args)

        log_level = logging.DEBUG if cli_args.debug else logging.INFO
        start_console_log(log_level=log_level, log_format=log_format)

        cli_args.run_dir = Path(cli_args.run_dir)

        if not cli_args.run_dir.exists():
            cli_args.run_dir.mkdir()
        if not cli_args.run_dir.is_dir():
           raise LayerStackError(f"The run directory '{cli_args.run_dir}' does not exist.")

        old_cur_dir = Path.cwd()
        chdir(cli_args.run_dir)

        try:
            cls._main_apply(cli_args, arg_list, kwarg_dict)
        # switch back to initial directory
            chdir(old_cur_dir)
        except:
            #Path.replace(old_cur_dir)
            chdir(old_cur_dir)
            raise

        sys.exit()

    @classmethod
    def _cli_desc(cls):
        """
        Get layer description

        Returns
        -------
        str
            Layer description or 'Apply Layer {}'.format(cls.name) by default
        """
        return cls.desc if cls.desc is not None else "Apply Layer '{}'".format(cls.name)

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
        # TODO: Fix KwargDict so **kwarg_dict works natively
        return cls.apply(Stack(run_dir=cli_args.run_dir), 
            *arg_list, **{k: v for k, v in kwarg_dict.items()})

    @classmethod
    def _add_positional_arguments(cls, parser): 
        """
        Add positional arguments for the apply method to parser.
        """
        pass


class ModelLayerBase(LayerBase):
    """
    Abstract base class for user-defined layers that operate on a model.

    .. automethod:: _check_model_type
    .. automethod:: _load_model
    .. automethod:: _save_model
    """

    @classmethod
    def args(cls, model=None, **kwargs):
        """
        Create ArgList

        Parameters
        ----------
        model : None or a model
            model to be operated on

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

        Returns
        -------
        'KwargDict'
            KwargDict class instance containing dict of layer's kwargs
        """
        return super().kwargs(**kwargs)

    @classmethod
    def _check_model_type(cls, model):
        """
        Check model type to ensure it is operable. Raises an exception if the
        model is the wrong type or some other error is encountered. Derived 
        classes should implement this method.

        Parameters
        ----------
        model
            model to be operated on

        Returns
        -------
        None
        """
        # Check to make sure model is of the proper type
        pass

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
        r"""
        Run this layer in the context of the stack, with positional and keyword
        arguments. In general in user-defined layers (classes derived from 
        LayerBase), \*args and \*\*kwargs should be replaced by the actual 
        positional argument names (defined in the args method) and keyword 
        argument name, default value pairs (defined in the kwargs method).

        Parameters
        ----------
        stack : 'Stack'
            Stack class instance in which the layer is being run
        model
            model this layer will operate on
        *args
            The layer's positional arguments
        **kwargs
            The layer's keyword arguments

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
        assert arg_list.mode == ArgMode.USE
        assert kwarg_dict.mode == ArgMode.USE
        from layerstack.stack import Stack
        # TODO: Fix KwargDict so **kwarg_dict works natively
        return cls.apply(Stack(run_dir=cli_args.run_dir, model=model), 
                         model, *arg_list, **{k: v for k, v in kwarg_dict.items()})

    @classmethod
    def _load_model(cls, model_path):
        """
        Load model from cli. Derived classes must implement this method if they
        support loading from disk.

        Parameters
        ----------
        model_path : 'str'
            Path from which to load model

        Returns
        -------
        model
        """
        pass

    @classmethod
    def _save_model(cls, model, model_path):
        """
        Save model from cli. Derived classes must implement this method if they 
        support saving the model out to disk.

        Parameters
        ----------
        model 
            model to be saved to disk
        model_path : 'str'
            Path to save model to
        """

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
    # *** need optional model argument to be passed to __init__
    def __init__(self, layer_dir, model=None):
        self.layer_dir = layer_dir
        # *** TLS is this what's needed? will create test for this to show failure then fix
        self._model = model
        # load the layer.py module and find the LayerBase class
        # self._layer = the LayerBase class we found
        logger.debug(f"Loading layer from {layer_dir}")
        self._layer = self.load_layer(layer_dir)
        self._checksum = checksum(self.layer_filename(layer_dir))
        self._name = self._layer.name

        # *** when args is called we need to test whether this is a model layer base layer
        # *** if it is then we need to pass the model to args and kwargs calls below?  
        # *** but this won't work for a regular layer base, so need to have an if statement for this

        model_layer_base_obj = isinstance(self._layer, ModelLayerBase)
        if model_layer_base_obj:
            self._args = self._layer.args(self._model)
            self._kwargs = self._layer.kwargs(self.model)
        else:
            self._args = self._layer.args()
            self._kwargs = self._layer.kwargs()

        self._args.mode = ArgMode.DESC
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
        if not parent_dir.exists():
            raise LayerStackError(f"The parent_dir {parent_dir} does not exist.") # maynot need the msg_begin here
        dir_name = name.lower().replace(" ", "_")
        dir_path = parent_dir / dir_name

        if dir_path.exists():
            raise LayerStackError(f"The new directory to be created, {dir_path}, already exists.")
        dir_path.mkdir()

        # Create the layer.py file
        j2env = Environment(loader=FileSystemLoader(str(Path(__file__).parent)))

        template = j2env.get_template('layer.template')
        with open((dir_path / 'layer.py'), 'w') as f:
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
            words = [y for x in name.split() for y in x.split('-')]
            result = ''
            for word in words:
                if word.isupper():
                    result += word
                else:
                    result += word.title()
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

        def class_doc_str(aclass, doc_str=''):
            if issubclass(aclass, LayerBase):
                result = '\n    {}\n    {}'.format(aclass.__name__, '=' * len(aclass.__name__))
                result += aclass.__doc__

                for base_class in aclass.__bases__:
                    result = class_doc_str(base_class, doc_str=(result + doc_str))

                return result
            return doc_str

        kwargs['layer_base_class_doc'] = class_doc_str(layer_base_class)
        kwargs['layer_base_class_args_doc'] = layer_base_class.args.__doc__
        kwargs['layer_base_class_kwargs_doc'] = layer_base_class.kwargs.__doc__
        kwargs['layer_base_class_apply_doc'] = layer_base_class.apply.__doc__

        main_opts = ""
        lead = None
        
        # below code is grabbing docstring and main parser options from LayerBase
        # to be added to end of the new layer.py file 
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
        layer_dir : str
            Parent directory for layer

        Returns
        -------
        str
            Path to layer.py file
        """
        return str(Path(layer_dir) / 'layer.py')

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

        module = load_module_from_file('loaded_layer_{}'.format(uuid4()),
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
        raise LayerStackError(f"No LayerBase subclass found in {layer_dir!r}. Module dir:\n{dir(module)}")

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
        # ETH@20200810 - This method seems redundant/unused. Deprecate?

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
