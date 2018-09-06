# Define required macros here
SHELL = /bin/sh -c

# Deployment subtasks

deploy-cluster :
	${SHELL} "echo Deploying full cluster"

deploy-cluster-devel :
	${SHELL} "echo Deploying devel cluster"

deploy-app:
	${SHELL} "echo Deploying the application"

# Test subtasks

unit-test :
	${SHELL} "echo Running unit tests"

functional-test : deploy-app
	${SHELL} "echo Running functional tests"

# Master level

test : unit-test functional-test
deploy-devel : deploy-cluster-devel deploy-app
deploy: deploy-cluster deploy-app
