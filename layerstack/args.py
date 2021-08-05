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
"""
Classes that allow the specification of arguments that can be serialized to and
loaded from json, as well as expressed on the command line.
"""

from collections import OrderedDict
from builtins import super
from enum import Enum
import logging

from layerstack import LayerStackTypeError, LayerStackRuntimeError

logger = logging.getLogger(__name__)

class KwArgBase(object):
    """
    Base class for expressing json- and CLI-compatible arguments. Builds off of
    the patterns established by argparse.

    Attributes
    ----------
    name : str or None
        name of the [keyword] argument
    description : str
        optional description text for this [keyword] argument
    parser : callable
        function to parse the [keyword] argument value. analogous to the type 
        argument in the argparse add_argument method 
    choices : None or list
        list of allowable values
    nargs : None, int, str
        analogous to the nargs argument in the argparse add_argument method
    list_parser : callable
        function to parse a [keyword] argument value list     
    save_parser : callable
        function to convert a [keyword] argument value to json-serializable form  
    """

    def __init__(self, description='', parser=None, choices=None, nargs=None,
                 list_parser=None, save_parser=None):
        self.name = None
        self.description = description
        self.parser = parser           
        self.choices = choices
        self._is_list = False
        self.nargs = nargs
        self.list_parser = list_parser
        self.save_parser = save_parser

    @property
    def nargs(self):
        return self._nargs

    @nargs.setter
    def nargs(self, value):
        if value not in [None, '?', '+', '*']:
            self._nargs = int(value)
            self._is_list = True # following argparse convention that if 
                                 # nargs = 1, the single element is placed in a
                                 # list
            return
        self._nargs = value
        self._is_list = self._nargs in ['+', '*']

    @property
    def choices_to_save(self):
        if (self.choices is not None) and (self.save_parser is not None):
            return [self.save_parser(choice) for choice in self.choices]
        return self.choices

    @property
    def is_list(self):
        """
        read-only attribute

        Returns
        -------
        bool
            whether this [keyword] argument is a list (True) or single value (False)    
        """
        return self._is_list

    def get_name(self, cleaned=True):
        if cleaned:
            return self.name.replace("-", "_")
        return self.name

    def _set_value(self, value):
        """
        Called by derived classes to set their _value attribute.
        """
        self._value = self._process_value(value)

    def _process_value(self, value, none_allowed=False):
        """
        Handles value and list parsing. If none_allowed, that means that the 
        value can be set to None, separate and prior to value and list parsing.
        This is used, e.g., for specifying Kwarg defaults. 

        Returns
        -------
        any
            parsed value or parsed list of values
        """
        if none_allowed and (value is None):
            return value
        if self.is_list:
            values = value
            if self.parser is not None:
                values = [self.parser(value) for value in values]
            if self.list_parser is not None:
                values = self.list_parser(values)
            if self.choices is not None:
                if not values in self.choices:
                    for value in values:
                        if value not in self.choices:
                            raise LayerStackRuntimeError(f"{values} and {value} not in choices = {self.choices}")
            return values
        assert not self.is_list
        value = self.parser(value) if self.parser is not None else value
        if (self.choices is not None) and (value not in self.choices):
            raise LayerStackRuntimeError(f"{value} not in the allowable choices: {self.choices}")
        return value

    def add_argument_kwargs(self):
        """
        Converts KwArgBase atttributes to argparse add_argument keyword 
        arugments. For use in constructing command-line interfaces.

        Returns
        -------
        dict
            kwargs for argparse add_argument call
        """
        kwargs = {}

        if self.description is not None:
            kwargs['help'] = self.description
        if self.parser is not None:
            kwargs['type'] = self.parser
        if self.choices is not None:
            kwargs['choices'] = self.choices
        if self.nargs is not None:
            kwargs['nargs'] = self.nargs

        return kwargs


