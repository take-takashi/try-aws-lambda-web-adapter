# Tasks

## フェーズ1: Terraformバックエンドの初期構築 (CloudFormation)

Terraformのstateを安全に管理するためのS3バケットとDynamoDBテーブルを一度だけ作成します。

   1. CloudFormationテンプレートの作成 (`tf-backend-setup.yaml`):
       * Terraformのstateファイル (.tfstate) を保存するためのS3バケットを定義します。
       * stateのロックを管理するためのDynamoDBテーブルを定義します。
   2. CloudFormationスタックのデプロイ:
       * AWS CLIを使い、作成したテンプレートをデプロイして、実際にS3バケットとDynamoDBテーブルを作成します。

## フェーズ2: Flaskアプリケーションのコンテナ化 (Docker)

  Lambdaで実行するために、FlaskアプリケーションをDockerイメージにまとめます。

   1. `gunicorn` の追加:
       * 本番環境でFlaskを動作させるためのWSGIサーバーとして gunicorn をプロジェクトの依存関係 (pyproject.toml) に追加します。
   2. Dockerfileの作成:
       * Pythonベースのイメージから開始します。
       * AWS Lambda Web Adapter をイメージ内にダウンロードします。
       * アプリケーションのソースコードをコピーします。
       * pyproject.toml を使って依存ライブラリをインストールします。
       * コンテナ起動時に gunicorn でFlaskアプリを起動するよう設定します。

## フェーズ3: AWSインフラのコード化 (Terraform)

  アプリケーションを実行するためのAWSリソースをTerraformで定義します。

   1. Terraform設定ファイルの作成:
       * backend.tf: フェーズ1で作成したS3/DynamoDBをTerraformのバックエンドとして設定します。
       * main.tf: 以下の主要なリソースを定義します。
           * ECRリポジトリ: Dockerイメージを保存する場所。
           * IAMロール: Lambda関数が動作するために必要な権限。
           * Lambda関数: ECRにあるDockerイメージを指定して作成。
           * API Gateway (HTTP API): Lambda関数をWeb経由で呼び出すためのエンドポイント。
           * CloudWatch Log Group: Lambdaのログを保存する場所。
       * variables.tf / outputs.tf: AWSリージョンなどの変数や、デプロイ後に払い出されるAPI GatewayのURLを定義します。

  フェーズ4: デプロイワークフローの実行

  上記で作成したファイルを使って、実際にAWSにデプロイします。

   1. Terraformの初期化: terraform init を実行し、バックエンド設定を読み込ませます。
   2. ECRリポジトリの作成: terraform apply を一度実行し、Dockerイメージのプッシュ先となるECRリポジトリを先に作成します。
   3. Dockerイメージのビルドとプッシュ: Dockerfileを使ってイメージをビルドし、作成されたECRリポジトリにプッシュします。
   4. LambdaとAPI Gatewayのデプロイ: 再度 terraform apply を実行し、プッシュしたイメージを使ってLambda関数とAPI Gatewayをデプロイします。

  ---

  このタスクリストに沿って、具体的なコード作成やコマンド実行を進めていくことになります。
  まずはどのタスクから始めますか？ 例えば、「フェーズ1: Terraformバックエンドの初期構築」から着手するのが一般的です。

## Next action

* COMPLETE!
