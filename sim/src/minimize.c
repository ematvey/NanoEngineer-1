// Copyright 2005-2006 Nanorex, Inc.  See LICENSE file for details. 
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>

#include "simulator.h"

static char const rcsid[] = "$Id: minimize.c 9214 2007-05-11 04:41:33Z emessick $";

// Some of the routines in this file are based on routines found in
// "Numerical Recipes in C, Second Edition", by William H. Press, Saul
// A. Teukolsky, William T. Vetterling, and Brian P. Flannery,
// Cambridge University Press, ISBN 0 521 43108 5.  The routines
// mnbrak(), brent(), linmin(), and frprmn() from Chapter 10 were
// heavily adapted for use here.  Adaptations included: the
// combination of coordinate, parametric, and gradient information
// into a single structure, addition of a reference count garbage
// collector for those structures, folding of linear parameterization
// from gradients into linear minimization and bracketing, and program
// commentary.  Many of the algorithms and variable names are similar
// or identical, so the text can be used as a reference for
// understanding these routines.

// Notes on the reference count garbage collector:
//
// Structures returned from routines are generally considered to have
// a reference to them already, so the return value from a function
// should be assigned directly instead of using SetConfiguration().
// The variable being assigned to in this situation should be NULL
// before the function call.  Set it to NULL using SetConfiguration()
// if necessary.
//
// Variables should be created with NULL values in them.  Be sure to
// set them back to NULL before returning.  Other than as above,
// assignments should be done with SetConfiguration() to track the
// reference counts properly.
//
// Enter() and Leave() allow you to declare the number of items that
// should be allocated by the routine.  A message will be printed to
// stderr if the actual count doesn't match.  These checks are minimal
// enough compared to a full function or gradient evaluation that they
// can be left in.
//
// Total allocation counts can also be used to insure that all memory
// is being freed properly.  See the test routine at the bottom.
//
// To track a single item and watch it's reference count changing, set
// PROBE to the object when it is first allocated.

#define GOLDEN_RATIO 1.61803399
#define DONT_DIVIDE_BY_ZERO 1e-10
#define PARABOLIC_BRACKET_LIMIT 10.0
#define TOLERANCE_AT_ZERO 1e-10
#define LINEAR_ITERATION_LIMIT 100
#define EPSILON 1e-10

static struct configuration *PROBE = NULL;

void
initializeFunctionDefinition(struct functionDefinition *fd,
                             void (*func)(struct configuration *p),
                             int dimension,
                             int messageBufferLength)
{
    NULLPTR(func);
    fd->func = func;
    fd->dfunc = NULL;
    fd->freeExtra = NULL;
    fd->termination = NULL;
    fd->constraints = NULL;
    fd->tolerance = 1e-8;
    fd->algorithm = PolakRibiereConjugateGradient;
    fd->linear_algorithm = LinearMinimize;
    fd->gradient_delta = 1e-8;
    fd->dimension = dimension;
    fd->initial_parameter_guess = 1.0;
    fd->parameter_limit = MAXDOUBLE;
    fd->functionEvaluationCount = 0;
    fd->gradientEvaluationCount = 0;
    if (messageBufferLength > 0) {
        fd->message = (char *)allocate(messageBufferLength);
        fd->message[0] = '\0';
        fd->messageBufferLength = messageBufferLength;
    } else {
        fd->message = "";
        fd->messageBufferLength = 0;
    }
    fd->allocationCount = 0;
    fd->freeCount = 0;
    fd->maxAllocation = 0;
}

// Append a message to then end of the message buffer.  The buffer is
// fixed length, and we just stop appending when it's full.
static void
message(struct functionDefinition *fd, const char *format, ...)
{
    va_list args;
    char subbuf[200];
    char *message = fd->message;
    int messageBufferLength = fd->messageBufferLength;
    int len;

    if (message == NULL || messageBufferLength == 0) {
	return;
    }
    len = strlen(message);
    message += len;
    messageBufferLength -= len;
    if (messageBufferLength <= 1) {
	return;
    }
    *message++ = ' ';
    *message = '\0';

    va_start(args, format);
    len = vsprintf(subbuf, format, args);
    va_end(args);

    if (messageBufferLength < len)
	len = messageBufferLength;
    strncpy(message, subbuf, len);
    message[len] = '\0';
}

struct configuration *
makeConfiguration(struct functionDefinition *fd)
{
    struct configuration *ret;

    ret = (struct configuration *)allocate(sizeof(struct configuration));
    ret->functionValue = 0.0;
    ret->coordinate = (double *)allocate(sizeof(double) * fd->dimension);
    ret->gradient = NULL;
    ret->parameter = 0.0;
    ret->functionDefinition = fd;
    ret->extra = NULL;
    ret->functionValueValid = 0;
    ret->referenceCount = 1;
    fd->allocationCount++;
    if (fd->allocationCount - fd->freeCount > fd->maxAllocation) {
	fd->maxAllocation = fd->allocationCount - fd->freeCount;
    }
    return ret;
}

void
freeConfiguration(struct configuration *conf)
{
    conf->functionDefinition->freeCount++;
    if (conf == PROBE) {
	fprintf(stderr, "freeing PROBE\n");
	return;
    }
    if (conf->extra != NULL && conf->functionDefinition->freeExtra != NULL) {
	(*conf->functionDefinition->freeExtra)(conf);
    }
    if (conf->coordinate != NULL) {
	free(conf->coordinate);
    }
    if (conf->gradient != NULL) {
	free(conf->gradient);
    }
    free(conf);
}

void
SetConfiguration(struct configuration **dst, struct configuration *src)
{
    if (*dst == src) {
	return;
    }
    if (*dst != NULL) {
	if (*dst == PROBE) {
	    fprintf(stderr, "decrementing PROBE from %d\n", (*dst)->referenceCount);
	}
	if (--((*dst)->referenceCount) < 1) {
	    freeConfiguration(*dst);
	}
    }
    *dst = src;
    if (*dst != NULL) {
	if (*dst == PROBE) {
	    fprintf(stderr, "incrementing PROBE from %d\n", (*dst)->referenceCount);
	}
	(*dst)->referenceCount++;
    }
}

#if 0
#define CheckRef(p, rc) CheckReferenceCount(p, rc, __LINE__, # p)
static void
CheckReferenceCount(struct configuration *p, int rc, int line, char *name)
{
    if (p->referenceCount != rc) {
	fprintf(stderr, "refcount of %s (%d) != %d at line %d\n", name, p->referenceCount, rc, line);
    }
}
#endif

#define Enter(config) int _used = config->functionDefinition->allocationCount - config->functionDefinition->freeCount
#define Leave(name, config, count) LeaveRoutine(# name, config, count, _used)
static void
LeaveRoutine(char *name, struct configuration *config, int count, int used)
{
    struct functionDefinition *fd = config->functionDefinition;
    int usedNow = fd->allocationCount - fd->freeCount;

    if (usedNow - used != count) {
	fprintf(stderr, "%s allocated %d instead of %d\n", name, usedNow - used, count);
    }
}



double
evaluate(struct configuration *p)
{
    struct functionDefinition *fd;

    NULLPTRR(p, 0.0);
    fd = p->functionDefinition;
    if (p->functionValueValid == 0) {
	NULLPTRR(fd->func, 0.0);
	(*fd->func)(p);
	CHECKNANR(p->functionValue, 0.0);
	p->functionValueValid = 1;
	fd->functionEvaluationCount++;
    }
    return p->functionValue;
}

void
evaluateGradientFromPotential(struct configuration *p)
{
    struct functionDefinition *fd;
    struct configuration *pPlusDelta = NULL;
    struct configuration *pMinusDelta = NULL;
    int i;
    int j;

    NULLPTR(p);
    fd = p->functionDefinition;
    NULLPTR(fd);
    if (fd->gradient_delta == 0.0) {
	fd->gradient_delta = 1e-8;
    }
    for (i=0; i<fd->dimension; i++) {
	pPlusDelta = makeConfiguration(fd);
	for (j=0; j<fd->dimension; j++) {
	    pPlusDelta->coordinate[j] = p->coordinate[j];
	}
	pPlusDelta->coordinate[i] += fd->gradient_delta / 2.0;

	pMinusDelta = makeConfiguration(fd);
	for (j=0; j<fd->dimension; j++) {
	    pMinusDelta->coordinate[j] = p->coordinate[j];
	}
	pMinusDelta->coordinate[i] -= fd->gradient_delta / 2.0;

	p->gradient[i] = (evaluate(pMinusDelta) - evaluate(pPlusDelta)) / fd->gradient_delta;
	BAIL();
	SetConfiguration(&pPlusDelta, NULL);
	SetConfiguration(&pMinusDelta, NULL);
    }
}

