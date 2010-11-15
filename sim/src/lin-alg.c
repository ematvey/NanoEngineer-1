// Copyright 2004-2006 Nanorex, Inc.  See LICENSE file for details. 
/**
 * Linear algebra stuff
 */

// XXX This stuff could possibly benefit from inlining.  Need to profile.
// NB the intent is for the macros to be used where speed is important,
//   namely inside the calc loop, and these to he used everywhere else,
//   for perspicuity.

#include "simulator.h"

static char const rcsid[] = "$Id: lin-alg.c 9214 2007-05-11 04:41:33Z emessick $";

struct xyz vcon(double x) {
	struct xyz u;
	vsetc(u,x);
	return u;
}

struct xyz vsum(struct xyz v, struct xyz w) {
	struct xyz u;
	vadd2(u,v,w);
	return u;
}

struct xyz vprod(struct xyz v, struct xyz w) {
	struct xyz u;
	vmul2(u,v,w);
	return u;
}

struct xyz vprodc(struct xyz v, double w) {
	struct xyz u;
	vmul2c(u,v,w);
	return u;
}

struct xyz vdif(struct xyz v, struct xyz w) {
	struct xyz u;
	vsub2(u,v,w);
	return u;
}

double vlen(struct xyz v) {	/* length of a vector */
	return sqrt(vdot(v,v));
}

struct xyz uvec(struct xyz v) {	/* unit vector in given direction */
	struct xyz w;
	double rlen;
	rlen=1.0/vlen(v);
        CHECKNANR(rlen, v);
	vmul2c(w,v,rlen);
	return w;
}

// angle between vectors
double vang(struct xyz v, struct xyz w) {
	struct xyz u1, u2;
	u1=uvec(v);
	u2=uvec(w);
	return acos(vdot(u1,u2));
}

// cross product
struct xyz vx(struct xyz v, struct xyz w) {
	struct xyz u;
	u.x = v.y * w.z - v.z * w.y;
	u.y = v.z * w.x - v.x * w.z;
	u.z = v.x * w.y - v.y * w.x;
	return u;
}

void
printMatrix3(FILE *f, double *m) 
{
  fprintf(f, "(%13.6f %13.6f %13.6f)\n", m[0], m[1], m[2]);
  fprintf(f, "(%13.6f %13.6f %13.6f)\n", m[3], m[4], m[5]);
  fprintf(f, "(%13.6f %13.6f %13.6f)\n", m[6], m[7], m[8]);
}

// a rotation matrix is organized like this:
//
// 0 1 2
// 3 4 5
// 6 7 8
//
// they are assumed to be pre-allocated before these routines are
// called.

// fill in a pre-allocated rotation matrix to rotate theta radians
// around the x axis
void
matrixRotateX(double *m, double theta)
{
  double sinTheta = sin(theta);
  double cosTheta = cos(theta);

  m[0] = 1.0;
  m[1] = 0.0;
  m[2] = 0.0;

  m[3] = 0.0;
  m[4] = cosTheta;
  m[5] = -sinTheta;

  m[6] = 0.0;
  m[7] = sinTheta;
  m[8] = cosTheta;
}

// fill in a pre-allocated rotation matrix to rotate theta radians
// around the y axis
void
matrixRotateY(double *m, double theta)
{
  double sinTheta = sin(theta);
  double cosTheta = cos(theta);

  m[0] = cosTheta;
  m[1] = 0.0;
  m[2] = -sinTheta;

  m[3] = 0.0;
  m[4] = 1.0;
  m[5] = 0.0;

  m[6] = sinTheta;
  m[7] = 0.0;
  m[8] = cosTheta;
}

// fill in a pre-allocated rotation matrix to rotate theta radians
// around the z axis
void
matrixRotateZ(double *m, double theta)
{
  double sinTheta = sin(theta);
  double cosTheta = cos(theta);

  m[0] = cosTheta;
  m[1] = -sinTheta;
  m[2] = 0.0;

  m[3] = sinTheta;
  m[4] = cosTheta;
  m[5] = 0.0;

  m[6] = 0.0;
  m[7] = 0.0;
  m[8] = 1.0;
}

