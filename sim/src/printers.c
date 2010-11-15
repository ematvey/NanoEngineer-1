// Copyright 2004-2007 Nanorex, Inc.  See LICENSE file for details. 
/*
 * Routines to handle printing to the trace file.
 *
 * CHANGES  (reverse chronological order, use CVS log for details)
 *
 * wware 060102 - Eliminated a large chunk of code that was if-0-ed off anyway.
 * Use write_traceline() function to replace direct writes to trace file. Add
 * doneNoExit() function, behaves like doneExit() but doesn't exit.
 *
 */

#include "simulator.h"

static char const rcsid[] = "$Id: printers.c 10609 2007-11-15 01:18:00Z ericmessick $";

static char __line[2000], *__p;

static int
countOutputColumns(struct jig *j)
{
    switch (j->type) {
    case RotaryMotor:
        return 2;
    case Ground:
    case Thermometer:
    case DihedralMeter:
    case AngleMeter:
    case RadiusMeter:
    case Thermostat:
    case LinearMotor:
        return 1;
    default:
        return 0;
    }
}

void
traceFileVersion()
{
    write_traceline("# NanoEngineer-1.com Simulator Trace File, Version 050310\n");
    write_traceline("#\n");
}

void traceHeader(struct part *part)
{
    int i, ncols;
    struct jig *j;
    struct tm *ptr;
    time_t tm;
    tm = time(NULL);
    ptr = localtime(&tm);

    if (CommandLine != NULL && CommandLine[0] != '\0') {
        write_traceline("# Command Line: %s\n", CommandLine);
    }
    printGlobals();
    
    // asctime provides '\n' so we needn't add one
    write_traceline("# Date and Time: %s", asctime(ptr));
    if (InputFileName != NULL && InputFileName[0] != '\0') {
        write_traceline("# Input File: %s\n", InputFileName);
    }
    if (GromacsOutputBaseName != NULL && GromacsOutputBaseName[0] != '\0') {
        write_traceline("# Gromacs Output Base Name: %s\n", GromacsOutputBaseName);
    }
    if (OutputFileName != NULL && OutputFileName[0] != '\0') {
        write_traceline("# Output File: %s\n", OutputFileName);
    }
    if (TraceFileName != NULL && TraceFileName[0] != '\0') {
        write_traceline("# Trace File: %s\n", TraceFileName);
    }
    if (IDKey != NULL && IDKey[0] != '\0') {
        write_traceline("# IDKey: %s\n", IDKey);
    }
    if (ToMinimize) {
        write_traceline("#\n");
        write_traceline("# Run type: Energy Minimization.\n");
        write_traceline("#\n");
        write_traceline("# iteration    RMS force (pN)      maximum force (pN)\n");
        write_traceline("#\n");
        return;
    }

    write_traceline("# \n");
    write_traceline("# Run type: Dynamics.\n");
    write_traceline("# \n");
    write_traceline("# Number of Frames: %d\n", NumFrames);
    write_traceline("# Steps per Frame: %d\n", IterPerFrame);
    write_traceline("# Temperature: %.1f\n", Temperature);

    if (part == NULL) {
        write_traceline("# Warning: no part supplied.\n");
        return;
    }

    write_traceline("# Number of Atoms: %d\n", part->num_atoms);
    write_traceline("# \n");

    for (i=0; i<part->num_jigs; i++) {
        j = part->jigs[i];
        switch (j->type) {
                    
        case Thermostat:
            write_traceline("# %s Temperature setting: %f K\n", j->name, j->j.thermostat.temperature);
            break;

        case LinearMotor:
            write_traceline("# %s Force: %f pN\n", j->name, j->j.lmotor.force);
            write_traceline("# %s Stiffness: %f N/m\n", j->name, j->j.lmotor.stiffness);
            break;
               
        case RotaryMotor:
            write_traceline("# %s Zero Speed Torque: %f nN-nm\n", j->name, j->j.rmotor.stall / 1e6);
            write_traceline("# %s Zero Torque Speed: %f Ghz\n", j->name, j->j.rmotor.speed / (2.0e9 * Pi));
            write_traceline("# %s Initial Speed: %f Ghz\n", j->name, j->j.rmotor.omega / (2.0e9 * Pi));
            write_traceline("# %s Damping coefficient: %f\n", j->name, j->j.rmotor.damping_enabled ? j->j.rmotor.dampingCoefficient : 0.0);
            break;

        default:
            break;
        }
    }    
    write_traceline("#\n");
    
    ncols = 0;
    if (PrintPotentialEnergy) {
	ncols += 3;
    }
    
    for (i=0; i<part->num_jigs; i++) {
        ncols += countOutputColumns(part->jigs[i]);
    }

    // Column count does not include the time column.  Cad uses this
    // to configure plotting interface.
    write_traceline("# %d columns:\n", ncols);
    
    for (i=0; i<part->num_jigs; i++) {
        j = part->jigs[i];
        switch (j->type) {

        case DihedralMeter:
            write_traceline("# %s: dihedral (degrees)\n", j->name); 
            break;

        case AngleMeter:
            write_traceline("# %s: angle (degrees)\n", j->name); 
            break;

        case RadiusMeter:
            write_traceline("# %s: distance (angstroms)\n", j->name); 
            break;
       
        case Ground:
            write_traceline("# %s: torque (nn-nm)\n", j->name); 
            break;
                    
        case Thermometer:
            write_traceline("# %s: temperature (K)\n", j->name);
            break;
                    
        case Thermostat:
            write_traceline("# %s: energy added (zJ)\n", j->name);
            break;

        case LinearMotor:
            write_traceline("# %s: displacement (angstroms)\n", j->name);
            break;
               
        case RotaryMotor:
            write_traceline("# %s: speed (GHz)\n", j->name);
            write_traceline("# %s: torque (nn-nm)\n", j->name);
            break;
        }
    }    
    if (PrintPotentialEnergy) {
	write_traceline("# Structure: potential energy (attojoules)\n");
	write_traceline("# Structure: kinetic energy (attojoules)\n");
	write_traceline("# Structure: total energy (attojoules)\n");
    }
    write_traceline("#\n");
}