void
evaluateGradient(struct configuration *p)
{
    struct functionDefinition *fd;
    int i;
    double gradientCoordinate;

    NULLPTR(p);
    fd = p->functionDefinition;
    NULLPTR(fd);
    if (p->gradient == NULL) {
	p->gradient = (double *)allocate(sizeof(double) * fd->dimension);
	if (fd->dfunc == NULL) {
	    evaluateGradientFromPotential(p); BAIL();
	} else {
	    (*fd->dfunc)(p); BAIL();
	}
	fd->gradientEvaluationCount++;
	p->parameter = 0.0;
	p->maximumCoordinateInGradient = 0.0;
	for (i=fd->dimension-1; i>=0; i--) {
	    CHECKNAN(p->gradient[i]);
	    gradientCoordinate = fabs(p->gradient[i]);
	    if (p->maximumCoordinateInGradient < gradientCoordinate) {
		p->maximumCoordinateInGradient = gradientCoordinate;
	    }
	}
    }
}

// Return a new configuration which is p+q*gradient(p)
struct configuration *
gradientOffset(struct configuration *p, double q)
{
    struct functionDefinition *fd = p->functionDefinition;
    struct configuration *r;
    int i;

    r = makeConfiguration(fd);
    evaluateGradient(p); BAILR(p);
    for (i=fd->dimension-1; i>=0; i--) {
	r->coordinate[i] = p->coordinate[i] + q * p->gradient[i];
    }
    r->parameter = q;
    if (fd->constraints != NULL) {
        (*fd->constraints)(r);
    }
    return r;
}

// return value, unless it is outside the range [-max..max], in which
// case return +/- max
static double
signClamp(double value, double max)
{
    return (value > max) ? max : ((value < -max) ? -max : value);
}

// Given a configuration p, find three configurations (a, b, c) such
// that f(b) < f(a) and f(b) < f(c), where a, b, and c are colinear in
// configuration space, with b between a and c.  This assures that a
// local minimum exists between a and c.
//
// If the function is monotonic to parameterLimit, we could exit with
// b and c having the same parameter value (but being distinct
// configuration objects).  It looks like this won't confuse brent(),
// but it would be nice to be sure...
static void
bracketMinimum(struct configuration **ap,
               struct configuration **bp,
               struct configuration **cp,
               struct configuration *p)
{
    struct configuration *a = NULL;
    struct configuration *b = NULL;
    struct configuration *c = NULL;
    struct configuration *u = NULL;
    double nx;
    double r;
    double q;
    double denom;
    double ulimit;
    double parameterLimit;

