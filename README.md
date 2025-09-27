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

## Githubリポジトリのsecretsを.mise.local.tomlの内容で設定する

```bash
% gh auth login
% mise run gh-update-secrets

```

# Terraform版のインフラ構築&削除

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

## aws setup infrastucture step 3

```bash
% mise run tf-plan
% mise run tf-apply

```

## When manually pushing the image

手動でDocker buildしたimageをECRにプッシュする場合の手順。

すでにGithub Actionsで自動化しているのであまり使わないかも。

```bash
# STEP0. 変数
AWS_ACCOUNT_ID=********
AWS_REGION=ap-northeast-1
IMAGE_NAME=try-aws-lambda-web-adapterなど

# STEP1. ECRへのログイン
# docker cli版
% aws ecr get-login-password --region ${AWS_REGION} | \
docker login --username AWS \
--password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# apple container版
aws ecr get-login-password --region ${AWS_REGION} | \
container registry login --username AWS \
--password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# STEP2. Dockerイメージをビルド
# docker cli版
% docker build -t ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:latest .

# apple container版
% container system start
% container build -t ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:latest .

# STEP3. Dockerイメージをプッシュ
# docker cli版
% docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:latest

# apple container版
% container images push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:latest
```

## destloy aws infrastructure step1

```bash
# terraform destroyでterraformで作成したインフラを削除
terraform -chdir=terraform destroy
```

## destloy aws infrastructure step2

```bash
# s3バケットの中身を強制的に削除する
% aws s3 rm s3://${TF_BACKEND_S3_BUCKET} --recursive
```

## destroy aws infrastructure step3

```bash
aws cloudformation delete-stack --stack-name ${TF_BACKEND_STACK_NAME}  --region ${AWS_DEFAULT_REGION}
```

## memo

- ローカルでDockerfileをビルドするの面倒なのでgithub actionsで済ませたい
- mdの更新（docker build系はgithub actionsに任せた）
- サイトのURLはどうにかなる？
- OIDC Roleの作成用のtasksが貧弱なので直したい

# CloudFormation版

- リポジトリSecretsに以下を設定が必要。（Github Actionsで動かすために）
  - AWS_OIDC_ROLE_ARN（既存）
  - WAF_ALLOWED_IPV4_CIDRS（カンマ区切りCIDR）
  - ORIGIN_SECRET（任意のシークレット:CloudFrontからのアクセスに制限をかける）

## AWS操作用のroleの作成

```bash
# envでGH_REPOとGH_USERを設定しておくこと（Github actionsからAWSを操作するため）
# ここで作成するroleはAdminなので本当は権限を絞ること
mise run cfn-create-oidc-role
# 実行結果で出力された値を控える
```
