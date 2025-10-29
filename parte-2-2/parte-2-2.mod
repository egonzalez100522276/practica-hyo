/* SETS */
set AUTOBUSES;
set TALLERES;
set FRANJAS;


/* PARAMETERS */
param c{AUTOBUSES, AUTOBUSES};
param o{FRANJAS, TALLERES} binary;

/* VARIABLES */
var x{AUTOBUSES, FRANJAS, TALLERES} binary;
var y {AUTOBUSES, AUTOBUSES,  FRANJAS} binary;

/* OBJECTIVE FUNCTION */
minimize TotalImpact:
  sum{i in AUTOBUSES, j in AUTOBUSES, s in FRANJAS} (if i < j then y[i,j,s]*c[i,j] else 0);

/* CONSTRAINTS */
s.t. Availability{s in FRANJAS, t in TALLERES}:
  sum{i in AUTOBUSES} x[i, s, t] <= o[s, t];

s.t. Assignation{i in AUTOBUSES}:
  sum{s in FRANJAS, t in TALLERES} x[i, s, t] = 1;

/* definition of the yijs varible (AND logic gate) */
s.t. y_up1 {i in AUTOBUSES, j in AUTOBUSES, s in FRANJAS: i < j}:
    y[i,j,s] <= sum{t in TALLERES} x[i,s,t];

s.t. y_up2 {i in AUTOBUSES, j in AUTOBUSES, s in FRANJAS: i < j}:
    y[i,j,s] <= sum{t in TALLERES} x[j,s,t];

s.t. y_low {i in AUTOBUSES, j in AUTOBUSES, s in FRANJAS: i < j}:
    y[i,j,s] >= sum{t in TALLERES} x[i,s,t] + sum{t in TALLERES} x[j,s,t] - 1;
