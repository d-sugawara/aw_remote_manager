<?php

namespace App\Http\Controllers;

use App\Models\Student;
use App\Services\JwtService;
use Google\Auth\AccessToken;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Throwable;

class StudentAuthController extends Controller
{
    public function __construct(private JwtService $jwt) {}

    /**
     * POST /api/student/auth
     * Google ID Token を受け取り JWT を発行する
     */
    public function login(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'google_id_token' => 'required|string',
        ]);

        try {
            $payload = $this->verifyGoogleIdToken($validated['google_id_token']);
        } catch (Throwable $e) {
            \Illuminate\Support\Facades\Log::error('verifyGoogleIdToken Error: ' . $e->getMessage());
            return response()->json(['message' => 'IDまたはパスワードを確認してください'], 400);
        }

        $googleSub = $payload['sub']   ?? null;
        $email     = $payload['email'] ?? null;
        $name      = $payload['name']  ?? ($email ?? '');

        if (!$googleSub || !$email) {
            return response()->json(['message' => 'IDまたはパスワードを確認してください'], 400);
        }

        try {
            // google_sub OR email でレコードを検索する
            $student = Student::where('google_sub', $googleSub)
                ->orWhere('email', $email)
                ->first();

            if (!$student) {
                // DBに存在しない場合は、テスト用に自動でアカウントを作成します
                $student = Student::create([
                    'student_number' => strstr($email, '@', true),
                    'name' => $name,
                    'email' => $email,
                    'google_sub' => $googleSub
                ]);
            }

            // google_sub が未設定なら紐付ける
            if (!$student->google_sub) {
                $student->update(['google_sub' => $googleSub]);
            }

            $token = $this->jwt->issue($student);
        } catch (Throwable $e) {
            \Illuminate\Support\Facades\Log::error('Login error: ' . $e->getMessage());
            return response()->json(['message' => '認証に失敗しました。サーバーエラーが発生しました。'], 500);
        }

        return response()->json([
            'student_number' => $student->student_number,
            'token'          => $token,
            'message'        => '認証に成功しました。',
        ]);
    }

    /**
     * GET /api/student/auth
     * JWTミドルウェアを通過した時点で認証済みなのでそのまま返す
     */
    public function status(Request $request): JsonResponse
    {
        try {
            $student = $request->attributes->get('student');

            if (!$student) {
                return response()->json(['message' => 'トークンの有効期限が切れています。再度ログインしてください。'], 400);
            }

            // JWTを再発行して返す（有効期限を延長したい場合はここで行う）
            $token = $this->jwt->issue($student);

            return response()->json([
                'student_number' => $student->student_number,
                'token'          => $token,
                'message'        => '認証に成功しました。',
            ]);
        } catch (Throwable $e) {
            return response()->json(['message' => '認証に失敗しました。サーバーエラーが発生しました。'], 500);
        }
    }

    /**
     * POST /api/student/logout
     */
    public function logout(Request $request): JsonResponse
    {
        try {
            $student = $request->attributes->get('student');

            if (!$student) {
                return response()->json(['message' => 'ログアウトに失敗しました。不正なリクエストです。'], 400);
            }

            // JWT はステートレスなため、クライアント側でトークンを削除する運用とする。
            // 必要に応じてブラックリストテーブルに記録する拡張が可能。
            return response()->json(['message' => 'ログアウトしました。']);
        } catch (Throwable $e) {
            return response()->json(['message' => 'ログアウトに失敗しました。サーバーエラーが発生しました。'], 500);
        }
    }

    // -----------------------------------------------------------------------
    // Private helpers
    // -----------------------------------------------------------------------

    /**
     * Google ID Token を検証してペイロードを返す
     *
     * @throws \RuntimeException
     */
    private function verifyGoogleIdToken(string $idToken): array
    {
        $clientId = config('services.google.client_id');

        // google/auth の AccessToken クラスで ID Token を署名検証する
        $accessToken = new AccessToken();
        $payload     = $accessToken->verify($idToken, [
            'audience' => $clientId,
        ]);

        if (!$payload) {
            throw new \RuntimeException('Invalid Google ID token');
        }

        // aud (audience) 検証
        $aud = is_array($payload['aud']) ? $payload['aud'] : [$payload['aud']];
        if ($clientId && !in_array($clientId, $aud, true)) {
            throw new \RuntimeException('Audience mismatch');
        }

        return $payload;
    }
}
