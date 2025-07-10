run-sql:
	# make run-sql AWS_ACCOUNT=1234
	@python running.py --output sql | sed "s/INSERT INTO usage(\(.*\)) VALUES(\(.*\))/INSERT INTO usage(\1, account_id) VALUES(\2, $(AWS_ACCOUNT))/"
