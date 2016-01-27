#!/bin/sh

for t in *.conf; do
  ../cstyle --conf ${t} ${t/.conf/.c}
done