class Arg(KwArgBase):
    """
    Defines a required, positional argument.

    Parameters
    ----------
    name : str
        name of the argument
    description : str
        optional description text for this argument
    parser : callable
        function to parse the argument value. analogous to the type argument in 
        the argparse add_argument method
    choices : None or list
        list of allowable values
    nargs : None, int, str
        analogous to the nargs argument in the argparse add_argument method
    list_parser : callable
        function to parse an argument value list
    save_parser : callable
        function to convert a [keyword] argument value to json-serializable form
    """

    def __init__(self, name, description='', parser=None, choices=None,
                 nargs=None, list_parser=None, save_parser=None):
        super().__init__(description=description, parser=parser,
                         choices=choices, nargs=nargs, list_parser=list_parser,
                         save_parser=save_parser)
        self.name = name

    def __repr__(self):
        return (f"{self.__class__.__name__}({self.name!r},\n"
            f"    description = {self.description!r},\n"
            f"    parser = {self.parser!r},\n"
            f"    choices = {self.choices!r},\n"
            f"    nargs = {self.nargs!r},\n"
            f"    list_parser = {self.list_parser!r},\n"
            f"    save_parser = {self.save_parser!r})")

    @property
    def set(self):
        """
        read-only attribute

        Returns
        -------
        bool
            whether the value has been set
        """
        return hasattr(self, '_value')

    @property
    def value(self):
        """
        settable attribute. setter parses value using parser and list_parser as 
        appropriate

        Returns
        -------
        any
            the value to which this argument has been set
        """
        return self._value

    @value.setter
    def value(self, value):
        self._set_value(value)

    @property
    def value_to_save(self):
        """
        JSON-serializable form of the argument value. Uses save_parser if provided.
        """
        if self.save_parser is None:
            return self.value
        return self.save_parser(self.value)


class Kwarg(KwArgBase):
    """
    Defines an optional or defaulted keyword argument.

    Attributes
    ----------
    default : None or any
        default value to be used if no explicit value has been set. is parsed 
        with parser and list_parser as appropriate, if default is not None
    description : str
        optional description text for this [keyword] argument
    parser : callable
        function to parse the [keyword] argument value. analogous to the type 
        argument in the argparse add_argument method
    choices : None or list
        list of allowable values
    nargs : None, int, str
        analogous to the nargs argument in the argparse add_argument method
    list_parser : callable
        function to parse a [keyword] argument value list
    action : str
        analogous to the action argument in the argparse add_argument method. 
        allows, e.g., command-line boolean flags.
    save_parser : callable
        function to convert a [keyword] argument value to json-serializable form
    """

    def __init__(self, default=None, description='', parser=None, choices=None,
                 nargs=None, list_parser=None, action=None, save_parser=None):
        super().__init__(description=description, parser=parser,
                         choices=choices, nargs=nargs, list_parser=list_parser,
                         save_parser=save_parser)
        self.action = action
        self.default = self._process_value(default,none_allowed=True)

    def __repr__(self):
        return (f"{self.__class__.__name__}(default = {self.default!r},\n"
            f"      description = {self.description!r},\n"
            f"      parser = {self.parser!r},\n"
            f"      choices = {self.choices!r},\n"
            f"      nargs = {self.nargs!r},\n"
            f"      list_parser = {self.list_parser!r},\n"
            f"      save_parser = {self.save_parser!r})")

    @property
    def defaulted(self):
        """
        read-only attribute

        Returns
        -------
        bool
            whether a non-default value has been set
        """
        return not hasattr(self, '_value')

    @property
    def value(self):
        """
        settable attribute. setter parses value using parser and list_parser as 
        appropriate. setting to None clears any user-defined value and reverts 
        to the default.

        Returns
        -------
        any
            the value to which this argument has been set
        """
        return self._value if hasattr(self, '_value') else self.default

    @value.setter
    def value(self, value):
        if value is None:
            if not self.defaulted:
                del self._value

            assert self.defaulted
            return
        self._set_value(value)

    @property
    def value_to_save(self):
        """
        JSON-serializable form of the keyword argument value. Uses save_parser 
        if provided and self.value is not None.
        """
        if (self.save_parser is None) or (self.value is None):
            return self.value
        return self.save_parser(self.value)

    @property
    def default_to_save(self):
        """
        JSON-serializable form of the keyword argument default value. Uses 
        save_parser if provided and self.default is not None.
        """
        if (self.save_parser is None) or (self.default is None):
            return self.default
        return self.save_parser(self.default)

    def add_argument_kwargs(self):
        kwargs = super().add_argument_kwargs()

        if self.action is not None:
            kwargs['action'] = self.action
        if self.default is not None:
            kwargs['default'] = self.default

        return kwargs


class ArgMode(Enum):
    """
    Enumeration describing whether the KwArgs in an ArgList or KwargDict are 
    currently being DESCribed (that is, they are being added to or removed from 
    the container objects, or are generally being edited), or USEd (that is, 
    the values are being set or queried in preparation for running a Layer or 
    a Stack).
    """
    DESC = 1
    USE = 2


