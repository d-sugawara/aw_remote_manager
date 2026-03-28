<?php

namespace App\Services;

use Firebase\JWT\JWT;
use Firebase\JWT\Key;
use App\Models\Student;

class JwtService
{
    /**
     * JWT を発行する
     */
    public function issue(Student $student): string
    {
        $secret = config('jwt.secret');
        $ttl    = config('jwt.ttl', 3600);

        $payload = [
            'iss' => config('app.url'),
            'sub' => $student->id,
            'student_number' => $student->student_number,
            'iat' => time(),
            'exp' => time() + $ttl,
        ];

        return JWT::encode($payload, $secret, 'HS256');
    }

    /**
     * JWT を検証して Student を返す。失敗時は null を返す
     *
     * @return Student|null
     */
    public function verify(string $token): ?Student
    {
        $secret = config('jwt.secret');

        $decoded = JWT::decode($token, new Key($secret, 'HS256'));
        return Student::find($decoded->sub);
    }
}
