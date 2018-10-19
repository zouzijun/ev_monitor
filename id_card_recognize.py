# -*- coding: UTF-8 -*-
import cv2
import pytesseract
import numpy as np


def get_name_photo_area(path):
    img_raw = cv2.imread(path)
    img_gray = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
    img_blur = cv2.GaussianBlur(img_gray, (3, 3), 0)
    img_norm = np.zeros(img_blur.shape, dtype=np.uint8)
    cv2.normalize(img_blur, img_norm, 0, 255, cv2.NORM_MINMAX)
    ret, img_binary = cv2.threshold(img_norm, 80, 255, cv2.THRESH_BINARY)
    img_contours, cnts, hierarchy = cv2.findContours(img_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # img_out = cv2.drawContours(img_raw, cnts, -1, (0, 255, 0), 1)
    for i, v in enumerate(cnts):
        if i == 0:
            t = np.max(v, axis=0)
            [[x_max, y_max]] = np.max(v, axis=0)
            [[x_min, y_min]] = np.min(v, axis=0)
        else:
            [[x_max_temp, y_max_temp]] = np.max(v, axis=0)
            [[x_min_temp, y_min_temp]] = np.min(v, axis=0)
            if x_max_temp > x_max:
                x_max = x_max_temp
            if x_min_temp < x_min:
                x_min = x_min_temp
            if y_max_temp > y_max:
                y_max = y_max_temp
            if y_min_temp < y_min:
                y_min = y_min_temp
    img_card = img_norm[y_min:y_max, x_min:x_max]
    (card_rows, card_cols) = img_card.shape
    # Name area cut out
    name_area_row_b = int(card_rows * 0.11)
    name_area_row_e = int(card_rows * 0.22)
    name_area_col_b = int(card_cols * 0.1744)
    name_area_col_e = int(card_cols * 0.465)
    sub_img_name_gray = img_card[name_area_row_b:name_area_row_e, name_area_col_b:name_area_col_e]
    sub_img_name_norm = np.zeros(sub_img_name_gray.shape, dtype=np.uint8)
    cv2.normalize(sub_img_name_gray, sub_img_name_norm, 0, 255, cv2.NORM_MINMAX)
    ret, sub_img_name_binary = cv2.threshold(sub_img_name_norm, 115, 255, cv2.THRESH_BINARY)
    # Photo area cut out
    photo_area_row_b = int(card_rows * 0.148)
    photo_area_row_e = int(card_rows * 0.74)
    photo_area_col_b = int(card_cols * 0.628)
    photo_area_col_e = int(card_cols * 0.942)
    sub_img_photo_gray = img_card[photo_area_row_b:photo_area_row_e, photo_area_col_b:photo_area_col_e]
    sub_img_photo_norm = np.zeros(sub_img_photo_gray.shape, dtype=np.uint8)
    cv2.normalize(sub_img_photo_gray, sub_img_photo_norm, 0, 255, cv2.NORM_MINMAX)

    return sub_img_name_binary, sub_img_photo_norm


if __name__ == '__main__':
    pic_name, pic_photo = get_name_photo_area("./id_cards/zouzijun.jpg")
    str_name = pytesseract.image_to_string(pic_name, lang='chi_sim')
    print('The name is {0}.'.format(str_name))
    cv2.imshow('Photo', pic_photo)
    cv2.waitKey(0)
