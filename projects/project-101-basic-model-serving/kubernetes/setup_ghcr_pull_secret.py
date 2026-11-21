#!/usr/bin/env python3
"""Configure a local GHCR pull Secret and deploy the API with Kustomize."""

import argparse
import base64
import getpass
import json
import os
import subprocess
import sys
from pathlib import Path


KUBERNETES_DIR = Path(__file__).resolve().parent
NAMESPACE = "ml-serving"
SECRET_DIR = KUBERNETES_DIR / ".secrets"
DOCKER_CONFIG_PATH = SECRET_DIR / "ghcr-dockerconfig.json"


def run_kubectl(context: str, *arguments: str) -> None:
    subprocess.run(
        ["kubectl", "--context", context, *arguments],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--context",
        default="docker-desktop",
        help="kubectl context to deploy to (default: docker-desktop)",
    )
    args = parser.parse_args()

    username = input("GitHub username with access to the package: ").strip()
    if not username:
        parser.error("GitHub username cannot be empty")

    token = getpass.getpass("GHCR token with read:packages access: ")
    if not token:
        parser.error("GHCR token cannot be empty")

    auth = base64.b64encode(f"{username}:{token}".encode("utf-8")).decode("ascii")
    docker_config = json.dumps(
        {"auths": {"ghcr.io": {"auth": auth}}},
        separators=(",", ":"),
    )

    SECRET_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    SECRET_DIR.chmod(0o700)
    file_descriptor = os.open(
        DOCKER_CONFIG_PATH,
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        0o600,
    )
    with os.fdopen(file_descriptor, "w", encoding="utf-8") as config_file:
        config_file.write(docker_config)
        config_file.write("\n")

    token = ""
    print("Credential input saved with owner-only permissions; it is git-ignored.")

    try:
        run_kubectl(args.context, "apply", "-k", str(KUBERNETES_DIR))
        run_kubectl(
            args.context,
            "-n",
            NAMESPACE,
            "rollout",
            "status",
            "deployment/ml-model-serving-deployment",
            "--timeout=300s",
        )
        run_kubectl(
            args.context,
            "-n",
            NAMESPACE,
            "get",
            "service/ml-model-serving-service",
            "endpoints/ml-model-serving-service",
        )
    except FileNotFoundError:
        print("kubectl was not found on PATH.", file=sys.stderr)
        return 127
    except subprocess.CalledProcessError as error:
        return error.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())