# Copyright 2007-2008 Nanorex, Inc.  See LICENSE file for details. 
"""
elements_data_PAM5.py -- data for PAM5 pseudoatom elements

@author: Mark, Eric D
@version: $Id: elements_data_PAM5.py 12853 2008-05-20 16:18:25Z brucesmith $
@copyright: 2007-2008 Nanorex, Inc.  See LICENSE file for details. 

History:

Bruce 071105 revised init code, and split PAM3 and PAM5 data
out of elements_data.py into separate files.

Bruce 080108 added Gv5 for use in Eric D's forthcoming PAM5 revision.
"""

from model.elements_data import tetra4, flat, tetra2, onebond
from utilities.constants import MODEL_PAM5

_DIRECTIONAL_BOND_ELEMENTS_PAM5 = ('Ss5', 'Pl5', 'Sj5', 'Pe5', 'Sh5', 'Hp5')

# ==

# mark 060129. New default colors for Alpha 7.
_defaultRad_Color = {
    "Ax5" : (5.0, [0.4, 0.4, 0.8]),
    "Ss5" : (4.0, [0.4, 0.8, 0.4]),
    "Pl5" : (3.2, [0.4, 0.1, 0.5]),
    "Sj5" : (4.0, [0.4, 0.8, 0.8]),
    "Ae5" : (3.5, [0.4, 0.4, 0.8]),
    "Pe5" : (3.0, [0.4, 0.1, 0.5]),
    "Sh5" : (2.5, [0.4, 0.8, 0.4]),
    "Hp5" : (4.0, [0.3, 0.7, 0.3]),
    "Gv5" : (5.0, [156./255, 83./255, 8./255]), #bruce 080108
    "Gr5" : (5.0, [156./255, 83./255, 8./255]),
    "Ub5" : (2.5, [0.428, 0.812, 0.808]), #bruce 080117 guess, "light blue"
    "Ux5" : (2.5, [0.428, 0.812, 0.808]), #bruce 080410 stub
    "Uy5" : (2.5, [0.812, 0.428, 0.808]), #bruce 080410 stub
    "Ah5" : (2.5, [0.8, 0.8, 0.8]), #bruce 080515 guess, "very light gray"
    }
  
_altRad_Color = {
    }
                 
# Format of _mendeleev: see elements_data.py

_mendeleev = [
    # B-DNA PAM5 pseudo atoms (see also _DIRECTIONAL_BOND_ELEMENTS)
    # Note: the bond vector lists are mainly what we want in length,
    # not necessarily in geometry.
    #
    #bruce 070415: End->Hydroxyl per Eric D email, in "Sh5" == "PAM5-Sugar-Hydroxyl"
    #bruce 071106: added option dicts; deprecated_to options are good guesses but are untested

    #bruce 080410 added Ux5 and Uy5 and updated all general comments below

    # axis element (old, only semi-supported, not generated anymore)
    ("Ax5", "PAM5-Axis",           200, 1.0, [[4, 200, tetra4]],     dict(role = 'axis')), # todo: convert to Gv5, moving it as you do

    # strand elements
    ("Ss5", "PAM5-Sugar",          201, 1.0, [[3, 210, flat]],       dict(role = 'strand')),
    ("Pl5", "PAM5-Phosphate",      202, 1.0, [[2, 210, tetra2]],     dict(role = 'strand')),

    # deprecated axis and strand elements
    # (btw, some of these say None, 'sp', which is probably wrong --
    #  don't imitate this in new elements) [bruce 080516 comment]
    ("Sj5", "PAM5-Sugar-Junction", 203, 1.0, [[3, 210, flat]],       dict(role = 'strand', deprecated_to = 'Ss5')),
    ("Ae5", "PAM5-Axis-End",       204, 1.0, [[1, 200, None, 'sp']], dict(role = 'axis',   deprecated_to = 'X')),
    ("Pe5", "PAM5-Phosphate-End",  205, 1.0, [[1, 210, None, 'sp']], dict(role = 'strand', deprecated_to = 'Pl5')), #bruce 080129 X->Pl5; UNCONFIRMED
    ("Sh5", "PAM5-Sugar-Hydroxyl", 206, 1.0, [[1, 210, None, 'sp']], dict(role = 'strand', deprecated_to = 'X')),
    ("Hp5", "PAM5-Hairpin",        207, 1.0, [[2, 210, tetra2]],     dict(role = 'strand', deprecated_to = 'Ss5')), # REVIEW: Ss or Pl?

    # major groove (used instead of axis for PAM5, bonded same as axis)
    ("Gv5", "PAM5-Major-Groove",   208, 1.0, [[4, 200, tetra4]],     dict(role = 'axis')), #bruce 080108
    ("Gr5", "PAM5-Major-Groove-End",209,1.0, [[3, 210, flat]],       dict(role = 'axis',   deprecated_to = 'Gv5')),

    # unpaired base components (experimental and mostly stubs as of 080410):
    
    # old one-atom (besides backbone) unpaired base (never used, may or may not end up being useful,
    #  mainly retained since the corresponding PAM3 element is more likely to be useful)
    ("Ub5", "PAM5-Unpaired-base",  210, 1.0, [[4, 200, tetra4]],     dict(role = 'unpaired-base')),

    # newly proposed two-atom (besides backbone) unpaired base (never yet used but under active development):
    #
    # Ux means "unpaired base x-point" and is in the same direction from the
    #    sugar (roughly) as the major groove or axis in a basepair
    #
    # Uy means "unpaired base y-point" and is in the same direction from the
    #    sugar as the other sugar in a basepair (exactly)
    #
    # The mnemonic is that the sugar-Uy line is the "PAM3+5 baseframe Y axis"
    # and the sugar-Ux line is then enough to define the X axis
    # (though its actual direction is a combination of Y and X).
    #
    ("Ux5", "PAM5-Unpaired-base-x",211, 1.0, [[4, 200, tetra4]],     dict(role = 'unpaired-base')), # (likely to be revised)
    ("Uy5", "PAM5-Unpaired-base-y",212, 1.0, [[4, 200, tetra4]],     dict(role = 'unpaired-base')), # (likely to be revised)

    # basepair axis handle (defined as PAM5 to make it more convenient to permit its bonding with Gv5)
    # (see also: elements_data_other.py)
    ("Ah5", "PAM5-Axis-handle",    213, 1.0, [[1, 200, onebond]], dict(role = 'handle')), #bruce 080515, revised 080516

 ]

# ==

def init_PAM5_elements( periodicTable):
    periodicTable.addElements( _mendeleev, _defaultRad_Color, _altRad_Color,
                               _DIRECTIONAL_BOND_ELEMENTS_PAM5,
                               default_options = dict(pam = MODEL_PAM5)
                              )
    return

# end
