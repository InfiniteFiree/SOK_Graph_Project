# SOK_Graph_Project
### Project for the visualization of graphs in space, utilizing plug-ins for the main functions of the app.

## Team 8 - members
- SV 28/2023	Marko	Đorđević
- SV 79/2023	Aleksa	Nenadović
- SV 85/2024	Lana	Vuković
- SV 82/2024	Luka	Berić

## How to run flask app:
### - first, run: 

```shell
python -m venv venv
```

### then:

```shell
.\venv\Scripts\activate
```

### both while inside the SOK_Graph_Project/flask folder.

### - then, when running for the first time, use:

```shell
pip install -r requirements.txt
```

### and then:

```shell
set FLASK_APP=app.py
```

### - finally, whenever you want the app to run, use 

```shell
flask run
``` 

### while inside the flask folder.


## CLI Commands:

### Node:
```shell
create_node id={int} attr1={int,float,date,str} attr2=...
edit_node id={int} attr1={int,float,date,str} attr2=...
delete_node id={int}
```

### Edge:
```shell
create_edge n1={int} n2={int}
delete_edge n1={int} n2={int}
```

### Search and Filter:
```shell
search {int,float,date,str}
filter attr={int,float,date,str}
```