void traceJigHeader(struct part *part) {
    struct jig *j;
    int i;
    int ncol;

    __p = __line;
    __p += sprintf(__p, "#     Time       ");
    for (i=0; i<part->num_jigs; i++) {
        j = part->jigs[i];
        
	j->data=0.0;
	j->data2=0.0;
	vsetc(j->xdata,0.0);

        switch (j->type) {
        case Ground:        __p += sprintf(__p, "Anchor          "); break;
        case Thermometer:   __p += sprintf(__p, "T.meter         "); break;
        case DihedralMeter: __p += sprintf(__p, "Dihedral        "); break;
        case AngleMeter:    __p += sprintf(__p, "Angle           "); break;
        case RadiusMeter:   __p += sprintf(__p, "Distance        "); break;
        case Thermostat:    __p += sprintf(__p, "T.stat          "); break;
        case LinearMotor:   __p += sprintf(__p, "Lmotor          "); break;
        case RotaryMotor:   __p += sprintf(__p, "speed           torque          ");
	}
    }
    sprintf(__p, "\n");
    write_traceline(__line);
    __p = __line;
    __p += sprintf(__p, "#  picosec      ");

    for (i=0; i<part->num_jigs; i++) {
        j = part->jigs[i];
        ncol = countOutputColumns(j);
        if (ncol > 0) {
            __p += sprintf(__p, " %-15.15s", j->name);
            while (ncol-- > 1)
		// 16 spaces
		__p += sprintf(__p, " %-15.15s", " ");
        }
    }
    if (PrintPotentialEnergy) {
	__p += sprintf(__p, " %-15.15s", "P.Energy");
	__p += sprintf(__p, " %-15.15s", "K.Energy");
	__p += sprintf(__p, " %-15.15s", "T.Energy");
    }
    sprintf(__p, "\n");
    write_traceline(__line);
    __p = __line;
    sprintf(__p, "#\n");
    write_traceline(__line);
}


