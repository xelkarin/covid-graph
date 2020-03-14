set title 'COVID-19 Infection Rate'
set xlabel 'Date'
set ylabel 'Confirmed Cases'
set offsets 1, 1
set nokey

set xdata time
set format x '%m/%d'
set timefmt '%m/%d/%Y'

plot datfile using 1:2 with lines

# vim: set filetype=gnuplot:
