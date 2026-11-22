"""Découpe les cœurs et le smiley du save the date (PNG transparents) et les efface du fond.

Usage : python3 outils/decor.py save-the-date.jpg decor
"""
import sys, json, numpy as np
from PIL import Image
src_path, out_dir = sys.argv[1], sys.argv[2]
src = Image.open(src_path).convert('RGB')
im = np.asarray(src).astype(np.float64)
H, W, _ = im.shape
R, G, B = im[..., 0], im[..., 1], im[..., 2]

def box(a, r):
    """Moyenne glissante carrée de rayon r (somme cumulée)."""
    p = np.pad(a, r, mode='edge')
    c = p.cumsum(0).cumsum(1)
    c = np.pad(c, ((1, 0), (1, 0)))
    k = 2 * r + 1
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)

boxes = {"coeur-haut": (137, 391, 213, 477), "coeur-bas": (88, 498, 181, 604), "smiley": (910, 302, 1044, 430)}
redness = np.clip((R - (G + B) / 2 - 8) / 45, 0, 1)
ink_any = redness > 0.05
base = im.copy()
meta = {}
for name, (x0, y0, x1, y1) in boxes.items():
    sl = (slice(y0, y1), slice(x0, x1))
    sub = im[sl]; red = redness[sl]
    ink = ink_any[sl]
    # masque élargi de 2 px pour l'estimation du papier
    m = ink.astype(float)
    for _ in range(2): m = np.maximum(m, box(m, 1) > 0)
    w = 1 - m
    bg = np.stack([box(sub[..., c] * w, 7) / np.maximum(box(w, 7), 1e-6) for c in range(3)], -1)
    # zones sans papier voisin (trop au centre d'un trait) : seconde passe plus large
    holes = box(w, 7) < 0.02
    if holes.any():
        bg2 = np.stack([box(sub[..., c] * w, 14) / np.maximum(box(w, 14), 1e-6) for c in range(3)], -1)
        bg[holes] = bg2[holes]
    # alpha : assombrissement du vert par rapport au papier, limité aux pixels rouges
    ink_g = 48.0
    a = np.clip((bg[..., 1] - sub[..., 1]) / (bg[..., 1] - ink_g), 0, 1) * np.clip(red * 3, 0, 1)
    a[a < 0.04] = 0
    # couleur « dé-mélangée » de l'encre
    with np.errstate(divide='ignore', invalid='ignore'):
        col = (sub - (1 - a[..., None]) * bg) / np.maximum(a[..., None], 1e-3)
    col = np.clip(np.nan_to_num(col), 0, 255)
    rgba = np.dstack([col, a * 255]).round().astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(f"{out_dir}/{name}.png", optimize=True)
    # fond : on remplace les pixels d'encre par le papier estimé + léger grain
    rng = np.random.default_rng(1)
    noise = rng.normal(0, 2.2, sub.shape)
    fill = np.clip(bg + noise, 0, 255)
    mm = (m > 0)[..., None]
    base[sl] = np.where(mm, fill, sub)
    meta[name] = {"left": x0 / W * 100, "top": y0 / H * 100, "width": (x1 - x0) / W * 100}
Image.fromarray(base.round().astype(np.uint8)).save(f"{out_dir}/save-the-date-fond.jpg", quality=90, optimize=True, progressive=True)
print(json.dumps(meta, indent=1))
