"""Image-array authoring fields, corroborated by native reflected layer values.

NPlugImageArray_SElem exposes separate Py and Pxz sizes/offsets and a Py
rotation. Compiled Block_PyPxz_ids uses the selected top matrix and separate
side scale/height offset; Py dimensions must never be reused for Pxz.
"""


def descriptor_transform(layer, side=False):
    size = [layer['U06'], layer['U07']] if side else [layer['U02'], layer['U03']]
    offset = [layer['U08'], layer['U09']] if side else [layer['U04'], layer['U05']]
    if min(size) <= 0:
        raise ValueError('Image-array projection dimensions must be positive')
    return dict(scale=[1 / value for value in size],
                translation=[-value / dimension for value, dimension in zip(offset, size)],
                rotation=0 if side else layer['U10'])
