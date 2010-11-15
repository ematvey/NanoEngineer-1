// Copyright 2005-2006 Nanorex, Inc.  See LICENSE file for details. 
//#define WWDEBUG
#include "simulator.h"

static char const rcsid[] = "$Id: jigs.c 9214 2007-05-11 04:41:33Z emessick $";

/** kT @ 300K is 4.14 zJ -- RMS V of carbon is 1117 m/s
    or 645 m/s each dimension, or 0.645 pm/fs  */

static double gavss(double v) {
    double v0,v1, rSquared;
    do {
	v0=(float)rand()/(float)(RAND_MAX/2) - 1.0;
	v1=(float)rand()/(float)(RAND_MAX/2) - 1.0;
	rSquared = v0*v0 + v1*v1;
    } while (rSquared>=1.0 || rSquared==0.0);
    return v*v0*sqrt(-2.0*log(rSquared)/rSquared);
}

struct xyz gxyz(double v) {
    struct xyz g;
    g.x=gavss(v);
    g.y=gavss(v);
    g.z=gavss(v);
    return g;
}

void
jigGround(struct jig *jig, double deltaTframe, struct xyz *position, struct xyz *new_position, struct xyz *force)
{
    struct xyz foo, bar;
    struct xyz q1;
    int k;
    struct xyz rx;

    vsetc(foo,0.0);
    vsetc(q1,0.0);
    for (k=0; k<jig->num_atoms; k++) { // find center
        vadd(foo,position[jig->atoms[k]->index]);
    }
    vmulc(foo,1.0 / jig->num_atoms);

    for (k=0; k<jig->num_atoms; k++) {
        vsub2(rx,position[jig->atoms[k]->index], foo);
        v2x(bar,rx,force[jig->atoms[k]->index]); // bar = rx cross force[]
        vadd(q1,bar);
    }
    vmulc(q1,deltaTframe);
    vadd(jig->xdata, q1);
    jig->data++;

    for (k=0; k<jig->num_atoms; k++) {
        new_position[jig->atoms[k]->index] = position[jig->atoms[k]->index];
    }
}

/*
 * Springs connect atoms to a flywheel. We drive the flywheel and it
 * pulls the atoms along. The units of spring stiffness are piconewtons
 * per picometer, or equivalently newtons per meter.
 *
 * 10 newtons/meter is too stiff, we get oscillations that grow out of
 * control. 1 N/m and 0.1 N/m give oscillations but they don't go crazy.
 */
#define SPRING_STIFFNESS  10.0

/*
 * We want a damping coefficient that is dimensionless and ranges from
 * zero to one, where zero is no damping at all, and one is complete
 * damping, no sinusoidal component at all.
 *
 * The magic equation here is Mx'' = -Kx - Dx', where M is atom mass,
 * x is atom displacement in the direction of the spring, K is spring
 * stiffness. D is a constant which multiplies by a velocity to give a
 * force, and it acts like friction. Plug in Laplace operator "s" as a
 * derivative, and we have s**2 + (D/M)s  + (K/M) = 0. The solutions to
 * this equation describe the two mechanical resonances of the system,
 * and the negative-ness of the real parts tell us how quickly the
 * oscillations in omega die away.
 *
 * Let z be our dimensionless number between zero and one, and let D =
 * 2z * sqrt(KM). Then the resonances occur at
 *
 *     s = sqrt(K/M) * (-z +/- j * sqrt(1-z**2))
 *
 * where "j" is sqrt(-1), giving the imaginary part of s. The real
 * part is negative, indicating that it's stable. A positive real part
 * would mean the oscillations were going to grow with time, a bad
 * thing.
 */

