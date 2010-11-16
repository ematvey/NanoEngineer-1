# Copyright 2004-2008 Nanorex, Inc.  See LICENSE file for details. 
"""
DnaDuplex.py -- DNA duplex generator helper classes, based on empirical data.

@author: Mark Sims
@version: $Id: Dna_Generator.py 14343 2008-09-24 18:53:34Z ninadsathaye $
@copyright: 2004-2008 Nanorex, Inc.  See LICENSE file for details.

History:

Mark 2007-10-18:
- Created. Major rewrite of DnaGenHelper.py.
"""

import foundation.env as env
import os

from math    import sin, cos, pi
from utilities.debug import print_compact_traceback, print_compact_stack
from platform_dependent.PlatformDependent import find_plugin_dir
from files.mmp.files_mmp import readmmp
from geometry.VQT import Q, V, angleBetween, cross, vlen
from commands.Fuse.fusechunksMode import fusechunksBase
from utilities.Log      import orangemsg
from utilities.exception_classes import PluginBug
from utilities.constants import gensym
from utilities.prefs_constants import dnaDefaultStrand1Color_prefs_key
from utilities.prefs_constants import dnaDefaultStrand2Color_prefs_key
from utilities.prefs_constants import dnaDefaultSegmentColor_prefs_key

from dna.model.Dna_Constants import getDuplexBasesPerTurn

##from dna.updater.dna_updater_prefs import pref_dna_updater_convert_to_PAM3plus5

from simulation.sim_commandruns import adjustSinglet
from model.elements import PeriodicTable
from model.Line import Line

from model.chem import Atom_prekill_prep
Element_Ae3 = PeriodicTable.getElement('Ae3')

from dna.model.Dna_Constants import basesDict, dnaDict
from dna.model.dna_model_constants import LADDER_END0

basepath_ok, basepath = find_plugin_dir("DNA")
if not basepath_ok:
    env.history.message(orangemsg("The cad/plugins/DNA directory is missing."))

RIGHT_HANDED = -1
LEFT_HANDED  =  1


from geometry.VQT import V, Q, norm, cross  
from geometry.VQT import  vlen
from Numeric import dot

from utilities.debug import print_compact_stack
from model.bonds import bond_at_singlets


