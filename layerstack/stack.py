from __future__ import print_function, division, absolute_import

import argparse
from builtins import super
from collections import MutableSequence, OrderedDict
from layerstack import LayerStackError
from .layer import Layer, LayerBase, ModelLayerBase
from .args import ArgMode
import json


class Stack(MutableSequence):
    """
    A Stack is a list of DiTTo Layers that can be applied to a DiTTo model.

    If all of the sub-layer args are defined, the Stack can be run.

    A Stack may also be an input to an algorithm.
    """

    def __init__(self, *layers, run_dir='.', model=None):
        self.run_dir = run_dir
        self.model = model
        self.__layers = []
        if len(layers):
            for layer in layers:
                self.__checkValue(layer)
            self.__layers.extend(layers)

    @staticmethod
    def __checkValue(value):
        if not isinstance(value, LayerBase):
            raise DiTToTypeError("Stacks only hold Layers. You passed a {}."
                                 .format(type(value)))

    def __getitem__(self, i):
        return self.__layers[i]

    def __setitem__(self, i, layer):
        self.__checkValue(layer)
        self.__layers.insert(i, layer)

    def __delitem__(self, i):
        del self.__layers[i]

    def insert(self, i, layer):
        self.__checkValue(layer)
        self.__layers.insert(i, layer)

    def append(self, layer):
        self.__checkValue(layer)
        self.__layers.append(layer)

    def __str__(self):
        return str(self.__layers)

    def __iter__(self):
        return iter(self.__layers)

    def __len__(self):
        return len(self.__layers)

    @property
    def layers(self):
        return self.__layers

    @property
    def runnable(self):
        for layer in self.layers:
            if not layer.runnable:
                return False
        return True

    def save(self, filename):
        """
        Save this Stack to filename in json format.
        """
        json_data = OrderedDict()
        json_data['run_dir'] = self.run_dir
        json_data['model'] = self.model
        stack_layers = OrderedDict()
        for layer in self.layers:
            layer.args.mode = ArgMode.DESC
            args = []
            for arg in layer.args:
                arg_dict = OrderedDict()
                arg_dict['name'] = arg.name
                if arg.set:
                    arg_dict['value'] = arg.value
                else:
                    arg_dict['value'] = None
                arg_dict['description'] = arg.description
                arg_dict['parser'] = arg.parser
                arg_dict['choices'] = arg.choices
                arg_dict['nargs'] = arg.nargs
                arg_dict['list_parser'] = arg.list_parser
                args.append(arg_dict)

            layer.kwargs.mode = ArgMode.DESC
            kwargs = OrderedDict()
            for name, kwarg in layer.kwargs.items():
                kwarg_dict = OrderedDict()
                kwarg_dict['value'] = kwarg.value
                kwarg_dict['default'] = kwarg.default
                kwarg_dict['description'] = kwarg.description
                kwarg_dict['parser'] = kwarg.parser
                kwarg_dict['choices'] = kwarg.choices
                kwarg_dict['nkwargs'] = kwarg.nkwargs
                kwarg_dict['list_parser'] = kwarg.list_parser
                kwargs[name] = kwarg_dict
            stack_layers[layer.name] = {'layer_dir': layer.layer_dir,
                                        'args': args, 'kwargs': kwargs}

        json_data['layers'] = stack_layers

        with open(filename, 'w') as f:
            json.dump(json_data, f)

    @classmethod
    def load(cls, filename):
        """
        Load a Stack from filename.
        """
        with open(filename) as json_file:
            json_data = json.load(json_file)

        layers = []
        for json_layer in json_data['layers']:
            layer = Layer(json_layer['layer_dir'])
            for i, value in enumerate(json_layer['args'].values()):
                if value is not None:
                    layer.args[i].value = value
            layer.kwargs = json_layer['kwargs']
            layers.append(layer)

        return Stack(*layers,
                     run_dir=json_data['run_dir'], model=json_data['model'])

    def run(self,log_level=logging.INFO):
        start_file_log(os.path.join(self.run_dir,'stack.log'),log_level=log_level):
        for layer in self.layers:
            # HERE -- Maybe load model from path here using first layer cls._load_model
            if layer.issubclass(ModelLayerBase):
                if self.model is None:
                    raise LayerStackError()
                logger.info("Running ...")
                self.model = layer.apply(self,self.model,*layer.args,**layer.kwargs)
            else:
                self.result = layer.apply(self,*layer.args,**layer.kwargs)
            # HERE -- Maybe save model to run_directory using last layer cls._save_model
        return self.model


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Load and optionally run a stack.")
    parser.add_argument('stack_file', help="Stack json file to load.")
    mode_parsers = parser.add_subparsers('mode')
    mode_parsers.add_parser('list')
    mode_parsers.add_parser('run')
    mode_parsers.add_parser('save')

    args = parser.parse_args()

    stack = Stack.load(args.stack_file)
