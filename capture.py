#!/usr/bin/env python

import yaml
import keyboard
import subprocess
import threading
from os import remove, path
from datetime import datetime
from tempfile import NamedTemporaryFile
from pywinauto.application import Application

with open('config.yml', 'r', encoding='utf-8') as file:
  CONFIG = yaml.safe_load(file)['japaricapture']


def process_image(window, number):
  image = window.capture_as_image()
  print(f'{number}: captured')

  width, height = image.size
  cropbound = CONFIG['capture']['crop_bound']
  image = image.crop((cropbound[0], cropbound[1], width - cropbound[2], height - cropbound[3]))

  with NamedTemporaryFile(suffix='.png', delete=False) as file:
    image.save(file)
    print(f'{number}: saved')

    output_filename = 'capture_' + datetime.now().strftime('%Y%m%d%H%M%S')
    filecount = 0

    while True:
      output_filepath = path.join(CONFIG['capture']['output'], output_filename + str(filecount).zfill(2))

      if not path.exists(output_filepath):
        break

      filecount = filecount + 1

    # image.save(f'{output_filepath}_base.png')

    complete_process = subprocess.run(
        [CONFIG['external']['path'],
         f'-i {file.name}',
         f'-o {output_filepath}.jpg',
         '-m scale',
         '-w 2880',
         '-p gpu',
         '-q 95',
         f'--model_dir models/{CONFIG["external"]["model"]}'], encoding='utf-8', shell=True, stdout=subprocess.DEVNULL)

    if complete_process.returncode == 0:
      print(f'{number}: transformed: {output_filename}.jpg')
    else:
      print(f'{number}: failed to transform! code: {complete_process.returncode}')


if __name__ == '__main__':
  app = Application().connect(path=CONFIG['target']['path'])
  window = app.top_window()
  image_number = 0

  def print_pressed_keys(e):
    global image_number
    if not window.is_active() or CONFIG['capture']['trigger_key'] not in keyboard._pressed_events:
      return

    thread = threading.Thread(target=process_image, args=(window, image_number))
    thread.start()
    image_number = image_number + 1

  keyboard.hook(print_pressed_keys)
  keyboard.wait()