void
jigMotor(struct jig *jig, double deltaTframe, struct xyz *position, struct xyz *new_position, struct xyz *force)
{
    int k;
    int a1;
    struct xyz tmp;
    struct xyz f;
    struct xyz r;
    double omega, domega_dt;
    double motorq, dragTorque = 0.0;
    double theta, cos_theta, sin_theta;
    double m;
    const double minspeed = 1.0;  // radians per second, very slow
    const double maxm = 1.0e-4;  // max value for multiplier, make it stable
    struct xyz anchor;

#ifdef WWDEBUG
    /*
     * Bug 1529, where two rotary motors fight. Even though one has
     * zero torque, the torque isn't really zero because it's got that
     * big flywheel to get up to speed. The weak links are the chemical
     * bonds, which go nuts.
     */
    int explain_stuff = 0;
    {
	static long count = 0;
	// odd modulo, so we switch motors
	if ((count % 101) == 0) {
	    MARK();
	    explain_stuff = 1;
	}
	count++;
    }
#endif

    // omega is current motor speed in radians per second.
    // jig->j.rmotor.speed is top (zero torque) speed in radians per second.
    // jig->j.rmotor.stall is zero speed torque in pN-pm or yNm (yocto Nm, 1e-24 Kg m^2 sec^-2)
    omega = jig->j.rmotor.omega;
    // Bosch model
    if (fabs(jig->j.rmotor.speed) < minspeed) {
	if (jig->j.rmotor.speed >= 0) {
	    m = jig->j.rmotor.stall / minspeed;
	} else {
	    m = -jig->j.rmotor.stall / minspeed;
	}
    } else {
	m = jig->j.rmotor.stall / jig->j.rmotor.speed;
    }
    // clip m to maintain stability
    if (m > maxm) m = maxm;
    else if (m < -maxm) m = -maxm;
    // m is yocto Kg m^2 sec^-1 radian^-1: it converts radians/second to pN-pm
    // motorq is yNm
    motorq = m * (jig->j.rmotor.speed - omega);
    // don't let the torque get too big
    if (motorq > 2.0 * jig->j.rmotor.stall) {
	motorq = 2.0 * jig->j.rmotor.stall;
    } else if (motorq < -2.0 * jig->j.rmotor.stall) {
	motorq = -2.0 * jig->j.rmotor.stall;
    }

    cos_theta = cos(jig->j.rmotor.theta);
    sin_theta = sin(jig->j.rmotor.theta);

    /* nudge atoms toward their new places */
    for (k = 0; k < jig->num_atoms; k++) {
	struct xyz rprev;
	a1 = jig->atoms[k]->index;
	// get the position of this atom's anchor
	anchor = jig->j.rmotor.center;
	vadd(anchor, jig->j.rmotor.u[k]);
	vmul2c(tmp, jig->j.rmotor.v[k], cos_theta);
	vadd(anchor, tmp);
	vmul2c(tmp, jig->j.rmotor.w[k], sin_theta);
	vadd(anchor, tmp);
        if (_last_iteration && DEBUG(D_DYNAMICS_SIMPLE_MOVIE)) { // -D15
            writeSimplePositionMarker(&anchor, 5.0, 1.0, 1.0, 1.0);
            writeSimplePositionMarker(&jig->j.rmotor.center, 5.0, 1.0, 1.0, 1.0);
        }
	// compute a force pushing on the atom, spring term plus damper term
	r = position[a1];
	vsub(r, anchor);
	rprev = r;
        // r in pm, SPRING_STIFFNESS in N/m, f in pN
	vmul2c(f, r, -SPRING_STIFFNESS);
	if (jig->j.rmotor.damping_enabled) {

	    // this could be optimized a bit more but the intent would be less clear
	    // frictionOverDt = 2 * jig->j.rmotor.dampingCoefficient *
	    //     sqrt(SPRING_STIFFNESS / jig->atoms[k]->inverseMass);
	    // vmul2c(tmp, r, -frictionOverDt);

	    // friction is force divided by velocity
	    double friction = 2 * jig->j.rmotor.dampingCoefficient *
		sqrt(SPRING_STIFFNESS * 1.e-27 * jig->atoms[k]->mass);
	    vsub(r, jig->j.rmotor.rPrevious[k]);
	    // we need a factor of Dt because of Verlet integration
	    vmul2c(tmp, r, -friction / Dt);
	    vadd(f, tmp);
	    jig->j.rmotor.rPrevious[k] = rprev;
	}

	// nudge the new positions accordingly
	vadd2scale(new_position[a1], f, jig->atoms[k]->inverseMass);

	// compute the drag torque pulling back on the motor
	r = vdif(position[a1], jig->j.rmotor.center);
	tmp = vx(r, f);
	dragTorque += vdot(tmp, jig->j.rmotor.axis);
    }

    domega_dt = (motorq - dragTorque) / jig->j.rmotor.momentOfInertia;
    theta = jig->j.rmotor.theta + omega * Dt;
    jig->j.rmotor.omega = omega = jig->j.rmotor.omega + domega_dt * Dt;

    /* update the motor's position */
    theta = fmod(theta, 2.0 * Pi);
    jig->j.rmotor.theta = theta;
    // convert rad/sec to GHz
    jig->data = jig->j.rmotor.omega / (2.0e9 * Pi);
    // convert from pN-pm to nN-nm
    jig->data2 = motorq / ((1e-9/Dx) * (1e-9/Dx));
}

