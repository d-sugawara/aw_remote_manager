<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Capture;
use App\Models\Student;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Throwable;

class CaptureController extends Controller
{
    /**
     * POST /api/student/capture/{student_number}
     * Base64エンコードされた画像を受け取り、storageに保存する
     */
    public function upload(Request $request, string $student_number): JsonResponse
    {
        // JWTミドルウェアで認証済みの学生を取得
        /** @var Student $authStudent */
        $authStudent = $request->attributes->get('student');

        if (!$authStudent) {
            return response()->json(['message' => '画像アップロードに失敗しました。不正なリクエストです。'], 400);
        }

        // URLパラメータの student_number と JWT の student_number が一致するか確認
        if ($authStudent->student_number !== $student_number) {
            return response()->json(['message' => '画像アップロードに失敗しました。不正なリクエストです。'], 400);
        }

        $validated = $request->validate([
            'image' => 'required|string',
        ]);

        try {
            $base64 = $validated['image'];

            // data:image/png;base64,... 形式に対応（プレフィックスがある場合は除去）
            if (str_contains($base64, ',')) {
                [, $base64] = explode(',', $base64, 2);
            }

            $imageData = base64_decode($base64, strict: true);

            if ($imageData === false) {
                return response()->json(['message' => '画像アップロードに失敗しました。不正なリクエストです。'], 400);
            }

            // ユーザーごとに1枚の画像を維持するため、名前を固定して上書き保存する
            $filename  = 'latest.png';
            $directory = 'captures/' . $student_number;
            $path      = $directory . '/' . $filename;

            Storage::disk('local')->put($path, $imageData);

            // DB側も追記ではなく更新にする（無ければ作成）
            $capture = Capture::updateOrCreate(
                ['student_id' => $authStudent->id],
                ['image_path' => $path]
            );
            $capture->touch();

            return response()->json([
                'id'      => $capture->id,
                'message' => '画像アップロードに成功しました。',
            ]);
        } catch (Throwable $e) {
            return response()->json(['message' => '画像アップロードに失敗しました。サーバーエラーが発生しました。'], 500);
        }
    }
}
