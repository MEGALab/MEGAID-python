id:
	cli/main.py create-utc $(filter-out $@,$(MAKECMDGOALS))

decode:
	cli/main.py decode $(filter-out $@,$(MAKECMDGOALS))

%:
	@:

.PHONY: decode id
