<?php

use App\Http\Controllers\CaptureController;
use App\Http\Controllers\StudentAuthController;
use App\Http\Middleware\JwtAuthenticate;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| API Routes – Student
|--------------------------------------------------------------------------
|
| ベースURL: /api/student
|
*/

// ログイン（認証不要）
Route::post('/student/auth', [StudentAuthController::class, 'login']);

// 認証済みルート
Route::middleware(JwtAuthenticate::class)->group(function () {
    // ログイン状態確認
    Route::get('/student/auth', [StudentAuthController::class, 'status']);

    // ログアウト
    Route::post('/student/logout', [StudentAuthController::class, 'logout']);

    // キャプチャ画像アップロード
    Route::post('/student/capture/{student_number}', [CaptureController::class, 'upload']);
});

/*
|--------------------------------------------------------------------------
| API Routes – Teacher
|--------------------------------------------------------------------------
*/

use App\Http\Controllers\TeacherController;

// 先生用ルート（現在は認証なし）
Route::get('/teacher/students', [TeacherController::class, 'getStudents']);
Route::get('/teacher/capture/{student_number}', [TeacherController::class, 'getCapture']);
