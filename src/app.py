import json
from subprocess import call

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException

app = FastAPI()

with open("pipelinerun.yaml", "r") as f:
    TEMPLATE = f.read()

repoconfigs = {
    "JustinGuese/tradingbot22-backend": {
        "k8s-deployment": "tradingbot-backend-deployment",
        "k8s-namespace": "tradingbot",
    }
}


@app.post("/")
async def root(request: Request):
    # get source url of request
    sourceurl = request.headers.get("Referer")
    if sourceurl and "github.com" not in sourceurl:
        raise HTTPException(
            status_code=403, detail="Not authorized for source URL " + sourceurl
        )

    body = await request.body()
    # will be bytes,
    body = json.loads(body.decode("utf-8"))
    repourl = body["repository"]["full_name"]
    branch = body["ref"].split("/")[-1]
    print("i detected repo and branch", repourl, branch)
    if "JustinGuese" not in repourl:
        return HTTPException(
            status_code=403, detail="Not authorized for repo " + repourl
        )
    if repourl not in repoconfigs:
        return HTTPException(status_code=404, detail="Repo not found")

    # create tmp pipelinerun
    tmp = TEMPLATE.replace("{{REPOURL}}", "git@github.com:" + repourl + ".git")
    tmp = tmp.replace("{{IMAGE_NAME}}", repourl.split("/")[-1])
    tmp = tmp.replace("{{K8S_DEPLOYMENT}}", repoconfigs[repourl]["k8s-deployment"])
    tmp = tmp.replace("{{K8S_NAMESPACE}}", repoconfigs[repourl]["k8s-namespace"])
    with open("tmp.yaml", "w") as f:
        f.write(tmp)
    call(["kubectl", "create", "-f", "tmp.yaml", "-n", "default"])
    # rollout restart
    call(
        [
            "kubectl",
            "rollout",
            "restart",
            "deployment",
            repoconfigs[repourl]["k8s-deployment"],
            "-n",
            repoconfigs[repourl]["k8s-namespace"],
        ]
    )
    return {"status": "ok"}
