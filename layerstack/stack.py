from __future__ import print_function, division, absolute_import

import argparse
from collections import MutableSequence, OrderedDict
import json
import logging
import os
from pathlib import Path
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

from layerstack import checksum, LayerStackError, start_file_log, TempJsonFilepath
from layerstack.layer import Layer, ModelLayerBase
from layerstack.args import ArgMode, Arg, Kwarg


class Stack(MutableSequence):
    """
    Base class to handle and run layer sequences
    - Save to json
    - Load from json
    - Run

    Attributes
    ----------
    name : 'str'
        Stack name
    version : 'str'
        Stack version
    run_dir : 'str'
        Run directory for stack
    model
        Model to apply layers to
    __uuid : 'uuid4'
        Unique identifier for stack
    __layers : 'list'
        List of layers in stack

    Parameters
    ----------
    layers : 'list'
        List of layers in stack
    name : 'str'
        name of stack
    version : 'str'
        stack version number
    run_dir : 'str'
        directory to run stack in
    model
        Model to apply layers to
    """

    # *layers has to go at the end for Python 2
    def __init__(self, layers=[], name=None, version='v0.1.0', run_dir=None,
                 model=None):
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
        """
        Check to ensure value is a Layer class object

        Parameters
        ----------
        value : 'Layer'
            New layer to add to stack
        """
        if not isinstance(value, Layer):
            raise LayerStackError("Stacks only hold Layers. You passed a {}."
                                  .format(type(value)))

    def __getitem__(self, i):
        """
        Get layer i

        Parameters
        ----------
        i : 'int'
            position of layer to get from stack

        Returns
        -------
        'Layer'
            Layer class for layer i in stack
        """
        return self.__layers[i]

    def __setitem__(self, i, layer):
        """
        Set ith layer in stack

        Parameters
        ----------
        i : 'int'
            position of layer to set in stack
        layer : 'Layer'
            Layer to place at ith position in stack
        """
        self.__checkValue(layer)
        self.__layers.insert(i, layer)

    def __delitem__(self, i):
        """
        Delete ith layer

        Parameters
        ----------
        i : 'int'
            Position of layer to delete
        """
        del self.__layers[i]

    def insert(self, i, layer):
        """
        Insert layer into stack

        Parameters
        ----------
        i : 'int'
            Position at which to insert layer
        layer : 'Layer'
            Layer to insert into stack
        """
        self.__checkValue(layer)
        self.__layers.insert(i, layer)

    def append(self, layer):
        """
        Append layer to end of stack

        Parameters
        ----------
        layer : 'Layer'
            Layer to append to end of stack
        """
        logger.debug("Appending Layer {!r}".format(layer.name))
        self.__checkValue(layer)
        self.__layers.append(layer)

    def __str__(self):
        """
        Return readable list for layers in stack

        Returns
        -------
        'str'
            Readable string of layers in stack
        """
        return str(self.__layers)

    def __iter__(self):
        """
        Create iterable of layers in stack

        Returns
        -------
        'iter'
            Iterable for layers in stack
        """
        return iter(self.__layers)

    def __len__(self):
        """
        Number of layers in stack

        Returns
        -------
        'int'
            Number of layers in stack
        """
        return len(self.__layers)

    @staticmethod
    def convert_path(path):
        """
        Convert windows file paths to linux path format

        Parameters
        ----------
        path : 'str'
            file path to convert

        Returns
        -------
        'Path'
            Path class object to handle file path
        """
        if '\\' in path:
            path = path.replace('\\', '/')

        return Path(path)

    @property
    def suggested_filename(self):
        """
        Create stack filename

        Returns
        -------
        'str'
            Stack json name
        """
        if self.name is None:
            return None
        return self.name.lower().replace(" ", "_") + ".json"

    @property
    def uuid(self):
        """
        Get stack uuid

        Returns
        -------
        'uuid4'
            Stack unique identifier
        """
        return self.__uuid

    @property
    def layers(self):
        """
        Get layers in stack

        Returns
        -------
        'list'
            List of layers in stack
        """
        return self.__layers

    @property
    def run_dir(self):
        """
        Get stack run directory

        Returns
        -------
        'str'
            Run directory for stack
        """
        return self._run_dir

    @run_dir.setter
    def run_dir(self, value):
        """
        Set run directory for stack

        Parameters
        ----------
        value : 'str'
            Stack run directory
        """
        self._run_dir = value

    @property
    def runnable(self):
        """
        Determine if stack is runnable:
        - Are args set for all layers in stack

        Returns
        -------
        'bool'
            All args are set for all layers in stack, stack can be run
        """
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
        Save stack

        Parameters
        ----------
        filename : 'str'
            file path to save stack to
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

        Parameters
        ----------
        filename : 'str'
            file path to save stack to
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
        """
        Extract data from stack and place in json format

        Returns
        -------
        json_data : 'dict'
            Dictionary containing stack information:
            - stack meta data
            - layers in stack
                - layer meta data
                - layer args
                - layer kwargs
        """
        json_data = OrderedDict()
        json_data['name'] = self.name
        json_data['uuid'] = str(self.uuid)
        json_data['version'] = self.version
        json_data['run_dir'] = self.run_dir
        json_data['model'] = self.model
        stack_layers = []
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
            stack_layers.append({
                'name': layer.name,
                'uuid': str(layer.layer.uuid),
                'layer_dir': str(layer.layer_dir),
                'version': layer.layer.version,
                'checksum': layer.checksum,
                'args': args, 'kwargs': kwargs})

        assert len(stack_layers) == len(self), "I have {} layers, but \
serialization has {}".format(len(self), len(stack_layers))
        json_data['layers'] = stack_layers
        return json_data

    @classmethod
    def load(cls, filename, layer_library_dir=None):
        """
        Load stack from given .json file

        Parameters
        ----------
        filename : 'str'
            File path from which to load stack
        layer_library_dir : 'str'
            Root directory containing layers to be loaded into stack

        Returns
        -------
        result : 'Stack'
            Instantiated Stack class instance
        """
        with open(filename) as json_file:
            json_data = json.load(json_file, object_pairs_hook=OrderedDict)

        stack_name = json_data['uuid']
        if json_data['name'] is not None:
            stack_name = json_data['name']

        layers = []
        for json_layer in json_data['layers']:

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
            if layer.name != json_layer['name']:
                logger.info(msg_begin +
                            'has different serialized name, {!r}'
                            .format(json_layer['name']))
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

        result = cls(layers=layers, name=json_data['name'],
                     version=json_data['version'],
                     run_dir=json_data['run_dir'], model=json_data['model'])
        result._uuid = UUID(json_data['uuid'])
        return result

    def run(self, save_path=None, log_level=logging.INFO, archive=True):
        """
        Run stack

        Parameters
        ----------
        save_path : 'str'
            Path to which results from running stack should be saved
        log_level : 'logging'
            Level of logging to be used while running stack
        archive : 'bool'
            Archive stack before running
        """
        if not self.runnable:
            msg = "Stack is not runnable. Be sure run_dir and arguments are \
set."
            logger.error(msg)
            raise LayerStackError(msg)

        if not os.path.exists(self.run_dir):
            os.mkdir(self.run_dir)

        start_file_log(os.path.join(self.run_dir, 'stack.log'),
                       log_level=log_level)

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
            if issubclass(layer.layer, ModelLayerBase):
                if self.model is None:
                    raise LayerStackError('Model not initialized')
                self.model = layer.run_layer(self, model=self.model)
            else:
                self.result = layer.run_layer(self)

        if save_path is not None:
            layer = self.layers[-1].layer
            if issubclass(layer, ModelLayerBase):
                layer._save_model(self.model)
            else:
                raise LayerStackError('Layer must be a ModelLayer but is a {:}'
                                      .format(type(layer)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Load and optionally run a stack.")
    parser.add_argument('stack_file', help="Stack json file to load.")
    mode_parsers = parser.add_subparsers('mode')
    mode_parsers.add_parser('list')
    mode_parsers.add_parser('run')
    mode_parsers.add_parser('save')

    args = parser.parse_args()

    stack = Stack.load(args.stack_file)
