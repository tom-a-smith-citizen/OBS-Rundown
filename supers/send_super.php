<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $text = file_get_contents('php://input');
    file_put_contents('super.txt', $text);
    echo "Updated";
}