<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../master.kid'">

<head>
    <title>BandRadar - Edit an event</title>
</head>

<body>
  <div class="content">
    <h2>Edit an event</h2>

    <script type="text/javascript">
        focusOnLoad("event_name")
    </script>

    ${event_form.display(form_vals, action="/events/save")}
 
 </div>
</body>
</html>
