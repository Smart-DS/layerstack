"""
Classes that allow the specification of arguments that can be serialized and
loaded from json, as well as expressed on the command line.
"""

from collections import OrderedDict
from builtins import super
from enum import Enum

from ditto.core.exceptions import DiTToTypeError


class KwArgBase(object):
    def __init__(self, description='',
                 parser=None,
                 choices=None,
                 nargs=None,
                 list_parser=None):
        self.name = None
        self.description = description
        self.parser = parser
        self.choices = choices
        self._is_list = False
        self.nargs = nargs
        self.list_parser = list_parser

    @property
    def nargs(self):
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
        return self._is_list

    def _set_value(self, value):
        if self.is_list:
            values = value
            if self.parser is not None:
                values = [self.parser(value) for value in values]
            self._value = self.list_parser(values) if self.list_parser is not None else values
            return
        assert not self.is_list
        self._value = self.parser(value) if self.parser is not None else value

    def add_argument_kwargs(self):
        return {'help': self.description,
                'type': self.parser,
                'choices': self.choices,
                'nargs': self.nargs}


class Arg(KwArgBase):
    """
    A layer argument.
    """
    def __init__(self, name, description='', parser=None, choices=None,
                 nargs=None, list_parser=None):
        super().__init__(description=description, parser=parser,
                         choices=choices, nargs=nargs, list_parser=list_parser)
        self.name = name

    @property
    def set(self):
        return hasattr(self, '_value')

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._set_value(value)


class Kwarg(KwArgBase):
    def __init__(self, default=None, description='', parser=None, choices=None,
                 nargs=None, list_parser=None, action=None):
        super().__init__(description=description, parser=parser,
                         choices=choices, nargs=nargs, list_parser=list_parser)
        self.action = action
        self.default = default

    @property
    def defaulted(self):
        return not hasattr(self, '_value')

    @property
    def value(self):
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
                raise DiTToTypeError("ArgLists only hold Args. You passed a {}."
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
                raise DiTToTypeError("KwargDicts only hold Kwargs. You passed a {}."
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
