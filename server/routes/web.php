<?php

use Illuminate\Support\Facades\Route;

use App\Http\Controllers\SettingsController;

Route::get('/', function () {
    return redirect('/settings');
});

Route::get('/settings', [SettingsController::class, 'edit']);
Route::post('/settings/save', [SettingsController::class, 'update']);
Route::get('/settings/export/student', [SettingsController::class, 'exportStudent']);
Route::get('/settings/export/teacher', [SettingsController::class, 'exportTeacher']);
