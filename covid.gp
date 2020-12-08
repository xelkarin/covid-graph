set title title
set xlabel 'Date'
set ylabel 'Confirmed Cases'
set offsets 1, 1, 100
set key autotitle

set xdata time
set format x '%m/%d'
set timefmt '%m/%d/%Y'

plot datfile using 1:2 with lines title "Confirmed cases", \
     datfile using 1:3 with lines title "7-day average"

# vim: set filetype=gnuplot:
