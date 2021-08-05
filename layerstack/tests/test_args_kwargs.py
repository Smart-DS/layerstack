'''
:copyright: (c) 2021, Alliance for Sustainable Energy, LLC
:license: BSD-3
'''

from typing import KeysView
import pytest

from layerstack.args import ArgMode, Arg, Kwarg, ArgList, KwargDict, get_short_name


def test_arglist_creation():
    # Variants that should work
    args = ArgList()

    arg1 = Arg('pv_penetration',parser=float)
    arg2 = Arg('house_size_threshold',parser=float,
               description='minimum size in ft2 for house to get pv')
    
    args = ArgList([arg1])
    args = ArgList([arg1,arg2])
    assert len(args) == 2, "Expected to create ArgList with two items, but have {}.".format(len(args))
    assert args.mode == ArgMode.DESC

    # Variants that should not work
    with pytest.raises(Exception):
        ArgList(arg1)
    with pytest.raises(Exception):
        ArgList(arg1,arg2)


def test_kwarg_creation():
    # Variants that should work
    kwargs = KwargDict()
    kwargs['max_pv_systems'] = Kwarg(parser=int,description='Maximum number of PV systems to install.')
    kwargs['fix_tap_changers'] = Kwarg(parser=bool,description='Whether to fix tap changer positions',
                                       action='store_true',default=False)
    kwargs['change_rate'] = Kwarg(parser=float,description="Rate of change (fraction)",
                                  default=0.01)
    assert len(kwargs) == 3
    assert kwargs['max_pv_systems'].name == 'max_pv_systems'

    kwargs = KwargDict([('max_pv',kwargs['max_pv_systems']),
                        ('fix_taps',kwargs['fix_tap_changers']),
                        ('change-rate', kwargs['change_rate'])])
    assert len(kwargs) == 3
    assert kwargs['max_pv'].name == 'max_pv'
    assert kwargs['max_pv'].get_name() == 'max_pv'
    assert kwargs['change-rate'].name == 'change-rate'
    assert kwargs['change-rate'].get_name() == 'change_rate'
    assert kwargs['change-rate'].get_name(cleaned=False) == 'change-rate'

    with pytest.raises(Exception):
        KwargDict(kwargs['max_pv'])


def test_get_short_name():
    short_names = ['r', 'd', 'h']

    assert get_short_name('dredge', short_names=short_names) == 'dr'
    assert get_short_name('rude-awakening', short_names=short_names) == 'ra'
    assert get_short_name('recharge_area', short_names=short_names) == 'rea'
