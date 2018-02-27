"""
Classes that allow the specification of arguments that can be serialized to and
loaded from json, as well as expressed on the command line.
"""

from collections import OrderedDict
from builtins import super
from enum import Enum

from layerstack import LayerStackTypeError, LayerStackRuntimeError


class KwArgBase(object):
    """
    Base class for expressing json- and CLI-compatible arguments. Builds off of
    the patterns established by argparse.

    Parameters
    ----------
    description : str
        optional description text for this [keyword] argument
    parser : callable
        function to parse the [keyword] argument value. analogous to the 
        type argument in the argparse add_argument method
    choices : None or list
        list of allowable values
    nargs: None, int, str
        analogous to the nargs argument in the argparse add_argument method
    list_parser : callable
        function to parse a [keyword] argument value list

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
    list_parser : callable
        function to parse a [keyword] argument value list       
    """

    def __init__(self, description='', parser=None, choices=None, nargs=None,
                 list_parser=None):
        self.name = None
        self.description = description # optional description text
        # function to parse the [keyword] argument value, e.g. int, float. 
        # analogous to the type argument in the argparse add_argument method.
        self.parser = parser           
        self.choices = choices
        self._is_list = False
        self.nargs = nargs
        self.list_parser = list_parser

    @property
    def nargs(self):
        """
        settable attribute

        Returns
        -------
        None, int, str
            analogous to the nargs argument in the argparse add_argument method
        """
        return self._nargs

    @nargs.setter
    def nargs(self, value):
        if value not in [None, '?', '+', '*']:
            self._nargs = int(value)
            self._is_list = True
        self._nargs = value
        self._is_list = self._nargs in ['+', '*']

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
            return self.list_parser(values) if self.list_parser is not None else values
        assert not self.is_list
        return self.parser(value) if self.parser is not None else value

    def add_argument_kwargs(self):
        """
        Converts KwArgBase atttributes to argparse add_argument keyword 
        arugments. For use in constructing command-line interfaces.

        Returns
        -------
        dict
            kwargs for argparse add_argument call
        """
        return {'help': self.description,
                'type': self.parser,
                'choices': self.choices,
                'nargs': self.nargs}


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
    """

    def __init__(self, name, description='', parser=None, choices=None,
                 nargs=None, list_parser=None):
        super().__init__(description=description, parser=parser,
                         choices=choices, nargs=nargs, list_parser=list_parser)
        self.name = name

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


class Kwarg(KwArgBase):
    """
    Defines an optional or defaulted keyword argument.

    Parameters
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
    :type list_parser: 
    :param action: analogous to the action argument in the argparse add_argument 
        method. allows, e.g., command-line boolean flags.
    :type action: str

    Attributes
    ----------
    default : None or any
        default value to be used if no explicit value has been set
    action : str
        analogous to the action argument in the argparse add_argument method. 
        allows, e.g., command-line boolean flags.
    """

    def __init__(self, default=None, description='', parser=None, choices=None,
                 nargs=None, list_parser=None, action=None):
        super().__init__(description=description, parser=parser,
                         choices=choices, nargs=nargs, list_parser=list_parser)
        self.action = action
        self.default = self._process_value(default,none_allowed=True)

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

    def add_argument_kwargs(self):
        kwargs = super().add_argument_kwargs()
        kwargs['action'] = self.action
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
            mode for this ArgList to be in upon return. is constructed in 
            ArgMode.DESC
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
            raise LayerStackRuntimeError("ArgList be in ArgMode.DESC to add " + 
                "arguments to an argparse parser.")
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
            raise LayerStackRuntimeError("ArgList must be in ArgMode.USE to " + 
                "set values.")
        try:
            self.mode = ArgMode.DESC
            for arg in self:
                try:
                    temp_value = eval('cli_args.' + arg.name) 
                except Exception as e:
                    raise LayerStackRuntimeError("{} not found in cli_args, {}".format(arg.name,e))
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
    def __init__(self, iterable=[], **kwargs):
        """
        Construct a KwargDict.

        Arguments

        - iterable=[] - An iterable passed to collections.OrderedDict.__init__.
                        If non-empty, values must be Kwarg objects.
        """
        self.mode = ArgMode.DESC
        super().__init__(iterable)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        self._mode = ArgMode(value)

    def __getitem__(self, key):
        result = super().__getitem__(key)
        if self.mode == ArgMode.DESC:
            return result
        return result.value

    def items(self):
        if self.mode == ArgMode.USE:
            return [(name, kwarg.value) for name, kwarg in super().items()]
        return super().items()

    def iteritems(self):
        for name, kwarg in super().iteritems():
            yield (name, kwarg) if self.mode == ArgMode.DESC else (name, kwarg.value)

    def values(self):
        if self.mode == ArgMode.USE:
            return [kwarg.value for kwarg in super().values()]
        return super().values()

    def itervalues(self):
        for kwarg in super().itervalues():
            yield kwarg if self.mode == ArgMode.DESC else kwarg.value

    def __setitem__(self, key, value):
        if self.mode == ArgMode.DESC:
            if not isinstance(value, Kwarg):
                raise LayerStackTypeError("KwargDicts only hold Kwargs. " + 
                    "You passed a {}.".format(type(value)))
            value.name = key
            super().__setitem__(key, value)
            return
        if key not in self:
            tmp = Kwarg()
            tmp.name = key
            super().__setitem__(key, tmp)
        tmp = super().__getitem__(key)
        tmp.value = value

    def add_arguments(self, parser, short_names=[]):

        def get_short_name(name):
            short_name = None; n = 0
            while not short_name:
                n += 1
                if name[:n] not in short_names:
                    short_name = name[:n]
                    short_names.append(short_name)
            assert short_name
            return short_name

        for name, kwarg in self.items():
            parser.add_argument('-' + get_short_name(name), '--' + name,
                                **kwarg.add_argument_kwargs())

    def set_kwargs(self, cli_args):
        self.mode = ArgMode.DESC
        for key, kwarg in self.items():
            kwarg.value = eval('cli_args.' + key)
        self.mode = ArgMode.USE
