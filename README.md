# coffee_project
An automatic post generator based on my Google Map saved list of coffee shops around the world.



## Local Development

If you are planning to edit this repo, you can install it for local development as follows:

```bash
# Assume that you have pyenv and uv installed.
pyenv local 3.12
uv venv .venv --python 3.12 --seed
source .venv/bin/activate
uv sync --frozen
```