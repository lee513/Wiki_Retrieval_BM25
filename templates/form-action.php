<?php
  $color = $_POST['color']; 
?>
<!doctype html>
<html lang="ko">
  <head>
  <meta charset="utf-8">
    <title>HTML</title>
    <style>
      * {
        font-size: 16px;
        font-family: Consolas, sans-serif;
      }
    </style>
  </head>
  <body>
    <h1>Submitted</h1>
    <p>Your color is <?php echo $color ?>.</p>
  </body>
</html>