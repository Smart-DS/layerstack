import pytest

from layerstack.args import ArgMode, Arg, Kwarg, ArgList, KwargDict


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
    assert len(kwargs) == 2
    assert kwargs['max_pv_systems'].name == 'max_pv_systems'

    kwargs = KwargDict([('max_pv',kwargs['max_pv_systems']),
                        ('fix_taps',kwargs['fix_tap_changers'])])
    assert len(kwargs) == 2
    assert kwargs['max_pv'].name == 'max_pv'

    with pytest.raises(Exception):
        KwargDict(kwargs['max_pv'])