class ArgList(list):
    def __init__(self, iterable=[], mode=ArgMode.DESC):
        """
        List that contains Arg objects. In describe mode (mode == ArgMode.DESC), 
        Arg objects may be added to and removed from this list. Their 
        descriptions and other attributes may be edited. In use mode (mode == 
        ArgMode.USE), only the argument values are accessible through this 
        class's get, set, and iter methods.

        Parameters
        ----------
        iterable : list or other iterable
            passed to list.__init__. if non-empty, must contain Arg objects.
        mode : ArgMode
            mode for this ArgList to be in upon return
        """
        self.mode = ArgMode.DESC
        super().__init__(iterable)
        self.mode = mode

    @property
    def mode(self):
        """
        settable attribute

        Returns
        -------
        ArgMode
            current mode of this ArgList, that is, whether it is being used to 
            DESCribe or USE arguments
        """
        return self._mode

    @mode.setter
    def mode(self, value):
        if isinstance(value, str):
            self._mode = ArgMode[value]
            return
        self._mode = ArgMode(value)

    def __getitem__(self, i):
        """
        Returns
        -------
        Arg or any
            Arg at position i (if mode == ArgMode.DESC), or Arg.value at 
            position i (if mode == ArgMode.USE)
        """
        result = super().__getitem__(i)
        if self.mode == ArgMode.DESC:
            return result
        assert self.mode == ArgMode.USE
        return result.value

    def __iter__(self):
        """
        Yields
        ------
        Arg or any
            the next Arg (if mode == ArgMode.DESC) or the next Arg.value (if 
            mode == ArgMode.USE)
        """
        for arg in super().__iter__():
            yield arg if self.mode == ArgMode.DESC else arg.value

    def __setitem__(self, i, value):
        """
        Set the Arg or the Arg.value at position i.

        Parameters
        ----------
        i : int
            index into this list
        value : Arg or any
            Arg to place at position i if mode == ArgMode.DESC, or value to set
            the Arg already in position i to if mode == ArgMode.USE

        Raises
        ------
        LayerStackTypeError
            if mode == ArgMode.DESC and value is not an Arg
        Exception
            if mode == ArgMode.USE and there is a failure in the value parsing
            process. value and value list parsers are provided by users, so 
            there could be unexpected behavior.
        """
        if self.mode == ArgMode.DESC:
            if not isinstance(value, Arg):
                raise LayerStackTypeError("ArgLists only hold Args. " + 
                    "You passed a {}.".format(type(value)))
            super().__setitem__(i, value)
            return
        assert self.mode == ArgMode.USE
        tmp = super().__getitem__(i)
        tmp.value = value

    def add_arguments(self, parser):
        """
        Adds this ArgList's arguments to parser, for use in a command-line 
        interface.

        Parameters
        ----------
        parser : argparse.ArgumentParser
            parser.add_argument is called once for each Arg in this ArgList

        Raises
        ------
        LayerStackRuntimeError
            if mode != ArgMode.DESC, since representing this ArgList's arguments
            in an argparse.ArgumentParser is a descriptive task
        """
        if not self.mode == ArgMode.DESC:
            raise LayerStackRuntimeError("{} ".format(self.__class__.__name__) + 
                "must be in ArgMode.DESC to add arguments to an argparse parser.")
        for arg in self:
            parser.add_argument(arg.name, **arg.add_argument_kwargs())

    def set_args(self, cli_args):
        """
        Sets this ArgList's argument values to those in cli_args, which is 
        assumed to have come from argparse.

        Parameters
        ----------
        cli_args : argparse.Namespace
            object returned by parser.parse_args(), where parser is an 
            argparse.ArgumentParser to which this ArgList's add_arguments method
            was applied

        Raises
        ------
        LayerStackRuntimeError
            if mode != ArgMode.USE, since setting this ArgList's argument values
            is a form of using a fixed ArgList
        LayerStackRuntimeError
            if an expected argument name is not found in cli_args
        Exception
            there could be a failure in the value parsing process. value and 
            value list parsers are provided by users, so there could be 
            unexpected behavior.
        """
        if not self.mode == ArgMode.USE:
            raise LayerStackRuntimeError(f"{self.__class__.__name__} "
                "must be in ArgMode.USE to set values.")
        try:
            self.mode = ArgMode.DESC
            for arg in self:
                try:
                    temp_value = getattr(cli_args, arg.get_name(cleaned=False))
                except Exception as e:
                    raise LayerStackRuntimeError(f"{arg.get_name(cleaned=False)} not found in "
                        f"cli_args:\n{cli_args},\nbecause {e}")
                arg.value = temp_value # may throw if temp_value is bad per arg.parser, etc.
            self.mode = ArgMode.USE
        except Exception as e:
            self.mode = ArgMode.USE
            raise e

    @property
    def set(self):
        """
        read-only attribute. behavior is independent of mode

        Returns
        -------
        bool
            whether all of the Args in this ArgList have had their values set
        """
        for arg in super().__iter__():
            if not arg.set:
                return False
        return True

    @property
    def names(self):
        """
        read-only attribute. behavior is independent of mode

        Returns
        -------
        list of str
            list of the names of the Args in this ArgList
        """
        names = []
        for arg in super().__iter__():
            names.append(arg.name)
        return names


