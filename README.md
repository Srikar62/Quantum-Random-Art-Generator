# Low-Poly Image Generator

This project transforms any input image into **low-poly art** using edge-aware point sampling and Delaunay triangulation. It uses a combination of classical image processing, custom sampling, and optional quantum randomness.

---

## 🚀 Features

* **Quantum or fallback randomness** for unique results
* **Edge-aware point sampling** (more triangles where detail exists)
* **Delaunay triangulation** to generate a mesh over sampled points
* **Adaptive Sobel + PIL edge fusion** for accurate edge detection
* **High‑quality rendering** using Pillow
* **Configurable parameters** for number of points, minimum distance, edge strength, and more
* **Automatic resizing** for performance

---

## 📂 Project Structure

```
lowpoly-art/
│-- lowpoly.py          # Main script
│-- requirements.txt    # Dependencies for easy installation
│-- examples/
│     └── monalisa.jpg  # Example input image
│-- output/
│     └── sample.png    # Example generated output
│-- README.md
```

project/
│-- lowpoly.py        # Main script (the code you provided)
│-- monalisa.jpg      # Example input image
│-- mona_lowpoly.png  # Output low‑poly artwork
│-- README.md

````

---

## 🧠 How It Works
### 1. **Quantum Seed Generation**
Attempts to fetch a 256‑bit seed using Qiskit & Aer simulator. Falls back to `os.urandom()` if unavailable.

### 2. **Edge Detection**
Uses:
- PIL’s `FIND_EDGES`
- Sobel gradient operator

These are blended to produce a robust edge map used for sampling.

### 3. **Edge‑Biased Sampling**
Custom dart‑throwing algorithm:
- Ensures minimum spacing between points
- Biases probability using edge magnitude
- Adds boundary points for clean edges

### 4. **Delaunay Triangulation**
Uses Matplotlib's Triangulation to compute mesh.
Color of each triangle = color of its centroid in the original image.

### 5. **Rendering**
Triangles are drawn using Pillow.

---

## 🛠️ Installation
Clone the repository:
```bash
git clone https://github.com/your-username/lowpoly-art.git
cd lowpoly-art
````

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Qiskit is optional — if you don't need quantum randomness, remove it from requirements.

---

## ▶️ How to Run

### Option 1 — Run using Python directly

```bash
python lowpoly.py --input examples/monalisa.jpg --output output/mona_lowpoly.png
```

### Option 2 — Modify the function call in `lowpoly.py`

```python
lowpoly_image(
    img_path="examples/monalisa.jpg",
    max_side=900,
    n_points=1400,
    min_dist=7,
    edge_enhance=True,
    show_preview=True,
    save_path="output/mona_lowpoly.png"
)
```

After running, the output image will appear in the `output/` folder.

---

## ⚙️ Parameters

| Parameter      | Description                            |
| -------------- | -------------------------------------- |
| `img_path`     | Input image path                       |
| `max_side`     | Scales image for speed (default 900px) |
| `n_points`     | Number of interior sample points       |
| `min_dist`     | Minimum spacing between sampled points |
| `edge_enhance` | Boosts edge influence                  |
| `show_preview` | Displays the output in matplotlib      |
| `save_path`    | Output filepath                        |

---

## 🖼 Example Output

**Input:** `monalisa.jpg`
**Output:** `mona_lowpoly.png`


## ⭐ Show Your Support

If you find this project helpful, please ⭐ the repository!
