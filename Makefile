compile: d2
	@echo "Compiling the project..."
	pdflatex  -file-line-error -halt-on-error -interaction=nonstopmode -shell-escape -recorder  "thesis.tex"


d2: 
	@echo "Compiling D2 figures..."
	mkdir -p figures/d2-pdf
	for f in figures/d2/*.d2; do \
	  d2 "$$f" "figures/d2-pdf/$$(basename "$$f" .d2).pdf"; \
	done