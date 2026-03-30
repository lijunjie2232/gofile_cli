# Gofile API 統合ガイド

## 認証
- 全てのリクエストは以下の認証ヘッダーを含む必要があります：
```
Authorization: Bearer あなたの_API_TOKEN
```

## エンドポイント概要

### ファイルアップロード
```
POST https://upload.gofile.io/uploadfile
```
- パラメータ：
  - `file`（必須） - アップロードするファイル
  - `folderId`（オプション） - 宛先フォルダID

パフォーマンス向上のためにリージョナルエンドポイントが提供されています。

### フォルダ管理
1. フォルダを作成:
```
POST https://api.gofile.io/contents/createFolder
```
- パラメータ：
  - `parentFolderId`（必須）
  - `folderName`（オプション）

2. フォルダ属性を更新:
```
PUT https://api.gofile.io/contents/{contentId}/update
```
- 更新可能な属性：名前、説明、タグ、公開ステータス、有効期限、パスワード

### コンテンツ管理
1. コンテンツを削除:
```
DELETE https://api.gofile.io/contents
```
- パラメータ：`contentsId`（カンマ区切りのIDリスト）

2. コンテンツ情報を取得:
```
GET https://api.gofile.io/contents/{contentId}
```
- オプション：`password`（保護されたコンテンツ用SHA-256ハッシュパスワード）

3. コンテンツを検索:
```
GET https://api.gofile.io/contents/search
```
- パラメータ：`contentId`（検索場所）、`searchedString`

### 直接リンク
1. 直接リンクを作成:
```
POST https://api.gofile.io/contents/{contentId}/directlinks
```
- 設定可能な制限：expireTime、sourceIpsAllowed、domainsAllowed、auth

2. 直接リンクを更新:
```
PUT https://api.gofile.io/contents/{contentId}/directlinks/{directLinkId}
```

3. 直接リンクを削除:
```
DELETE https://api.gofile.io/contents/{contentId}/directlinks/{directLinkId}
```

### コンテンツ操作
1. コンテンツをコピー:
```
POST https://api.gofile.io/contents/copy
```
- パラメータ：`contentsId`、`folderId`

2. コンテンツを移動:
```
PUT https://api.gofile.io/contents/move
```
- パラメータ：`contentsId`、`folderId`

3. 公開コンテンツをインポート:
```
POST https://api.gofile.io/contents/import
```
- パラメータ：`contentsId`

### アカウント管理
1. アカウントIDを取得:
```
GET https://api.gofile.io/accounts/getid
```

2. アカウント情報を取得:
```
GET https://api.gofile.io/accounts/{accountId}
```

3. APIトークンをリセット:
```
POST https://api.gofile.io/accounts/{accountId}/resettoken
```

## 重要なお知らせ
- **プレミアムアカウントが必要**：ほとんどのエンドポイントはプレミアムアカウントが必要です
- **レート制限**：各エンドポイントにレート制限があります。過剰な使用によりIPがブロックされる可能性があります
- **アカウント構造**：全てのコンテンツの基盤となる永続的なルートフォルダがあります
- **データ削除**：DELETE操作は恒久的で取り消し不可です
- **BETA版について**：APIはベータテスト段階にあり、変更される可能性があります。定期的にドキュメントの更新を確認してください