double
jigMinimizePotentialRotaryMotor(struct part *p, struct jig *jig,
                                struct xyz *positions,
                                double *pTheta)
{
    int k;
    int a1;
    // potential is in aJ (1e-18 J, 1e-18 N m)
    // here, aJ radians
    // torque is aN m (nN-nm)
    double potential = -jig->j.rmotor.minimizeTorque * *pTheta;
    double cos_theta = cos(*pTheta);
    double sin_theta = sin(*pTheta);
    struct xyz tmp;
    struct xyz r;
    struct xyz anchor;

    for (k = 0; k < jig->num_atoms; k++) {
	a1 = jig->atoms[k]->index;
	// get the position of this atom's anchor
	anchor = jig->j.rmotor.center;
	vadd(anchor, jig->j.rmotor.u[k]);
	vmul2c(tmp, jig->j.rmotor.v[k], cos_theta);
	vadd(anchor, tmp);
	vmul2c(tmp, jig->j.rmotor.w[k], sin_theta);
	vadd(anchor, tmp);
        if (DEBUG(D_MINIMIZE_POTENTIAL_MOVIE)) { // -D4
            writeSimplePositionMarker(&anchor, 5.0, 1.0, 1.0, 1.0);
            writeSimplePositionMarker(&jig->j.rmotor.center, 5.0, 1.0, 1.0, 1.0);
        }
	// compute potential of the  spring term
	r = positions[a1];
	vsub(r, anchor);
        // r in pm
        // SPRING_STIFFNESS is in N/m
        // potential in N/m * pm * pm * 1e-6 am/ym or aJ
        potential += 0.5 * SPRING_STIFFNESS * vdot(r, r) * 1e-6; 
    }
    
    return potential;
}

// force is in pN (1e-12 J/m)
// gradient is in pJ/radian
void
jigMinimizeGradientRotaryMotor(struct part *p, struct jig *jig,
                               struct xyz *positions,
                               struct xyz *force,
                               double *pTheta,
                               double *pGradient)
{
    int k;
    int a1;
    double gradient = jig->j.rmotor.minimizeTorque; // aN m
    double cos_theta = cos(*pTheta);
    double sin_theta = sin(*pTheta);
    struct xyz tmp;
    struct xyz r;
    struct xyz f;
    struct xyz anchor;

    for (k = 0; k < jig->num_atoms; k++) {
	a1 = jig->atoms[k]->index;
	// get the position of this atom's anchor
	anchor = jig->j.rmotor.center;
	vadd(anchor, jig->j.rmotor.u[k]);
	vmul2c(tmp, jig->j.rmotor.v[k], cos_theta);
	vadd(anchor, tmp);
	vmul2c(tmp, jig->j.rmotor.w[k], sin_theta);
	vadd(anchor, tmp);
        if (DEBUG(D_MINIMIZE_GRADIENT_MOVIE)) { // -D4
            writeSimplePositionMarker(&anchor, 5.0, 1.0, 1.0, 1.0);
            writeSimplePositionMarker(&jig->j.rmotor.center, 5.0, 1.0, 1.0, 1.0);
        }

        // compute a force pushing on the atom due to a spring to the anchor position
	r = positions[a1];
	vsub(r, anchor);
        // r in pm, SPRING_STIFFNESS in N/m, f in pN
	vmul2c(f, r, -SPRING_STIFFNESS);
        vadd(force[a1], f);

	// compute the drag torque pulling back on the motor
	r = vdif(positions[a1], jig->j.rmotor.center);
        // r in pm, f in pN, tmp in yJ, multiply by 1e-6 to get aJ
	tmp = vx(r, f);
	gradient -= vdot(tmp, jig->j.rmotor.axis) * 1e-6; // axis is unit vector
    }

    *pGradient = gradient;
}

