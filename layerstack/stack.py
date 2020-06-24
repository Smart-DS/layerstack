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
import os
from pathlib import Path
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

from layerstack import (LayerStackError, TempJsonFilepath, checksum, 
    start_console_log, start_file_log)
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

    Attributes
    ----------
    name : str
        Stack name
    version : str
        Stack version
    run_dir : str
        Run directory for stack
    model : None, str, *
        Optional model layers are being applied to. Upon initialization, 
        Stack.model may be None or a str path pointing to where a model exists 
        that may be loaded. Stack relies on Layers that implement the 
        :class:`ModelLayerBase <layerstack.layer.ModelLayerBase>` interface for 
        model loading and saving.
    __uuid : 'uuid4'
        Unique identifier for stack
    __layers : 'list'
        List of layers in stack

    Parameters
    ----------
    layers : list
        List of layers in stack
    name : str
        name of stack
    version : str
        stack version number
    run_dir : str
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

        return

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

# *** TLS thoughts, 5.14.20 ***
# if filename is needed then I think issue 14 pertaining to the layer_library_dir may be a separate task from the directory search elaine mentioned, unless
# filename is made optional or is removed and the load function is changed such that when opening the layer file it will always search through a passed
# list of layer directories and there repsective nested layer filenames


# *** TLS: Revised Thoughts after check-in w/ Elaine ***
# the layer_library_dir arg should always be passed and handled such that the layer directory is repointed when load is called and layerstack is run in CLI
# use nargs + functionality within the load function; add some additional code to main()


    @classmethod
    def load(cls, filename, layer_library_dir=None):
    #def load(cls, run_list):
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

        # change the layer_library_dir 
        lib_check_layer = self.layers[-1].layer
        if new_layer_library_dir is not None:
            lib_check_layer.layer_dir = new_layer_library_dir

        if not self.runnable:
            msg = "Stack is not runnable. Be sure run_dir and arguments are set."
            logger.error(msg)
            raise LayerStackError(msg)

        # get absolute paths
        model_path = None

        if isinstance(self.model, (str, Path)):
            temp_path = Path(self.model).absolute()
            if temp_path.exists():
                model_path = Path(self.model).absolute()

        if save_path is not None:
            save_path = Path(save_path).absolute()

        if not os.path.exists(self.run_dir):
            os.mkdir(self.run_dir)

        # change directory to run_dir
        old_cur_dir = os.getcwd()
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
                    layer._save_model(self.model, save_path)
                else:
                    raise LayerStackError('Layer must be a ModelLayer but is a {:}'
                                        .format(type(layer)))
            # switch back to initial directory
            os.chdir(old_cur_dir)
        except:
            os.chdir(old_cur_dir)
            raise        


def repoint_stack(p, layer_library_dir=None, run_dir=None, model=None, outfile=None):
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

    stack = Stack.load(p, layer_library_dir)
    
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
    # TLS 5.29.20 - per 5.21 meeting, will implement a flag to either use the path specified in the device set JSON or to use
    # a new library_dir path that is passed in at runtime in the CLI  
    parser.add_argument('stack_file', help="Stack json file to load and optionally a new layer library directory to reassign.")
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
    # TLS 5.29.20; BELOW: can repoint the layer_libbrary_dir like this which will create a new stack with an underscore appended to the front of the file name
    # per 5.21.20 checkin, a new run argument was added that default to change the layer_library_dir, otherwise will use existing path
    # --> this seems redundant as the user could just repoint...it seems like th only benefit is in not having a new stack created w/ the underscore 
    parser_repoint.add_argument('-ld', '--layer-library-dir', help="""new layer library directory to run the stack with.""")    

    # run arguments
    parser_run.add_argument('-dd', '--layer-library-dir', help="""Default is for this
        flag to be set to false, in which case the stack uses the existing
        layer_library_dir""")
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
                      run_dir=args.run_dir, 
                      model=args.model_path, 
                      outfile=args.outfile)
    elif args.mode == 'run':
        # added line 747 and 748 for changing default dir
        new_layer_library_dir=args.layer_library_dir
        stack = Stack.load(args.stack_file, new_layer_library_dir)
        stack.run(save_path=args.save_path, log_level=log_level, archive=args.archive)
    else:
        assert False, 'Unknown mode {}'.format(args.mode)
    
    return


if __name__ == '__main__':
    main()
