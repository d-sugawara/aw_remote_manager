<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Student;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;

class TeacherController extends Controller
{
    /**
     * GET /api/teacher/students
     * 学生の一覧とキャプチャ情報を取得する
     */
    public function getStudents(Request $request): JsonResponse
    {
        $prefix = $request->query('prefix');

        $query = Student::with('captures')
                        ->orderBy('student_number', 'asc');

        if ($prefix) {
            // パラメータとして来た prefix が部分一致または前方一致するか
            $query->where('student_number', 'like', $prefix . '%');
        }

        // 1画面内に最大49名分
        $students = $query->limit(49)->get();

        // 必要な情報だけにフォーマット
        $formatted = $students->map(function (Student $student) {
            $latestCapture = $student->captures->sortByDesc('updated_at')->first();

            return [
                'student_number' => $student->student_number,
                'name'           => $student->name,
                'updated_at'     => $latestCapture ? $latestCapture->updated_at->toIso8601String() : null,
                'image_url'      => url('/api/teacher/capture/' . $student->student_number),
            ];
        });

        return response()->json($formatted);
    }

    /**
     * GET /api/teacher/capture/{student_number}
     * キャプチャ画像を返す
     */
    public function getCapture(string $student_number)
    {
        $filename = 'latest.png';
        $path     = 'captures/' . $student_number . '/' . $filename;

        if (Storage::disk('local')->exists($path)) {
            $file = Storage::disk('local')->path($path);
            
            // Return raw image with appropriate headers
            return response()->file($file, [
                'Content-Type' => 'image/png',
                'Cache-Control' => 'no-store, no-cache, must-revalidate, max-age=0',
            ]);
        }

        return response()->json(['message' => '画像が見つかりません'], 404);
    }
}