class KwargDict(OrderedDict):
    def __init__(self, iterable=[], mode=ArgMode.DESC):
        """
        OrderedDict that contains Kwarg objects. In describe mode (mode == 
        ArgMode.DESC), Kwarg objects may be add and removed. Their descriptions 
        and other attributes may be edited. In use mode (mode == ArgMode.USE), 
        only the argument values are accessible through this class's get, set, 
        and iter methods.

        Parameters
        ----------
        iterable : list or other iterable
            passed to collections.OrderedDict.__init__. if non-empty, values 
            must be Kwarg objects.
        mode : ArgMode
            mode for this KwargDict to be in upon return
        """
        self.mode = ArgMode.DESC
        super().__init__(iterable)
        self.mode = mode

    @property
    def mode(self):
        """
        settable attribute

        Returns
        -------
        ArgMode
            current mode of this KwargDict, that is, whether it is being used to 
            DESCribe or USE arguments
        """
        return self._mode

    @mode.setter
    def mode(self, value):
        if isinstance(value, str):
            self._mode = ArgMode[value]
            return
        self._mode = ArgMode(value)

    def __getitem__(self, key):
        """
        Parameters
        ----------
        key : str
            name of the Kwarg of interest

        Returns
        -------
        Kwarg or any
            Kwarg with name key (if mode == ArgMode.DESC), or Kwarg.value for 
            the Kwarg with name key (if mode == ArgMode.USE)
        """        
        result = super().__getitem__(key)
        if self.mode == ArgMode.DESC:
            return result
        return result.value

    def items(self):
        """
        return the items in this KwargDict

        Returns
        -------
        list of name, value pairs
            name is always the Kwarg.name. the value is either the Kwarg itself 
            (if mode == ArgMode.DESC), or its .value (if mode == ArgMode.USE)
        """
        if self.mode == ArgMode.USE:
            return [(kwarg.get_name(), kwarg.value) for kwarg in super().values()]
        return super().items()

    def iteritems(self):
        """
        iterate throught the items in this KwargDict

        Yields
        ------
        name, value pair
            name is always the next Kwarg.name. the value is either the next 
            Kwarg itself (if mode == ArgMode.DESC), or its .value (if mode == 
            ArgMode.USE)
        """
        for name, kwarg in super().items():
            yield (name, kwarg) if self.mode == ArgMode.DESC else (kwarg.get_name(), kwarg.value)

    def values(self):
        """
        return the list of values in this KwargDict

        Returns
        -------
        list of values
            values are either Kwargs (if mode == ArgMode.DESC) or the 
            Kwarg.values (if mode == ArgMode.USE)
        """
        if self.mode == ArgMode.USE:
            return [kwarg.value for kwarg in super().values()]
        return super().values()

    def itervalues(self):
        """
        iterate through the list of values in this KwargDict

        Yields
        -------
        value
            value is either the next Kwarg (if mode == ArgMode.DESC) or the 
            next Kwarg.value (if mode == ArgMode.USE)
        """
        for kwarg in super().values():
            yield kwarg if self.mode == ArgMode.DESC else kwarg.value

    def __setitem__(self, key, value):
        """
        Add or edit a Kwarg named key, or set its value, depending on mode.

        Parameters
        ----------
        key : str
            Kwarg name
        value : Kwarg or any
            Kwarg to assign to name key if mode == ArgMode.DESC, or value to set
            the Kwarg already named key if mode == ArgMode.USE

        Raises
        ------
        LayerStackTypeError
            if mode == ArgMode.DESC and value is not an Kwarg
        Exception
            if mode == ArgMode.USE and there is a failure in the value parsing
            process. value and value list parsers are provided by users, so 
            there could be unexpected behavior.
        """
        if self.mode == ArgMode.DESC:
            if not isinstance(value, Kwarg):
                raise LayerStackTypeError("KwargDicts only hold Kwargs. " + 
                    "You passed a {}.".format(type(value)))
            value.name = key
            super().__setitem__(key, value)
            return
        if key not in self:
            logger.warn("{} not in this {},".format(key,self.__class__.__name__) + 
                " but asked to set its value. Creating a default Kwarg.")
            tmp = Kwarg()
            tmp.name = key
            super().__setitem__(key, tmp)
        tmp = super().__getitem__(key)
        tmp.value = value

    def add_arguments(self, parser, short_names=[]):
        """
        Adds this KwargDict's keyword arguments to parser, for use in a 
        command-line interface.

        Parameters
        ----------
        parser : argparse.ArgumentParser
            parser.add_argument is called once for each Arg in this ArgList
        short_names : list
            list of short names (e.g., 'd' for an argument specified as '-d',
            '--debug') already registered in parser

        Raises
        ------
        LayerStackRuntimeError
            if mode != ArgMode.DESC, since representing this KwargDict's 
            keyword arguments in an argparse.ArgumentParser is a descriptive 
            task
        """
        if not self.mode == ArgMode.DESC:
            raise LayerStackRuntimeError("{} ".format(self.__class__.__name__) + 
                "must be in ArgMode.DESC to add arguments to an argparse parser.")

        for name, kwarg in self.items():
            short_name = get_short_name(name, short_names=short_names)
            kwarg_kwargs = kwarg.add_argument_kwargs()
            try:
                parser.add_argument('-' + short_name, '--' + name,
                                    **kwarg_kwargs)
            except:
                logger.error("Unable to add kwarg '{}' to parser with ".format(name) + 
                             "short name '{}' and add_argument kwargs {}".format(short_name,kwarg_kwargs))
                raise

    def set_kwargs(self, cli_args):
        """
        Sets this KwargDict's keyword argument values to those in cli_args, 
        which is assumed to have come from argparse.

        Parameters
        ----------
        cli_args : argparse.Namespace
            object returned by parser.parse_args(), where parser is an 
            argparse.ArgumentParser to which this ArgList's add_arguments method
            was applied

        Raises
        ------
        LayerStackRuntimeError
            if mode != ArgMode.USE, since setting this ArgList's argument values
            is a form of using a fixed ArgList
        LayerStackRuntimeError
            if an expected argument name is not found in cli_args
        Exception
            there could be a failure in the value parsing process. value and 
            value list parsers are provided by users, so there could be 
            unexpected behavior.
        """
        if not self.mode == ArgMode.USE:
            raise LayerStackRuntimeError("{} ".format(self.__class__.__name__) + 
                "must be in ArgMode.USE to set values.")
        try:
            self.mode = ArgMode.DESC
            for key, kwarg in self.items():
                try:
                    temp_value = getattr(cli_args, kwarg.get_name())
                except Exception as e:
                    raise LayerStackRuntimeError(f"{kwarg.get_name()} not found in "
                        f"cli_args:\n{cli_args},\nbecause {e}")
                kwarg.value = temp_value # may throw if temp_value is bad per kwarg.parser, etc.
            self.mode = ArgMode.USE
        except Exception as e:
            self.mode = ArgMode.USE
            raise e
        

