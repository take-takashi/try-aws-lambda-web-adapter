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
uv add gunicorn==23.0.0
```

## aws setup infrastucture step 1

```bash
# CFnでTerraformのtfstateを保存するS3バケット、DynamoDBを作成する
% aws cloudformation deploy \
--stack-name try-aws-lambda-web-adapter-tf-backend \
--template-file bootstrap/tf-backend-setup.yaml \
--region ap-northeast-1
```

## destloy aws infrastructure step1

```bash
# s3バケットの中身を強制的に削除する
# ※BUCKET_NAMEは実際のバケット名に置き換える
% aws s3 rb s3://BUCKET_NAME --force
```
