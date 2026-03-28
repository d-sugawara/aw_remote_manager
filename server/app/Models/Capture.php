<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Capture extends Model
{
    use HasFactory;

    protected $fillable = [
        'student_id',
        'image_path',
    ];

    public function student()
    {
        return $this->belongsTo(Student::class);
    }
}
