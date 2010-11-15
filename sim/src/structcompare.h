// Copyright 2005-2006 Nanorex, Inc.  See LICENSE file for details. 
#ifndef STRUCTCOMPARE_H_INCLUDED
#define STRUCTCOMPARE_H_INCLUDED

#define RCSID_STRUCTCOMPARE_H  "$Id: structcompare.h 9214 2007-05-11 04:41:33Z emessick $"

extern int doStructureCompare(int numberOfAtoms,
                              struct xyz *basePositions,
                              struct xyz *initialPositions,
                              int iterLimit,
                              double deviationLimit,
                              double maxDeltaLimit,
                              double maxScale);


#endif
