

lint:  ## Lint and static-check
	black -l 88 --check airthings_ble 
	pylint airthings_ble
	mypy airthings_ble
	
