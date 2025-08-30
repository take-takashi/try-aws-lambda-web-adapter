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

## aws setup infrastucture step 3

```bash
% terraform -chdir=terraform apply -target=aws_ecr_repository.app

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
# s3バケットの中身を強制的に削除する
# ※BUCKET_NAMEは実際のバケット名に置き換える
% aws s3 rb s3://BUCKET_NAME --force
```

## memo

- ローカルでDockerfileをビルドするの面倒なのでgithub actionsで済ませたい
- main.tfをいきなりapplyできない（先にECRにimageをpushする必要がある）
  - ECR部分はmain.tfから逃した方がいいのでは？
- mdの更新（docker build系はgithub actionsに任せた）
- サイトのURLはどうにかなる？

## try actions

GitHub Actionsで行うこと

1. ワークフローファイルの作成: プロジェクト内に.github/workflows/build-and-push.ymlのようなYAMLファイルを作成します。
2. トリガーの設定:
    例えば、mainブランチにコードがプッシュされた時などに、このワークフローが自動で実行されるように設定します。手動実行のトリガーも設定できます。
3. AWS認証情報の設定: GitHubリポジトリの「Secrets」にAWSのアクセスキーを設定します。これにより、パスワードなどを直接ファイルに書き込むことなく、安
    全にAWSを操作できます。
4. ワークフローの処理内容の定義:
    - ソースコードをチェックアウトする
    - AWS認証を行う
    - Amazon ECRにログインする
    - DockerイメージをビルドしてECRにプッシュする
