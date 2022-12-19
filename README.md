# TikiTok

To start the database and services run:
```shell
docker compose up --build
```
To upload a sample video with title `title` run:
```shell
curl -F "file=@{path to video}" http://localhost:8001/upload/{title}
```
e.g.
```shell
curl -F "file=@/Downloads/movie.mp4" http://localhost:8001/upload/IronMan
```