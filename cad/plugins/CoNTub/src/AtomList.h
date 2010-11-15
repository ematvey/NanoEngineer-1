// Copyright 2006-2007 Nanorex, Inc.  See LICENSE file for details. 
/* $Id: AtomList.h 7321 2007-05-17 18:17:07Z emessick $ */

#ifndef ATOMLIST_H_INCLUDED
#define ATOMLIST_H_INCLUDED

#include "Atomo.h"

class AtomList
{
    int _size, capacity;
    Atomo *contents;
public:
    AtomList(void);
    AtomList(int n);
    ~AtomList(void);
    Atomo *get(int i);
    AtomList neighborhood(Atomo *);
    void add(Atomo a);
    int size(void);
    void remove(int);
    void set(int, Atomo);
    int contains(Atomo);
};

#endif
