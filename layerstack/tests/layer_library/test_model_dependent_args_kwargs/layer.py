from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from layerstack.tests.test_layer import LayerBaseClassForTestsWithModels

logger = logging.getLogger('layerstack.layers.TestModelDependentArgsKwargs')


class TestModelDependentArgsKwargs(LayerBaseClassForTestsWithModels):
    '''
    LayerBase
    =========
    Abstract base class for user-defined layers. All attributes and methods are
    class level.
    
    ModelLayerBase
    ==============
    Abstract base class for user-defined layers that operate on a model.

    .. automethod:: _check_model_type
    .. automethod:: _load_model
    .. automethod:: _save_model
    
    LayerBaseClassForTestsWithModels
    ================================
    '''

    name = "Test model dependent args kwargs"
    uuid = UUID("ba0672e4-b7f6-4ea6-9d30-90a4580344cd")
    version = '0.1.0'
    desc = "A test layer with args and kwargs that depend on what model is passed in"

    @classmethod
    def args(cls, model=None):
        '''
        Create ArgList

        Parameters
        ----------
        model : None or a model
            model to be operated on

        Returns
        -------
        'ArgList'
            ArgList class instance containing list of layer's args
        '''
        arg_list = super().args()
        arg_list.append(Arg('a_str_argument'))
        arg_list.append(Arg('an_int_argument', parser = int, 
            description = "Pass in an integer" if model is None else f"Pass in {model.count} integers",
            nargs = None if model is None else model.count))
        if model is not None and model.count > 1:
            assert arg_list[-1].is_list, arg_list[-1]
        return arg_list

    @classmethod
    def kwargs(cls, model=None):
        '''
        Create KwargDict

        Parameters
        ----------
        model
            model to be operated on

        Returns
        -------
        'KwargDict'
            KwargDict class instance containing dict of layer's kwargs
        '''
        kwarg_dict = super().kwargs()
        kwarg_dict['data_element'] = Kwarg(
            default = None if (model is None) or (not model.data) else model.data[0], 
            description = 'Pass in a data element',
            parser = None, 
            choices = None if (model is None) or (not model.data) else model.data)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, a_str_argument, an_int_argument, data_element = None):
        '''
        Run this layer in the context of the stack, with positional and keyword
        arguments. In general in user-defined layers (classes derived from 
        LayerBase), \*args and \*\*kwargs should be replaced by the actual 
        positional argument names (defined in the args method) and keyword 
        argument name, default value pairs (defined in the kwargs method).

        Parameters
        ----------
        stack : 'Stack'
            Stack class instance in which the layer is being run
        model
            model this layer will operate on
        a_str_argument : str
        an_int_argument : int or list of int
        data_element : any

        Returns
        -------
        model
            Updated model
        '''
        return model


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    TestModelDependentArgsKwargs.main()

    