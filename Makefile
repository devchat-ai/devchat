.PHONY: check fix

div = $(shell printf '=%.0s' {1..120})

DIR="."
check:
	@echo ${div}
	poetry run ruff check $(DIR)
	poetry run ruff format $(DIR) --check
	@echo "Done!"

fix:
	@echo ${div}
	poetry run ruff format $(DIR)
	@echo ${div}
	poetry run ruff check $(DIR) --fix
	@echo "Done!"
