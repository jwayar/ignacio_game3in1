# 0. instalar dependencias

```shell
pip install pyinstaller
pip install pygame
pip install pytmx
```

# 1. Limpiar compilaciones anteriores

```shell
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
```

# 3. Conpilar incluyendo todos los archivos necesarios

# 3.3 Opción que funciona

```shell
python -m PyInstaller --onefile --console --name "Game3en1" --icon="meme.jpg" --collect-all pygame --collect-all pytmx --add-data "menu;menu" --add-data "FlappyBird;FlappyBird" --add-data "Snake;Snake" --add-data "SpaceInvaders;SpaceInvaders" --add-data "data;data" --add-data "notificaciones;notificaciones" --add-data "meme.jpg;." --hidden-import=snake --hidden-import=flappy --hidden-import=SpaceInvaders --hidden-import=pytmx menu.py
```

# Ejecutable
En la carpeta
```shell
Game3en1/dist
```