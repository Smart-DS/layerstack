'''
layerstack.stack
----------------
- :class:`layerstack.stack.Stack`
- :func:`layerstack.stack.main`

:copyright: (c) 2021, Alliance for Sustainable Energy, LLC
:license: BSD-3
'''
from __future__ import print_function, division, absolute_import

import argparse
from collections import OrderedDict
from collections.abc import MutableSequence
import json
import logging
from pathlib import Path
from os import chdir
from timeit import default_timer as timer
from uuid import UUID, uuid4
import sys

logger = logging.getLogger(__name__)

from layerstack import (LayerStackError, TempJsonFilepath, checksum, 
    start_console_log, start_file_log, end_file_log, timer_str)
from layerstack.layer import Layer, ModelLayerBase
from layerstack.args import ArgMode, Arg, Kwarg


class Stack(MutableSequence):
    """
    Class to create, edit, save, load, and run workflows stored as sequences of 
    :class:`Layers <layerstack.layer.Layer>`. 

    Stacks are serialized to .json files. Loading and running them is contingent
    upon being able to locate the :class:`Layers <layerstack.layer.Layer>` in 
    the current environment.

    Stacks are run in a specified directory, but at this time provide little 
    scaffolding as far as what contents are ultimately saved to that directory.
    """

    def __init__(self, layers=[], name=None, version='v0.1.0', run_dir=None,
                 model=None):
        """
        Parameters
        ----------
        layers : list of :class:`layerstack.layer.Layer`
            List of layers in stack
        name : str
            name of stack
        version : str
            stack version number
        run_dir : None, str, or pathlib.Path
            directory to run stack in
        model : None, str, or other
            Model to apply layers to, if applicable. Can be None, an object, or 
            a path to a serialized model.
        """

        #: str: stack name
        self.name = name
        
        #: str: stack version
        self.version = version
        
        #: None or str: run directory for the stack
        self.run_dir = run_dir

        #: None, str, or other: Model to apply layers to, if applicable. 
        #: Upon initialization, Stack.model may be None or a str path pointing 
        #: to where a model exists that may be loaded. Stack relies on Layers 
        #: that implement the :class:`ModelLayerBase <layerstack.layer.ModelLayerBase>` 
        #: interface for model loading and saving.
        self.model = model

        #: uuid.uuid4: unique identifier for the stack. Initialized in __init__, 
        #: but if loading from disk, the newly created UUID will be overridden.
        self.__uuid = uuid4()

        #: list of :class:`layerstack.layer.Layer`
        self.__layers = []
        if len(layers):
            for layer in layers:
                self.__checkLayer(layer)
            self.__layers.extend(layers)

    @staticmethod
    def __checkLayer(value):
        """
        Check to ensure value is a Layer class object

        Parameters
        ----------
        value : Layer
            New layer to add to stack
        """
        if not isinstance(value, Layer):
            raise LayerStackError("Stacks only hold layerstack.layer.Layer "
                f"objects. You passed a {type(value)}.")                

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
        self.__checkLayer(layer)
        # ETH@20200901 - This was self.__layers.insert(i, layer), but we have 
        # an insert method, so changing this to behave more as expected
        self.__layers[i] = layer

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
        self.__checkLayer(layer)
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
        self.__checkLayer(layer)
        self.__layers.append(layer)

    def __str__(self):
        """
        Return readable description of this stack

        Returns
        -------
        str
        """
        result = '{}, v{}\n'.format(self.name, 
                                    self.version[1:] if self.version.startswith(('v','V')) else self.version)
        result += 'runnable\n' if self.runnable else 'NOT runnable\n'
        result += "run_dir: '{}'\n".format(self.run_dir)
        result += "model: '{}'\n".format(self.model)
        json_data = self._json_data()
        result += 'layers:\n'
        result += json.dumps(json_data['layers'], indent=4, separators=(',', ': '))
        return result

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
        None or pathlib.Path
            Run directory for stack
        """
        return self._run_dir 

    @run_dir.setter
    def run_dir(self, value):
        """
        Set run directory for stack

        Parameters
        ----------
        value : None, str, or pathlib.Path
            Stack run directory
        """
        self._run_dir = value if value is None else Path(value) 

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
            logger.info("The run_dir must be assigned for this stack to be runnable.")
            return False
        for layer in self.layers:
            if not layer.runnable:
                logger.info(f"Set arguments on layer '{layer.name}' to make this stack runnable.")
                return False
        return True

    def set_arg_mode(self, arg_mode):
        """
        Convenience function for setting all args and kwargs objects to the same
        ArgMode.
        """
        for layer in self.layers:
            layer.set_arg_mode(arg_mode)

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

        return

    def archive(self, filename=None):
        """
        Archives this stack by computing the .json checksum on the
        without-checksum json file, and then saving a json with the checksum
        data added in. Called by the run method with with default filename
        self.run_dir / 'stack.archive'.

        Parameters
        ----------
        filename : 'str'
            file path to save stack to
        """
        if filename is None:
            filename = self.run_dir / 'stack.archive' 
        with TempJsonFilepath() as tmpjson:
            self.save(tmpjson)
            my_checksum = checksum(tmpjson)
        json_data = self._json_data()
        json_data['checksum'] = my_checksum
        with open(filename, 'w') as f:
            json.dump(json_data, f, indent=4, separators=(',', ': '))

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
        json_data['run_dir'] = str(self.run_dir) # convert to str due to Path JSON issue
        json_data['model'] = str(self.model) # model can be all sorts of things--write out as str
        stack_layers = []
        for layer in self.layers:
            layer.args.mode = ArgMode.DESC
            args = []
            for arg in layer.args:
                arg_dict = OrderedDict()
                arg_dict['name'] = arg.name
                if arg.set:
                    arg_dict['value'] = arg.value_to_save
                else:
                    arg_dict['value'] = None
                arg_dict['description'] = arg.description
                arg_dict['parser'] = repr(arg.parser)
                arg_dict['choices'] = arg.choices_to_save
                arg_dict['nargs'] = arg.nargs
                arg_dict['list_parser'] = repr(arg.list_parser)
                args.append(arg_dict)

            layer.kwargs.mode = ArgMode.DESC
            kwargs = OrderedDict()
            for name, kwarg in layer.kwargs.items():
                kwarg_dict = OrderedDict()
                kwarg_dict['value'] = kwarg.value_to_save
                kwarg_dict['default'] = kwarg.default_to_save
                kwarg_dict['description'] = kwarg.description
                kwarg_dict['parser'] = repr(kwarg.parser)
                kwarg_dict['choices'] = kwarg.choices_to_save
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

        assert len(stack_layers) == len(self), f"I have {len(self)} layers, but serialization has {len(stack_layers)}"
        json_data['layers'] = stack_layers
        return json_data

    @classmethod
    def get_layer_dir(cls, layer_dir, layer_library_dirs=[], original_preferred=True, hard_fail=False):
        """
        Determine the best path to the :class:`layerstack.layer.Layer` indicated 
        by layer_dir, based on the user-provided options. This method may be 
        helpful when :class:`Layers <layerstack.layer.Layer>` and 
        :class:`Stacks <layerstack.stack.Stack>` are used by different people or 
        on different systems.

        Parameters
        ----------
        layer_dir : str or pathlib.Path
            Location of the :class:`layerstack.layer.Layer` as originally 
            represented
        layer_library_dirs : list of str or pathlib.Path
            Location(s) where the :class:`layerstack.layer.Layer` may now be 
            found. If multiple locations are provided, it is assumed that they 
            are listed in descending preference order. 
        original_preferred : bool
            If True and the original layer_dir path exists, it will be used 
            directly. If False, the original layer_dir path will only be used if
            the :class:`layerstack.layer.Layer` is not found in any of the 
            locations listed in layer_library_dirs.
        hard_fail : bool
            If True, raises LayerStackError if the layer cannot be located.

        Returns
        -------
        pathlib.Path or None
            If the :class:`layerstack.layer.Layer` is located, its path is 
            returned and pathlib.Path.exists(). Otherwise, a warning is logged
            and None is returned, unless hard_fail, in which case a 
            LayerStackError is raised instead.

        Raises
        ------
        LayerStackError
            If the :class:`layerstack.layer.Layer` cannot be located and 
            hard_fail is True.
        """
        layer_dir = Path(layer_dir)

        candidate_locations = [Path(dirname) for dirname in layer_library_dirs]
        if original_preferred:
            candidate_locations.insert(0, layer_dir.parent)
        else:
            candidate_locations.append(layer_dir.parent)

        for candidate_location in candidate_locations:
            candidate = candidate_location / layer_dir.name
            if candidate.exists():
                return candidate
        
        msg = (f"Unable to find the layer {layer_dir.name} in any of the locations\n  " +
            "\n  ".join([str(candidate_location) for candidate_location in candidate_locations]))
        if hard_fail:
            raise LayerStackError(msg)
        logger.warning(msg)
        return None


    @classmethod
    def load(cls, filename, layer_library_dir=None, original_locations_preferred=True):
        """
        Load stack from given .json file

        Parameters
        ----------
        filename : str or pathlib.Path
            .json file path from which to load :class:`layerstack.stack.Stack`
        layer_library_dir : None, str, pathlib.Path, or list of str or pathlib.Path
            If one or more paths are provided, these will be used to locate layer 
            directories listed in the :class:`layerstack.stack.Stack` json file. 
            If multiple directories are provided, they will be checked in order.
        original_locations_preferred : bool
            If True, the original locations of the layers listed in the 
            :class:`layerstack.stack.Stack` json file will be preferred and use
            if they exist on the current file system. If False, any location(s) 
            passed in through layer_library_dir will be preferred and checked 
            first

        Returns
        -------
        result : Stack
            Instantiated Stack class instance
        """

        with open(filename) as json_file:
            json_data = json.load(json_file, object_pairs_hook=OrderedDict)

        stack_name = json_data['uuid']
        if json_data['name'] is not None:
            stack_name = json_data['name']

        # list of places where we will look for Layers
        layer_library_dirs = [] 
        if layer_library_dir is not None:
            if isinstance(layer_library_dir, (str, Path)):
                layer_library_dirs.append(layer_library_dir)
            else:
                try:
                    layer_library_dirs = [Path(dirname) for dirname in layer_library_dir]
                except Exception as e:
                    raise LayerStackError(f"Unexpected layer_library_dir = {layer_library_dir}. "
                        f"Was expecting str, pathlib.Path, or list thereof. Failed because, {e}.")

        # now process each layer
        layers = []
        for json_layer in json_data['layers']:

            layer_dir = cls.get_layer_dir(
                json_layer['layer_dir'], 
                layer_library_dirs = layer_library_dirs, 
                original_preferred = original_locations_preferred,
                hard_fail=True)

            layer = Layer(layer_dir)

            msg_begin = f"Layer {layer.name!r} loaded by Stack {stack_name!r} "

            # inform the user about version changes
            # TODO: Continue streamlining log text
            expected_uuid = UUID(json_layer['uuid'])
            if layer.layer.uuid != expected_uuid:
                logger.warning(f"{msg_begin} has unexpected uuid. Expected "
                    f"{expected_uuid!r}, got {layer.layer.uuid!r}.")
            if layer.name != json_layer['name']:
                logger.info(f"{msg_begin} has different serialized name, got {json_layer['name']!r}.")
            if layer.layer.version != json_layer['version']:
                logger.info(f"{msg_begin} is Version {layer.layer.version}, whereas the stack was "
                f"saved at Version {json_layer['version']}.")
            elif layer.checksum != json_layer['checksum']:
                logger.info(f"{msg_begin} has same version identifier as when the stack was saved"
                f"(Version {layer.layer.version!r}), but the checksum has changed.")

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
                    logger.info(f"{msg_begin} Position of Layer {layer.name!r} argument {arg['name']!r} moved "
                        f"from {i} to {actual_args[arg['name']]!r} since serialization of Stack {stack_name!r}.")
                    continue
                serialized_to_actual_map[i] = None
                unassigned_sargs.append(i)
            for i in unassigned_sargs:
                # there was no full match and no name match for this argument
                if (i < nargs) and (i not in assigned_args):
                    serialized_to_actual_map[i] = i
                    assigned_args.append(i)
                    logger.warn(f"{msg_begin} Setting the value of Layer {layer.name!r}s {i}'th "
                        f"argument based on argument in same position in Stack {stack_name!r} even "
                        f"though names are different. Serialized argument name: "
                        f"{json_layer['args'][i]['name']!r} Current argument name: {layer.args[i].name!r}.")
                    continue
                logger.warn(f"{msg_begin} Argument {json_layer['args'][i]!r}'s serialized information "
                    f"won't be used in loading Layer {layer.name!r} in Stack {stack_name!r}.")

            for i, j in serialized_to_actual_map.items():
                if j is not None:
                    try:
                        layer.args[j].value = json_layer['args'][i]['value']
                    except Exception as e:
                        logger.error(f"{msg_begin} Unable to set the value of Layer {layer.name!r}'s "
                        f"{j}'th argument {layer.args[j].name!r} to "
                        f"{json_layer['args'][i]['value']!r}, because {e}.")

            for name, kwarg in json_layer['kwargs'].items():
                if name in layer.kwargs:
                    try:
                        layer.kwargs[name].value = kwarg['value']
                    except Exception as e:
                        logger.error(f"{msg_begin} Unable to set the value of Layer {layer.name!r}'s "
                        f"kwarg {name!r} to {kwarg['value']}, because {e}.")
                else:
                    logger.warn(f"{msg_begin} Kwarg {name!r} is no longer in Layer {layer.name!r}, so "
                    f"the information serialized for it in Stack {stack_name!r} will not be used.")

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
        save_path : str
            Path to which results from running stack should be saved
        log_level : logging
            Level of logging to be used while running stack
        archive : bool
            Archive stack before running
        """
        start = timer()

        if not self.runnable:
            raise LayerStackError("Stack is not runnable. Be sure run_dir and arguments are set.")

        # get absolute paths
        model_path = None

        if isinstance(self.model, (str, Path)):
            model_path = Path(self.model)
            if model_path.exists():
                model_path = model_path.absolute()

        if save_path is not None:
            save_path = Path(save_path).absolute()

        # set up and switch into the run directory
        if not self.run_dir.exists():
            self.run_dir.mkdir()

        old_cur_dir = Path.cwd()
        chdir(self.run_dir) 

        # set up logging
        logfile = start_file_log('stack.log',log_level=log_level)
        # also archive
        if archive:
            self.archive()

        # run the stack
        try:
            if self.model is not None:
                layer = self.layers[0]._layer
                if issubclass(layer, ModelLayerBase):
                    if model_path is not None:
                        self.model = layer._load_model(model_path)
                    layer._check_model_type(self.model)
                else:
                    raise LayerStackError(f"To use non-None model {self.model}, "
                        "Layer must be a ModelLayer, but this Stack's first layer "
                        f"is a {type(layer)}")

            for layer in self.layers:
                logger.info(f"Running {layer.name!r} layer")
                if issubclass(layer.layer, ModelLayerBase):
                    self.model = layer.run_layer(self, model=self.model)
                else:
                    self.result = layer.run_layer(self)

            if save_path is not None:
                layer = self.layers[-1].layer
                if issubclass(layer, ModelLayerBase):
                    layer._save_model(self.model, save_path)
                else:
                    raise LayerStackError(f"To use non-None save_path {save_path}, "
                        "Layer must be a ModelLayer, but this Stack's last Layer "
                        f"is a {type(layer)}")

            # switch back to initial directory
            chdir(old_cur_dir)
            logger.info(f"Stack ran successfully in {timer_str(timer() - start)}")
            end_file_log(logfile)
        except:
            chdir(old_cur_dir)
            logger.error(f"Stack failed after {timer_str(timer() - start)}")
            end_file_log(logfile)
            raise        