    Enter(p);
    SetConfiguration(&a, p);
    a->parameter = 0.0;
    evaluateGradient(p); // this lets (*dfunc)() set initial_parameter_guess
    BAIL();
    parameterLimit = fabs(p->functionDefinition->parameter_limit);
    // when we step GOLDEN_RATIO beyond b, we don't want to exceed parameterLimit.
    b = gradientOffset(p,
                       signClamp(p->functionDefinition->initial_parameter_guess,
                                 parameterLimit / (GOLDEN_RATIO + 1.0)));
    BAIL();
    if (evaluate(b) > evaluate(a)) {
	// swap a and b, so b is downhill of a
	u = a;
	a = b;
	b = u;
	u = NULL;
    }
    nx = b->parameter + GOLDEN_RATIO * (b->parameter - a->parameter);
    c = gradientOffset(p, nx); BAIL();
    while (evaluate(b) > evaluate(c) && !Interrupted && !EXCEPTION) {

	// u is the extreme point for a parabola passing through a, b, and c:
	r = (b->parameter - a->parameter) * (evaluate(b) - evaluate(c));
	q = (b->parameter - c->parameter) * (evaluate(b) - evaluate(a));
	denom = q - r;
	if (denom < 0.0) {
	    if (denom > -DONT_DIVIDE_BY_ZERO) {
		denom = -DONT_DIVIDE_BY_ZERO;
	    }
	} else {
	    if (denom < DONT_DIVIDE_BY_ZERO) {
		denom = DONT_DIVIDE_BY_ZERO;
	    }
	}
	nx = b->parameter -
	    ((b->parameter - c->parameter) * q - (b->parameter - a->parameter) * r) /
	    (2.0 * denom);
        nx = signClamp(nx, parameterLimit);
	SetConfiguration(&u, NULL);
	u = gradientOffset(p, nx); BAIL();

	// a, b, and c are in order, ulimit is far past c
	ulimit = b->parameter + PARABOLIC_BRACKET_LIMIT * (c->parameter - b->parameter);
        ulimit = signClamp(ulimit, parameterLimit);

	if ((b->parameter-u->parameter) * (u->parameter-c->parameter) > 0.0) {
	    // u is between b and c, also f(c) < f(b) and f(b) < f(a)
	    if (evaluate(u) < evaluate(c)) { // success: (b, u, c) brackets
		*ap = b;
		*bp = u;
		*cp = c;
		SetConfiguration(&a, NULL);
		Leave(bracketMinimum, p, (p == *ap || p == *bp || p == *cp) ? 2 : 3);
		return;
	    }
	    if (evaluate(u) > evaluate(b)) { // success: (a, b, u) brackets
		*ap = a;
		*bp = b;
		*cp = u;
		SetConfiguration(&c, NULL);
		Leave(bracketMinimum, p, (p == *ap || p == *bp || p == *cp) ? 2 : 3);
		return;
	    }
	    // b, u, c monotonically decrease, u is useless.
	    // try default golden ration extension for u:
	    nx = c->parameter + GOLDEN_RATIO * (c->parameter - b->parameter);
            nx = signClamp(nx, parameterLimit);
	    SetConfiguration(&u, NULL);
	    u = gradientOffset(p, nx);
	} else if ((c->parameter-u->parameter) * (u->parameter-ulimit) > 0.0) {
	    // u is between c and ulimit
	    if (evaluate(u) < evaluate(c)) {
		// we're still going down, keep going
		SetConfiguration(&b, c);
		SetConfiguration(&c, u);
		SetConfiguration(&u, NULL);
		nx = c->parameter + GOLDEN_RATIO * (c->parameter - b->parameter);
                nx = signClamp(nx, parameterLimit);
		u = gradientOffset(p, nx);
	    }
	} else if ((u->parameter-ulimit) * (ulimit-c->parameter) >= 0.0) {
	    // u is past ulimit, reign it in
	    nx = ulimit;
	    SetConfiguration(&u, NULL);
	    u = gradientOffset(p, nx);
	    // XXX we did an extra gradientOffset of the old ux that we're
	    // discarding.  would be nice to avoid that.
	} else {
	    // u must be before b
	    // since (a b c) are monotonic decreasing, u should be a
	    // maximum, so we reject it.
	    nx = c->parameter + GOLDEN_RATIO * (c->parameter - b->parameter);
            nx = signClamp(nx, parameterLimit);
	    SetConfiguration(&u, NULL);
	    u = gradientOffset(p, nx);
	}
	SetConfiguration(&a, b);
	SetConfiguration(&b, c);
	SetConfiguration(&c, u);
	SetConfiguration(&u, NULL);
    }
    if (Interrupted) {
        SetConfiguration(&a, NULL);
	evaluateGradient(p);
	BAIL();
	parameterLimit = fabs(p->functionDefinition->parameter_limit);
	*bp = gradientOffset(p,
			     signClamp(p->functionDefinition->initial_parameter_guess,
				       parameterLimit / (GOLDEN_RATIO + 1.0)));
        SetConfiguration(&c, NULL);
        SetConfiguration(&u, NULL);
        Leave(bracketMinimum, p, 0);
        return;
    }
    if (EXCEPTION) {
        // We haven't succeeded in bracketing, so we leave the results
        // as all NULL's.  Caller needs to check for this.
        SetConfiguration(&a, NULL);
        SetConfiguration(&b, NULL);
        SetConfiguration(&c, NULL);
        SetConfiguration(&u, NULL);
        Leave(bracketMinimum, p, 0);
        return;
    }
        
