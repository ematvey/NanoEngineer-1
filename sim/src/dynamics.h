// Copyright 2005-2006 Nanorex, Inc.  See LICENSE file for details. 
#ifndef DYNAMICS_H_INCLUDED
#define DYNAMICS_H_INCLUDED

#define RCSID_DYNAMICS_H  "$Id: dynamics.h 9214 2007-05-11 04:41:33Z emessick $"

extern void oneDynamicsFrame(struct part *part,
			     int iters,
			     struct xyz *averagePositions,
			     struct xyz **pOldPositions,
			     struct xyz **pNewPositions,
			     struct xyz **pPositions,
			     struct xyz *force);

extern void dynamicsMovie(struct part *part);

#endif
