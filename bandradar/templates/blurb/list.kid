<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../master.kid'">
    <head>
        <title>${title}</title>
    </head>
    <body>
        <p><img src="/static/images/date_add.png"/><a href="/blurbs/edit">Add a Blurb</a></p>  

	    ${grid(data)}
    </body>
</html>