    // success: (a, b, c) brackets
    *ap = a;
    *bp = b;
    *cp = c;
    SetConfiguration(&u, NULL);
    Leave(bracketMinimum, p, (p == *ap || p == *bp || p == *cp) ? 2 : 3);
}

// Brent's method of inverse parabolic interpolation.
// parent is only used to make new configurations along it's gradient line.
// (a, b, c) bracket a minimum.  Returns a new configuration within
// tolerance of the actual minimum within the bracketing interval.
static struct configuration *
brent(struct configuration *parent,
      struct configuration *initial_a,
      struct configuration *initial_b,
      struct configuration *initial_c,
      double tolerance)
{
    struct configuration *a = NULL; // left side of bracketing interval
    struct configuration *b = NULL; // right side of bracketing interval
    struct configuration *u = NULL; // most recent function evaluation
    struct configuration *v = NULL; // previous value of w
    struct configuration *w = NULL; // second least function value
    struct configuration *x = NULL; // least function value found so far
    double d; // how far to move x
    double e; // previous value of d
    double r;
    double q;
    double p;
    double ux; // parameter value used to construct new point u
    double etemp;
    double xm; // midpoint between a and b
    double tol; // tolerance scaled by x position
    double maxp; // maximum coordinate in gradient, multiply parameters by this for tolerance testing
    int iteration;

    Enter(parent);
    SetConfiguration(&x, initial_b);
    SetConfiguration(&w, initial_b);
    SetConfiguration(&v, initial_b);
    // a and b may be swapped, put them in the right order
    if (initial_a->parameter > initial_c->parameter) {
	SetConfiguration(&a, initial_c);
	SetConfiguration(&b, initial_a);
    } else {
	SetConfiguration(&a, initial_a);
	SetConfiguration(&b, initial_c);
    }

    maxp = parent->maximumCoordinateInGradient;

    // At this point, a is the left side of the interval, b is the right
    // side.  v, w, and x are all our middle point between the ends.

    d = 0.0;
    e = 0.0;
    Leave(brent_beforeLoop, parent, 0);
    for (iteration=1; iteration<=LINEAR_ITERATION_LIMIT && !Interrupted && !EXCEPTION; iteration++) {
	xm = 0.5 * (a->parameter + b->parameter); // midpoint of bracketing interval
	tol = tolerance * fabs(x->parameter) + TOLERANCE_AT_ZERO ;
	DPRINT3(D_MINIMIZE, "brent: x: %e xm: %e |x-xm|: %e\n",
		x->parameter, xm, fabs(x->parameter - xm));
	DPRINT3(D_MINIMIZE, "brent: tol: %e (b-a)/2: %e 2*tol-(b-a)/2: %e\n",
		tol, 0.5 * (b->parameter - a->parameter),
		2.0 * tol - 0.5 * (b->parameter - a->parameter));
	// if (b - a > 4 * tol) then right hand side of following is < 0
	if (fabs(x->parameter - xm) <= (tol * 2.0 - 0.5 * (b->parameter - a->parameter))) {
	    // width of interval (a, b) is less than 4 * tol
	    // x is close to the center of the interval
	    // we're done!
	    SetConfiguration(&a, NULL);
	    SetConfiguration(&b, NULL);
	    SetConfiguration(&u, NULL);
	    SetConfiguration(&v, NULL);
	    SetConfiguration(&w, NULL);
	    Leave(brent, parent, (x == initial_b) ? 0 : 1);
            DPRINT3(D_MINIMIZE, "leaving brent, parameter %e * %e == %e\n",
                   x->parameter, maxp, x->parameter * maxp);
	    return x;
	}
	if (fabs(e) > tol) {
	    // v, w, and x are our best points so far, compute the minimum
	    // of a parabola passing through them.
	    r = (x->parameter - w->parameter) * (evaluate(x) - evaluate(v)) ;
	    q = (x->parameter - v->parameter) * (evaluate(x) - evaluate(w)) ;
	    p = (x->parameter - v->parameter) * q - (x->parameter - w->parameter) * r ;
	    q = 2.0 * (q - r) ;
	    if (q > 0.0) {
		p = -p ;
	    } else {
		q = -q;
	    }
	    // parabolic minimum is at: x->parameter + p / q
	    // q >= 0

	    etemp = e;
	    e = d;
	    if (fabs(p) >= fabs(0.5 * q * etemp) ||       // step >= prev_step / 2
		p <= q * (a->parameter - x->parameter) || // step goes to the left of a
		p >= q * (b->parameter - x->parameter))   // step goes to the right of b
		{
		    // we don't like the parabolic step, try golden mean instead
		    e = (x->parameter >= xm) ?
			(a->parameter - x->parameter) :
			(b->parameter - x->parameter) ;
		    d = (2.0 - GOLDEN_RATIO) * e ;
		} else {
		    d = p / q ;
		    ux = x->parameter + d ; // this is the pure parabolic minimum
		    if (ux - a->parameter < tol * 2.0 || b->parameter - ux < tol * 2.0) {
			// too close to left or right bound
			// step in just a bit towards the middle instead
			d = (xm - x->parameter < 0) ? -tol : tol ;
		    }
		}
	} else {
	    // not enough points for parabolic interpolation
	    // use golden mean instead
	    e = (x->parameter >= xm) ?
		(a->parameter - x->parameter) :
		(b->parameter - x->parameter) ;
	    d = (2.0 - GOLDEN_RATIO) * e ;
	}
	// u = x + d, but is at least tol different from x
	ux = (fabs(d) >= tol) ?
	    (x->parameter + d) :
	    (x->parameter + ((d<0) ? -tol : tol)) ;
	SetConfiguration(&u, NULL);
	u = gradientOffset(parent, ux);
	if (evaluate(u) <= evaluate(x)) {
	    // u is better than x (the best up until now)
	    // pull the opposite side bound in to x
	    if (u->parameter >= x->parameter) {
		SetConfiguration(&a, x);
	    } else {
		SetConfiguration(&b, x);
	    }
	    // ratchet all vars down one step so x is new best
	    SetConfiguration(&v, w);
	    SetConfiguration(&w, x);
	    SetConfiguration(&x, u);
	    SetConfiguration(&u, NULL);
	} else {
	    // u doesn't beat the current x
	    // since u is closer to x than the bound
	    // pull the appropriate bound in to u
	    if (u->parameter < x->parameter) {
		SetConfiguration(&a, u);
	    } else {
		SetConfiguration(&b, u);
	    }
	    if (evaluate(u) <= evaluate(w) || u->parameter == w->parameter) {
		// u is better than w (the second best until now)
		// ratchet v and w down, but leave x alone (still the best)
		SetConfiguration(&v, w);
		SetConfiguration(&w, u);
	    } else if (evaluate(u) <= evaluate(v) ||
		       v->parameter == x->parameter ||
		       v->parameter == w->parameter)
		{
		    // u is third best, so set v to record that
		    SetConfiguration(&v, u);
		}
	}
    }
    // For either an interrupt or an exception, x should always be the
    // best value found so far, so we can safely return it.
    if (!Interrupted && !EXCEPTION) {
        message(parent->functionDefinition, "reached iteration limit in linearMinimize\n");
    }
    // too many iterations without getting close enough
    SetConfiguration(&a, NULL);
    SetConfiguration(&b, NULL);
    SetConfiguration(&u, NULL);
    SetConfiguration(&v, NULL);
    SetConfiguration(&w, NULL);
    if (x == initial_b) {
	Leave(brent, parent, 0);
    } else {
	Leave(brent, parent, 1);
    }
    return x;
}


