<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;

class SettingsController extends Controller
{
    private const SECRET_KEY = 'AwRemoteManagerSecretKey202611!!'; // 32 bytes exact
    private const SETTINGS_FILE = 'settings.json';

    public function edit()
    {
        $settings = $this->loadSettings();
        return view('settings', compact('settings'));
    }

    public function update(Request $request)
    {
        $validated = $request->validate([
            'base_url' => 'required|url',
            'google_client_id' => 'required|string',
            'google_client_secret' => 'required|string',
        ]);

        Storage::disk('local')->put(self::SETTINGS_FILE, json_encode($validated, JSON_PRETTY_PRINT));

        return redirect('/settings')->with('success', '設定を保存しました。画面下部からアプリへのエクスポートが行えます。');
    }

    public function exportStudent()
    {
        $settings = $this->loadSettings();
        // 学生側はトークンなどを空にして渡すフォーマット
        $payload = [
            'base_url' => rtrim($settings['base_url'], '/') . '/api',
            'token' => '',
            'student_number' => '',
            'language' => 'ja',
            'google_client_id' => $settings['google_client_id'],
            'google_client_secret' => $settings['google_client_secret'],
        ];

        $encrypted = $this->encryptPayload($payload);

        return response($encrypted, 200, [
            'Content-Type' => 'application/octet-stream',
            'Content-Disposition' => 'attachment; filename="config.enc"',
        ]);
    }

    public function exportTeacher()
    {
        $settings = $this->loadSettings();
        
        $payload = [
            'base_url' => rtrim($settings['base_url'], '/') . '/api',
            'google_client_id' => $settings['google_client_id'],
        ];

        // 秘匿情報（secret）が含まれなくなったため、暗号化せずそのままJSオブジェクトとして出力
        $json = json_encode($payload, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
        $jsContent = "const CONFIG = {$json};\n";

        return response($jsContent, 200, [
            'Content-Type' => 'application/javascript',
            'Content-Disposition' => 'attachment; filename="config.js"',
        ]);
    }

    private function loadSettings()
    {
        if (Storage::disk('local')->exists(self::SETTINGS_FILE)) {
            $json = Storage::disk('local')->get(self::SETTINGS_FILE);
            return json_decode($json, true);
        }

        return [
            'base_url' => url('/'),
            'google_client_id' => '',
            'google_client_secret' => '',
        ];
    }

    private function encryptPayload(array $data): string
    {
        $json = json_encode($data, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
        
        $iv = random_bytes(16);
        $ciphertext = openssl_encrypt($json, 'aes-256-cbc', self::SECRET_KEY, OPENSSL_RAW_DATA, $iv);
        
        // 先頭16バイトにIVをくっつけてBase64文字列にする
        return base64_encode($iv . $ciphertext);
    }
}
