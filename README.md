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

# 3. Compilar incluyendo todos los archivos necesarios

## Opción que funciona

Ir a la carpeta `\Game3en1`

```shell
python -m PyInstaller --onefile --console --name "Game3en1" --icon="meme.jpg" --collect-all pygame --collect-all pytmx --add-data "menu;menu" --add-data "FlappyBird;FlappyBird" --add-data "Snake;Snake" --add-data "SpaceInvaders;SpaceInvaders" --add-data "data;data" --add-data "notificaciones;notificaciones" --add-data "meme.jpg;." --hidden-import=snake --hidden-import=flappy --hidden-import=SpaceInvaders --hidden-import=pytmx menu.py
```

# 4. Ver Ejecutable
En la carpeta `\Game3en1/dist` se puede ver el `Game3en1.exe`, la opcón --console permite correr el juego con la consola encendida (para debug).