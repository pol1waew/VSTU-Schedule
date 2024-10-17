<?php 
    $connection = new SQLite3("db.sqlite3");
    if (!$connection) {
        echo $connection->lastErrorMsg();
    }

    $request = "select time_slot_id from api_eventholding;";

    $result = $connection->query($request);
    var_dump($result);

    return;
    while ($data = $result->fetchArray(SQLITE3_ASSOC)) {
        echo "<tr>";
        echo "<td>" . $data["time_slot_id"] . "</td>";
        echo "<td>" . "</td>";
        echo "<td>" . "</td>";
        echo "<td>" . "</td>";
        echo "</tr";
    }

    $connection->close();
?>