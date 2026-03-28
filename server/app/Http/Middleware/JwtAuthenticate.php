<?php

namespace App\Http\Middleware;

use App\Services\JwtService;
use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;
use Throwable;

class JwtAuthenticate
{
    public function __construct(private JwtService $jwt) {}

    public function handle(Request $request, Closure $next): Response
    {
        $authHeader = $request->header('Authorization', '');

        if (!str_starts_with($authHeader, 'Bearer ')) {
            return response()->json(['message' => 'トークンの有効期限が切れています。再度ログインしてください。'], 400);
        }

        $token = substr($authHeader, 7);

        try {
            $student = $this->jwt->verify($token);
        } catch (Throwable $e) {
            return response()->json(['message' => 'トークンの有効期限が切れています。再度ログインしてください。'], 400);
        }

        if (!$student) {
            return response()->json(['message' => 'トークンの有効期限が切れています。再度ログインしてください。'], 400);
        }

        // コントローラーで $request->student として参照できるようにする
        $request->merge(['_student' => $student]);
        $request->attributes->set('student', $student);

        return $next($request);
    }
}
