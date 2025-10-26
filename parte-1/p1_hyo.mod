/* SETS */
set TALLER;
set AUTOBUS;

/* PARAMETERS */
param COST{TALLER, AUTOBUS};

/* VARIABLES */
var x{TALLER, AUTOBUS} binary;

/* OBJECTIVE FUNCTION */
minimize OverallCost:
  sum{i in TALLER, j in AUTOBUS} x[i,j]*COST[i,j];

/* CONSTRAINTS */
s.t. BusAssignment{j in AUTOBUS}:
  sum{i in TALLER} x[i,j] = 1;

s.t. WorkshopAssignment{i in TALLER}:
  sum{j in AUTOBUS} x[i,j] = 1; 