def repoint_stack(p, layer_library_dir=None, original_locations_preferred=True, 
                  run_dir=None, model=None, outfile=None):
    """
    Load Stack from p, update run_dir and/or model, and save to outfile or to the
    same folder but with the file name prepended with an underscore.

    Parameters
    ----------
    p : str
        path to Stack .json file
    layer_library_dir : None, str, pathlib.Path, or list of str or pathlib.Path
        If one or more paths are provided, these will be used to locate layer 
        directories listed in the :class:`layerstack.stack.Stack` json file. 
        If multiple directories are provided, they will be checked in order.
    original_locations_preferred : bool
        If True, the original locations of the layers listed in the 
        :class:`layerstack.stack.Stack` json file will be preferred and use
        if they exist on the current file system. If False, any location(s) 
        passed in through layer_library_dir will be preferred and checked 
        first
    run_dir : str or None
        run directory to use
    model : str or None
        path to starting model
    outfile : str or None
        where to save modified stack. If not provided, will save the result to 
        the same directory but with the filename prepended with an underscore
    """
    stack = Stack.load(p, 
        layer_library_dir=layer_library_dir, 
        original_locations_preferred=original_locations_preferred)
    
    if run_dir is not None:
        stack.run_dir = run_dir
    if model is not None:
        stack.model = model

    filepath = outfile
    if filepath is None:
        orig_p = Path(p)
        filepath = orig_p.parent / ('_' + orig_p.name)

    stack.save(filepath)
    
    return    


