from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from layerstack.layer import LayerBase

logger = logging.getLogger('layerstack.layers.TestListArgs')


class TestListArgs(LayerBase):
    '''
    LayerBase
    =========
    Abstract base class for user-defined layers. All attributes and methods are
    class level.

    Attributes
    ----------
    name : str
        layer name, expected to be human-readable (spaces are okay and even 
        preferred)
    uuid : uuid.uuid4
        unique identifier for the layer
    version : str
        human readable version number for the layer (defaults to '0.1.0')
    desc : str
        layer description
    '''

    name = "Test List Args"
    uuid = UUID("6077c40f-2640-44fe-a587-601879c0bdad")
    version = '0.1.0'
    desc = None

    @classmethod
    def args(cls, model=None):
        '''
        Each layer must define its positional arguments by populating and 
        returning an ArgList object.

        Returns
        -------
        ArgList
            ArgList object describing the layer's positional arguments. Arg
            names should appear as positional arguments in the apply method in 
            the same order as they are defined here.
        '''
        arg_list = super().args()
        arg_list.append(Arg('list_arg', description='This arg takes a list of strings', 
            parser=str, choices=None, nargs='+'))
        return arg_list

    @classmethod
    def kwargs(cls):
        '''
        Each layer must define its keyword arguments by populating and returning
        a KwargDict object.

        Returns
        -------
        KwargDict
            KwargDict object describing the layer's keyword arguments. Keyword
            argument specifications in the apply method should match what is 
            defined in this method (i.e., be equivalent to 
            Kwarg.name=Kwarg.default).
        '''
        kwarg_dict = super().kwargs()
        return kwarg_dict

    @classmethod
    def apply(cls, stack, list_arg):
        '''
        Run this layer in the context of the stack, with positional and keyword
        arguments. In general in user-defined layers (classes derived from 
        LayerBase), \*args and \*\*kwargs should be replaced by the actual 
        positional argument names (defined in the args method) and keyword 
        argument name, default value pairs (defined in the kwargs method).

        Parameters
        ----------
        stack : layerstack.stack.Stack
            Stack class instance in which the layer is being run
        *args
            the layer's positional arguments
        **kwargs
            the layer's keyword arguments
        '''
        logger.info(f"Received list_arg: {list_arg}")

        return True


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    TestListArgs.main()

    