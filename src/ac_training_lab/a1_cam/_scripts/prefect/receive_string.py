from prefect.deployments import run_deployment

flow_run = run_deployment(
    name="echo/prod",  # "<flow name>/<deployment name>"
    parameters={"msg": "hi"},
    timeout=None,  # wait until the run finishes
)

value = flow_run.state.result()  # -> "hi"
print(value)
