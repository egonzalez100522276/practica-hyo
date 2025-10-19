/* SETS */
set AUTOBUSES;
set FRANJAS;


/* PARAMETERS */
param kd;
param kp;
param d{AUTOBUSES};
param p{AUTOBUSES};

/* PARAMETER VALIDATION */
check: kd >= 0;
check: kp >= 0;
check {i in AUTOBUSES}: d[i] >= 0;
check {i in AUTOBUSES}: p[i] >= 0;


/* VARIABLES */ 
var x{AUTOBUSES, FRANJAS} binary;

/* OBJECTIVE FUNCTION */
minimize OverallCost:
  sum{i in AUTOBUSES, j in FRANJAS} kd * d[i] * x[i,j] +
  sum{i in AUTOBUSES} kp * p[i] * (1- sum{j in FRANJAS} x[i, j]);

/* CONSTRAINTS */

s.t. ConstraintFranjas{j in FRANJAS}:
  sum{i in AUTOBUSES} x[i, j] <= 1;

s.t. ConstraintAutobuses{i in AUTOBUSES}:
  sum{j in FRANJAS} x[i, j] <= 1;
