# インフラ設計図

## 前提

- AWSを利用
- Cloudformationを用いてデプロイ
  - フロントエンド、バックエンドのようにスタックを分離

## パラメータストア

- SSMを使用
- 各CloudFormationスタックからパラメータをここから参照する

## フロントエンド

- Lambda+Lambda Web Adapterを用いる
- フロントエンドはnode+React
- LambdaはECRのDockerイメージで動かす
- IP制限を設けるため、CloudFrontからLambdaにアクセスするイメージ
- ログインはCognitoを使う

## バックエンド

- Lambda+Lambda Web Adapterを用いる
- バックエンドはpython+FastAPI
- LambdaはECRのDockerイメージで動かす
- APIはCognitoでログインしていないとアクセスできないようにする
- データベースはAmazon Aurora Serverless V2(postgres)
- FastAPIからDrizzleをでDBにアクセス

## ユーザー管理

- Cognitoを使用

## 開発用Assume Role

- Assule RoleでCloudFormationを実行できる制限を実施