class Dna_Generator:
    """
    Dna_Generator base class. It is inherited by B_Dna and Z_Dna subclasses.

    @ivar baseRise: The rise (spacing) between base-pairs along the helical
                    (Z) axis.
    @type baseRise: float

    @ivar handedness: Right-handed (B and A forms) or left-handed (Z form).
    @type handedness: int

    @ivar model: The model representation, where:
                    - "PAM3" = PAM3 reduced model.
                    - "PAM5" = PAM5 reduced model.

    @type model: str

    @ivar numberOfBasePairs: The number of base-pairs in the duplex.
    @type numberOfBasePairs: int

    @note: Atomistic models are not supported.
    @TODO: This classe's attribute 'assy' (self.assy) is determined in self.make
           Its okay because callers only call dna.make() first. If assy object 
           is going to remain constant,(hopefully is the case) the caller should
           pass it to the costructor of this class. (not defined as of 
           2008-03-17.

    """
    #initialize sel.assy to None. This is determined each time in self.make()
    #using the 'group' argument of that method. 
    assy = None
    #The following is a list bases inserted in to the model while generating
    #dna. see self.make()
    baseList = []

    strandA_atom_end1 = None

    def modify(self,
               group,
               resizeEndAxisAtom,
               numberOfBasePairs, 
               basesPerTurn, 
               duplexRise,
               endPoint1,
               endPoint2 ,  
               resizeEndStrandAtom = None
               ):
        """
        Modify the original (double or single stranded) dna with the 
        new dna. It creats a raw dna (single or double stranded) OR removes 
        bases from the oridinal dna if resizing 
        operation is to lengthen or shorten the original dna respctively. 
        If it is lengthening operation, then after creating a raw duplex
        it does a basic orientation to align new dna axis with original one
        and then a final orientation to make the end strand and axis atoms 
        fusable with the resize end.         

        AVAILABLE AS A DEBUG PREFERENCE ONLY AS OF 2008-04-02. 
        NEED CLEANUP , LOTS OF DOCUMENTATION AND RENAMING. 
        @see: self._fuse_new_dna_with_original_duplex
        @see: self.orient_for_modify()
        @see: B-Dna_PAM3_singleStrand
        TODO:
        - the optional argument resizeEndStrandAtom and assignment of 
          self.resizeEndStrand1Atom needs to be cleaned up.
        - refactoring cleanup and more renaming etc planned post FNANO
        - See also comments in B_Dna_PAM3_SingleStrand_Generator
        """  
        self.assy               =  group.assy         
        assy                    =  group.assy
        #Make sure to clear self.baseList each time self.modify() is called
        self.baseList           =  []

        self.setNumberOfBasePairs(abs(numberOfBasePairs))
        self.setBaseRise(duplexRise)

        #@TODO: See a note in DnaSegment_EditCommand._createStructure(). Should 
        #the parentGroup object <group> be assigned properties such as
        #duplexRise, basesPerTurn in this method itself? to be decided 
        self.setBasesPerTurn(basesPerTurn)

        #End axis atom at end1. i.e. the first mouse click point from which 
        #user started resizing the dna duplex (rubberband line). This is initially
        #set to None. When we start creating the duplex and read in the first 
        #mmp file:  MiddleBasePair.mmp, we assign the appropriate atom to this 
        #variable. See self._determine_axis_and_strandA_endAtoms_at_end_1()
        self.axis_atom_end1 = None

        #The strand base atom of Strand-A, connected to the self.axis_atom_end1
        #The vector between self.axis_atom_end1 and self.strandA_atom_end1 
        #is used to determine the final orientation of the created duplex. 
        #that aligns this vector such that it is parallel to the screen. 
        #see self._orient_to_position_first_strandA_base_in_axis_plane() for 
        #more details.
        self.strandA_atom_end1 = None


        #The end strand base-atom of the original structure (segment) being 
        #resized. This and the corresponding axis end atom ot the original 
        #structure will be used to orient the new bases we will create and fuse
        #to the original structure. 
        self._resizeEndStrand1Atom = resizeEndStrandAtom

        #The axis end base atom of the original structure (at the resize end)
        self._resizeEndAxisAtom = None

        #Do a safety check. If number of base pairs to add or subtract is 0, 
        #don't proceed further. 
        if numberOfBasePairs == 0:
            print "Duplex not created. The number of base pairs are unchanged"
            return

        #If the number of base pairs supplied by the caller are negative, it 
        #means the caller wants to delete those from the original structure
        #(duplex). 
        if numberOfBasePairs < 0:
            numberOfBasePairsToRemove = abs(numberOfBasePairs)
            self._remove_bases_from_dna(group, 
                                           resizeEndAxisAtom,
                                           numberOfBasePairsToRemove)
            return

        #Create a raw duplex first in Z direction. Using reference mmp basefiles
        #Later we will reorient this duplex and then fuse it with the original
        #duplex (which is being resized)
        self._create_raw_duplex(group, 
                                numberOfBasePairs, 
                                basesPerTurn, 
                                duplexRise )      


        # Orient the duplex.

        #Do the basic orientation so that axes of the newly created raw duplex
        #aligns with the original duplex
        self._orient(self.baseList, resizeEndAxisAtom.posn(), endPoint2)

        #Now determine the the strand1-end and axis-endAtoms at the resize 
        #end of the *original structure*. We will use this information 
        #for final orientation of the new duplex and also for fusing the new 
        #duplex with the original one. 

        #find out dna ladder to which the end axis atom of the original duplex
        #belongs to
        ladder = resizeEndAxisAtom.molecule.ladder 

        #list of end base atoms of the original duplex, at the resize end.
        #This list includes the axis end atom and strand end base atoms 
        #(so for a double stranded dna, this will return 3 atoms whereas
        #for a single stranded dna, it will return 2 atoms
        endBaseAtomList  = ladder.get_endBaseAtoms_containing_atom(resizeEndAxisAtom)        

        #As of 2008-03-26, we support onlu double stranded dna case
        #So endBaseAtomList should have atleast 3 atoms to proceed further. 
        if endBaseAtomList and len(endBaseAtomList) > 2:
            if not resizeEndStrandAtom:
                self._resizeEndStrand1Atom = endBaseAtomList[0]

            self._resizeEndAxisAtom = endBaseAtomList[1]   

            self._resizeEndStrand2Atom = None
            if endBaseAtomList[2] not in (None, self._resizeEndStrand1Atom):
                self._resizeEndStrand2Atom = endBaseAtomList[2]

            #Run full dna update so that the newly created duplex represents
            #one in dna data model. Do it before calling self._orient_for_modify
            #The dna updater run will help us use dna model features such as
            #dna ladder, rail. These will be used in final orientation 
            #of the new duplex and later fusing it with the original duplex
            #REVIEW: Wheather dna updater should be run without 
            #calling assy.update_parts... i.e. only running a local update 
            #than the whole on -- Ninad 2008-03-26
            self.assy.update_parts()

            #Do the final orientation of the new duplex. i.e rotate the new 
            #duplex around its own axis such that its then fusable with the
            #original duplex.
            self._orient_for_modify(endPoint1, endPoint2)

            #new_ladder is the dna ladder of the newly generated duplex.
            new_ladder = self.axis_atom_end1.molecule.ladder     

            #REFACTOR: Reset the dnaBaseNames of the atoms to 'X' 
            #replacing the original dnaBaseNames 'a' or 'b'. Do not do it 
            #inside self._postProcess because that method is also used by
            #self.make that calls self._create_atomLists_for_regrouping
            #after calling self._postProcess
            for m in new_ladder.all_chunks():
                for atm in m.atoms.values():
                    if atm.element.symbol in ('Ss3') and atm.getDnaBaseName() in ('a','b'):
                        atm.setDnaBaseName('X')

            #Find out the 'end' of the new ladder i.e. whether it is end0 or 
            #end1, that contains the first end axis base atom of the new duplex
            #i.e. atom self.axis_atom_end1)
            new_ladder_end = new_ladder.get_ladder_end(self.axis_atom_end1)

            #Find out three the end base atoms list of the new duplex 

            endBaseAtomList_generated_duplex = new_ladder.get_endBaseAtoms_containing_atom(self.axis_atom_end1)

            #strandA atom should be first in the list. If it is not, 
            #make sure that this list includes end atoms in this order: 
            #[strand1, axis, strand2] 
            if self.strandA_atom_end1 in endBaseAtomList_generated_duplex and \
               self.strandA_atom_end1 != endBaseAtomList_generated_duplex[0]:
                endBaseAtomList_generated_duplex.reverse()


            #Note that after orienting the duplex the first set of end base atoms 
            #in endBaseAtomList_generated_duplex will be killed. Why? because 
            #the corrsponding atoms are already present on the original duplex
            #We just used this new set for proper orientation. 


            #As we will be deleting the first set of 
            #endBaseAtomList_generated_duplex, et a set of base atoms connected 
            #to) the end base atoms in endBaseAtomList_generated_duplex. This 
            #will become our new end base atoms 

            new_endBaseAtomList = []
            for atm in endBaseAtomList_generated_duplex:
                if atm is not None:
                    rail = atm.molecule.get_ladder_rail()                        
                    baseindex = rail.baseatoms.index(atm)

                    next_atm = None
                    if len(rail.baseatoms) == 1:
                        for bond_direction in (1, -1):
                            next_atm = atm.next_atom_in_bond_direction(bond_direction)
                    else:                        
                        if new_ladder_end == 0:
                            #@@@BUG 2008-03-21. Handle special case when len(rail.baseatoms == 1)
                            next_atm = rail.baseatoms[1]
                        elif new_ladder_end == 1:
                            next_atm = rail.baseatoms[-2]

                    assert next_atm is not None                        
                    new_endBaseAtomList.append(next_atm)

            DEBUG_FUSE = True

            if DEBUG_FUSE:
                #@@REVIEW This doesn't invalidate the ladder. We just delete 
                #all the atoms and then the dna updater runs. 
                for atm in endBaseAtomList_generated_duplex:
                    if atm is not None:
                        atm.kill()   

                #Run dna updater again
                self.assy.update_parts()

                self.axis_atom_end1 = None




                self._fuse_new_dna_with_original_duplex(new_endBaseAtomList, 
                                                        endBaseAtomList)



        self.assy.update_parts()


    def _replace_overlapping_axisAtoms_of_new_dna(self, new_endBaseAtomList):
        """
        @see: B_Dna_PAM3_SingleStrand_Generator._replace_overlapping_axisAtoms_of_new_dna()
        """
        pass

    def _bond_bare_strandAtoms_with_orig_axisAtoms(self,
                                                   new_endBaseAtomList):
        pass




    def _fuse_new_dna_with_original_duplex(self, 
                                           new_endBaseAtomList,
                                           endBaseAtomList):
        """
        Fuse the new dna strand (and axxis) end atom to the original dna 

        TODO: method needs to be renamed The original dna may be a single stranded
        dna or a duplex. Until 2008-04-02 ,it was possible to create or modify
        only a duplex and thats why the name 'duplex'

        @see: self.modify()
        @see: B_Dna_PAM3_SingleStrand_Generator._fuse_new_dna_with_original_duplex()
        """


        #FUSE new duplex with the original duplex

        #strand1 chunks
        chunkList1 = \
                   [ new_endBaseAtomList[0].molecule, 
                     self._resizeEndStrand1Atom.molecule]

        #Axis chunks
        chunkList2 = \
                   [ new_endBaseAtomList[1].molecule,
                     self._resizeEndAxisAtom.molecule]

        if endBaseAtomList[2]:
            #strand2 chunks
            chunkList3 = \
                       [new_endBaseAtomList[2].molecule,
                        endBaseAtomList[2].molecule]
        else:
            chunkList3 = []

        #Set the chunk color and chunk display of the new duplex such that
        #it matches with the original duplex chunk color and display
        #Actually, fusing the chunks should have taken care of this, but 
        #for some unknown reasons, its not happening. May be because 
        #chunks are not 'merged'?  ... Setting display and color for new 
        #duplex chunk is explicitely done below. Fixes bug 2711            
        for chunkPair in (chunkList1, chunkList2, chunkList3):
            if chunkPair:
                display = chunkPair[1].display
                color   = chunkPair[1].color
                chunkPair[0].setDisplayStyle(display)
                if color:
                    chunkPair[0].setcolor(color)


        #Original implementation which relied on  on fuse chunks for finding 
        #bondable atom pairs within a tolerance limit. This is no longer
        #used and can be removed after more testing of explicit bonding
        #done in self._bond_atoms_in_atomPairs() (called below)
        #-- Ninad 2008-04-14
        ##self.fuseBasePairChunks(chunkList1)
        ##self.fuseBasePairChunks(chunkList2, fuseTolerance = 1.5)
        ##if chunkList3:
            ##self.fuseBasePairChunks(chunkList3)

        strandPairsToBond =   [ (new_endBaseAtomList[0], 
                                 self._resizeEndStrand1Atom)]

        if endBaseAtomList[2]:
            strandPairsToBond.append((new_endBaseAtomList[2],
                                      endBaseAtomList[2]))

        axisAtomPairsToBond = [  (new_endBaseAtomList[1], 
                                  self._resizeEndAxisAtom)]


        self._bond_strandAtom_pairs(strandPairsToBond)

        #Create explicit bonds between the end base atoms 
        #(like done in self._bond_bare_strandAtoms_with_orig_axisAtoms())
        #instead of relying on fuse chunks (which relies on finding 
        #bondable atom pairs within a tolerance limit. This fixes bug 2798
        #-- Ninad 2008-04-14
        self._bond_atoms_in_atomPairs(axisAtomPairsToBond)


        #Now replace the overlapping axis atoms with the corresponding 
        #original axis atoms, make bonds between strand and axis atoms as needed
        #see this method docstrings for details
        self._replace_overlapping_axisAtoms_of_new_dna(new_endBaseAtomList)

    def _bond_strandAtom_pairs(self, strandPairsToBond):
        bondPoint1 = None
        bondPoint2 = None
        bondPoint3 = None
        bondPoint4 = None

        if len(strandPairsToBond) == 2:
            firstStrandAtomPair = strandPairsToBond[0]
            secondStrandAtomPair = strandPairsToBond[1]            
            bondablePairs_1 = self._getBondablePairsForStrandAtoms(firstStrandAtomPair)
            bondablePairs_2 = self._getBondablePairsForStrandAtoms(secondStrandAtomPair)

            if bondablePairs_1[0] is not None and bondablePairs_2[1] is not None:
                bondPoint1, bondPoint2 = bondablePairs_1[0]                
                bondPoint3, bondPoint4 = bondablePairs_2[1]
            elif bondablePairs_1[1] is not None and bondablePairs_2[0] is not None:
                bondPoint1, bondPoint2 = bondablePairs_1[1]                
                bondPoint3, bondPoint4 = bondablePairs_2[0]

        elif len(strandPairsToBond) == 1:
            firstStrandAtomPair = strandPairsToBond[0]                 
            bondablePairs_1 = self._getBondablePairsForStrandAtoms(firstStrandAtomPair)           
            if bondablePairs_1[0] is not None:
                bondPoint1, bondPoint2 = bondablePairs_1[0]                
            elif bondablePairs_1[1] is not None:
                bondPoint1, bondPoint2 = bondablePairs_1[1]                

            #Do the actual bonding        
        if bondPoint1 and bondPoint2:
            bond_at_singlets(bondPoint1, bondPoint2, move = False)

        if bondPoint3 and bondPoint4:
            bond_at_singlets(bondPoint3, bondPoint4, move = False)



    def _getBondablePairsForStrandAtoms(self, strandAtomPair):    
        bondablePairs = []

        atm1 = strandAtomPair[0]
        atm2 = strandAtomPair[1]

        assert atm1.element.role == 'strand' and atm2.element.role == 'strand'
        #Initialize all possible bond points to None

        five_prime_bondPoint_atm1  = None
        three_prime_bondPoint_atm1 = None
        five_prime_bondPoint_atm2  = None
        three_prime_bondPoint_atm2 = None
        #Initialize the final bondPoints we will use to create bonds
        bondPoint1 = None
        bondPoint2 = None

        #Find 5' and 3' bondpoints of atm1 (BTW, as of 2008-04-11, atm1 is 
        #the new dna strandend atom See self._fuse_new_dna_with_original_duplex
        #But it doesn't matter here. 
        for s1 in atm1.singNeighbors():
            bnd = s1.bonds[0]            
            if bnd.isFivePrimeOpenBond():
                five_prime_bondPoint_atm1 = s1                
            if bnd.isThreePrimeOpenBond():
                three_prime_bondPoint_atm1 = s1

        #Find 5' and 3' bondpoints of atm2
        for s2 in atm2.singNeighbors():
            bnd = s2.bonds[0]
            if bnd.isFivePrimeOpenBond():
                five_prime_bondPoint_atm2 = s2
            if bnd.isThreePrimeOpenBond():
                three_prime_bondPoint_atm2 = s2
        #Determine bondpoint1 and bondPoint2 (the ones we will bond). See method
        #docstring for details.
        if five_prime_bondPoint_atm1 and three_prime_bondPoint_atm2:
            bondablePairs.append((five_prime_bondPoint_atm1, 
                                  three_prime_bondPoint_atm2 ))
        else:
            bondablePairs.append(None)


        #Following will overwrite bondpoint1 and bondPoint2, if the condition is
        #True. Doesn't matter. See method docstring to know why.
        if three_prime_bondPoint_atm1 and five_prime_bondPoint_atm2:
            bondablePairs.append((three_prime_bondPoint_atm1,
                                  five_prime_bondPoint_atm2))
        else:
            bondablePairs.append(None)

        return bondablePairs


    def _bond_atoms_in_atomPairs(self, atomPairs):
        """
        Create bonds between the atoms in given atom pairs. It creats explicit 
        bonds between the two atoms at the specified bondpoints (i.e. it doesn't
        use fuseChunkBase to find the bondable pairs within certain tolerance)

        @see: self._fuse_new_dna_with_original_duplex()
        @see: _bond_two_strandAtoms() called here

        @TODO: Refactor self._bond_bare_strandAtoms_with_orig_axisAtoms
           self._bond_axisNeighbors_with_orig_axisAtoms to use this method
        """
        for atm1, atm2 in atomPairs:
            if atm1.element.role == 'strand' and atm2.element.role == 'strand':
                self._bond_two_strandAtoms(atm1, atm2)
            else:
                #@REVIEW -- As of 2008-04-14, the atomPairs send to this method
                #are of the same type i.e. (axis, axis) or (strand, strand) 
                #but when we do refactoring of methods like 
                #self._bond_bare_strandAtoms_with_orig_axisAtoms, to use this 
                #method, may be we must make sure that we are not bonding
                #an axis atom with a 5' or 3' bondpoint of the strand atom.
                #Skip the pair if its one and the same atom.
                #-- Ninad 2008-04-14
                if atm1 is not atm2:     
                    for s1 in atm1.singNeighbors():
                        if atm2.singNeighbors(): 
                            s2 = atm2.singNeighbors()[0]
                            bond_at_singlets(s1, s2, move = False)
                            break

                #reposition bond points (if any) on the new dna's end axis atom 
                #that is just bonded with the resize end axis atom of the original 
                #duplex .
                #This fixes bug BUG 2928
                # '1st Ax atom missing bondpoint when lengthening DnaStrand'
                #Note that this bug was observed only in Ax-Ax bonding. 
                #Ss bonding is not affected. And, if we also reposition the 
                #bondpoints for Ss atoms, the bondpoints may not be oriented 
                #in desired way (i.e. reposition_baggage may not handle strand 
                #bondpoint orientation well)/. For these reasons, it is only 
                #implemented for Ax-Ax bonding. --Ninad 2008-08-22
                atm1.reposition_baggage()
                atm2.reposition_baggage()

    def _bond_two_strandAtoms(self, atm1, atm2):
        """
        Bonds the given strand atoms (sugar atoms) together. To bond these atoms, 
        it always makes sure that a 3' bondpoint on one atom is bonded to 5'
        bondpoint on the other atom. 
        Example:
        User lengthens a strand by a single strand baseatom. The final task done
        in self.modify() is to fuse the created strand base atom with the 
        strand end atom of the original dna. But this new atom has two bondpoints
        -- one is a 3' bondpoint and other is 5' bondpoint. So we must find out 
        what bondpoint is available on the original dna. If its a 5' bondpoint, 
        we will use that and the 3'bondpoint available on the new strand 
        baseatom. But what if even the strand endatom of the original dna is a
        single atom not bonded to any strand neighbors? ..thus, even that
        atom will have both 3' and 5' bondpoints. In that case it doesn't matter
        what pair (5' orig and 3' new) or (3' orig and 5' new) we bond, as long
        as we honor bonding within the atoms of any atom pair mentioned above.

        @param atm1: The first sugar atom of PAM3 (i.e. the strand atom) to be 
                     bonded with atm2. 
        @param atm2: Second sugar atom
        @see: self._fuse_new_dna_with_original_duplex()
        @see: self._bond_atoms_in_atomPairs() which calls this
        """
        #Moved from B_Dna_PAM3_SingleStrand_Generator to here, to fix bugs like 
        #2711 in segment resizing-- Ninad 2008-04-14
        assert atm1.element.role == 'strand' and atm2.element.role == 'strand'
        #Initialize all possible bond points to None

        five_prime_bondPoint_atm1  = None
        three_prime_bondPoint_atm1 = None
        five_prime_bondPoint_atm2  = None
        three_prime_bondPoint_atm2 = None
        #Initialize the final bondPoints we will use to create bonds
        bondPoint1 = None
        bondPoint2 = None

        #Find 5' and 3' bondpoints of atm1 (BTW, as of 2008-04-11, atm1 is 
        #the new dna strandend atom See self._fuse_new_dna_with_original_duplex
        #But it doesn't matter here. 
        for s1 in atm1.singNeighbors():
            bnd = s1.bonds[0]            
            if bnd.isFivePrimeOpenBond():
                five_prime_bondPoint_atm1 = s1                
            if bnd.isThreePrimeOpenBond():
                three_prime_bondPoint_atm1 = s1

        #Find 5' and 3' bondpoints of atm2
        for s2 in atm2.singNeighbors():
            bnd = s2.bonds[0]
            if bnd.isFivePrimeOpenBond():
                five_prime_bondPoint_atm2 = s2
            if bnd.isThreePrimeOpenBond():
                three_prime_bondPoint_atm2 = s2
        #Determine bondpoint1 and bondPoint2 (the ones we will bond). See method
        #docstring for details.
        if five_prime_bondPoint_atm1 and three_prime_bondPoint_atm2:
            bondPoint1 = five_prime_bondPoint_atm1
            bondPoint2 = three_prime_bondPoint_atm2
        #Following will overwrite bondpoint1 and bondPoint2, if the condition is
        #True. Doesn't matter. See method docstring to know why.
        if three_prime_bondPoint_atm1 and five_prime_bondPoint_atm2:
            bondPoint1 = three_prime_bondPoint_atm1
            bondPoint2 = five_prime_bondPoint_atm2

        #Do the actual bonding        
        if bondPoint1 and bondPoint2:
            bond_at_singlets(bondPoint1, bondPoint2, move = False)
        else:
            print_compact_stack("Bug: unable to bond atoms %s and %s: " %
                                (atm1, atm2) )
            
    def _determine_axisAtomsToRemove(self, 
                                     resizeEndAxisAtom,
                                     baseatoms, 
                                     numberOfBasePairsToRemove):
        """
        Determine the axis atoms to be removed from the Dna while resizing 
        a DnaStrand or segment. Returns a list
        
        @param resizeEndAxisAtom: The axis atom at the resize end.         
        @type resizeEndAxisAtom: B{Atom}
        
        @param baseatoms: A list of all axis atoms of the dna strand or segment 
                          to be resized
                          
        @type baseatoms: list
        
        @param numberOfBasePairsToRemove: Number of bases (if resizing strands) 
                               or number of base-pairs (it resizing DnaSegments) 
                               to be removed during the resize operation.
                               this number is used to determine the axis atoms
                               to remove (including the resizeEndAxisAtom)
        @type numberOfBasePairsToRemove: int
        
        @return : axis atoms to be removed during resize operation. The caller 
                  then uses this list to determine which strand base atoms need 
                  to be deleted. 
        @rtype: list
        
        @see: self._remove_bases_from_dna() which calls this. 
        """        
        atm = resizeEndAxisAtom  
        resizeEnd_strand_neighbors = self._strand_neighbors_to_delete(atm)
        strand_neighbors_to_delete = resizeEnd_strand_neighbors
        axisAtomsToRemove = []
        
        try:        
            resizeEndAtom_baseindex = baseatoms.index(resizeEndAxisAtom)
            # note: this is an index in a list of baseatoms, which is not
            # necessary equal to the atom's "baseindex" (since that can be
            # negative for some atoms), but should be in the same order.
            # [bruce 080807 comment]
        except:            
            print_compact_traceback("bug resize end axis atom not in " \
                                    "segments baseatoms!: ")
            return

        if resizeEndAtom_baseindex == 0:
            axisAtomsToRemove = baseatoms[:numberOfBasePairsToRemove]
        elif resizeEndAtom_baseindex == len(baseatoms) - 1:
            axisAtomsToRemove = baseatoms[-numberOfBasePairsToRemove:]
        else:
            #The axis atom is not at either 'ends' of the DnaSegment. So, 
            #check if is a single strand that is being resized. In that case, 
            #the axis atom at the resize end may not be at the extreme ends. 
            #see bug 2939 for an example. The following code fixes that bug.
            if len(resizeEnd_strand_neighbors) == 1:
                #Axis neighbors of the resize end axis atom (len 0 or 1 or 2) --
                next_axis_atoms = resizeEndAxisAtom.axis_neighbors() 
                #strand atom at the resize end
                resizeEndStrandAtom = resizeEnd_strand_neighbors[0]
                #Find out the next strand base atom bonded to the the resize 
                #end strand atom. This will give us the connected axis neighbor
                #In the following figure, S1 is the resize end strand atom, 
                #A1 is resize end axis atom. S2 is next_strand_atom  and A2
                #is next_axis_atom. 
                #
                # ---o----o----o----S2----S1----> (strand being resized)
                # ---x----x----x----A2----A1----x----x----x----x (axis)
                #<---o----o----o----o ---- o----o----o----o----o (second strand)
                
                #Note that resize end strand atom will have only one strand base
                #atom connected to it. This code will never be reached if it has
                #more than 1 strand atoms connected! 
                next_strand_atom = None
                #The axis neighbor of next_strand_atom
                next_axis_atom = None
                for bond_direction in (1, -1):
                    next_strand_atom = resizeEndStrandAtom.strand_next_baseatom(bond_direction)
                    if next_strand_atom:
                        next_axis_atom = next_strand_atom.axis_neighbor()
                        break    
                    
                if not next_axis_atom:
                    print_compact_stack("bug: end axis atom not at "\
                                        "either end of list and unable to" \
                                        "determine axisAtomsToRemove")
                    return axisAtomsToRemove
                
                if not next_axis_atom in resizeEndAxisAtom.axis_neighbors():
                    print_compact_stack(
                        "bug:unable to determine axisAtomsToRemove"\
                        "%s not an axis neighbor of %s"%(next_axis_atom, 
                                                         resizeEndAxisAtom))
                    
                next_axis_atom_baseindex = baseatoms.index(next_axis_atom)
                if resizeEndAtom_baseindex < next_axis_atom_baseindex:
                    startindex = resizeEndAtom_baseindex
                    endindex = startindex + numberOfBasePairsToRemove
                    axisAtomsToRemove = baseatoms[startindex:endindex]
                else:
                    startindex = resizeEndAtom_baseindex - (numberOfBasePairsToRemove - 1)
                    endindex = resizeEndAtom_baseindex + 1
                    axisAtomsToRemove = baseatoms[startindex:endindex]
            else:
                #Its not a strand resize operation and still the axis atom at resize
                #end is not at an extreme end. This indicates a bug.
                print_compact_stack("bug: end axis atom not at either end of list: ") #bruce 080807 added this

        assert len(axisAtomsToRemove) == min(numberOfBasePairsToRemove, len(baseatoms)) #bruce 080807 added this
        
        return axisAtomsToRemove


    def _remove_bases_from_dna(self,
                                  group, 
                                  resizeEndAxisAtom, 
                                  numberOfBasePairsToRemove):
        """
        Remove the specified number of base pairs from the duplex. 

        @param group: The DnaGroup which contains this duplex
        @type group: DnaGroup

        @param resizeEndAxisAtom: The end axis base atom at a DnaLadder end of 
        the duplex. This end base atom is used as a starting base atom while 
        determining which base atoms to remove. 
        @type resizeEndAxisAtom: Atom

        @param numberOfBasePairsToRemove: The total number of base pairs to 
        remove from the duplex. 
        @type numberOfBasePairsToRemove: int
        @see: self._determine_axisAtomsToRemove()
        """

        #Use whole_chain.get_all_baseatoms_in_order() and then remove the 
        #requested number of bases from the resize end given by 
        #numberOfBasePairsToRemove (including the resize end axis atom). 
        #this fixes bug 2924 -- Ninad 2008-08-07

        segment = resizeEndAxisAtom.getDnaSegment()        
        if not segment:
            print_compact_stack("bug: can't resize dna segment: ")
            return 

        whole_chain = segment.get_wholechain()
        if whole_chain is None:
            print_compact_stack("bug: can't resize dna segment: ") #bruce 080807 added this
            return

        baseatoms = whole_chain.get_all_baseatoms_in_order()

        if len(baseatoms) < 2:
            print_compact_stack("WARNING: resizing a dna segment with < 2 "\
                                "base atoms is not supported: ")
            return 

        atomsScheduledForDeletionDict = {}
        
        axisAtomsToRemove = self._determine_axisAtomsToRemove(
            resizeEndAxisAtom,
            baseatoms, 
            numberOfBasePairsToRemove)
        
        
        for atm in axisAtomsToRemove:  
            strand_neighbors_to_delete = self._strand_neighbors_to_delete(atm)

            for a in strand_neighbors_to_delete:
                if not atomsScheduledForDeletionDict.has_key(id(a)):
                    atomsScheduledForDeletionDict[id(a)] = a

            #Add the axis atom to the atoms scheduled for deletion only when 	 
            #both the strand neighbors of this axis atom are scheduled for 	 
            #deletion. But this is not true if its a sticky end i.e. the 	 
            #axis atom has only one strand atom. To fix that problem 	 
            #we also check (second condition) if all the strand neighbors 	 
            #of an axis atom are scheduled for deletion... if so, ot also 	 
            #adds that axis atom to the atom scheduled for deletion) 	 
            #Axis atoms are explicitely deleted to fix part of memory 	 
            #leak bug 2880 (and thus no longer depends on dna updater 	 
            #to delete bare axis atoms .. which is good because there is a 	 
            #debug pref that permits bare axis atoms for some other 	 
            #uses -- Ninad 2008-05-15 	 
            if len(strand_neighbors_to_delete) == 2 or \
               len(atm.strand_neighbors()) == len(strand_neighbors_to_delete): 	 
                if not atomsScheduledForDeletionDict.has_key(id(atm)):
                    atomsScheduledForDeletionDict[id(atm)] = atm
                else:
                    print "unexpected: atom %r already in atomsScheduledForDeletionDict" % atm #bruce 080807 added this              

            # REVIEW: if any atom can be added twice to that dict above without
            # this being a bug, then the has_key tests can simply be removed
            # (as an optimization). If adding it twice is a bug, then we should
            # print a warning when it happens, as I added in one case above
            # (but would be good in both cases). [bruce 080807 comment]

        #Now kill all the atoms.

        # [TODO: the following ought to be encapsulated in a helper method to
        #  efficiently kill any set of atoms; similar code may exist in
        #  several places. [bruce 080807 comment]]
        #
        #Before killing them, set a flag on each atom so that
        #Atom.kill knows not to create new bondpoints on its neighbors if they
        #will also be killed right now (it notices this by noticing that
        #a._will_kill has the same value on both atoms). Fixes a memory leak
        #(at least in some code where it's done). See bug 2880 for details.
        val = Atom_prekill_prep()
        for a in atomsScheduledForDeletionDict.itervalues():
            a._will_kill = val # inlined a._prekill(val), for speed

        for atm in atomsScheduledForDeletionDict.values():
            if atm: # this test is probably not needed [bruce 080807 comment]
                try:                   
                    atm.kill()    
                except:
                    print_compact_traceback("bug in deleting atom while "\
                                            "resizing the segment: ")

        atomsScheduledForDeletionDict.clear()

        #IMPORTANT TO RUN DNA UPDATER after deleting these atoms! Otherwise we
        #will have to wait for next event to finish before the dna updater runs.
        #There are things like resize handle positions that depend on the 
        #axis end atoms of a dna segment. Those update methods may be called 
        #before dna updater is run again, thereby spitting out errors.
        self.assy.update_parts()

    def _strand_neighbors_to_delete(self, axisAtom):
        """
        Overridden in subclasses
        Returns a list of strand neighbors of the given axis atom to delete 
        from the original dna being resized (and resizing will result in
        removing bases/ basepairs from the dna). This method determines
        whether both the strand neigbors of this axisAtom need to be deleted
        or is it just a single strand neighbor on a specific Dna ladder 
        needs to be deleted. The latter is the case while resizing a 
        single strand of a Dna. 
        @see: self._remove_bases_from_dna() where this is called.
        @see: B_Dna_PAM3_Generator._strand_neighbors_to_delete()
        @see: B_Dna_PAM3_SingleStrand_Generator._strand_neighbors_to_delete()
        """
        return ()


    def make(self, 
             group, 
             numberOfBasePairs, 
             basesPerTurn, 
             duplexRise,
             endPoint1,
             endPoint2,
             position = V(0, 0, 0)):
        """
        Makes a DNA duplex with the I{numberOfBase} base-pairs. 
        The duplex is oriented with its central axis coincident to the
        line (endPoint1, endPoint1), with its origin at endPoint1.

        @param assy: The assembly (part).
        @type  assy: L{assembly}

        @param group: The group node object containing the DNA. The caller
                      is responsible for creating an empty group and passing
                      it here. When finished, this group will contain the DNA
                      model.
        @type  group: L{Group}

        @param numberOfBasePairs: The number of base-pairs in the duplex.
        @type  numberOfBasePairs: int

        @param basesPerTurn: The number of bases per helical turn.
        @type  basesPerTurn: float

        @param duplexRise: The rise; the distance between adjacent bases.
        @type  duplexRise: float

        @param endPoint1: The origin of the duplex.
        @param endPoint1: L{V}

        @param endPoint2: The second point that defines central axis of 
                          the duplex.
        @param endPoint2: L{V}

        @param position: The position in 3d model space at which to create
                         the DNA strand. This should always be 0, 0, 0.
        @type position:  position

        @see: self.fuseBasePairChunks()
        @see:self._insertBasesFromMMP()
        @see: self._regroup()
        @see: self._postProcess()
        @see: self._orient()
        @see: self._rotateTranslateXYZ()
        """      

        self.assy               =  group.assy         
        assy                    =  group.assy
        #Make sure to clear self.baseList each time self.make() is called
        self.baseList           =  []

        self.setNumberOfBasePairs(numberOfBasePairs)
        self.setBaseRise(duplexRise)
        #See a note in DnaSegment_EditCommand._createStructure(). Should 
        #the parentGroup object <group> be assigned properties such as
        #duplexRise, basesPerTurn in this method itself? to be decided 
        #once dna data model is fully functional (and when this method is 
        #revised) -- Ninad 2008-03-05
        self.setBasesPerTurn(basesPerTurn)

        #End axis atom at end1. i.e. the first mouse click point from which 
        #user started drawing the dna duplex (rubberband line). This is initially
        #set to None. When we start creating the duplex and read in the first 
        #mmp file:  MiddleBasePair.mmp, we assign the appropriate atom to this 
        #variable. See self._determine_axis_and_strandA_endAtoms_at_end_1()
        self.axis_atom_end1 = None

        #The strand base atom of Strand-A, connected to the self.axis_atom_end1
        #The vector between self.axis_atom_end1 and self.strandA_atom_end1 
        #is used to determine the final orientation of the created duplex. 
        #that aligns this vector such that it is parallel to the screen. 
        #see self._orient_to_position_first_strandA_base_in_axis_plane() for more details.
        self.strandA_atom_end1 = None

        #Create a duplex by inserting basepairs from the mmp file. 
        self._create_raw_duplex(group, 
                                numberOfBasePairs, 
                                basesPerTurn, 
                                duplexRise,
                                position = position)


        # Orient the duplex.
        self._orient(self.baseList, endPoint1, endPoint2)

        #do further adjustments so that first base of strandA always lies
        #in the screen parallel plane, which is passing through the 
        #axis. 
        self._orient_to_position_first_strandA_base_in_axis_plane(self.baseList, 
                                                                  endPoint1, 
                                                                  endPoint2)

        # Regroup subgroup into strand and chunk groups
        self._regroup(group)
        return

    #START -- Helper methods used in generating dna (see self.make())===========

    def _create_raw_duplex(self,
                           group, 
                           numberOfBasePairs, 
                           basesPerTurn, 
                           duplexRise,
                           position = V(0, 0, 0)):
        """
        Create a raw dna duplex in the specified group. This will be created 
        along the Z axis. Later it will undergo more operations such as 
        orientation change anc chunk regrouping. 

        @return: A group object containing the 'raw dna duplex'
        @see: self.make()

        """
        # Make the duplex.
        subgroup = group
        subgroup.open = False    


        # Calculate the twist per base in radians.
        twistPerBase = (self.handedness * 2 * pi) / basesPerTurn
        theta = 0.0
        z     = 0.5 * duplexRise * (numberOfBasePairs - 1)

        # Create duplex.
        for i in range(numberOfBasePairs):
            basefile, zoffset, thetaOffset = self._strandAinfo(i)

            def tfm(v, theta = theta + thetaOffset, z1 = z + zoffset):
                return self._rotateTranslateXYZ(v, theta, z1)

            #Note that self.baseList gets updated in the the following method
            self._insertBaseFromMmp(basefile, 
                                    subgroup, 
                                    tfm, 
                                    self.baseList,
                                    position = position)

            if i == 0:
                #The chunk self.baseList[0] should always contain the information 
                #about the strand end and axis end atoms at end1 we are 
                #interested in. This chunk is obtained by reading in the 
                #first mmp file (at i =0) .

                #Note that we could have determined this after the for loop 
                #as well. But now harm in doing it here. This is also safe 
                #from any accidental modifications to the chunk after the for 
                #loop. Note that 'self.baseList' gets populated in 
                #sub 'def insertBasesFromMMP'.... Related TODO: The method 
                #'def make' itself needs reafcatoring so that all submethods are
                #direct methods of class Dna.
                #@see self._determine_axis_and_strandA_endAtoms_at_end_1() for 
                #more comments
                firstChunkInBaseList = self.baseList[0]
                #@ATTENTION: The strandA endatom at end1 is later modified 
                #in self.orient_for_modify (if its a resize operation) 
                #Its done to fix bug 2888 (for v1.1.0). 
                #Perhaps computing this strand atom  always be done at a later 
                #stage. But I am unsure if this will cause any bugs. So not 
                #changing the original implementation . 
                #See B_Dna_PAM3_Generator.orient_for_modify() for details. 
                #This NEEDS CLEANUP -- Ninad 2008-06-02 
                self._determine_axis_and_strandA_endAtoms_at_end_1(self.baseList[0])

            theta -= twistPerBase
            z     -= duplexRise

        # Fuse the base-pair chunks together into continuous strands.
        self.fuseBasePairChunks(self.baseList)

        try:
            self._postProcess(self.baseList)
        except:
            if env.debug():
                print_compact_traceback( 
                    "debug: exception in %r._postProcess(self.baseList = %r) " \
                    "(reraising): " % (self, self.baseList,))
            raise



    def _insertBaseFromMmp(self,
                           filename, 
                           subgroup, 
                           tfm, 
                           baseList,
                           position = V(0, 0, 0) ):
        """
        Insert the atoms for a nucleic acid base from an MMP file into
        a single chunk.
         - If atomistic, the atoms for each base are in a separate chunk.
         - If PAM5, the pseudo atoms for each base-pair are together in a 
           chunk.

        @param filename: The mmp filename containing the base 
                         (or base-pair).
        @type  filename: str

        @param subgroup: The part group to add the atoms to.
        @type  subgroup: L{Group}

        @param tfm: Transform applied to all new base atoms.
        @type  tfm: V

        @param baseList: A list that maintains the bases inserted into the 
                         model Example self.baseList

        @param position: The origin in space of the DNA duplex, where the
                         3' end of strand A is 0, 0, 0.
        @type  position: L{V}

        """

        #@TODO: The argument baselist ACTUALLY MODIFIES self.baseList. Should we 
        #directly use self.baseList instead? Only comments are added for 
        #now. See also self.make()(the caller)
        try:
            ok, grouplist = readmmp(self.assy, filename, isInsert = True)
        except IOError:
            raise PluginBug("Cannot read file: " + filename)
        if not grouplist:
            raise PluginBug("No atoms in DNA base? " + filename)

        viewdata, mainpart, shelf = grouplist

        for member in mainpart.members:
            # 'member' is a chunk containing a full set of 
            # base-pair pseudo atoms.

            for atm in member.atoms.values():                            
                atm._posn = tfm(atm._posn) + position

            member.name = "BasePairChunk"
            subgroup.addchild(member)

            #Append the 'member' to the baseList. Note that this actually 
            #modifies self.baseList. Should self.baseList be directly used here?
            baseList.append(member)

        # Clean up.
        del viewdata                
        shelf.kill()

    def _rotateTranslateXYZ(self, inXYZ, theta, z):
        """
        Returns the new XYZ coordinate rotated by I{theta} and 
        translated by I{z}.

        @param inXYZ: The original XYZ coordinate.
        @type  inXYZ: V

        @param theta: The base twist angle.
        @type  theta: float

        @param z: The base rise.
        @type  z: float

        @return: The new XYZ coordinate.
        @rtype:  V
        """
        c, s = cos(theta), sin(theta)
        x = c * inXYZ[0] + s * inXYZ[1]
        y = -s * inXYZ[0] + c * inXYZ[1]
        return V(x, y, inXYZ[2] + z)


    def fuseBasePairChunks(self, baseList, fuseTolerance = 1.5):
        """
        Fuse the base-pair chunks together into continuous strands.

        @param baseList: The list of bases inserted in the model. See self.make
                          (the caller) for an example.
        @see: self.make()
        @NOTE: self.assy is determined in self.make() so this method 
               must be called from that method only.
        """

        if self.assy is None:
            print_compact_stack("bug: self.assy not defined. Unable to fuse bases: ")
            return 

        # Fuse the base-pair chunks together into continuous strands.
        fcb = fusechunksBase()
        fcb.tol = fuseTolerance

        for i in range(len(baseList) - 1):
            #Note that this is actually self.baseList that we are using. 
            #Example see self.make() which calls this method. 
            tol_string = fcb.find_bondable_pairs([baseList[i]], 
                                                 [baseList[i + 1]],
                                                 ignore_chunk_picked_state = True
                                                 ) 
            fcb.make_bonds(self.assy)

    def _postProcess(self, baseList):
        return

    #END Helper methods used in dna generation (see self.make())================

    def _baseFileName(self, basename):
        """
        Returns the full pathname to the mmp file containing the atoms 
        of a nucleic acid base (or base-pair).

        Example: If I{basename} is "MidBasePair" and this is a PAM5 model of
        B-DNA, this returns:

          - "C:$HOME\cad\plugins\DNA\B-DNA\PAM5-bases\MidBasePair.mmp"

        @param basename: The basename of the mmp file without the extention
                         (i.e. "adenine", "MidBasePair", etc.).
        @type  basename: str

        @return: The full pathname to the mmp file.
        @rtype:  str
        """
        form    = self.form             # A-DNA, B-DNA or Z-DNA
        model   = self.model + '-bases' # PAM3 or PAM5
        return os.path.join(basepath, form, model, '%s.mmp' % basename)

    def _orient(self, baseList, pt1, pt2):
        """
        Orients the DNA duplex I{dnaGroup} based on two points. I{pt1} is
        the first endpoint (origin) of the duplex. The vector I{pt1}, I{pt2}
        defines the direction and central axis of the duplex.

        @param pt1: The starting endpoint (origin) of the DNA duplex.
        @type  pt1: L{V}

        @param pt2: The second point of a vector defining the direction
                    and central axis of the duplex.
        @type  pt2: L{V}
        """

        a = V(0.0, 0.0, -1.0)
        # <a> is the unit vector pointing down the center axis of the default
        # DNA structure which is aligned along the Z axis.
        bLine = pt2 - pt1
        bLength = vlen(bLine)
        b = bLine/bLength
        # <b> is the unit vector parallel to the line (i.e. pt1, pt2).
        axis = cross(a, b)
        # <axis> is the axis of rotation.

        theta = angleBetween(a, b)
        # <theta> is the angle (in degress) to rotate about <axis>.
        scalar = self.getBaseRise() * (self.getNumberOfBasePairs() - 1) * 0.5
        rawOffset = b * scalar

        if 0: # Debugging code.
            print "~~~~~~~~~~~~~~"
            print "uVector  a = ", a
            print "uVector  b = ", b
            print "cross(a,b) =", axis
            print "theta      =", theta
            print "baserise   =", self.getBaseRise()
            print "# of bases =", self.getNumberOfBasePairs()
            print "scalar     =", scalar
            print "rawOffset  =", rawOffset 

        if theta == 0.0 or theta == 180.0:
            axis = V(0, 1, 0)
            # print "Now cross(a,b) =", axis

        rot =  (pi / 180.0) * theta  # Convert to radians
        qrot = Q(axis, rot) # Quat for rotation delta.

        # Move and rotate the base chunks into final orientation.
        ##for m in dnaGroup.members:
        for m in baseList:
            if isinstance(m, self.assy.Chunk):        
                m.move(qrot.rot(m.center) - m.center + rawOffset + pt1)
                m.rot(qrot)



    def _determine_axis_and_strandA_endAtoms_at_end_1(self, chunk):
        """
        Overridden in subclasses. Default implementation does nothing. 

        @param chunk: The method itereates over chunk atoms to determine 
                      strand and axis end atoms at end 1. 
        @see: B_DNA_PAM3._determine_axis_and_strandA_endAtoms_at_end_1()
              for documentation and implementation. 
        """
        pass

    def _orient_for_modify(self, baseList, end1, end2):        
        pass

    def _orient_to_position_first_strandA_base_in_axis_plane(self, baseList, end1, end2):
        """
        Overridden in subclasses. Default implementation does nothing.

        The self._orient method orients the DNA duplex parallel to the screen
        (lengthwise) but it doesn't ensure align the vector
        through the strand end atom on StrandA and the corresponding axis end 
        atom  (at end1) , parallel to the screen. 

        This function does that ( it has some rare bugs which trigger where it
        doesn't do its job but overall works okay )

        What it does: After self._orient() is done orienting, it finds a Quat 
        that rotates between the 'desired vector' between strand and axis ends at
        end1(aligned to the screen)  and the actual vector based on the current
        positions of these atoms.  Using this quat we rotate all the chunks 
        (as a unit) around a common center. 

        @BUG: The last part 'rotating as a unit' uses a readymade method in 
        ops_motion.py -- 'rotateSpecifiedMovables' . This method itself may have
        some bugs because the axis of the dna duplex is slightly offset to the
        original axis. 

        @see: self._determine_axis_and_strandA_endAtoms_at_end_1()
        @see: self.make()

        @see: B_DNA_PAM3._orient_to_position_first_strandA_base_in_axis_plane

        """
        pass


    def _regroup(self, dnaGroup):
        """
        Regroups I{dnaGroup} into group containing three chunks: I{StrandA},
        I{StrandB} and I{Axis} of the DNA duplex.

        @param dnaGroup: The DNA group which contains the base-pair chunks
                         of the duplex.
        @type  dnaGroup: L{Group}

        @return: The new DNA group that contains the three chunks
                 I{StrandA}, I{StrandB} and I{Axis}.
        @rtype:  L{Group}
        """
            #Get the lists of atoms (two lists for two strands and one for the axis
            #for creating new chunks 

        _strandA_list, _strandB_list, _axis_list = \
                     self._create_atomLists_for_regrouping(dnaGroup)



        # Create strand and axis chunks from atom lists and add 
        # them to the dnaGroup.

        # [bruce 080111 add conditions to prevent bugs in PAM5 case
        #  which is not yet supported in the above code. It would be
        #  easy to support it if we added dnaBaseName assignments
        #  into the generator mmp files and generalized the above
        #  symbol names, and added a 2nd pass for Pl atoms.
        #  update, bruce 080311: it looks like something related to
        #  this has been done without this comment being updated.]

        if _strandA_list:
            strandAChunk = self._makeChunkFromAtomList(
                _strandA_list,
                name = gensym("Strand", self.assy),
                group = dnaGroup,
                color = env.prefs[dnaDefaultStrand1Color_prefs_key])

        if _strandB_list:
            strandBChunk = self._makeChunkFromAtomList(
                _strandB_list,
                name = gensym("Strand", self.assy),
                group = dnaGroup,
                color = env.prefs[dnaDefaultStrand2Color_prefs_key])

        if _axis_list:
            axisChunk = self._makeChunkFromAtomList(
                _axis_list,
                name = "Axis",
                group = dnaGroup,
                color = env.prefs[dnaDefaultSegmentColor_prefs_key])
        return

    def _makeChunkFromAtomList(self, atomList, **options):
        #bruce 080326 split this out, revised it for PAM3+5 (partway)
        chunk = self.assy.makeChunkFromAtomList( atomList, **options)
        ### todo: in some cases, set chunk.display_as_pam = MODEL_PAM5
        # initial stub: always do that (when making PAM5 dna),
        # but only if edit pref would otherwise immediately convert it to PAM3.
        #update, bruce 080401: always do it, regardless of that edit pref.
        #update, bruce 080523: never do it, until the bug 2842 dust completely
        # settles. See also a comment added in rev 12846. This is #2 of 2 changes
        # (in the same commit) which eliminates all ways of setting this attribute,
        # thus fixing bug 2842 well enough for v1.1.
        ## if self.model == "PAM5": ##  and pref_dna_updater_convert_to_PAM3plus5():
        ##     if debug_flags.atom_debug:
        ##         print "debug fyi: %r is setting .display_as_pam = MODEL_PAM5 " \
        ##               "on %r" % (self, chunk)
        ##     chunk.display_as_pam = MODEL_PAM5
        return chunk

    def getBaseRise( self ):
        """
        Get the base rise (spacing) between base-pairs.
        """
        return float( self.baseRise )

    def setBaseRise( self, inBaseRise ):
        """
        Set the base rise (spacing) between base-pairs.

        @param inBaseRise: The base rise in Angstroms.
        @type  inBaseRise: float
        """
        self.baseRise  =  inBaseRise

    def getNumberOfBasePairs( self ):
        """
        Get the number of base-pairs in this duplex.
        """
        return self.numberOfBasePairs

    def setNumberOfBasePairs( self, inNumberOfBasePairs ):
        """
        Set the base rise (spacing) between base-pairs.

        @param inNumberOfBasePairs: The number of base-pairs.
        @type  inNumberOfBasePairs: int
        """
        self.numberOfBasePairs  =  inNumberOfBasePairs

    def setBasesPerTurn(self, basesPerTurn):
        """
        Sets the number of base pairs per turn
        @param basesPerTurn: Number of bases per turn
        @type  basesPerTurn: int
        """
        self.basesPerTurn = basesPerTurn

    def getBasesPerTurn(self):
        """
        returns the number of bases per turn in the duplex
        """
        return self.basesPerTurn

    pass

