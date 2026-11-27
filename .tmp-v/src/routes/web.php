<?php
use Illuminate\Support\Facades\Route;
Route::get('/hello/{name}', function ($name) {
    if ($name === 'admin') {
        return 'Hello boss';
    }
    return 'Hi ' . $name;
});
