set TALLER;
set AUTOBUS;

param COST{TALLER, AUTOBUS};

var x{TALLER, AUTOBUS} binary;


minimize OverallCost:
  sum{i in TALLER, j in AUTOBUS} x[i,j]*COST[i,j];

s.t. ConstraintColumnas{j in AUTOBUS}:
  sum{i in TALLER} x[i,j] >= 1;

s.t. ConstraintFilas{i in TALLER}:
  sum{j in AUTOBUS} x[i,j] >= 1; 
