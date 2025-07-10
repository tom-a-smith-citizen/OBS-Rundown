<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $text = trim($_POST['text'] ?? '');
    file_put_contents('super.txt', $text);
    echo "Updated";
}