// Perform a one dimensional minimization starting at configuration p.
// The gradient of the function at p is calculated, and the
// minimization is along the line of that gradient.  The resulting
// minimum configuration point is returned.
static struct configuration *
linearMinimize(struct configuration *p,
               double tolerance,
               enum linearAlgorithm algorithm)
{
    struct configuration *a = NULL;
    struct configuration *b = NULL;
    struct configuration *c = NULL;
    struct configuration *min = NULL;

    Enter(p);
    bracketMinimum(&a, &b, &c, p);
    BAILR(NULL);
    if (Interrupted) return b;
    NULLPTRR(a, p);
    NULLPTRR(b, p);
    NULLPTRR(c, p);
    if (DEBUG(D_MINIMIZE)) {
        message(p->functionDefinition, "bmin: a %e[%e] b %e[%e] c %e[%e]",
                evaluate(a), a->parameter,
                evaluate(b), b->parameter,
                evaluate(c), c->parameter);
    }
    if (algorithm == LinearBracket && b != p) {
	SetConfiguration(&min, b);
    } else {
	min = brent(p, a, b, c, tolerance);
    }
    //printf("minimum at parameter value: %e, function value: %e\n", min->parameter, evaluate(min));
    SetConfiguration(&a, NULL);
    SetConfiguration(&b, NULL);
    SetConfiguration(&c, NULL);
    if (DEBUG(D_MINIMIZE) && min == p) {
	message(p->functionDefinition, "linearMinimize returning argument");
    }
    Leave(linearMinimize, p, (min == p) ? 0 : 1);
    return min;
}