void traceJigData(struct part *part, struct xyz *positions) {
    double x;
    int i;
    struct jig *j;

    __p = __line;
    __p += sprintf(__p, "%10.4f ", Iteration * Dt / PICOSEC);
    
    for (i=0; i<part->num_jigs; i++) {
        j = part->jigs[i];
        switch (j->type) {
        case DihedralMeter:
        case AngleMeter:
	    __p += sprintf(__p, " %15.5f", j->data);
	    break;
        case Ground:
	    x=vlen(j->xdata)/1e4;
	    __p += sprintf(__p, " %15.2f", x / j->data);
	    j->data=0.0;
	    vsetc(j->xdata, 0.0);
	    break;
        case RadiusMeter:
        case LinearMotor:
	    // convert from picometers to angstroms
	    __p += sprintf(__p, " %15.4f", 0.01 * j->data);
	    j->data = 0.0;
	    break;
        case Thermometer:
        case Thermostat:
	    __p += sprintf(__p, " %15.2f", j->data);
	    j->data = 0.0;
	    break;
        case RotaryMotor:
	    __p += sprintf(__p, " %15.3f %15.3f", j->data, j->data2);
	    j->data = 0.0;
	    j->data2 = 0.0;
	    break;
	}
    }
    if (PrintPotentialEnergy) {
        double potential_energy = calculatePotential(part, positions);
        double kinetic_energy = calculateKinetic(part);
        
	__p += sprintf(__p, " %15.6f", potential_energy);
	__p += sprintf(__p, " %15.6f", kinetic_energy);
	__p += sprintf(__p, " %15.6f", potential_energy + kinetic_energy);
    }
    sprintf(__p, "\n"); // each snapshot is one line
    write_traceline(__line);
}

void
printError(const char *file, int line, int error_type,
	   int doPerror, const char *format, ...)
{
  va_list args;
  char *errorType;
  int toStderr = 0;

  switch (error_type) {
  case TYPE_ERROR:
      errorType = "Error";
      toStderr = 1;
      break;
  case TYPE_WARNING:
      errorType = "Warning";
      break;
  default:
      errorType = "Info";
      break;
  }
  
  __p = __line;
  __p += sprintf(__p, "# %s: ", errorType);
  va_start(args, format);
  __p += vsprintf(__p, format, args);
  va_end(args);
  if (doPerror) {
      sprintf(__p, ": %s\n", strerror(errno));
  } else {
      sprintf(__p, "\n");
  }
  write_traceline(__line);
  if (toStderr) {
      fprintf(stderr, "%s", __line);
  }
}

static FILE *testAlertFile = NULL;

void
testAlert(const char *format, ...)
{
    va_list args;

    if (testAlertFile == NULL) {
        testAlertFile = fopen("/tmp/simTestAlerts", "a");
        if (testAlertFile == NULL) {
            ERROR("failed to open /tmp/simTestAlerts");
            testAlertFile = stderr;
        } else {
            fprintf(testAlertFile, "----------------------------------------------\nInputFile: %s\n", InputFileName);
        }
    }
    va_start(args, format);
    vfprintf(testAlertFile, format, args);
    va_end(args);
    fflush(testAlertFile);
}

void
done(const char *format, ...)
{
    va_list args;

    __p = __line;
    __p += sprintf(__p, "# Done: ");
    va_start(args, format);
    __p += vsprintf(__p, format, args);
    va_end(args);
    sprintf(__p, "\n");
    write_traceline(__line);
}

/*
 * Local Variables:
 * c-basic-offset: 4
 * tab-width: 8
 * End:
 */
