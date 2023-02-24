INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Index</title>
  <script>
    function launch(el, ev) {
        ev.preventDefault();
        slides = window.open(el.href, "", "%(size)s");
    }
  </script>
</head>
<body>
  <ul>
%(items)s
  </ul>
</body>
</html>
"""

ITEM_TEMPLATE = """
    <li><a href="%(file)s" onclick="launch(this, event)">%(framework)s</a></li>
"""
