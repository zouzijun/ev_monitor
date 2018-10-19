# -*- coding: UTF-8 -*-
import cv2
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

IMG_MIN_SIZE = 50
PIX_TOLERANCE = 10


def calc_camera_offset(pre, aft):
    rows_pre = pre.shape[0]
    cols_pre = pre.shape[1]
    rows_aft = aft.shape[0]
    cols_aft = aft.shape[1]
    if rows_pre > IMG_MIN_SIZE and cols_pre > IMG_MIN_SIZE and rows_aft > IMG_MIN_SIZE and cols_aft > IMG_MIN_SIZE:
        template = pre[rows_pre // 2 - IMG_MIN_SIZE // 2:rows_pre // 2 + IMG_MIN_SIZE // 2,
                       cols_pre // 2 - IMG_MIN_SIZE // 2:cols_pre // 2 + IMG_MIN_SIZE // 2]
        res = cv2.matchTemplate(aft, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        offset_row = - (max_loc[0] + IMG_MIN_SIZE // 2 - rows_aft // 2)
        offset_col = - (max_loc[1] + IMG_MIN_SIZE // 2 - cols_aft // 2)
        print(min_val, max_val, min_loc, max_loc)
        # plt.colorbar(plt.imshow(res, cmap=mpl.cm.hot))
        # plt.show()
        return offset_row, offset_col
    else:
        print("Image size too small.")
        return 0, 0


def get_overlap_area(pre, aft, offset_row, offset_col):
    # Get overlaped area for pre image
    pre_begin_row = offset_row if offset_row >= 0 else 0
    pre_end_row = pre.shape[0] if offset_row >= 0 else pre.shape[0] + offset_row
    pre_begin_col = offset_col if offset_col >= 0 else 0
    pre_end_col = pre.shape[1] if offset_col >= 0 else pre.shape[1] + offset_col
    pre_overlap = pre[pre_begin_row:pre_end_row, pre_begin_col:pre_end_col]
    # Get overlaped area for aft image
    aft_begin_row = 0 if offset_row >= 0 else -offset_row
    aft_end_row = aft.shape[0] - offset_row if offset_row >= 0 else aft.shape[0]
    aft_begin_col = 0 if offset_col >= 0 else -offset_col
    aft_end_col = aft.shape[1] - offset_col if offset_col >= 0 else aft.shape[1]
    aft_overlap = aft[aft_begin_row:aft_end_row, aft_begin_col:aft_end_col]
    return pre_overlap, aft_overlap


def get_image_diff(pre, aft):
    pre_norm = np.zeros((pre.shape[0], aft.shape[1]), dtype=np.uint8)
    aft_norm = np.zeros((aft.shape[0], aft.shape[1]), dtype=np.uint8)
    cv2.normalize(pre, pre_norm, 0, 255, cv2.NORM_MINMAX)
    cv2.normalize(aft, aft_norm, 0, 255, cv2.NORM_MINMAX)
    pre_blur = cv2.GaussianBlur(pre_norm, (9, 9), 0)
    aft_blur = cv2.GaussianBlur(aft_norm, (9, 9), 0)
    (rows, cols) = aft_norm.shape
    # Diff mat and diff ratio
    diff_mat = np.zeros((rows, cols), dtype=np.float32)
    diff_count = 0
    for i in range(rows):
        for j in range(cols):
            diff = abs(int(aft_blur[i][j]) - int(pre_blur[i][j]))
            if diff > PIX_TOLERANCE:
                diff_count += 1
                diff_mat[i][j] = diff / 255.0
    return diff_count / (rows * cols), diff_mat


if __name__ == '__main__':
    # Read image and gray scaling
    pre_raw = cv2.imread("./img_compare/pre.jpg")
    pre_gray = cv2.cvtColor(pre_raw, cv2.COLOR_BGR2GRAY)
    aft_raw = cv2.imread("./img_compare/aft.jpg")
    aft_gray = cv2.cvtColor(aft_raw, cv2.COLOR_BGR2GRAY)

    # Get camera moving direction
    cam_offset_row, cam_offset_col = calc_camera_offset(pre_gray, aft_gray)
    # Get overlaped area
    pre_overlap_img, aft_overlap_img = get_overlap_area(pre_gray, aft_gray, cam_offset_row, cam_offset_col)
    # Compare
    diff_ratio, diff_graph = get_image_diff(pre_overlap_img, aft_overlap_img)
    # Show result
    plt.colorbar(plt.imshow(diff_graph, cmap=mpl.cm.hot))
    plt.show()
    print(diff_ratio)
