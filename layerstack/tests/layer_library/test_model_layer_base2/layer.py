from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from layerstack.layer import ModelLayerBase

logger = logging.getLogger('layerstack.layers.Test_Model_Layer_Base2')


class Test_Model_Layer_Base2(ModelLayerBase):
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
    '''

    name = "test_model_layer_base2"
    uuid = UUID("4837f326-4e60-49ec-8926-fa83405dd696")
    version = '0.1.0'
    desc = "this is a texst layer testing the new classes and methods"

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
        arg_list.append(Arg('arg_name', description='', parser=None,
                            choices=None, nargs=None))
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
        kwarg_dict['kwarg_name'] = Kwarg(default=None, description='',
                                         parser=None, choices=None,
                                         nargs=None, action=None)
        return kwarg_dict

    @classmethod
    def apply(cls, stack, model, *args, **kwargs):
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
        *args
            The layer's positional arguments
        **kwargs
            The layer's keyword arguments

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
    Test_Model_Layer_Base2.main()

    