int
defaultTermination(struct functionDefinition *fd,
                   struct configuration *previous,
                   struct configuration *current)
{
    double fp = evaluate(previous);
    double fq = evaluate(current);
    double tolerance = fd->tolerance;
    
    DPRINT2(D_MINIMIZE, "delta %e, tol*avgVal %e\n",
            fabs(fq-fp), tolerance * (fabs(fq)+fabs(fp)+EPSILON)/2.0);
    if (2.0 * fabs(fq-fp) <= tolerance * (fabs(fq)+fabs(fp)+EPSILON)) {
        if (DEBUG(D_MINIMIZE)) {
            message(fd,
                    "fp: %e fq: %e || delta %e <= tolerance %e * averageValue %e",
                    fp, fq,
                    fabs(fq-fp), tolerance, (fabs(fq)+fabs(fp)+EPSILON)/2.0);
        }
        return 1;
    }
    return 0;
}


// Starting with an initial configuration p, find the configuration
// which minimizes the value of the function (as defined by fd).  The
// number of iterations used is returned in iteration.
static struct configuration *
minimize_one_tolerance(struct configuration *initial_p,
                       int *iteration,
                       int iterationLimit)
{
    struct functionDefinition *fd;
    double fp;
    double dgg;
    double gg;
    double gamma;
    struct configuration *p = NULL;
    struct configuration *q = NULL;
    int i;

    Enter(initial_p);
    NULLPTRR(initial_p, NULL);
    NULLPTRR(iteration, initial_p);
    fd = initial_p->functionDefinition;
    NULLPTRR(fd, initial_p);
    if (fd->termination == NULL) {
        fd->termination = defaultTermination;
    }
    SetConfiguration(&p, initial_p);
    fp = evaluate(p);
    BAILR(initial_p);
    for ((*iteration)=0; (*iteration) < iterationLimit && !Interrupted; (*iteration)++) {
	SetConfiguration(&q, NULL);
	q = linearMinimize(p, fd->tolerance, fd->linear_algorithm);
        // If linearMinimize made some progress, but threw an
        // exception, then we want the best result, which is q.  If it
        // threw an exception and returned NULL, the best we can do
        // at this point is p.  Beyond this point, we can bail with q.
	BAILR(q == NULL ? p : q);
        if ((fd->termination)(fd, p, q)) {
	    SetConfiguration(&p, NULL);
	    Leave(minimize_one_tolerance, initial_p, (q == initial_p) ? 0 :1);
	    return q;
	}
	evaluateGradient(p); // should have been evaluated by linearMinimize already
	BAILR(q);
	evaluateGradient(q);
	BAILR(q);
	if (fd->algorithm != SteepestDescent) {
	    dgg = gg = 0.0;
	    if (fd->algorithm == PolakRibiereConjugateGradient) {
		for (i=fd->dimension-1; i>=0; i--) {
		    gg += p->gradient[i] * p->gradient[i];
		    // following line implements Polak-Ribiere
		    dgg += (q->gradient[i] + p->gradient[i]) * q->gradient[i] ;
		}
	    } else { // fd->algorithm == FletcherReevesConjugateGradient
		// NOTE: Polak-Ribiere may handle non-quadratic minima better
		// than Fletcher-Reeves
		for (i=fd->dimension-1; i>=0; i--) {
		    gg += p->gradient[i] * p->gradient[i];
		    // following line implements Fletcher-Reeves
		    dgg += q->gradient[i] * q->gradient[i] ;
		}
	    }
	    if (gg == 0.0) {
		// rather than divide by zero below, note that the gradient
		// is zero, so we must be done.
		DPRINT(D_MINIMIZE, "gg==0 in minimize_one_tolerance\n");
		SetConfiguration(&p, NULL);
		Leave(minimize_one_tolerance, initial_p, 1);
		return q;
	    }
	    gamma = dgg / gg;
	    DPRINT3(D_MINIMIZE, "gamma[%e] = %e / %e\n", gamma, dgg, gg);
	    for (i=fd->dimension-1; i>=0; i--) {
		q->gradient[i] += gamma * p->gradient[i];
	    }
	}
	fp = evaluate(q); // previous value of function
	BAILR(q);
	SetConfiguration(&p, q);
    }
    if (Interrupted) {
        message(fd, "minimization interrupted");
    } else {
        message(fd, "reached iteration limit");
    }
    SetConfiguration(&p, NULL);
    Leave(minimize_one_tolerance, initial_p, 1);
    return q;
}

