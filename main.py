from PIL import ImageGrab
from pynput import keyboard
import win32gui
import glob
import re
import cv2
import numpy as np
import sqlite3

PICKABLE_TERMS = 5
DB_NAME = 'offer_recommender.db'
SS_PATH = './screenshot.png'
DEBUG = True
RECT_PADDING = 2

class ButtonsCountException(Exception):
    pass
class TopRarityException(Exception):
    pass

def detect_terms(mat_img):
    detected_terms = []

    templates = glob.glob('./buttons/term_*.jpg')
    templates.extend(glob.glob('./buttons/term_*.png'))
    if DEBUG:
        print(templates)

    for t in templates:
        t_img = cv2.imread(t)
        match = re.search(r'term_(.*)\.(jpg|JPG|png)', t)
        button_name = match.group(1)

        # スクリーンショットからテンプレートを検出
        result = cv2.matchTemplate(mat_img, t_img, cv2.TM_CCORR_NORMED)

        minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(result)
        tmp_height, tmp_width = t_img.shape[:2]

        if DEBUG:
            print(t)
            print(maxVal)

        if maxVal > 0.995:
            print('ボタン{}存在'.format(button_name))
            print('一致度: {}'.format(maxVal))
            top_left = (maxLoc[0] - RECT_PADDING, maxLoc[1] - RECT_PADDING)
            bottom_right = (maxLoc[0] + tmp_width + RECT_PADDING, maxLoc[1] + tmp_height + RECT_PADDING)
            cv2.rectangle(mat_img, top_left, bottom_right, (255, 255, 0), 2)
            detected_terms.append(button_name)

    cv2.imwrite('detected_button.jpg', mat_img)
    print('検出したボタンを強調し、保存しました')
    print('ボタン個数: {}'.format(len(detected_terms)))

    if len(detected_terms) != PICKABLE_TERMS:
        raise ButtonsCountException('Buttons count should be {} but actually {}.'.format(PICKABLE_TERMS, len(detected_terms)))

    return detected_terms


def screen_shot():
    # 最前面のウィンドウのスクショを取得する
    handle = win32gui.GetForegroundWindow() # 最前面のウィンドウハンドルを取得
    rect = win32gui.GetWindowRect(handle)   # ウィンドウの位置を取得
    try:
        screenshot = ImageGrab.grab()
        screenshot.putalpha(255)
        cropped_screenshot = screenshot.crop(rect)
        cropped_screenshot.save(SS_PATH)
    except Exception as e:
        print(e)

    return cropped_screenshot

def unpack_mono_list(l):
    return [e[0] for e in l]

def search_picks(detected_terms):
    pickable_data = {}
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    if 'sperior_elite' in detected_terms:
        raise TopRarityException('rank 6 characters cannot be searched.')

    query = 'select name, display_name from term where ' + 'name=? or ' * len(detected_terms)
    query = query[:-4] # delete last ' or '

    cursor.execute(query, tuple(detected_terms))
    res = cursor.fetchall()
    terms = []
    for r in res:
        terms.append({
            'name': r[0],
            'display_name': r[1]
        })

    s1Range = list(range(-2, PICKABLE_TERMS - 2))
    s1Range.remove(-1)
    
    pickable_data = []

    for s1 in s1Range:
        for s2 in range(s1 + 1, PICKABLE_TERMS - 1):
            for s3 in range(s2 + 1, PICKABLE_TERMS):
                query = 'select display_name from character c join junction j on c.name == j.character_name where j.term_name = ?'
                low_rarity_query = query + ' and c.rarity = 3'
                query += ' and c.rarity > 3'
                query += ' order by c.rarity asc, c.belongs asc'

                if DEBUG:
                    print('terms: ')
                    if s1 >= 0:
                        print('  ' + terms[s1]['name'])
                    if s2 >= 0:
                        print('  ' + terms[s2]['name'])
                    if s3 >= 0:
                        print('  ' + terms[s3]['name'])

                cursor.execute(query, (terms[s3]['name'],))
                high_rarity = set(unpack_mono_list(cursor.fetchall()))
                cursor.execute(low_rarity_query, (terms[s3]['name'],))
                low_rarity = set(unpack_mono_list(cursor.fetchall()))

                if s1 >= 0:
                    cursor.execute(query, (terms[s1]['name'],))
                    high_rarity = high_rarity & set(unpack_mono_list(cursor.fetchall()))
                    cursor.execute(low_rarity_query, (terms[s1]['name'],))
                    low_rarity = low_rarity & set(unpack_mono_list(cursor.fetchall()))
                if s2 >= 0:
                    cursor.execute(query, (terms[s2]['name'],))
                    high_rarity = high_rarity & set(unpack_mono_list(cursor.fetchall()))
                    cursor.execute(low_rarity_query, (terms[s2]['name'],))
                    low_rarity = low_rarity & set(unpack_mono_list(cursor.fetchall()))

                if DEBUG:
                    print('high_rarity: ')
                    for h in high_rarity:
                        print('  {}'.format(h))
                    print('low_rarity: ')
                    for l in low_rarity:
                        print('  {}'.format(l))

                if len(low_rarity) == 0 and len(high_rarity) > 0:
                    if DEBUG:
                        print('Good selection was found!')
                    pickable_obj = {
                        'terms': [],
                        'characters': []
                    }
                    if s1 >= 0:
                        pickable_obj['terms'].append(terms[s1]['display_name'])
                    if s2 >= 0:
                        pickable_obj['terms'].append(terms[s2]['display_name'])
                    if s3 >= 0:
                        pickable_obj['terms'].append(terms[s3]['display_name'])

                    for hr in high_rarity:
                        pickable_obj['characters'].append(hr)

                    pickable_data.append(pickable_obj)

    connection.close()

    return pickable_data

def press(key):
    try:
        if key == keyboard.Key.esc:
            print('終了')
            return False
        elif key != keyboard.Key.print_screen:
            if DEBUG:
                print('アルファベット {0} が押されました'.format(key.char))
        else:
            print('スクリーンショットを保存します')
            screen_shot()
            
            print('ボタン位置を検出します')
            mat_img = cv2.imread(SS_PATH)
            try:
                detected_terms = detect_terms(mat_img)
            except(Exception) as e:
                print('failed to detect buttons')
                print(e)

            print('該当キャラクターの検索を開始します')
            try:
                pickable_data = search_picks(detected_terms)
            except(Exception) as e:
                print('failed to search pickable characters.')
                print(e)

            if DEBUG:
                print(pickable_data)

            if len(pickable_data) > 0:
                print('条件に該当するキャラクターが見つかりました！')
                for p in pickable_data:
                    print(', '.join(p['terms']) + '\n=> ')
                    for c in p['characters']:
                        print('   ' + c)
            else:
                print('条件に該当するキャラクターは存在しませんでした')

            print('完了')

            return False
    except:
        pass

with keyboard.Listener(on_press=press) as listener:
    print('入力受付開始')
    listener.join()
