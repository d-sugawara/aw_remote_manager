# サーバーAPI仕様
## 共通
### ベースURL
http://localhost:8000

## 学生側API
### ログイン
#### URL
/api/student/auth
#### メソッド
POST

#### 認証方式
Google OAuth 2.0 (Authorization Code Flow with PKCE)

クライアントはシステムブラウザで Google 認証を行い、取得した **Google ID トークン** をサーバーへ送信する。  
サーバーは ID トークンを Google API で検証し、紐づく学生レコードを特定して JWT を発行する。

#### リクエストボディ
```json
{
    "google_id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6..."
}
```

#### レスポンス
##### 200 OK
```json
{
    "student_number": "26aw0100",
    "token" : "jwt_token",
    "message": "認証に成功しました。"
}
```

##### 400 Bad Request
```json
{
    "message": "IDまたはパスワードを確認してください"
}
```

##### 500 Internal Server Error
```json
{
    "message": "認証に失敗しました。サーバーエラーが発生しました。"
}
```

### ログイン状態確認
#### URL
/api/student/auth
#### メソッド
GET

#### ヘッダー
- Authorization: Bearer {token}

#### レスポンス
##### 200 OK
```json
{
    "student_number": "26aw0100",
    "token" : "jwt_token",
    "message": "認証に成功しました。"
}
```

##### 400 Bad Request
```json
{
    "message": "トークンの有効期限が切れています。再度ログインしてください。"
}
```

##### 500 Internal Server Error
```json
{
    "message": "認証に失敗しました。サーバーエラーが発生しました。"
}
```

### ログアウト
#### URL
/api/student/logout
#### メソッド
POST

#### ヘッダー
- Authorization: Bearer {token}

#### レスポンス
##### 200 OK
```json
{
    "message": "ログアウトしました。"
}
```

##### 400 Bad Request
```json
{
    "message": "ログアウトに失敗しました。不正なリクエストです。"
}
```

##### 500 Internal Server Error
```json
{
    "message": "ログアウトに失敗しました。サーバーエラーが発生しました。"
}
```

### キャプチャ画面アップロード
#### URL
/api/student/capture/{student_number}
#### メソッド
POST

#### ヘッダー
- Authorization: Bearer {token}

#### パラメータ
- image: キャプチャ画像（base64エンコード済み）

#### リクエストボディ
```json
{
    "image": "base64_encoded_image"
}
```

#### レスポンス
##### 200 OK
```json
{
    "id" : 1,
    "message": "画像アップロードに成功しました。"
}
```

##### 400 Bad Request
```json
{
    "message": "画像アップロードに失敗しました。不正なリクエストです。"
}
```

##### 500 Internal Server Error
```json
{
    "message": "画像アップロードに失敗しました。サーバーエラーが発生しました。"
}
```
