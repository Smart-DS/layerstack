'''
Contents
--------
- :class:`layerstack.stack.Stack`
- :func:`layerstack.stack.main`

[LICENSE]
Copyright (c) 2019 Alliance for Sustainable Energy, LLC, All Rights Reserved

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
from collections import MutableSequence, OrderedDict
import json
import logging
from pathlib import Path
import os
from timeit import default_timer as timer
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

from layerstack import (LayerStackError, TempJsonFilepath, checksum, 
    start_console_log, start_file_log)
from layerstack.layer import Layer, ModelLayerBase
from layerstack.args import ArgMode, Arg, Kwarg

# TODO:
#  - Convert from using os to using pathlib.Path 
#  - Verify tests pass again
#  - Implement continuous integration -- testing and docs
#  - Implement get_layer_dir
#  - Test implementation of get_layer_dir
#  - Update Stack.load accordingly
#  - Update Stack.main accordingly
#  - Test layer_library_dir functionality as used in main
#  - Iterate on documentation

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
                "objects. You passed a {type(value)}.")                

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

    @staticmethod
    def convert_path(path):
        """
        Convert windows file paths to linux path format

        Parameters
        ----------
        path : str
            file path to convert

        Returns
        -------
        Path
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
            layer.args.mode = arg_mode
            layer.kwargs.mode = arg_mode

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
        json_data['model'] = self.model
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

        assert len(stack_layers) == len(self), "I have {} layers, but \
serialization has {}".format(len(self), len(stack_layers))
        json_data['layers'] = stack_layers
        return json_data

    @classmethod
    def get_layer_dir(cls, layer_dir, layer_library_dirs=[], original_preferred=True):
        """
        Determine the best path to the :class:`layerstack.layer.Layer` indicated 
        by layer_dir, based on the user-provided options. This method may be 
        helpful when :class:`Layers <layerstack.layer.Layer>` and 
        :class:`Stacks <layerstack.stack.Stack>` are used by different people or 
        on different systems.

        Parameters
        ----------
        layer_dir : str or pathlib.Path # (should always be string to avoid issues where first elmt fails)
            Location of the :class:`layerstack.layer.Layer` as originally represented
        layer_library_dirs : list of str or pathlib.Path
            Location(s) where the :class:`layerstack.layer.Layer` may now be 
            found. If multiple locations are provided, it is assumed that they 
            are listed in descending preference order. 
        original_preferred : bool
            If True and the original layer_dir path exists, it will be used 
            directly. If False, the original layer_dir path will only be used if
            the :class:`layerstack.layer.Layer` is not found in any of the 
            locations listed in layer_library_dirs.

        Returns
        -------
        pathlib.Path or None
            If the :class:`layerstack.layer.Layer` is located, its path is 
            returned and pathlib.Path.exists(). Otherwise, a warning is logged
            and None is returned.
        """

        for tmp_dir in layer_library_dirs:
            layer_lib_dir_elmt = Path(tmp_dir)
            if layer_lib_dir_elmt.exists(): 
                layer_dir = layer_lib_dir_elmt / layer_dir.name
                return layer_dir
            else:
                print('Invalid directory specified in directory list. Trying next directory in list.')


    @classmethod
    def load(cls, filename, layer_library_dir=None, original_layer_dir_preferred=True):
        """
        Load stack from given .json file

        Parameters
        ----------
        filename : str or pathlib.Path
            File path from which to load stack
        layer_library_dir : None, str, pathlib.Path, or list of str or pathlib.Path
            If one or more paths are provided, these will be used to locate layer 
            directories listed in the :class:`layerstack.stack.Stack` json file

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

        layers = []

        for json_layer in json_data['layers']:

            layer_dir = Path(json_layer['layer_dir'])

            if layer_library_dir is not None:
                if original_layer_dir_preferred is False:
                    layer_dir = Stack.get_layer_dir(layer_dir, layer_library_dir, original_layer_dir_preferred) # check it
                else:
                    if layer_dir.exists():
                        print('Using original layer-library directory')

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

    def run(self, save_path=None, new_layer_library_dir=None, log_level=logging.INFO, archive=True):
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

        start = timer()
        def timer_str(elapsed_seconds):
            result = ''; sep = ''
            days, remainder = divmod(elapsed_seconds, 60*60*24)
            if days:
                result += sep + f'{days:0.0f} d'; sep = ' '
            hours, remainder = divmod(remainder, 60*60)
            if hours: 
                result += sep + f'{hours:0.0f} h'; sep = ' '
            minutes, remainder = divmod(remainder, 60)
            if minutes:
                result += sep + f'{minutes:0.0f} m'; sep = ' '
            if days or hours:
                result += sep + f'{remainder:0.0f} s'
            elif minutes:
                result += sep + f'{remainder:0.1f} s'
            else:
                result += sep + f'{remainder} s'
            return result

        # change the layer_library_dir 
        lib_check_layer = self.layers[-1].layer
        if new_layer_library_dir is not None:
            lib_check_layer.layer_dir = new_layer_library_dir

        if not self.runnable:
            raise LayerStackError("Stack is not runnable. Be sure run_dir and arguments are set.")

        # get absolute paths
        model_path = None

        if isinstance(self.model, (str, Path)):
            temp_path = Path(self.model).absolute()
            if temp_path.exists():
                model_path = Path(self.model).absolute()

        if save_path is not None:
            save_path = Path(save_path).absolute()

        if not self.run_dir.exists():
            self.run_dir.mkdir()

        old_cur_dir = Path.cwd()
        os.chdir(self.run_dir) 

        # set up logging
        start_file_log('stack.log',log_level=log_level)
        # also archive
        if archive:
            self.archive()

        # #run the stack
        logger.debug('run try-except')
        try:
            if model_path is not None:
                layer = self.layers[0]._layer
                if issubclass(layer, ModelLayerBase):
                    self.model = layer._load_model(model_path)
                    layer._check_model_type(self.model)
                else:
                    raise LayerStackError(f"To use non-None model_path {model_path}, "
                        "Layer must be a ModelLayer, but this Stack's first layer "
                        f"is a {type(layer)}")

            for layer in self.layers:
                logger.info(f"Running {layer.name}")
                if issubclass(layer.layer, ModelLayerBase):
                    if self.model is None:
                        raise LayerStackError('Model not initialized')
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
            os.chdir(old_cur_dir)
            logger.info(f"Stack ran successfully in {timer_str(timer() - start)}")
        except:
            os.chdir(old_cur_dir)
            logger.info(f"Stack failed after {timer_str(timer() - start)}")
            raise        


def repoint_stack(p, layer_library_dir=None, original_layer_dir_preferred=True, run_dir=None, model=None, outfile=None):
    """
    Load Stack from p, update run_dir and/or model, and save to outfile or to the
    same folder but with the file name prepended with an underscore.

    Parameters
    ----------
    p : str
        path to Stack .json file
    lyr_lib_dir : str or None
        layer library directory to use if not specified or if needing to be changed
    run_dir : str or None
        run directory to use
    model : str or None
        path to starting model
    outfile : str or None
        where to save modified stack. If not provided, will save the result to 
        the same directory but with the filename prepended with an underscore
    """

    # layer_library_dir) is either none or is a list of the dirs desired to be passed 
    stack = Stack.load(p, layer_library_dir, original_layer_dir_preferred)
    
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


def main():
    parser = argparse.ArgumentParser("Load and optionally run a stack.")
    parser.add_argument('stack_file', help="""Stack json file to load and optionally a new layer 
        library directory to reassign.""")
    parser.add_argument('-d','--debug', action='store_true', default=False)
    parser.add_argument('-w','--warning-only', action='store_true', default=False)
    
    mode_parsers = parser.add_subparsers(title='mode', dest='mode', help='sub-command')
    parser_list = mode_parsers.add_parser('list')
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
    parser_repoint.add_argument('-ld', '--layer-library-dir', help="""list of layer library 
        directories to use.""") 
    parser_repoint.add_argument('-op', '--original-layer-dir-preferred', help="""Default for this 
        flag is True such that the existing directoryspecified in the stack layer_dir argument is 
        used.""", action='store_true')    

    # run arguments 
    parser_run.add_argument('-ld', '--layer-library-dir', type=str, nargs='+', help="""Default is 
        for this flag to be set to false, in which case the stack uses the existing
        layer_library_dir""")
    parser_run.add_argument('-op', '--original-layer-dir-preferred', help="""Default for this flag 
        is True such that the existing directory
        specified in the stack layer_dir argument is used.""", action='store_true')
    parser_run.add_argument('-sp', '--save-path', help="""Where the results of 
        running this stack should be saved. This is an output path for the 
        stack's final model.""")
    parser_run.add_argument('-a', '--archive', help="""Default is for this 
        flag to be set to true, in which case the stack is archived to the run 
        directory.""", dest='archive', default=True, action='store_true')
    parser_run.add_argument('-na', '--no-archive', help="""Set this flag to 
        turn off stack archiving.""", dest='archive', action='store_false')

    args = parser.parse_args()

    # determine log level
    log_level = logging.INFO
    if args.warning_only:
        log_level = logging.WARNING
    if args.debug:
        log_level = logging.DEBUG

    # start logging
    start_console_log(log_level=log_level)

    if args.mode == 'list':
        stack = Stack.load(args.stack_file)
        print(stack)
    elif args.mode == 'repoint':
        repoint_stack(args.stack_file, 
                      layer_library_dir=args.layer_library_dir,
                      original_layer_dir_preferred=args.original_layer_dir_preferred,
                      run_dir=args.run_dir, 
                      model=args.model_path, 
                      outfile=args.outfile)
    elif args.mode == 'run':
        layer_library_dir_list = args.layer_library_dir
        original_layer_dir_preferred = args.original_layer_dir_preferred
        stack = Stack.load(args.stack_file, layer_library_dir_list, original_layer_dir_preferred)
        stack.run(save_path=args.save_path, log_level=log_level, archive=args.archive)
    else:
        assert False, 'Unknown mode {}'.format(args.mode)
    
    return


if __name__ == '__main__':
    main()