void
jigLinearMotor(struct jig *jig, struct xyz *position, struct xyz *new_position, struct xyz *force, double deltaTframe)
{
    int i;
    int a1;
    struct xyz r;
    struct xyz f;
    double ff, x;

    // calculate the average position of all atoms in the motor (r)
    r = vcon(0.0);
    for (i=0;i<jig->num_atoms;i++) {
        /* for each atom connected to the "shaft" */
        r=vsum(r,position[jig->atoms[i]->index]);
    }
    r=vprodc(r, 1.0/jig->num_atoms);

    // x is length of projection of r onto axis (axis is unit vector)
    x=vdot(r,jig->j.lmotor.axis);
    jig->data = x - jig->j.lmotor.motorPosition;

    // f is the amount of force to apply to each atom.  Always a
    // vector along the motor axis.
    if (jig->j.lmotor.stiffness == 0.0) {
        vset(f, jig->j.lmotor.constantForce);
    } else {
	// zeroPosition is projection distance of r onto axis for 0 force
	ff = jig->j.lmotor.stiffness * (jig->j.lmotor.zeroPosition - x) / jig->num_atoms;
	f = vprodc(jig->j.lmotor.axis, ff);
    }
    // Calculate the resulting force on each atom, and project it onto
    // the motor axis.  This dissapates lateral force from the system
    // without translating it anywhere else, or reporting it out.
    // XXX report resulting force on linear bearing out to higher level
    for (i=0;i<jig->num_atoms;i++) {
        a1 = jig->atoms[i]->index;
        // constrain new_position to be along motor axis from position
        ff = vdot(vdif(new_position[a1], position[a1]), jig->j.lmotor.axis);
        vadd2(new_position[a1], position[a1], vprodc(jig->j.lmotor.axis, ff));

        // add f to force, and remove everything except the axial component
        ff = vdot(vsum(force[a1], f), jig->j.lmotor.axis) ;
        vmul2c(force[a1], jig->j.lmotor.axis, ff);
    }
}

// note linear motor has zero degrees of freedom, so pDistance is not valid.
double
jigMinimizePotentialLinearMotor(struct part *p, struct jig *jig,
                                struct xyz *position,
                                double *pDistance)
{
    int i;
    struct xyz r;
    double x;
    double potential;

    // calculate the average position of all atoms in the motor (r)
    r = vcon(0.0);
    for (i=0;i<jig->num_atoms;i++) {
        /* for each atom connected to the "shaft" */
        r=vsum(r,position[jig->atoms[i]->index]);
    }
    r=vprodc(r, 1.0/jig->num_atoms);

    // x is length of projection of r onto axis (axis is unit vector)
    x=vdot(r,jig->j.lmotor.axis);

    if (jig->j.lmotor.stiffness == 0.0) {
	// motorPosition is projection distance of r onto axis for 0 displacement
        x -= jig->j.lmotor.motorPosition;
        // x in pm, jig->j.lmotor.force in pN
        // x * force in yJ
        potential = x * jig->j.lmotor.force * -1e-6; // in aJ
    } else {
	// zeroPosition is projection distance of r onto axis for 0 force
        x -= jig->j.lmotor.zeroPosition;
        // x in pm, stiffness in N/m
        // stiffness * x * x / 2 in yJ
	potential = jig->j.lmotor.stiffness * x * x * 0.5 * 1e-6; // in aJ
    }
    return potential;
}

void
jigMinimizeGradientLinearMotor(struct part *p, struct jig *jig,
                               struct xyz *position,
                               struct xyz *force,
                               double *pDistance,
                               double *pGradient)
{
    int i;
    int a1;
    struct xyz r;
    struct xyz f;
    double ff, x;

    // calculate the average position of all atoms in the motor (r)
    r = vcon(0.0);
    for (i=0;i<jig->num_atoms;i++) {
        /* for each atom connected to the "shaft" */
        r=vsum(r,position[jig->atoms[i]->index]);
    }
    r=vprodc(r, 1.0/jig->num_atoms);

    // x is length of projection of r onto axis (axis is unit vector)
    x=vdot(r,jig->j.lmotor.axis);

    // f is the amount of force to apply to each atom.  Always a
    // vector along the motor axis.
    if (jig->j.lmotor.stiffness == 0.0) {
        vset(f, jig->j.lmotor.constantForce);
    } else {
	// zeroPosition is projection distance of r onto axis for 0 force
	ff = jig->j.lmotor.stiffness * (jig->j.lmotor.zeroPosition - x) / jig->num_atoms;
	f = vprodc(jig->j.lmotor.axis, ff);
    }
    // Calculate the resulting force on each atom, and project it onto
    // the motor axis.
    for (i=0;i<jig->num_atoms;i++) {
        a1 = jig->atoms[i]->index;
        // position constraints have already been applied, and
        // besides, with no non-axial forces we should never get off
        // axis anyway...

        // add f to force, and remove everything except the axial component
        ff = vdot(vsum(force[a1], f), jig->j.lmotor.axis) ;
        vmul2c(force[a1], jig->j.lmotor.axis, ff);
    }
}

