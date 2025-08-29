# try-aws-lambda-web-adapter

AWS Lambda Web Adapterを動かす試み

## your setup

```bash
% mise trust
% mise install
```

## `mise` setup

```bash
% cat <<EOF > .mise.toml
[tools]
python = "3.12.1"
terraform = "1.13.1"
uv = "0.8.14"

[env]
_.python.venv = { path = ".venv", create = true }
EOF
% mise trust
% mise install

# python version check
% python --version
Python 3.12.1

# terraform version check
% terraform --version
Terraform v1.13.1
on darwin_arm64

# uv version check
% uv --version
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

## aws setup infrastucture step 2

```bash
# .mise.local.tomlを作成（.mise.example.tomlを参考）し、envを定義した後に実行
% mise run tf-init
```

## destloy aws infrastructure step1

```bash
# s3バケットの中身を強制的に削除する
# ※BUCKET_NAMEは実際のバケット名に置き換える
% aws s3 rb s3://BUCKET_NAME --force
```
