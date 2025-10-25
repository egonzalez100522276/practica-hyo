/* SETS */
set AUTOBUSES;
set TALLERES;
set FRANJAS;


/* PARAMETERS */
param c{AUTOBUSES, AUTOBUSES};
param o{FRANJAS, TALLERES} binary;


/* VARIABLES */
var x{AUTOBUSES, FRANJAS, TALLERES} binary;
var y {AUTOBUSES, FRANJAS} binary;
var w {AUTOBUSES, AUTOBUSES, FRANJAS} binary;

/* OBJECTIVE FUNCTION */
minimize TotalImpact:
  sum{i in AUTOBUSES, j in AUTOBUSES, s in FRANJAS} (if i <= j then w[i,j,s]*c[i,j] else 0);

/* CONSTRAINTS */
s.t. Availability{s in FRANJAS, t in TALLERES}:
  sum{i in AUTOBUSES} x[i, s, t] <= o[s, t];

s.t. Assignation{i in AUTOBUSES}:
  sum{s in FRANJAS, t in TALLERES} x[i, s, t] = 1;

/* definifion of the Yis variable*/
s.t. DefinitionY{i in AUTOBUSES, s in FRANJAS}:
  y[i, s] = sum{t in TALLERES} x[i, s, t];

/* definition of the Wijs varible (AND logic gate) */
s.t. W_up1 {i in AUTOBUSES, j in AUTOBUSES, s in FRANJAS: i <= j}:
    w[i,j,s] <= y[i,s];

s.t. W_up2 {i in AUTOBUSES, j in AUTOBUSES, s in FRANJAS: i <= j}:
    w[i,j,s] <= y[j,s];

s.t. W_low {i in AUTOBUSES, j in AUTOBUSES, s in FRANJAS: i <= j}:
    w[i,j,s] >= y[i,s] + y[j,s] - 1;
