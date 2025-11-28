from prefect import flow


@flow(name="echo", persist_result=True)
def echo(msg: str) -> str:
    return msg
