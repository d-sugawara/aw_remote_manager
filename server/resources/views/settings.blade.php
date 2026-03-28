<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>構成設定 | AW Remote Manager</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #f3f4f6; color: #1f2937; margin: 0; padding: 2rem; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        h1 { font-size: 1.5rem; margin-top: 0; border-bottom: 2px solid #e5e7eb; padding-bottom: 1rem; }
        .form-group { margin-bottom: 1.5rem; }
        label { display: block; font-weight: 600; margin-bottom: 0.5rem; }
        input[type="text"], input[type="url"] { width: 100%; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 4px; box-sizing: border-box; }
        .btn { padding: 0.75rem 1.5rem; background-color: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; text-decoration: none; display: inline-block; }
        .btn:hover { background-color: #2563eb; }
        .btn-green { background-color: #10b981; }
        .btn-green:hover { background-color: #059669; }
        .actions { margin-top: 2rem; display: flex; gap: 1rem; border-top: 2px solid #e5e7eb; padding-top: 2rem; }
        .alert { background-color: #dcfce7; color: #166534; padding: 1rem; border-radius: 4px; margin-bottom: 1.5rem; border: 1px solid #bbf7d0; }
        .hint { font-size: 0.85rem; color: #6b7280; margin-top: 0.25rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>アプリ設定とエクスポート</h1>

        @if (session('success'))
            <div class="alert">
                {{ session('success') }}
            </div>
        @endif

        <form method="POST" action="{{ url('/settings/save') }}">
            @csrf
            
            <div class="form-group">
                <label for="base_url">サーバーURL (base_url)</label>
                <input type="url" id="base_url" name="base_url" value="{{ old('base_url', $settings['base_url']) }}" required>
                <div class="hint">例: http://localhost/aw_remote_manager/server/public</div>
            </div>

            <div class="form-group">
                <label for="google_client_id">Google OAuth クライアントID</label>
                <input type="text" id="google_client_id" name="google_client_id" value="{{ old('google_client_id', $settings['google_client_id']) }}" required>
            </div>

            <div class="form-group">
                <label for="google_client_secret">Google OAuth クライアントシークレット (暗号化されます)</label>
                <input type="text" id="google_client_secret" name="google_client_secret" value="{{ old('google_client_secret', $settings['google_client_secret']) }}" required>
            </div>

            <button type="submit" class="btn">設定を保存</button>
        </form>

        <div class="actions">
            <!-- エクスポートボタン -->
            <div>
                <h3>学生アプリ (Python)</h3>
                <p class="hint">config.enc をダウンロードし、exeと同じフォルダに配置してください。</p>
                <a href="{{ url('/settings/export/student') }}" class="btn btn-green">Student Config出力</a>
            </div>
            <div>
                <h3>先生アプリ (WebUI)</h3>
                <p class="hint">config.js をダウンロードし、/assets/js内に配置してください。</p>
                <a href="{{ url('/settings/export/teacher') }}" class="btn btn-green">Teacher Config出力</a>
            </div>
        </div>
    </div>
</body>
</html>
