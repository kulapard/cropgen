#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from collections import defaultdict

TEMPLATE = """\
#!/bin/bash
#crop ver. 1
#В зависимости от количества кроп-зон, необходимо менять параметры запуска ffmpeg, чтобы было полное их соответствие.
set -u
source /root/conf.conf
#DIR=/mnt/share/cam/input
CROP=/mnt/share/crop

[ $CAMID{camid} ] || exit
ID=$CAMID{camid}
{vars}
while :; do
while [ `ls -p $DIR/$ID | grep -v / | wc -l` -ge 2 ]; do
[ -f /mnt/share/control/ch{camid}_{sboxid} ] || exit
FILE=$(ls -p $DIR/$ID | grep -v / | head -1)
NAME=$(echo $FILE | awk -F"\_" '{{print $3}}')
cp $DIR/$ID/$FILE /tmp/$FILE
{cmd}
if [ $? -ne 0 ]
then
echo "Error. Something is wrong. Moving bad file..."
test -d /mnt/share/cam/processed/$ID/BAD || mkdir -p /mnt/share/cam/processed/$ID/BAD ; mv $DIR/$ID/$FILE /mnt/share/cam/processed/$ID/BAD/
else
{mv}
{cp}
#rm /root/video/$ID/$FILE
test -d /mnt/share/cam/processed/$ID/Done || mkdir -p /mnt/share/cam/processed/$ID/Done ; mv $DIR/$ID/$FILE /mnt/share/cam/processed/$ID/Done/
fi
rm /tmp/$FILE
unset FILE
unset NAME
done
sleep 1
done
"""

CMD_TAMPLETE_BASE = """\
ffmpeg -i "/tmp/$FILE" -y -c:v libx264 -an -filter_complex "\\
{cmd_1}" \\
{cmd_2}\
"""
CMD_TAMPLETE_1 = "[0:v]crop=$CROP{index}[out{index}]"
CMD_TAMPLETE_2 = "-crf $CRF{index} -preset faster -r $R{index} -map [out{index}] /tmp$FOLDER{index}/$PREFIX{index}\_$NAME"

VARS_TEMPLATE = """\
FOLDER{index}=$CROP/input/$ID/{folder}; test -d $FOLDER{index} || mkdir -p $FOLDER{index}; test -d /tmp$FOLDER{index} || mkdir -p /tmp$FOLDER{index}
FOLDER100=$CROP/processed/$ID/{folder}; test -d $FOLDER100 || mkdir -p $FOLDER100
CROP{index}={crop}
PREFIX{index}={prefix}
CRF{index}={crf}
R{index}={r}"""

MV_TEMPLATE = "mv /tmp$FOLDER{index}/$PREFIX{index}\_$NAME $FOLDER{index}/$PREFIX{index}\_$NAME"
CP_TEMPLATE = "cp $FOLDER{index_from}/$PREFIX{index_from}\_$NAME $FOLDER{index_to}/$PREFIX{index_to}\_$NAME"


def gen_vars(crops):
    return '\n'.join([VARS_TEMPLATE.format(index=index, **crop) for index, crop in enumerate(crops, start=1)])


def gen_mv(sorted_crops):
    """
    Возвращает строку вида:
        mv /tmp$FOLDER3/$PREFIX3\_$NAME $FOLDER3/$PREFIX3\_$NAME
        mv /tmp$FOLDER6/$PREFIX6\_$NAME $FOLDER6/$PREFIX6\_$NAME
        mv /tmp$FOLDER1/$PREFIX1\_$NAME $FOLDER1/$PREFIX1\_$NAME
    """
    mv_list = []
    for crop, indexes in sorted_crops.iteritems():
        mv_list.append(MV_TEMPLATE.format(index=indexes[0]))
    return '\n'.join(mv_list)


