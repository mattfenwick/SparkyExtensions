#!/bin/bash

pdflatex sparkyext
echo "
finished 1

"

bibtex sparkyext
echo "
finished bibtex

"

pdflatex sparkyext
echo "
finished 2

"

pdflatex sparkyext
echo "
finished 3

"

