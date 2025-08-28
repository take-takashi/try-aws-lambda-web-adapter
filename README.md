# try-aws-lambda-web-adapter

AWS Lambda Web Adapterを動かす試み

## `mise` setup

```bash
% cat <<EOF > .mise.toml
[tools]
python = "3.12.1"

[env]
_.python.venv = { path = ".venv", create = true }
EOF
% mise trust
% mise use python@3.12.1
% mise exec -- pip install uv
%  uv --version
uv 0.8.13 (ede75fe62 2025-08-21)
```

## project setup

```bash
% uv init --no-cache --lib
```

## install package

```bash
uv add Flask==3.1.2
```
