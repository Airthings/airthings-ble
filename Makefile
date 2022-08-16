

lint:  ## Lint and static-check
	black -l 79 --check airthings_ble 
	pylint airthings_ble
	mypy airthings_ble
	