// Starting with an initial configuration p, find the configuration
// which minimizes the value of the function (as defined by fd).  The
// number of iterations used is returned in iteration.
struct configuration *
minimize(struct configuration *initial_p,
         int *iteration,
         int iterationLimit)
{
    struct functionDefinition *fd;
    struct configuration *final = NULL;

    Enter(initial_p);
    NULLPTRR(initial_p, NULL);
    fd = initial_p->functionDefinition;
    NULLPTRR(fd, initial_p);
    NULLPTRR(iteration, initial_p);
    final = minimize_one_tolerance(initial_p,
                                   iteration,
                                   iterationLimit);
    Leave(minimize, initial_p, (final == initial_p) ? 0 :1);
    // final probably shouldn't ever be NULL, but it's conceivable in
    // some exception processing cases.  If that happens, then we
    // haven't made any progress, so return initial_p.
    return final == NULL ? initial_p : final;
}

#ifdef TEST

static double
test(double x, double y)
{
    double rsquared = x*x + y*y;
    //return cos(sqrt(rsquared) + atan2(x, y) + 3.1415926) * exp(-rsquared/700);
    double r = sqrt(rsquared);
    double theta = atan2(x, y);
    double phi = r + theta + 3.1415926;
    double expterm = exp(-rsquared/700);
    double costerm = cos(phi);
    double result = costerm * expterm;
    return result;
}

static void
testFunction(struct configuration *p)
{
    p->functionValue = test(p->coordinate[0], p->coordinate[1]);
    //printf("%f %f\n", p->coordinate[0], p->coordinate[1]);
}

#define DELTA 1e-5
static void
testGradient(struct configuration *p)
{
    double x = p->coordinate[0];
    double y = p->coordinate[1];

    printf("%f %f\n", p->coordinate[0], p->coordinate[1]);
    p->gradient[0] = (test(x, y) - test(x+DELTA, y)) / DELTA;
    p->gradient[1] = (test(x, y) - test(x, y+DELTA)) / DELTA;
}

static void
testMinimize()
{
    struct functionDefinition fd;
    struct configuration *initial = NULL;
    struct configuration *final = NULL;
    int iteration;

    initializeFunctionDefinition(&fd, testFunction, 2, 0);
    fd.func = testFunction;

    fd.coarse_tolerance = 1e-5;
    fd.fine_tolerance = 1e-8;

    initial = makeConfiguration(&fd);
    initial->coordinate[0] = 6.0;
    initial->coordinate[1] = -5.0;

    final = minimize(initial, &iteration, 400);
    fprintf(stderr, "final minimum at (%f %f): %f\n",
	    final->coordinate[0],
	    final->coordinate[1],
	    evaluate(final));
    SetConfiguration(&initial, NULL);
    SetConfiguration(&final, NULL);
    fprintf(stderr, "after %d iterations, %d function evals, %d gradient evals\n",
	    iteration,
	    fd.functionEvaluationCount,
	    fd.gradientEvaluationCount);
    fprintf(stderr, "allocation: %d, free: %d, remaining: %d, maximum: %d\n",
	    fd->allocationCount,
	    fd->freeCount,
	    fd->allocationCount - fd->freeCount,
	    fd->maxAllocation);
}

int
main(int argc, char **argv)
{
    testMinimize();
    exit(0);
}

#endif

/*
 * Local Variables:
 * c-basic-offset: 4
 * tab-width: 8
 * End:
 */
