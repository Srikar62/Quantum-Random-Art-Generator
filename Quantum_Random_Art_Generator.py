import os, math
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
import matplotlib.pyplot as plt
import matplotlib.tri as mtri

def quantum_seed_256():
    try:
        from qiskit import QuantumCircuit, transpile
        from qiskit_aer import AerSimulator
        sim = AerSimulator()
        qc = QuantumCircuit(256, 256)
        qc.h(range(256)); qc.measure(range(256), range(256))
        tqc = transpile(qc, sim, optimization_level=0)
        res = sim.run(tqc, shots=1, memory=True).result()
        bits = res.get_memory()[0]
        return int(bits, 2)
    except Exception:
        return int.from_bytes(os.urandom(32), "big")

RNG = np.random.default_rng(quantum_seed_256())

def to_np(img):
    return np.asarray(img)

def from_np(arr):
    return Image.fromarray(arr)

def resize_for_speed(img, max_side=900):
    w, h = img.size
    scale = min(1.0, max_side / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w*scale), int(h*scale)), Image.Resampling.LANCZOS)
    return img

def sobel_edges(img_gray_np):
    g = img_gray_np.astype(np.float32) / 255.0
    Kx = np.array([[1,0,-1],[2,0,-2],[1,0,-1]], dtype=np.float32)
    Ky = np.array([[1,2,1],[0,0,0],[-1,-2,-1]], dtype=np.float32)
 
    gp = np.pad(g, 1, mode="edge")
    Gx = (gp[:-2,:-2]*Kx[0,0] + gp[:-2,1:-1]*Kx[0,1] + gp[:-2,2:]*Kx[0,2] +
          gp[1:-1,:-2]*Kx[1,0] + gp[1:-1,1:-1]*Kx[1,1] + gp[1:-1,2:]*Kx[1,2] +
          gp[2:, :-2]*Kx[2,0] + gp[2:, 1:-1]*Kx[2,1] + gp[2:, 2:]*Kx[2,2])
    Gy = (gp[:-2,:-2]*Ky[0,0] + gp[:-2,1:-1]*Ky[0,1] + gp[:-2,2:]*Ky[0,2] +
          gp[1:-1,:-2]*Ky[1,0] + gp[1:-1,1:-1]*Ky[1,1] + gp[1:-1,2:]*Ky[1,2] +
          gp[2:, :-2]*Ky[2,0] + gp[2:, 1:-1]*Ky[2,1] + gp[2:, 2:]*Ky[2,2])
    mag = np.hypot(Gx, Gy)
    mag /= (mag.max() + 1e-8)
    return mag

def sample_points_edge_biased(w, h, edge_map, n_points=1200, min_dist=8, border_pts=True):
    """
    Edge-aware dart throwing:
    - More samples where edges are strong
    - Enforces a soft minimum distance using grid hashing
    """
    pts = []
    if border_pts:
        n_b = 50
        xs = np.linspace(0, w-1, n_b, dtype=np.float32)
        ys = np.linspace(0, h-1, n_b, dtype=np.float32)
        for x in xs:
            pts.append((x, 0)); pts.append((x, h-1))
        for y in ys:
            pts.append((0, y)); pts.append((w-1, y))

    cell = max(1, int(min_dist))
    grid_w, grid_h = (w + cell - 1)//cell, (h + cell - 1)//cell
    grid = [[[] for _ in range(grid_w)] for __ in range(grid_h)]

    def can_place(x, y):
        gx, gy = int(x)//cell, int(y)//cell
        for yy in range(max(0, gy-2), min(grid_h, gy+3)):
            for xx in range(max(0, gx-2), min(grid_w, gx+3)):
                for (px, py) in grid[yy][xx]:
                    if (px-x)**2 + (py-y)**2 < (min_dist**2):
                        return False
        return True

    def put(x, y):
        pts.append((x, y))
        grid[int(y)//cell][int(x)//cell].append((x, y))

    
    edge_pow = 1.25  
    target = n_points + len(pts)
    attempts = 0
    while len(pts) < target and attempts < target*50:
        attempts += 1
        x = RNG.random() * (w-1)
        y = RNG.random() * (h-1)
        e = edge_map[int(y), int(x)]
        p = (0.25 + 0.75 * (e ** edge_pow))  
        if RNG.random() < p and can_place(x, y):
            put(x, y)

    return np.array(pts, dtype=np.float32)

def triangulate_and_paint(img_rgb_np, pts, show_edges=False, line_alpha=0.0):
    h, w, _ = img_rgb_np.shape
    tri = mtri.Triangulation(pts[:,0], pts[:,1])
    
    out = Image.new("RGB", (w, h), (0,0,0))
    draw = ImageDraw.Draw(out)

    for tri_ix in tri.triangles:
        poly = pts[tri_ix]  # (3,2)
        cx = np.clip(np.mean(poly[:,0]), 0, w-1)
        cy = np.clip(np.mean(poly[:,1]), 0, h-1)
        c = tuple(map(int, img_rgb_np[int(cy), int(cx), :]))
        xy = [(float(poly[0,0]), float(poly[0,1])),
              (float(poly[1,0]), float(poly[1,1])),
              (float(poly[2,0]), float(poly[2,1]))]
        draw.polygon(xy, fill=c)
        if show_edges and line_alpha > 0:
            la = int(255*line_alpha)
            draw.line([xy[0], xy[1], xy[2], xy[0]], fill=(0,0,0,la), width=1)

    return out

def lowpoly_image(
    img_path,
    max_side=900,
    n_points=1200,
    min_dist=8,
    edge_enhance=True,
    show_preview=True,
    save_path="lowpoly.png"
):
    img = Image.open(img_path).convert("RGB")
    img = resize_for_speed(img, max_side=max_side)
    w, h = img.size
    gray = img.convert("L")

    
    pil_edge = np.asarray(gray.filter(ImageFilter.FIND_EDGES), dtype=np.float32)/255.0
    sob_edge = sobel_edges(np.asarray(gray))
    edge_map = np.clip(0.5*pil_edge + 0.5*sob_edge, 0, 1)
    if edge_enhance:
        edge_map = np.clip(edge_map**0.9, 0, 1) 

    pts = sample_points_edge_biased(w, h, edge_map, n_points=n_points, min_dist=min_dist, border_pts=True)
    out = triangulate_and_paint(np.asarray(img), pts, show_edges=False)

    out.save(save_path, "PNG")
    if show_preview:
        plt.figure(figsize=(8, 8*h/w))
        plt.imshow(out); plt.axis("off"); plt.show()
    print(f"✓ Saved low-poly art to {save_path} (size: {w}×{h}, points: {len(pts)})")

lowpoly_image(
    img_path="examples/monalisa.jpg",   
    max_side=900,              
    n_points=1400,             
    min_dist=7,                
    edge_enhance=True,
    show_preview=True,
    save_path="output/mona_lowpoly.png"

)
