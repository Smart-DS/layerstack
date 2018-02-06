from __future__ import print_function, division, absolute_import

import argparse
from collections import MutableSequence, OrderedDict
import json
import logging
import os
from uuid import uuid4

from layerstack import checksum, LayerStackError, start_file_log, TempJsonFilepath
from layerstack.layer import Layer, ModelLayerBase
from layerstack.args import ArgMode


class Stack(MutableSequence):
    """
    A Stack is a list of DiTTo Layers that can be applied to a DiTTo model.

    If all of the sub-layer args are defined, the Stack can be run.

    A Stack may also be an input to an algorithm.
    """

    def __init__(self, *layers, name=None, version='v0.1.0', run_dir=None, model=None):
        self.name = name
        self.version = version
        self.run_dir = run_dir
        self.model = model
        # if loading from disk, this will be overridden
        self.__uuid = uuid4()

        self.__layers = []
        if len(layers):
            for layer in layers:
                self.__checkValue(layer)
            self.__layers.extend(layers)

    @staticmethod
    def __checkValue(value):
        if not isinstance(value, Layer):
            raise LayerStackError("Stacks only hold Layers. You passed a {}."
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
    def suggested_filename(self):
        if self.name is None:
            return None
        return self.name.lower().replace(" ", "_") + ".json"

    @property
    def uuid(self):
        return self.__uuid

    @property
    def layers(self):
        return self.__layers

    @property
    def run_dir(self):
        return self._run_dir

    @run_dir.setter
    def run_dir(self,value):
        self._run_dir = value

    @property
    def runnable(self):
        if not self.run_dir:
            logger.info("The run_dir must be assigned for this stack to be runnable.")
            return False
        for layer in self.layers:
            if not layer.runnable:
                logger.info("Set arguments on layer '{}' to make this stack runnable.".format(layer.name))
                return False
        return True

    def save(self, filename):
        """
        Save this Stack to filename in json format.
        """
        json_data = self._json_data()

        with open(filename, 'w') as f:
            json.dump(json_data, f)

    def archive(self, filename=None):
        """
        Archives this stack by computing the .json checksum on the 
        without-checksum json file, and then saving a json with the checksum 
        data added in. Called by the run method with with default filename 
        os.path.join(self.run_dir, 'stack.archive').
        """
        if filename is None:
            filename = os.path.join(self.run_dir, 'stack.archive')
        with TempJsonFilepath() as tmpjson:
            self.save(tmpjson)
            my_checksum = checksum(tmpjson)
        json_data = self._json_data()
        json_data['checksum'] = my_checksum
        with open(filename, 'w') as f:
            json.dump(json_data, f)

    def _json_data(self):
        json_data = OrderedDict()
        json_data['name'] = self.name
        json_data['uuid'] = self.uuid
        json_data['version'] = self.version
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
                kwarg_dict['nargs'] = kwarg.nargs
                kwarg_dict['list_parser'] = kwarg.list_parser
                kwargs[name] = kwarg_dict
            stack_layers[layer.name] = {'uuid': layer.layer.uuid,
                                        'layer_dir': layer.layer_dir,
                                        'version': layer.layer.version,
                                        'checksum': layer.checksum,
                                        'args': args, 'kwargs': kwargs}

        json_data['layers'] = stack_layers
        return json_data

    @classmethod
    def load(cls, filename, layer_library_dir=None):
        """
        Load a Stack from filename.
        """
        with open(filename) as json_file:
            json_data = json.load(json_file)

        stack_name = json_data['uuid']
        if json_data['name'] is not None:
            stack_name = json_data['name']

        layers = []
        for json_layer in json_data['layers'].values():

            # load each layer, using layer_library_dir if not None
            layer_dir = json_layer['layer_dir']
            if layer_library_dir is not None:
                layer_dir = os.path.join(layer_library_dir,os.path.basename(layer_dir))
            layer = Layer(layer_dir)

            msg_begin = "Layer '{}' loaded by stack '{}' ".format(layer.name,stack_name)

            # inform the user about version changes
            if layer.layer.uuid != json_layer['uuid']:
                logger.warn(msg_begin + 'has unexpected uuid. Expected {}, got {}.'.format(json_layer['uuid'],layer.layer.uuid))
            if layer.layer.version != json_layer['version']:
                logger.info(msg_begin + 'is Version {}, whereas the stack was saved at Version {}.'.format(layer.layer.version,json_layer['version']))
            elif layer.layer.checksum != json_layer['checksum']:
                logger.info(msg_begin + 'has same version identifier as when the stack was saved (Version {}), but the checksum has changed.'.format(layer.layer.version))

            # set arg and kwarg values based on the json file
            for i, arg in enumerate(json_layer['args']):
                value = arg['value']
                if value is not None:
                    layer.args[i].value = value
            kwargs = {}
            for name, kwarg in json_layer['kwargs'].items():
                value = kwarg['value']
                kwargs[name] = value
            layer.kwargs = kwargs

            layers.append(layer)

        result = Stack(*layers, name=json_data['name'], version=json_data['version'], 
                       run_dir=json_data['run_dir'], model=json_data['model'])
        result._uuid = json_data['uuid']
        return result

    def run(self, log_level=logging.INFO, archive=True):
        logger = start_file_log(os.path.join(self.run_dir, 'stack.log'),
                                log_level=log_level)

        if not self.runnable:
            msg = "Stack is not runnable. Be sure run_dir and arguments are set."
            logger.error(msg)
            raise LayerStackError(msg)
        
        if archive:
            self.archive()

        if isinstance(self.model, str):
            layer = self.layers[0]._layer
            if issubclass(layer, ModelLayerBase):
                self.model = layer._load_model(self.model)
            else:
                raise LayerStackError('Layer must be a ModelLayer but is a {:}'
                                      .format(type(Layer)))
        for layer in self.layers:
            if issubclass(layer, ModelLayerBase):
                if self.model is None:
                    raise LayerStackError('Model not initialized')
                logger.info("Running {}".format(layer.name))
                self.model = layer.run_layer(self, model=self.model)
            else:
                self.result = layer.run_layer(self)

        layer = self.layers[-1]._layer
        if issubclass(layer, ModelLayerBase):
            layer._save_model(self.model)

        # Do we need/want to return the model if we are already saving it above?
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
