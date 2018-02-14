from __future__ import print_function, division, absolute_import

import argparse
from collections import MutableSequence, OrderedDict
import json
import logging
import os
from pathlib import Path, PureWindowsPath
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

from layerstack import checksum, LayerStackError, start_file_log, TempJsonFilepath
from layerstack.layer import Layer, ModelLayerBase
from layerstack.args import ArgMode, Arg, Kwarg


class Stack(MutableSequence):
    """
    A Stack is a list of DiTTo Layers that can be applied to a DiTTo model.

    If all of the sub-layer args are defined, the Stack can be run.

    A Stack may also be an input to an algorithm.
    """

    # *layers has to go at the end for Python 2
    def __init__(self, name=None, version='v0.1.0', run_dir=None, model=None,
                 *layers):
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
        logger.debug("Appending Layer {!r}".format(layer.name))
        self.__checkValue(layer)
        self.__layers.append(layer)

    def __str__(self):
        return str(self.__layers)

    def __iter__(self):
        return iter(self.__layers)

    def __len__(self):
        return len(self.__layers)

    @staticmethod
    def convert_path(path):
        if '\\' in path:
            path_parts = PureWindowsPath(path).parts
            path_parts = [part for part in path_parts if part != '\\']
        else:
            path_parts = Path(path)
            path_parts = [part for part in path_parts if part != '/']

        return os.path.join(*path_parts)

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
    def run_dir(self, value):
        self._run_dir = value

    @property
    def runnable(self):
        if not self.run_dir:
            logger.info("The run_dir must be assigned for this stack to be \
runnable.")
            return False
        for layer in self.layers:
            if not layer.runnable:
                logger.info("Set arguments on layer '{}' to make this stack \
runnable.".format(layer.name))
                return False
        return True

    def save(self, filename):
        """
        Save this Stack to filename in json format.
        """
        json_data = self._json_data()

        with open(filename, 'w') as f:
            json.dump(json_data, f, indent=4, separators=(',', ': '))

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
        json_data['uuid'] = str(self.uuid)
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
                arg_dict['parser'] = repr(arg.parser)
                arg_dict['choices'] = arg.choices
                arg_dict['nargs'] = arg.nargs
                arg_dict['list_parser'] = repr(arg.list_parser)
                args.append(arg_dict)

            layer.kwargs.mode = ArgMode.DESC
            kwargs = OrderedDict()
            for name, kwarg in layer.kwargs.items():
                kwarg_dict = OrderedDict()
                kwarg_dict['value'] = kwarg.value
                kwarg_dict['default'] = kwarg.default
                kwarg_dict['description'] = kwarg.description
                kwarg_dict['parser'] = repr(kwarg.parser)
                kwarg_dict['choices'] = kwarg.choices
                kwarg_dict['nargs'] = kwarg.nargs
                kwarg_dict['list_parser'] = repr(kwarg.list_parser)
                kwargs[name] = kwarg_dict

            logger.debug("Serializing Layer {!r}".format(layer.name))
            stack_layers[layer.name] = {'uuid': str(layer.layer.uuid),
                                        'layer_dir': layer.layer_dir,
                                        'version': layer.layer.version,
                                        'checksum': layer.checksum,
                                        'args': args, 'kwargs': kwargs}

        assert len(stack_layers) == len(self), "I have {} layers, but \
serialization has {}".format(len(self), len(stack_layers))
        json_data['layers'] = stack_layers
        return json_data

    @classmethod
    def load(cls, filename, layer_library_dir=None):
        """
        Load a Stack from filename.
        """
        with open(filename) as json_file:
            json_data = json.load(json_file, object_pairs_hook=OrderedDict)

        stack_name = json_data['uuid']
        if json_data['name'] is not None:
            stack_name = json_data['name']

        layers = []
        for json_layer_name, json_layer in json_data['layers'].items():

            # load each layer, using layer_library_dir if not None
            layer_dir = cls.convert_path(json_layer['layer_dir'])
            if layer_library_dir is not None:
                layer_dir = os.path.join(layer_library_dir,
                                         os.path.basename(layer_dir))
            layer = Layer(layer_dir)

            msg_begin = "Layer {!r} loaded by Stack {!r} ".format(layer.name,
                                                                  stack_name)

            # inform the user about version changes
            if layer.layer.uuid != UUID(json_layer['uuid']):
                logger.warn(msg_begin +
                            'has unexpected uuid. Expected {!r}, got {!r}.'
                            .format(UUID(json_layer['uuid']),
                                    layer.layer.uuid))
            if layer.name != json_layer_name:
                logger.info(msg_begin +
                            'has different serialized name, {!r}'
                            .format(json_layer_name))
            if layer.layer.version != json_layer['version']:
                logger.info(msg_begin + 'is Version {}, whereas the stack was \
saved at Version {}.'.format(layer.layer.version, json_layer['version']))
            elif layer.checksum != json_layer['checksum']:
                logger.info(msg_begin + 'has same version identifier as when \
the stack was saved (Version {}), but the checksum has \
changed.'.format(layer.layer.version))

            # set arg and kwarg values based on the json file

            # try to handle shifts in argument order and naming
            actual_args = {}
            for i, arg in enumerate(layer.args):
                actual_args[arg.name] = i
            nargs = len(layer.args)

            assigned_args = []
            unassigned_sargs = []
            serialized_to_actual_map = OrderedDict()
            for i, arg in enumerate(json_layer['args']):
                if (i < nargs) and (i not in assigned_args) and (layer.args[i].name == arg['name']):
                    serialized_to_actual_map[i] = i
                    assigned_args.append(i)
                    continue
                # not a full match -- next try name
                if (arg['name'] in actual_args) and (actual_args[arg['name']] not in assigned_args):
                    serialized_to_actual_map[i] = actual_args[arg['name']]
                    assigned_args.append(actual_args[arg['name']])
                    logger.info("Position of Layer {!r} argument {!r} moved \
from {} to {} since serialization of Stack {!r}."
                                .format(layer.name, arg['name'], i,
                                        actual_args[arg['name']], stack_name))
                    continue
                serialized_to_actual_map[i] = None
                unassigned_sargs.append(i)
            for i in unassigned_sargs:
                # there was no full match and no name match for this argument
                if (i < nargs) and (i not in assigned_args):
                    serialized_to_actual_map[i] = i
                    assigned_args.append(i)
                    logger.warn("Setting the value of Layer {!r}s {}'th \
argument based on argument in same position in Stack {!r} even though names \
are different. Serialized argument name: {!r} Current argument name: {!r}"
                                .format(layer.name, i, stack_name,
                                        json_layer['args'][i]['name'],
                                        layer.args[i].name))
                    continue
                logger.warn("Argument {!r}'s serialized information will not \
be used in loading Layer {!r} in Stack {!r}.".format(json_layer['args'][i],
                                                     layer.name, stack_name))

            for i, j in serialized_to_actual_map.items():
                if j is not None:
                    try:
                        layer.args[j].value = json_layer['args'][i]['value']
                    except Exception as e:
                        logger.error("Unable to set the value of Layer {!r}'s \
{}'th argument {!r} to {}, because {}."
                                     .format(layer.name, j, layer.args[j].name,
                                             json_layer['args'][i]['value'],
                                             e))

            for name, kwarg in json_layer['kwargs'].items():
                if name in layer.kwargs:
                    try:
                        layer.kwargs[name].value = kwarg['value']
                    except Exception as e:
                        logger.error("Unable to set the value of Layer {!r}'s \
kwarg {!r} to {}, because {}.".format(layer.name, name, kwarg['value'], e))
                else:
                    logger.warn("Kwarg {!r} is no longer in Layer {!r}, so the\
 information serialized for it in Stack {!r} will not be used."
                                .format(name, layer.name, stack_name))

            layers.append(layer)

        logger.debug("Instantiating Stack with\n  name: {!r}\n version: \
{!r}\n  run_dir: {!r}\n  model: {!r}"
                     .format(json_data['name'], json_data['version'],
                             json_data['run_dir'], json_data['model']))
        result = Stack(name=json_data['name'], version=json_data['version'],
                       run_dir=json_data['run_dir'], model=json_data['model'],
                       *layers)
        result._uuid = UUID(json_data['uuid'])
        return result

    def run(self, save_path=None, log_level=logging.INFO, archive=True):
        logger = start_file_log(os.path.join(self.run_dir, 'stack.log'),
                                log_level=log_level)

        if not self.runnable:
            msg = "Stack is not runnable. Be sure run_dir and arguments are \
set."
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
            logger.info("Running {}".format(layer.name))
            if issubclass(layer, ModelLayerBase):
                if self.model is None:
                    raise LayerStackError('Model not initialized')
                self.model = layer.run_layer(self, model=self.model)
            else:
                self.result = layer.run_layer(self)

        if save_path is not None:
            layer = self.layers[-1]._layer
            if issubclass(layer, ModelLayerBase):
                layer._save_model(self.model)
            else:
                raise LayerStackError('Layer must be a ModelLayer but is a {:}'
                                      .format(type(Layer)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Load and optionally run a stack.")
    parser.add_argument('stack_file', help="Stack json file to load.")
    mode_parsers = parser.add_subparsers('mode')
    mode_parsers.add_parser('list')
    mode_parsers.add_parser('run')
    mode_parsers.add_parser('save')

    args = parser.parse_args()

    stack = Stack.load(args.stack_file)
