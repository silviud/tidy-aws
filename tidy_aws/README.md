# Tidy-AWS

List unsed resources in AWS, good for cost savings.

## Dev

Install [uv](https://github.com/astral-sh/uv).

This repo makes use of [.gitignore](https://raw.githubusercontent.com/github/gitignore/refs/heads/main/Python.gitignore).

### Virtual environment

On a linux/mac/wsl system after you install `uv` under this directory execute `uv sync`.

This will create a new virtual environment under `.venv` and install all dependencies.

Once is finished activate this environment as you normally do `source .venv/bin/activate`.

## Authentication

I use boto3 which makes use of different authentication methods see [details](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials).
