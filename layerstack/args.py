"""
Classes that allow the specification of arguments that can be serialized to and
loaded from json, as well as expressed on the command line.
"""

from collections import OrderedDict
from builtins import super
from enum import Enum

from layerstack import LayerStackError


class KwArgBase(object):
    """
    Base class for expressing json- and CLI-compatible arguments. Builds off of
    the patterns established by argparse.

    :var name: name of the [keyword] argument
    :vartype name: str or None
    :var description: optional description text for this [keyword] argument
    :vartype description: str
    :var parser: function to parse the [keyword] argument value. analogous 
        to the type argument in the argparse add_argument method
    :vartype parser: callable
    :var choices: list of allowable values
    :vartype choices: None or list
    :var nargs: analogouose to the nargs argument in the argparse 
        add_argument method
    :vartype nargs: None, int, str
    :var list_parser: function to parse a [keyword] argument value list
    :vartype list_parser: callable
    :var is_list: whether this [keyword] argument is a list (True) or single 
        value (False)
    :vartype is_list: bool
    """

    def __init__(self, description='', parser=None, choices=None, nargs=None,
                 list_parser=None):
        """
        :param description: optional description text for this [keyword] argument
        :type description: str
        :param parser: function to parse the [keyword] argument value. analogous 
            to the type argument in the argparse add_argument method
        :type parser: callable
        :param choices: list of allowable values
        :type choices: None or list
        :param nargs: analogous to the nargs argument in the argparse 
            add_argument method
        :type nargs: None, int, str
        :param list_parser: function to parse a [keyword] argument value list
        :type list_parser: callable
        """
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
        """
        return self._is_list

    def _set_value(self, value):
        self._value = self._process_value(value)

    def _process_value(self, value, none_allowed=False):
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

        :return: kwargs for argparse add_argument call
        :rtype: dict
        """
        return {'help': self.description,
                'type': self.parser,
                'choices': self.choices,
                'nargs': self.nargs}


class Arg(KwArgBase):
    """
    Defines a required, positional argument.

    :var set: whether the value has been set
    :vartype set: bool
    :var value: the value to which this argument has been set
    """

    def __init__(self, name, description='', parser=None, choices=None,
                 nargs=None, list_parser=None):
        """
        :param name: name of the argument
        :type name: str
        :param description: optional description text for this [keyword] argument
        :type description: str
        :param parser: function to parse the [keyword] argument value. analogous 
            to the type argument in the argparse add_argument method
        :type parser: callable
        :param choices: list of allowable values
        :type choices: None or list
        :param nargs: analogous to the nargs argument in the argparse 
            add_argument method
        :type nargs: None, int, str
        :param list_parser: function to parse a [keyword] argument value list
        :type list_parser: callable
        """
        super().__init__(description=description, parser=parser,
                         choices=choices, nargs=nargs, list_parser=list_parser)
        self.name = name

    @property
    def set(self):
        """
        read-only attribute
        """
        return hasattr(self, '_value')

    @property
    def value(self):
        """
        settable attribute. setter parses value using parser and list_parser as 
        appropriate
        """
        return self._value

    @value.setter
    def value(self, value):
        self._set_value(value)


class Kwarg(KwArgBase):
    """
    Defines an optional or defaulted keyword argument.

    :var default: default value to be used if no explicit value has been set
    :var defaulted: whether a non-default value has been set
    :vartype defaulted: bool
    :var value: the value to which this argument has been set
    :var action: analogous to the action argument in the argparse add_argument 
        method. allows, e.g., command-line boolean flags.
    :vartype action: str
    """

    def __init__(self, default=None, description='', parser=None, choices=None,
                 nargs=None, list_parser=None, action=None):
        """
        :param default: default value to be used if no explicit value has been 
            set. is parsed with parser and list_parser as appropriate, if 
            default is not None
        :param description: optional description text for this [keyword] argument
        :type description: str
        :param parser: function to parse the [keyword] argument value. analogous 
            to the type argument in the argparse add_argument method
        :type parser: callable
        :param choices: list of allowable values
        :type choices: None or list
        :param nargs: analogous to the nargs argument in the argparse 
            add_argument method
        :type nargs: None, int, str
        :param list_parser: function to parse a [keyword] argument value list
        :type list_parser: callable
        :param action: analogous to the action argument in the argparse add_argument 
            method. allows, e.g., command-line boolean flags.
        :type action: str
        """
        super().__init__(description=description, parser=parser,
                         choices=choices, nargs=nargs, list_parser=list_parser)
        self.action = action
        self.default = self._process_value(default,none_allowed=True)

    @property
    def defaulted(self):
        """
        read-only attribute
        """
        return not hasattr(self, '_value')

    @property
    def value(self):
        """
        settable attribute. setter parses value using parser and list_parser as 
        appropriate. setting to None clears any user-defined value and reverts 
        to the default.
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
    DESC = 1
    USE = 2


class ArgList(list):
    def __init__(self, iterable=[], **kwargs):
        """
        Construct an ArgList.

        Arguments

        - iterable=[] - An iterable passed to list.__init__. If non-empty, must
                        contain Arg objects.
        """
        # HERE -- May want to let user specify with __mode = ArgMode.USE
        self.mode = ArgMode.DESC
        super().__init__(iterable)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        self._mode = ArgMode(value)

    def __getitem__(self, i):
        result = super().__getitem__(i)
        if self.mode == ArgMode.DESC:
            return result
        assert self.mode == ArgMode.USE
        return result.value

    def __iter__(self):
        for arg in super().__iter__():
            yield arg if self.mode == ArgMode.DESC else arg.value

    def __setitem__(self, i, value):
        if self.mode == ArgMode.DESC:
            if not isinstance(value, Arg):
                raise LayerStackError("ArgLists only hold Args. You passed a {}."
                                     .format(type(value)))
            super().__setitem__(i, value)
            return
        assert self.mode == ArgMode.USE
        tmp = super().__getitem__(i)
        tmp.value = value

    def add_arguments(self, parser):
        for arg in self:
            parser.add_argument(arg.name, **arg.add_argument_kwargs())

    def set_args(self, cli_args):
        self.mode = ArgMode.DESC
        for arg in self:
            arg.value = eval('cli_args.' + arg.name)
        self.mode = ArgMode.USE

    @property
    def set(self):
        for arg in super().__iter__():
            if not arg.set:
                return False
        return True

    @property
    def names(self):
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
                raise LayerStackError("KwargDicts only hold Kwargs. You passed a {}."
                                     .format(type(value)))
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
