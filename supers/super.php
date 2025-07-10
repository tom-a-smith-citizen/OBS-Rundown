<?php
header('Content-Type: text/event-stream');
header('Cache-Control: no-cache');

$last = '';
while (true) {
    clearstatcache();
    $data = trim(@file_get_contents('super.txt'));
    if ($data !== $last) {
        echo "data: $data\n\n";
        ob_flush();
        flush();
        $last = $data;
    }
    sleep(1);
}
