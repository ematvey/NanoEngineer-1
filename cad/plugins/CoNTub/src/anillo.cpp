// Copyright 2006-2007 Nanorex, Inc.  See LICENSE file for details. 
/* $Id: anillo.cpp 7321 2007-05-17 18:17:07Z emessick $ */

#include "anillo.h"
#include "Atomo.h"
#include "String.h"

void anillo::addVert (int pton) {
    if (num < 14) {
	num++;
	vert[num] = pton;
    }
}

void anillo::setCentro (pto3D cide) {
    centroide = cide;
}


void anillo::centracentroide (MoleculaT mol) {
    pto3D ncide = pto3D ();
    for (int i = 1; i <= num; i++) {
	Atomo *at = mol.susatomos.get (vert[i]);
	ncide = ncide.mas (at->vert);
    }
    ncide.escala (1 / num);
    if (ncide.dista (centroide) < 0.7)
	centroide = ncide;
}


void anillo::ordena (pto3D vecref, MoleculaT mol) {	//vector de referencia y molecula a la que pertenecen (con toda  informacion 3D
    //creamos un vector que nos indique donde esta el exterior del tubo, y desde donde miramos
    pto3D ciderel = centroide.menos (mol.TEST1);
    pto3D vtop = ciderel.proyeccplano (mol.TESTC);
    //Buscamos atomo mas cercano por la derecha
    int dcha = 0;
    double dis = 10;
    for (int i = 1; i <= num; i++) {
	Atomo *at = mol.susatomos.get (vert[i]);
	pto3D p = at->vert;
	pto3D a = p.menos (centroide).menos (vecref);
	double di = vecref.dista (p.menos (centroide));
	double dh = a.dihedrog (vecref, vtop);
	if (di < dis && dh > 30 && dh < 150) {
	    dis = di;
	    dcha = i;
	}
    }

    ordenaccw (vert[dcha], mol);

}

void anillo::ordenaccw (int ini, MoleculaT mol) {	//vector de referencia y molecula a la que pertenecen (con toda  informacion 3D
    int *newvert = new int[num + 1];
    //creamos un vector que nos indique donde esta el exterior del tubo, y desde donde miramos
    pto3D ciderel = centroide.menos (mol.TEST1);
    pto3D vtop = ciderel.proyeccplano (mol.TESTC);
    //Comenzamos por el atomo de inicio
    newvert[1] = ini;

    for (int i = 2; i <= num; i++) {
	pto3D pobj = mol.susatomos.get(newvert[i - 1])->vert;
	int nizq = 0;
	double dihedrotemp = 0;
	double distan = 10;
	for (int j = 1; j <= num; j++) {
	    Atomo *at = mol.susatomos.get (vert[j]);
	    pto3D c = at->vert;
	    pto3D a = c.menos (pobj);
	    pto3D b = pobj.menos (centroide);
	    double dist = a.modulo ();
	    double dhdr = a.dihedrog (b, vtop);
	    if (dist < distan && dist > 0.01 && dhdr > -150 && dhdr < -30) {
		distan = dist;
		nizq = j;
		dihedrotemp = dhdr;
	    }
	}
	newvert[i] = vert[nizq];
    }
    for (int i = 1; i <= num; i++)
	vert[i] = newvert[i];
}

void anillo::ordenacw (int ini, MoleculaT mol) {	//vector de referencia y molecula a la que pertenecen (con toda  informacion 3D
    int *newvert = new int[num + 1];
    //creamos un vector que nos indique donde esta el exterior del tubo, y desde donde miramos
    pto3D ciderel = centroide.menos (mol.TEST1);
    pto3D vtop = ciderel.proyeccplano (mol.TESTC);
    //Comenzamos por el atomo de inicio
    newvert[1] = ini;

    for (int i = 2; i <= num; i++) {
	pto3D pobj = mol.susatomos.get(newvert[i - 1])->vert;
	int nizq = 0;
	double dihedrotemp = 0;
	double distan = 10;
	for (int j = 1; j <= num; j++) {
	    pto3D c = mol.susatomos.get(vert[j])->vert;
	    pto3D a = c.menos (pobj);
	    pto3D b = pobj.menos (centroide);
	    double dist = a.modulo ();
	    double dhdr = a.dihedrog (b, vtop);
	    if (dist < distan && dist > 0.01 && dhdr < 150 && dhdr > 30) {
		distan = dist;
		nizq = j;
		dihedrotemp = dhdr;
	    }
	}
	newvert[i] = vert[nizq];
    }
    for (int i = 1; i <= num; i++)
	vert[i] = newvert[i];
}

void anillo::rota (int giro) {	//pasa los indices hacia abajo(si giro>0), con lo que se cambia la orientaci�n ccw)
    int *newvert = new int[num + 1];
    for (int i = 1; i <= num; i++) {
	int nuevapos = i - giro;
	if (nuevapos > num && nuevapos < 2 * num)
	    nuevapos = nuevapos - num;
	else if (nuevapos <= 0 && nuevapos > -num)
	    nuevapos = nuevapos + num;
	newvert[i] = vert[nuevapos];
    }
    for (int i = 1; i <= num; i++)
	vert[i] = newvert[i];

}

#if 0
String anillo::aCadena () {
    String cad = String("Miembros: ");
    for (int i = 1; i <= num; i++)
	cad = cad + " " + vert[i];
    if (centroide != NULL)
	cad = cad + " centroide en " + centroide.aTexto ();

    return cad;
}
#endif

/* http://gethelp.devx.com/techtips/cpp_pro/10min/10min0400.asp */
std::ostream& operator<< (std::ostream& s, anillo &a) {
    s << "Miembros: ";
    for (int i = 1; i <= a.num; i++)
	s << " " << a.vert[i];
    if (a.centroide.valid()) {
	s << " centroide en ";
	s << a.centroide;
    }
    //s << " centroide en " << a.centroide.aTexto ();
    return s;
}
