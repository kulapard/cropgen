# Генератор кропалки видюшек
Настройки кропалки хранятся в `config.py`

Запускаем генератор скрипта так:
```bash
python cropgen.py --config config.txt > crop_script.sh
```
На выходе получаем желанный скрипт (`crop_script.sh`).

Пример конфига:
```
camid: 19;
sboxid: 0000;
crop: 400:290:472:580; prefix: 106_472_580_400_290; crf: 25; r: 3; folder: stanS1_roll_on_clips;
crop: 400:290:472:580; prefix: 106_472_580_400_290; crf: 25; r: 3; folder: stanS1_roll_far_clips;
crop: 270:340:200:210; prefix: 110_200_210_270_340; crf: 25; r: 3; folder: stanS1_perenaladka_move_clips;
```

Особенности конфига:
- `;` в конце опциональные
- строчкек с `crop: ...` может быть несколько
- переменные в остальных строчках должны быть уникальны в рамках конфига