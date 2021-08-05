from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from layerstack.layer import LayerBase

logger = logging.getLogger('layerstack.layers.TestManyKwargNameClashes')


class TestKwargNameClashes(LayerBase):
    name = "Test kwarg name clashes"
    uuid = UUID("88cfcb69-27c0-4664-a295-c909a61ad832")
    version = '0.1.0'
    desc = None

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
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
        kwarg_dict['hit_rate'] = Kwarg(
            description="Kwargs starting with h should be allowed")
        return kwarg_dict

    @classmethod
    def apply(cls, stack, hit_rate = None):
        """
        No logic required--just testing kwarg-passing.
        """
        return True


if __name__ == '__main__':
    # Single-layer command-line interface entry point.

    # Parameters
    # ----------
    # log_format : str
    #     custom logging format to use with the logging package via 
    #     layerstack.start_console_log
    # 
    TestKwargNameClashes.main()

    