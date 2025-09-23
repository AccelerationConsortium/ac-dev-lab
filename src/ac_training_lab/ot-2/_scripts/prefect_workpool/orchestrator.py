from prefect.deployments import run_deployment

# Run the deployments (assuming they are already created and deployed to the work pool)
run_deployment(
    name="mix-color/mix-color",
    parameters={"R": 120, "Y": 50, "B": 80, "mix_well": "B2"},
)

run_deployment(
    name="move-sensor-to-measurement-position/move-sensor-to-measurement-position",
    parameters={"mix_well": "B2"},
)

run_deployment(name="move-sensor-back/move-sensor-back")
