// Copyright 2005-2006 Nanorex, Inc.  See LICENSE file for details. 
#ifndef READERS_H_INCLUDED
#define READERS_H_INCLUDED

#define RCSID_READERS_H  "$Id: readers.h 9214 2007-05-11 04:41:33Z emessick $"

extern void makatom(int elem, struct xyz posn);

extern void makbond(int a, int b, char ord);

extern void maktorq(int center, int a, int b);

extern void makvdw(int a1, int a2);

extern int makcon(int typ, struct MOT *mot, int n, int *atnos);

extern struct MOT *makmot(double stall, double speed, struct xyz vec1,  struct xyz vec2);

extern void makmot2(int i);

extern struct MOT *maklmot(double force, double stiff, struct xyz vec1,  struct xyz vec2);

extern void maklmot2(int i);

extern void filred(char *filnam);

extern struct xyz *readXYZ(char *filename, int *natoms);

#endif
