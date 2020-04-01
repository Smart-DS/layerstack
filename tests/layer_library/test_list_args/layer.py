from __future__ import print_function, division, absolute_import

from builtins import super
import logging
from uuid import UUID

from layerstack.args import Arg, Kwarg
from layerstack.layer import LayerBase

logger = logging.getLogger('layerstack.layers.TestListArgs')


class TestListArgs(LayerBase):
    name = "Test List Args"
    uuid = UUID("6077c40f-2640-44fe-a587-601879c0bdad")
    version = '0.1.0'
    desc = None

    @classmethod
    def args(cls, model=None):
        arg_list = super().args()
        arg_list.append(Arg('list_arg', description='This arg takes a list of strings', 
            parser=str, choices=None, nargs='+'))
        return arg_list

    @classmethod
    def kwargs(cls):
        kwarg_dict = super().kwargs()
        return kwarg_dict

    @classmethod
    def apply(cls, stack, list_arg):
        logger.info(f"Received list_arg: {list_arg}")

        return True


if __name__ == '__main__':
    TestListArgs.main()

    