void
matrixRotateXYZ(double *rotation, double thetaX, double thetaY, double thetaZ)
{
  double oneAxis[9];
  double tmp[9];

  // rotate first around X, then Y, then Z
  matrixRotateX(rotation, thetaX);
  matrixRotateY(oneAxis, thetaY);
  matrixMultiply(tmp, rotation, oneAxis);
  matrixRotateZ(oneAxis, thetaZ);
  matrixMultiply(rotation, tmp, oneAxis);
}

// prod = a * b
// all three are pre-allocated rotation matrices
void
matrixMultiply(double *prod, double *a, double *b)
{
  int i;
  int j;
  
  for (i=0; i<3; i++) {
    for (j=0; j<3; j++) {
      prod[i+3*j] = a[i] * b[3*j] + a[i+3] * b[1+3*j] + a[i+6] * b[2+3*j];
    }
  }
}

// transform in by matrix m to produce out.
// everything is pre-allocated.
void
matrixTransform(struct xyz *out, double *m, struct xyz *in)
{
  out->x = in->x * m[0] + in->y * m[1] + in->z * m[2];
  out->y = in->x * m[3] + in->y * m[4] + in->z * m[5];
  out->z = in->x * m[6] + in->y * m[7] + in->z * m[8];
}

// transform in by matrix Transpose(m) to produce out.
// everything is pre-allocated.
// since rotation matricies are orthogonal, Transpose(m) == m^-1
void
matrixInverseTransform(struct xyz *out, double *m, struct xyz *in)
{
  out->x = in->x * m[0] + in->y * m[3] + in->z * m[6];
  out->y = in->x * m[1] + in->y * m[4] + in->z * m[7];
  out->z = in->x * m[2] + in->y * m[5] + in->z * m[8];
}

// minor(i, j) is the determinant of the matrix with row i and column
// j deleted
static double
matrixMinor3(double *m, int i, int j)
{
  double submatrix[4];
  int ii;
  int jj;
  int k = 0;

  // create submatrix by deleting row i and column j:
  for (ii=0; ii<3; ii++) {
    if (ii != i) {
      for (jj=0; jj<3; jj++) {
        if (jj != j) {
          submatrix[k++] = m[ii*3 + jj];
        }
      }
    }
  }
  // 2x2 determinant of submatrix:
  return submatrix[0] * submatrix[3] - submatrix[1] * submatrix[2];
}

// determinant of a 3x3 matrix
static double
matrixDeterminant3(double *m)
{
  return
      m[0] * matrixMinor3(m, 0, 0)
    - m[1] * matrixMinor3(m, 0, 1)
    + m[2] * matrixMinor3(m, 0, 2);
}

// invert a 3x3 matrix
// returns zero if the matrix has no inverse
int
matrixInvert3(double *inverse, double *m)
{
  double det = matrixDeterminant3(m);

  if (fabs(det) < 1e-15) {
    return 0;
  }
  // cofactorMatrix = minor with alternating signs
  // inverse = transpose(cofactorMatrix) / det
  inverse[0] = +matrixMinor3(m, 0, 0) / det;
  inverse[1] = -matrixMinor3(m, 1, 0) / det;
  inverse[2] = +matrixMinor3(m, 2, 0) / det;

  inverse[3] = -matrixMinor3(m, 0, 1) / det;
  inverse[4] = +matrixMinor3(m, 1, 1) / det;
  inverse[5] = -matrixMinor3(m, 2, 1) / det;

  inverse[6] = +matrixMinor3(m, 0, 2) / det;
  inverse[7] = -matrixMinor3(m, 1, 2) / det;
  inverse[8] = +matrixMinor3(m, 2, 2) / det;
  return 1;
}