def get_short_name(name, short_names = [], seps = ['_', '-']):
    short_name = None

    def multisplit(astr, seps):
        parts = None
        for sep in seps:
            if parts is None:
                parts = astr.split(sep)
                continue
            tmp = []
            for part in parts:
                tmp.extend(part.split(sep))
            parts = tmp
        return parts

    parts = multisplit(name, seps)
    len_parts = [len(part) for part in parts]

    M = 1; N = len(parts); candidates = set(); k = 0
    logger.debug(parts)
    while not short_name:
        if k and (len(candidates) == k):
            raise LayerStackRuntimeError("Unable to find a short name "
                "for {name}. Current short names:\n[\n  {short_names}\n]"
                "\nStarted with parts = {parts},\nevaluated "
                "candidates:\n[\n  {candidates}\n]".format(
                    name = name, 
                    short_names = ",\n  ".join([repr(sn) for sn in short_names]),
                    parts = parts,
                    candidates = ",\n  ".join([repr(candi) for candi in candidates])
                ))
        n = 1; k = len(candidates)
        logger.debug(f"M = {M}; N = {N}; k = {k}")
        while n <= N:
            candidate = ''
            for i in range(n):
                m = min(len_parts[i], M)
                candidate += parts[i][:m]
                logger.debug(f"  n = {n}; i = {i}; m = {m}; {candidate}")
            for i in range(n,N):
                mm1 = min(len_parts[i], M - 1)
                candidate += parts[i][:mm1]
                logger.debug(f"  n = {n}; N = {N}; i = {i}; mm1 = {mm1}; {candidate}")
            if candidate not in short_names:
                short_name = candidate
                break
            candidates.add(candidate)
            n += 1
        M += 1
    
    assert short_name
    short_names.append(short_name)
    return short_name