def parse_args_helper(args):
    parser = argparse.ArgumentParser("Load and optionally run a stack.")
    
    # all CLI options require loading a Stack json file
    parser.add_argument('stack_file', help="""Stack json file to load""")
    parser.add_argument('-ld', '--layer-library-dirs', help="""List of layer 
        parent directories where the layers listed in the Stack .json file may 
        be found on this file system.""", nargs='*') 
    parser.add_argument('-nop', '--non-original-locations-preferred', 
        help="""Set this flag if the original layer locations listed in the 
            .json file should be checked last instead of first (after the 
            layer-library-dirs instead of before).""", 
        action='store_false', dest='original_locations_preferred')
    parser.set_defaults(original_locations_preferred=True)

    # all CLI options also involve configuring logging (at least console)
    parser.add_argument('-d','--debug', action='store_true', default=False)
    parser.add_argument('-w','--warning-only', action='store_true', default=False)

    # CLI options    
    mode_parsers = parser.add_subparsers(title='mode', dest='mode', help='sub-command')
    _parser_list = mode_parsers.add_parser('list')
    parser_repoint = mode_parsers.add_parser('repoint')
    parser_run = mode_parsers.add_parser('run')

    # repoint arguments
    parser_repoint.add_argument('-o', '--outfile', help="""Where to save the 
        modified stack. By default, will be saved in the same location with '_' 
        added as a prefix to the filename.""")
    parser_repoint.add_argument('-rd', '--run-dir', help="""Where this stack 
        should be run.""")
    parser_repoint.add_argument('-mp', '--model-path', help="""Model this stack 
        should be run on.""")

    # run arguments 
    parser_run.add_argument('-sp', '--save-path', help="""Where the results of 
        running this stack should be saved. This is an output path for the 
        stack's final model.""")
    parser_run.add_argument('-na', '--no-archive', help="""Set this flag to 
        turn off stack archiving.""", dest='archive', action='store_false')
    parser_run.set_defaults(archive=True)

    return parser.parse_args(args)


def main():

    args = parse_args_helper(sys.argv[1:])

    # determine log level
    log_level = logging.INFO
    if args.warning_only and (args.mode != 'list'):
        log_level = logging.WARNING
    if args.debug:
        log_level = logging.DEBUG

    # start logging
    start_console_log(log_level=log_level)

    if args.mode == 'list':
        stack = Stack.load(
            args.stack_file, 
            layer_library_dir=args.layer_library_dirs, 
            original_locations_preferred=args.original_locations_preferred)
        logger.info(f"Stack loaded from {args.stack_file}:\n{stack}")
    elif args.mode == 'repoint':
        repoint_stack(args.stack_file, 
                      layer_library_dir=args.layer_library_dir,
                      original_locations_preferred=args.original_locations_preferred,
                      run_dir=args.run_dir, 
                      model=args.model_path, 
                      outfile=args.outfile)
    elif args.mode == 'run':
        stack = Stack.load(
            args.stack_file, 
            layer_library_dir=args.layer_library_dirs, 
            original_locations_preferred=args.original_locations_preferred)
        stack.run(save_path=args.save_path, log_level=log_level, archive=args.archive)
    else:
        assert False, f'Unknown mode {args.mode}'
    
    return
    

if __name__ == '__main__':
    main()
