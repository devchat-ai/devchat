.PHONY: check fix

div = $(shell printf '=%.0s' {1..120})

check:
	@echo ${div}
	ruff check .
	ruff format . --check
	@echo "Done!"

fix:
	@echo ${div}
	ruff format .
	@echo ${div}
	ruff check . --fix
	@echo "Done!"