def gen_cp(sorted_crops):
    """
    Возвращает строку вида:
        cp $FOLDER3/$PREFIX3\_$NAME $FOLDER4/$PREFIX4\_$NAME
        cp $FOLDER6/$PREFIX6\_$NAME $FOLDER7/$PREFIX7\_$NAME
        cp $FOLDER1/$PREFIX1\_$NAME $FOLDER2/$PREFIX2\_$NAME
        cp $FOLDER1/$PREFIX1\_$NAME $FOLDER5/$PREFIX5\_$NAME
    """
    cp_list = []
    for crop, indexes in sorted_crops.iteritems():
        original, copies = indexes[0], indexes[1:]
        for index in copies:
            cp_list.append(CP_TEMPLATE.format(index_from=original, index_to=index))
    return '\n'.join(cp_list)


def gen_cmd(sorted_crops):
    """
    Возвращает строку вида:
        ffmpeg -i "/tmp/$FILE" -y -c:v libx264 -an -filter_complex "\
        [0:v]crop=$CROP3[out3];\
        [0:v]crop=$CROP6[out6];\
        [0:v]crop=$CROP1[out1]" \
        -crf $CRF3 -preset faster -r $R3 -map [out3] /tmp$FOLDER3/$PREFIX3\_$NAME \
        -crf $CRF6 -preset faster -r $R6 -map [out6] /tmp$FOLDER6/$PREFIX6\_$NAME \
        -crf $CRF1 -preset faster -r $R1 -map [out1] /tmp$FOLDER1/$PREFIX1\_$NAME
    """
    cmd_1_list = []
    cmd_2_list = []
    for crop, indexes in sorted_crops.iteritems():
        cmd_1_list.append(CMD_TAMPLETE_1.format(index=indexes[0]))
        cmd_2_list.append(CMD_TAMPLETE_2.format(index=indexes[0]))

    cmd_1 = ';\\\n'.join(cmd_1_list)
    cmd_2 = ' \\\n'.join(cmd_2_list)
    return CMD_TAMPLETE_BASE.format(cmd_1=cmd_1, cmd_2=cmd_2)


def sort_crops(crops):
    """
    Пример crops:
    [
        {
            'prefix': '106_472_580_400_290',
            'r': '3',
            'crf': '25',
            'folder': 'stanS1_roll_on_clips',
            'crop': '400:290:472:580'
        },
        ...
    ]

    Возвращает словарь вида:
    {('400:290:472:580', '25', '3'): [1, 2]}
    где в списке первый элемент - оригинал, остальные - копии
    """
    sorted_crops = defaultdict(list)
    for index, crop in enumerate(crops, start=1):
        unique_key = (crop['crop'], crop['crf'], crop['r'])
        sorted_crops[unique_key].append(index)
    return sorted_crops


def parse_config(path):
    """
    Парсит текстовый файл конфига и возвращает словарь с настройками для генерации кроп-скрипта
    """
    config = {
        'crops': [],
    }
    with open(path, 'r') as f:
        for line in f:
            line = line.rstrip('\n;')
            if not line:
                # Пропускаем пустые строки
                continue

            line_vars = {}
            for kv in line.split(';'):
                k, v = kv.split(':', 1)
                k = k.strip()
                v = v.strip()
                line_vars[k] = v

            if 'crop' in line_vars:
                config['crops'].append(line_vars)
            else:
                config.update(line_vars)

    return config


def gen_script(config):
    """
    Основная функция для генерации кроп-скрипта
    """
    vars = gen_vars(crops=config['crops'])
    sorted_crops = sort_crops(crops=config['crops'])
    cmd = gen_cmd(sorted_crops)
    mv = gen_mv(sorted_crops)
    cp = gen_cp(sorted_crops)

    return TEMPLATE.format(vars=vars, cmd=cmd, mv=mv, cp=cp, **config)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='path to config file (default: ./config.txt)', default='./config.txt')
    args = parser.parse_args()

    config = parse_config(args.config)
    print(gen_script(config))
