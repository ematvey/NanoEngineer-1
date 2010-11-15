// Copyright 2006-2007 Nanorex, Inc.  See LICENSE file for details. 
/* $Id: W15.h 7321 2007-05-17 18:17:07Z emessick $ */

#ifndef W15_H_INCLUDED
#define W15_H_INCLUDED

#include "W1.h"

class W15: public W1
{
 public:
    W15(int a, int b, double c, int nshells, double sshell, int terminator);
};

#endif