void
jigThermometer(struct jig *jig, double deltaTframe, struct xyz *position, struct xyz *new_position)
{
    double z;
    double ff;
    int a1;
    int k;
    int dof; // degrees of freedom
    struct xyz f;

    dof = 3 * jig->num_atoms;

    // average(m * v * v / 2) == 3 * k * T / 2

    // This divides out both the number of iterations (to average one
    // frame), and the number of degrees of freedom.  DOF = 3N-3 if
    // translation has been cancelled, and 3N-6 if rotation has been
    // cancelled as well.
    z = deltaTframe / ((double)dof);
    ff=0.0;
    for (k=0; k<jig->num_atoms; k++) {
	a1 = jig->atoms[k]->index;
        // f is pm/fs (actually Dt/Dx)
	f = vdif(position[a1],new_position[a1]);
        // mass in yg (1e-24 g)
        // ff in yg Dt*Dt/Dx*Dx
	ff += vdot(f, f) * jig->atoms[k]->mass;
    }
    // Boltz is in J/K
    // ff in 1e3 g m m K / s s J   or K
    ff *= Dmass * Dx * Dx / (Dt * Dt * Boltz);
    jig->data += ff*z;
}

// Langevin thermostat
void
jigThermostat(struct jig *jig, double deltaTframe, struct xyz *position, struct xyz *new_position)
{
    double z;
    double ke;
    int a1;
    int k;
    double therm;
    struct xyz v1;
    struct xyz v2;
    double ff;
    double mass;

    z = deltaTframe / (3 * jig->num_atoms);
    ke=0.0;

    for (k=0; k<jig->num_atoms; k++) {
	a1 = jig->atoms[k]->index;
	mass = jig->atoms[k]->mass;
	therm = sqrt((Boltz*jig->j.thermostat.temperature)/
		     (mass * 1e-27))*Dt/Dx;
        v1 = vdif(new_position[a1],position[a1]);
        ff = vdot(v1, v1) * mass;

        vmulc(v1, 1.0 - ThermostatGamma);
        v2= gxyz(ThermostatG1 * therm);
        vadd(v1, v2);
        vadd2(new_position[a1],position[a1],v1);

        // add up the energy
        ke += vdot(v1, v1) * mass - ff;

    }
    ke *= 0.5 * Dx*Dx/(Dt*Dt) * 1e-27 * 1e18;
    jig->data += ke;
}

double
angleBetween(struct xyz xyz1, struct xyz xyz2)
{
    double Lsq1, Lsq2, dprod;
    Lsq1 = vdot(xyz1, xyz1);
    if (Lsq1 < 1.0e-10)
	return 0.0;
    Lsq2 = vdot(xyz2, xyz2);
    if (Lsq2 < 1.0e-10)
	return 0.0;
    dprod = vdot(xyz1, xyz2) / sqrt(Lsq1 * Lsq2);
    if (dprod >= 1.0)
	return 0.0;
    if (dprod <= -1.0)
	return 180.0;
    return (180.0 / Pi) * acos(dprod);
}


void
jigDihedral(struct jig *jig, struct xyz *new_position)
{
    struct xyz wx;
    struct xyz xy;
    struct xyz yx;
    struct xyz zy;
    struct xyz u, v;

    // better have 4 atoms exactly
    vsub2(wx,new_position[jig->atoms[0]->index],
          new_position[jig->atoms[1]->index]);
    vsub2(yx,new_position[jig->atoms[2]->index],
          new_position[jig->atoms[1]->index]);
    vsub2(xy,new_position[jig->atoms[1]->index],
          new_position[jig->atoms[2]->index]);
    vsub2(zy,new_position[jig->atoms[3]->index],
          new_position[jig->atoms[2]->index]);
    // vx = cross product
    u = vx(wx, yx);
    v = vx(xy, zy);
    if (vdot(zy, u) < 0) {
	jig->data = -angleBetween(u, v);
    } else {
	jig->data = angleBetween(u, v);
    }
}


void
jigAngle(struct jig *jig, struct xyz *new_position)
{
    struct xyz v1;
    struct xyz v2;

    // better have 3 atoms exactly
    vsub2(v1,new_position[jig->atoms[0]->index],
          new_position[jig->atoms[1]->index]);
    vsub2(v2,new_position[jig->atoms[2]->index],
          new_position[jig->atoms[1]->index]);
    // jig->data = acos(vdot(v1,v2)/(vlen(v1)*vlen(v2)));
    jig->data = angleBetween(v1, v2);
}


void
jigRadius(struct jig *jig, struct xyz *new_position)
{
    struct xyz v1;

    // better have 2 atoms exactly
    vsub2(v1,new_position[jig->atoms[0]->index],
          new_position[jig->atoms[1]->index]);

    jig->data = vlen(v1);
}

/*
 * Local Variables:
 * c-basic-offset: 4
 * tab-width: 8
 * End:
 */
